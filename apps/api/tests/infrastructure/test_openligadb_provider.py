from datetime import UTC, datetime, timedelta

import httpx
import pytest

from app.infrastructure.openligadb_provider import OpenLigaDbProvider


@pytest.mark.asyncio
async def test_openligadb_provider_normalizes_and_caches_live_fixtures() -> None:
    now = datetime.now(UTC)
    kickoff = now + timedelta(hours=6)
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.url.path == "/getmatchdata/la1"
        return httpx.Response(
            200,
            json=[
                {
                    "matchID": 85349,
                    "matchDateTimeUTC": kickoff.isoformat().replace("+00:00", "Z"),
                    "leagueName": "LaLiga EA Sports 2026/2027",
                    "leagueSeason": 2026,
                    "leagueShortcut": "la1",
                    "matchIsFinished": False,
                    "team1": {"teamId": 1, "teamName": "Espanyol Barcelona"},
                    "team2": {"teamId": 2, "teamName": "Real Madrid"},
                    "matchResults": [],
                    "goals": [],
                    "location": {"locationStadium": "RCDE Stadium"},
                }
            ],
        )

    client = httpx.AsyncClient(
        base_url="https://api.openligadb.test", transport=httpx.MockTransport(handler)
    )
    provider = OpenLigaDbProvider(
        base_url="https://api.openligadb.test",
        league_shortcuts=("la1",),
        refresh_seconds=60,
        client=client,
    )
    try:
        fixtures = await provider.list_fixtures(
            start_utc=now,
            end_utc=now + timedelta(days=1),
            competition_ids=[],
        )
        search = await provider.search_fixtures(query="Real Madrid", start_utc=None, end_utc=None)
        factors = await provider.features_for(fixtures[0])
    finally:
        await client.aclose()

    assert calls == 1
    assert len(fixtures) == 1
    assert fixtures[0].source_provider == "openligadb"
    assert fixtures[0].provider_fixture_id == "85349"
    assert fixtures[0].venue_name == "RCDE Stadium"
    assert search == fixtures
    assert factors.source_freshness_score > factors.market_coverage_score
