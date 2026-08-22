from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.scans import scan_service
from app.main import app


def test_scan_returns_three_dates_ranked_candidates_and_replays() -> None:
    original_clock = scan_service.clock
    scan_service.clock = lambda: datetime(2026, 8, 22, 9, 0, tzinfo=UTC)
    try:
        with TestClient(app) as client:
            headers = {"Idempotency-Key": "scan-test-0001"}
            first = client.post(
                "/api/v1/scans",
                json={"timezone": "Europe/Istanbul", "ui_config_version": "dashboard.v1"},
                headers=headers,
            )
            replay = client.post(
                "/api/v1/scans",
                json={"timezone": "Europe/Istanbul", "ui_config_version": "dashboard.v1"},
                headers=headers,
            )
    finally:
        scan_service.clock = original_clock
    assert first.status_code == 201
    assert first.json()["local_dates"] == ["2026-08-22", "2026-08-23", "2026-08-24"]
    assert len(first.json()["candidates"]) == 4
    assert (
        first.json()["candidates"][0]["worthwhile_score"]
        >= first.json()["candidates"][1]["worthwhile_score"]
    )
    assert first.json()["scan_id"] == replay.json()["scan_id"]
