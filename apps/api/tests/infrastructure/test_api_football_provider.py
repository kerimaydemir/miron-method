from urllib.parse import parse_qs

import httpx
import pytest

from app.infrastructure.api_football_provider import ApiFootballProvider
from app.infrastructure.mock_fixture_provider import FIXTURES


@pytest.mark.asyncio
async def test_collects_fixture_scoped_deep_evidence_from_api_football() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        query = parse_qs(request.url.query.decode())
        if request.url.path == "/fixtures" and "date" in query:
            response = [
                {
                    "fixture": {"id": 9001, "venue": {"name": "Pilot", "city": "Istanbul"}},
                    "league": {"id": 203, "season": 2026},
                    "teams": {
                        "home": {"id": 10, "name": "Anka FK"},
                        "away": {"id": 20, "name": "Boğaz SK"},
                    },
                }
            ]
        else:
            response = [{"endpoint": request.url.path, "query": query}]
        return httpx.Response(200, json={"errors": [], "response": response})

    client = httpx.AsyncClient(
        base_url="https://api-football.test",
        transport=httpx.MockTransport(handler),
    )
    provider = ApiFootballProvider(
        api_key="api-football-test", client=client, requests_per_minute=60_000
    )

    evidence = await provider.collect(FIXTURES[0])

    assert evidence.provider == "api_football"
    assert evidence.provider_fixture_id == "9001"
    assert evidence.home_team_id == 10
    assert evidence.away_team_id == 20
    assert evidence.league_id == 203
    assert evidence.season == 2026
    assert len(evidence.artifacts) == 17
    assert all(evidence.coverage.values())
    assert {request.url.path for request in requests} >= {
        "/fixtures/statistics",
        "/fixtures/lineups",
        "/fixtures/players",
        "/injuries",
        "/predictions",
        "/odds",
        "/standings",
        "/fixtures/headtohead",
        "/coachs",
    }
    assert all(request.headers["x-apisports-key"] == "api-football-test" for request in requests)
    await client.aclose()


@pytest.mark.asyncio
async def test_failed_optional_endpoint_is_recorded_as_missing_coverage() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        query = parse_qs(request.url.query.decode())
        if request.url.path == "/fixtures" and "date" in query:
            return httpx.Response(
                200,
                json={
                    "errors": [],
                    "response": [
                        {
                            "fixture": {"id": 9001},
                            "league": {"id": 203, "season": 2026},
                            "teams": {
                                "home": {"id": 10, "name": "Anka FK"},
                                "away": {"id": 20, "name": "Boğaz SK"},
                            },
                        }
                    ],
                },
            )
        if request.url.path == "/injuries":
            return httpx.Response(503, json={"error": "temporary"})
        return httpx.Response(200, json={"errors": [], "response": [{"ok": True}]})

    client = httpx.AsyncClient(
        base_url="https://api-football.test",
        transport=httpx.MockTransport(handler),
    )
    provider = ApiFootballProvider(
        api_key="api-football-test", client=client, requests_per_minute=60_000
    )

    evidence = await provider.collect(FIXTURES[0])

    assert evidence.coverage["fixture"] is True
    assert evidence.coverage["injuries"] is False
    assert evidence.coverage["statistics"] is True
    await client.aclose()
