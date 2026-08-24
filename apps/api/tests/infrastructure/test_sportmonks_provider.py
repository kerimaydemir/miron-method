from urllib.parse import parse_qs

import httpx
import pytest

from app.infrastructure.mock_fixture_provider import FIXTURES
from app.infrastructure.sportmonks_provider import SportmonksProvider


@pytest.mark.asyncio
async def test_collects_rich_fixture_evidence_from_sportmonks() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        query = parse_qs(request.url.query.decode())
        assert query["api_token"] == ["sportmonks-test"]
        if request.url.path.endswith("/fixtures/between/2026-08-22/2026-08-22"):
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": 19683241,
                            "league_id": 501,
                            "season_id": 24000,
                            "participants": [
                                {"id": 10, "name": "Anka FK", "meta": {"location": "home"}},
                                {"id": 20, "name": "Boğaz SK", "meta": {"location": "away"}},
                            ],
                            "scores": [],
                            "state": {"name": "NS"},
                            "venue": {"name": "Pilot"},
                        }
                    ]
                },
            )
        assert request.url.path.endswith("/fixtures/19683241")
        assert "participants" in query["include"][0]
        return httpx.Response(
            200,
            json={
                "data": {
                    "id": 19683241,
                    "league_id": 501,
                    "season_id": 24000,
                    "participants": [
                        {"id": 10, "name": "Anka FK", "meta": {"location": "home"}},
                        {"id": 20, "name": "Boğaz SK", "meta": {"location": "away"}},
                    ],
                    "scores": [{"score": {"goals": 0}}],
                    "events": [{"type_id": 14}],
                    "lineups": [{"player_id": 7}],
                    "statistics": [{"type_id": 45, "data": {"value": 12}}],
                    "xgfixture": [{"team_id": 10, "value": "1.65"}],
                    "predictions": [{"type_id": 237, "predictions": {"yes": "61%"}}],
                    "sidelined": [{"player_id": 9}],
                    "odds": [{"market_id": 1}],
                    "venue": {"name": "Pilot"},
                    "state": {"name": "NS"},
                    "referees": [{"id": 3}],
                }
            },
        )

    client = httpx.AsyncClient(
        base_url="https://sportmonks.test/v3/football",
        transport=httpx.MockTransport(handler),
    )
    provider = SportmonksProvider(
        api_key="sportmonks-test", client=client, requests_per_minute=60_000
    )

    evidence = await provider.collect(FIXTURES[0])

    assert evidence.provider == "sportmonks"
    assert evidence.provider_fixture_id == "19683241"
    assert evidence.home_team_id == 10
    assert evidence.away_team_id == 20
    assert evidence.league_id == 501
    assert evidence.season == 24000
    assert {artifact.kind for artifact in evidence.artifacts} == {"fixture", "fixture_rich"}
    assert evidence.coverage["participants"] is True
    assert evidence.coverage["lineups"] is True
    assert evidence.coverage["statistics"] is True
    assert evidence.coverage["predictions"] is True
    await client.aclose()


@pytest.mark.asyncio
async def test_sportmonks_degrades_to_resolved_fixture_when_rich_include_fails() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/fixtures/between/2026-08-22/2026-08-22"):
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": 19683241,
                            "participants": [
                                {"id": 10, "name": "Anka FK", "meta": {"location": "home"}},
                                {"id": 20, "name": "Boğaz SK", "meta": {"location": "away"}},
                            ],
                        }
                    ]
                },
            )
        return httpx.Response(403, json={"message": "include not allowed"})

    client = httpx.AsyncClient(
        base_url="https://sportmonks.test/v3/football",
        transport=httpx.MockTransport(handler),
    )
    provider = SportmonksProvider(
        api_key="sportmonks-test", client=client, requests_per_minute=60_000
    )

    evidence = await provider.collect(FIXTURES[0])

    assert evidence.provider_fixture_id == "19683241"
    assert evidence.coverage["fixture"] is True
    assert evidence.coverage["participants"] is True
    assert evidence.coverage["lineups"] is False
    await client.aclose()
