from fastapi.testclient import TestClient

from app.main import app


def test_local_fixture_search_requires_explicit_selection_context() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/fixtures/search", params={"query": "Anka"})
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["items"][0]["home_team"] == "Anka FK"
    assert response.json()["items"][0]["source_provider"] == "mock_fixture"
    assert response.json()["items"][0]["provider_fixture_id"] is None


def test_fixture_search_rejects_one_character() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/fixtures/search", params={"query": "a"})
    assert response.status_code == 422
