import hashlib
import json
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.analysis_runs import service
from app.api.post_match import service as post_match_service
from app.infrastructure.mock_fixture_provider import FIXTURES
from app.main import app


def test_full_mock_analysis_chief_probability_and_immutable_replay() -> None:
    original_clock = service.clock
    service.clock = lambda: datetime(2026, 8, 22, 8, 0, tzinfo=UTC)
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/analysis-runs",
                headers={"Idempotency-Key": "analysis-test-0001"},
                json={"fixture_id": str(FIXTURES[0].id)},
            )
            run_id = response.json()["run_id"]
            locked = client.post(f"/api/v1/analysis-runs/{run_id}/lock")
            replay = client.post(f"/api/v1/analysis-runs/{run_id}/lock")
            lock_id = locked.json()["lock_id"]
            lock_view = client.get(f"/api/v1/prediction-locks/{lock_id}")
            exported_json = client.get(f"/api/v1/prediction-locks/{lock_id}/export.json")
            exported_markdown = client.get(f"/api/v1/prediction-locks/{lock_id}/export.md")
    finally:
        service.clock = original_clock
    assert response.status_code == 201
    assert len(response.json()["stages"]) == 31
    assert (
        sum(
            float(item["probability"])
            for item in response.json()["forecast"]["outcome_probabilities"]
        )
        == 1.0
    )
    assert locked.json()["state"] == "LOCKED"
    assert len(locked.json()["lock_sha256"]) == 64
    assert replay.json()["lock_sha256"] == locked.json()["lock_sha256"]
    assert lock_view.status_code == 200
    assert exported_json.status_code == 200
    assert exported_json.json() == lock_view.json()
    assert exported_markdown.status_code == 200
    assert exported_markdown.headers["content-type"].startswith("text/markdown")
    assert locked.json()["lock_sha256"] in exported_markdown.text

    manifest = lock_view.json()["manifest"]
    canonical = json.dumps(
        manifest,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert hashlib.sha256(canonical.encode()).hexdigest() == locked.json()["lock_sha256"]


def test_post_match_api_keeps_pre_match_manifest_immutable() -> None:
    original_analysis_clock = service.clock
    original_post_match_clock = post_match_service.clock
    service.clock = lambda: datetime(2026, 8, 22, 8, 0, tzinfo=UTC)
    try:
        with TestClient(app) as client:
            run = client.post(
                "/api/v1/analysis-runs",
                headers={"Idempotency-Key": "post-match-api-0001"},
                json={"fixture_id": str(FIXTURES[0].id)},
            ).json()
            locked = client.post(f"/api/v1/analysis-runs/{run['run_id']}/lock").json()
            lock_id = locked["lock_id"]
            manifest_before = client.get(f"/api/v1/prediction-locks/{lock_id}/export.json").json()[
                "manifest"
            ]
            post_match_service.clock = lambda: datetime(2026, 8, 22, 21, 0, tzinfo=UTC)
            autopsy = client.post(
                f"/api/v1/prediction-locks/{lock_id}/post-match",
                headers={"Idempotency-Key": "post-match-result-0001"},
                json={
                    "home_score": 2,
                    "away_score": 1,
                    "observed_at": "2026-08-22T20:00:00Z",
                    "source": "official-mock",
                },
            )
            replay = client.get(f"/api/v1/prediction-locks/{lock_id}/autopsy")
            manifest_after = client.get(f"/api/v1/prediction-locks/{lock_id}/export.json").json()[
                "manifest"
            ]
    finally:
        service.clock = original_analysis_clock
        post_match_service.clock = original_post_match_clock

    assert autopsy.status_code == 201
    assert replay.json() == autopsy.json()
    assert autopsy.json()["pre_match_lock_sha256"] == locked["lock_sha256"]
    assert manifest_after == manifest_before
    assert "result" not in manifest_after
    assert "autopsy" not in manifest_after


def test_analysis_idempotency_replay_and_conflict() -> None:
    original_clock = service.clock
    service.clock = lambda: datetime(2026, 8, 22, 8, 0, tzinfo=UTC)
    try:
        with TestClient(app) as client:
            headers = {"Idempotency-Key": "analysis-idempotency-0001"}
            first = client.post(
                "/api/v1/analysis-runs",
                headers=headers,
                json={"fixture_id": str(FIXTURES[0].id)},
            )
            replay = client.post(
                "/api/v1/analysis-runs",
                headers=headers,
                json={"fixture_id": str(FIXTURES[0].id)},
            )
            conflict = client.post(
                "/api/v1/analysis-runs",
                headers=headers,
                json={"fixture_id": str(FIXTURES[1].id)},
            )
    finally:
        service.clock = original_clock

    assert first.status_code == 201
    assert replay.status_code == 201
    assert replay.json()["run_id"] == first.json()["run_id"]
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "IDEMPOTENCY_CONFLICT"
