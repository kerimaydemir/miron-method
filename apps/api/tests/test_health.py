from fastapi.testclient import TestClient

from app.main import app


def test_health_ready_uses_canonical_product_name() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["product"] == "MİRON BABA AI"


def test_auto_coupon_readiness_fails_closed_without_live_odds_and_deep_stages() -> None:
    with TestClient(app) as client:
        readiness = client.get("/api/v1/auto-coupons/readiness")
        create = client.post(
            "/api/v1/auto-coupons",
            headers={"Idempotency-Key": "fail-closed-test-001"},
        )

    assert readiness.status_code == 200
    assert readiness.json()["ready"] is False
    assert "AUTO_COUPON_LIVE_MARKET_REQUIRED" in readiness.json()["blockers"]
    assert "AUTO_COUPON_DEEP_DATA_REQUIRED" in readiness.json()["blockers"]
    assert "AUTO_COUPON_DEEP_ANALYSIS_NOT_READY" in readiness.json()["blockers"]
    assert create.status_code == 409
    assert create.json()["detail"]["code"] == "AUTO_COUPON_LIVE_MARKET_REQUIRED"
