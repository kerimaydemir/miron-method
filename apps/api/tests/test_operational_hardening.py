from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app
from app.observability import redact_sensitive


def test_security_headers_correlation_and_metrics() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health/live")
        metrics = client.get("/metrics")
    UUID(response.headers["x-correlation-id"])
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "miron_baba_ai_http_requests_total" in metrics.text
    assert "/health/live" in metrics.text


def test_invalid_correlation_and_oversized_body_fail_closed() -> None:
    with TestClient(app) as client:
        invalid = client.get("/api/v1/health/live", headers={"X-Correlation-ID": "not-a-uuid"})
        oversized = client.post(
            "/api/v1/scans",
            headers={
                "Idempotency-Key": "oversized-0001",
                "Content-Length": "1048577",
            },
            content=b"{}",
        )
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "INVALID_CORRELATION_ID"
    assert invalid.headers["content-type"].startswith("application/problem+json")
    assert oversized.status_code == 413
    assert oversized.json()["code"] == "REQUEST_TOO_LARGE"


def test_sensitive_values_are_recursively_redacted() -> None:
    source = {
        "authorization": "Bearer raw-secret",
        "nested": {"api_key": "raw-key", "safe": "visible"},
        "items": [{"password": "raw-password"}],
    }
    redacted = redact_sensitive(source)
    assert "raw-secret" not in str(redacted)
    assert "raw-key" not in str(redacted)
    assert "raw-password" not in str(redacted)
    assert redacted["nested"]["safe"] == "visible"
