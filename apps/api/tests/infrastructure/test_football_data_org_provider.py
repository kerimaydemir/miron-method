from datetime import UTC, datetime, timedelta

import httpx
import pytest

from app.domain.auto_coupon import league_for_fixture
from app.infrastructure.football_data_org_provider import FootballDataOrgProvider


@pytest.mark.asyncio
async def test_football_data_org_provider_normalizes_free_top_league_matches() -> None:
    now = datetime.now(UTC)
    kickoff = now + timedelta(hours=6)
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.url.path == "/v4/matches"
        assert request.headers["X-Auth-Token"] == "test-token"
        assert request.url.params["competitions"] == "PL,PD,BL1,SA,FL1,DED,PPL,ELC"
        return httpx.Response(
            200,
            json={
                "matches": [
                    {
                        "id": 551234,
                        "utcDate": kickoff.isoformat().replace("+00:00", "Z"),
                        "status": "TIMED",
                        "competition": {"code": "PL", "name": "Premier League"},
                        "homeTeam": {"name": "Arsenal FC"},
                        "awayTeam": {"name": "Liverpool FC"},
                        "score": {"fullTime": {"home": None, "away": None}},
                        "venue": "Emirates Stadium",
                    }
                ]
            },
        )

    client = httpx.AsyncClient(
        base_url="https://api.football-data.test/v4",
        headers={"X-Auth-Token": "test-token"},
        transport=httpx.MockTransport(handler),
    )
    provider = FootballDataOrgProvider(
        api_key="test-token",
        base_url="https://api.football-data.test/v4",
        refresh_seconds=300,
        client=client,
    )
    try:
        fixtures = await provider.list_fixtures(
            start_utc=now,
            end_utc=now + timedelta(days=1),
            competition_ids=(),
        )
        search = await provider.search_fixtures(
            query="Liverpool",
            start_utc=None,
            end_utc=None,
        )
        factors = await provider.features_for(fixtures[0])
    finally:
        await client.aclose()

    assert calls == 1
    assert fixtures == search
    assert fixtures[0].source_provider == "football_data_org"
    assert fixtures[0].provider_fixture_id == "551234"
    assert fixtures[0].competition_key.startswith("football-data:pl:")
    assert league_for_fixture(fixtures[0]) is not None
    assert league_for_fixture(fixtures[0]).name == "Premier League"
    assert factors.coverage_score > factors.market_coverage_score


def test_football_data_org_provider_requires_a_token() -> None:
    with pytest.raises(ValueError, match="FOOTBALL_DATA_API_KEY_MISSING"):
        FootballDataOrgProvider(
            api_key="",
            base_url="https://api.football-data.test/v4",
            refresh_seconds=300,
        )
