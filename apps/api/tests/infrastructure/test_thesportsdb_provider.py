from datetime import UTC, datetime

import httpx
import pytest

from app.infrastructure.mock_fixture_provider import FIXTURES
from app.infrastructure.thesportsdb_provider import TheSportsDbProvider


@pytest.mark.asyncio
async def test_thesportsdb_collects_team_event_lineup_timeline_and_stats() -> None:
    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        path = request.url.path
        query = dict(request.url.params)
        if path.endswith("/123/searchteams.php") and query.get("t") == FIXTURES[0].home_team:
            return httpx.Response(
                200,
                json={"teams": [{"idTeam": "11", "strTeam": FIXTURES[0].home_team}]},
            )
        if path.endswith("/123/searchteams.php") and query.get("t") == FIXTURES[0].away_team:
            return httpx.Response(
                200,
                json={"teams": [{"idTeam": "22", "strTeam": FIXTURES[0].away_team}]},
            )
        if path.endswith("/123/eventsnext.php") and query.get("id") == "11":
            return httpx.Response(
                200,
                json={
                    "events": [
                        {
                            "idEvent": "9001",
                            "idLeague": "39",
                            "strSeason": "2026-2027",
                            "dateEvent": FIXTURES[0].kickoff_at.date().isoformat(),
                            "strHomeTeam": FIXTURES[0].home_team,
                            "strAwayTeam": FIXTURES[0].away_team,
                        }
                    ]
                },
            )
        if path.endswith("/123/eventsnext.php") or path.endswith("/123/eventslast.php"):
            return httpx.Response(200, json={"events": []})
        if path.endswith("/123/lookupevent.php"):
            return httpx.Response(200, json={"events": [{"idEvent": "9001"}]})
        if path.endswith("/123/lookuplineup.php"):
            return httpx.Response(
                200,
                json={"lineup": [{"idPlayer": "7", "strPlayer": "Lineup Player"}]},
            )
        if path.endswith("/123/lookuptimeline.php"):
            return httpx.Response(
                200,
                json={"timeline": [{"strTimeline": "Goal", "intTime": "31"}]},
            )
        if path.endswith("/123/lookupeventstats.php"):
            return httpx.Response(
                200,
                json={"eventstats": [{"strStat": "Shots", "intHome": "12", "intAway": "7"}]},
            )
        return httpx.Response(404, json={})

    async with httpx.AsyncClient(
        base_url="https://www.thesportsdb.com/api/v1/json",
        transport=httpx.MockTransport(handler),
    ) as client:
        provider = TheSportsDbProvider(api_key="123", client=client)
        evidence = await provider.collect(FIXTURES[0])

    assert evidence.provider == "thesportsdb"
    assert evidence.provider_fixture_id == "9001"
    assert evidence.observed_at <= datetime.now(UTC)
    assert evidence.home_team_id == 11
    assert evidence.away_team_id == 22
    assert evidence.league_id == 39
    assert evidence.season == 2026
    assert evidence.coverage["fixture"] is True
    assert evidence.coverage["team_metadata"] is True
    assert evidence.coverage["lineups"] is True
    assert evidence.coverage["timeline"] is True
    assert evidence.coverage["statistics"] is True
    assert any(path.endswith("/123/lookuplineup.php") for path in seen_paths)
    assert any(path.endswith("/123/lookuptimeline.php") for path in seen_paths)
    assert any(path.endswith("/123/lookupeventstats.php") for path in seen_paths)


@pytest.mark.asyncio
async def test_thesportsdb_fails_closed_without_key() -> None:
    async with httpx.AsyncClient(
        base_url="https://example.invalid",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={})),
    ) as client:
        provider = TheSportsDbProvider(api_key="", client=client)
        with pytest.raises(PermissionError, match="THESPORTSDB_KEY_REQUIRED"):
            await provider.collect(FIXTURES[0])
