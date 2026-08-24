from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid5

import httpx
import pytest

from app.domain.fixtures import CanonicalFixture
from app.infrastructure.espn_soccer_provider import EspnSoccerProvider


def _fixture() -> CanonicalFixture:
    return CanonicalFixture(
        id=uuid5(NAMESPACE_URL, "miron-baba-ai:test:bologna-lazio"),
        competition_key="serie_a",
        competition_name="Serie A",
        home_team="Bologna FC",
        away_team="Lazio Rome",
        kickoff_at=datetime(2026, 8, 24, 16, 30, tzinfo=UTC),
        venue_name="Stadio Renato Dall'Ara",
    )


@pytest.mark.asyncio
async def test_espn_soccer_collects_summary_news_rosters_injuries_and_schedules() -> None:
    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        seen_paths.append(path)
        if path.endswith("/ita.1/scoreboard"):
            assert request.url.params.get("dates") == "20260824"
            return httpx.Response(
                200,
                json={
                    "events": [
                        {
                            "id": "401874927",
                            "date": "2026-08-24T16:30Z",
                            "competitions": [
                                {
                                    "league": {"id": "12", "name": "Italian Serie A"},
                                    "competitors": [
                                        {
                                            "homeAway": "home",
                                            "team": {
                                                "id": "107",
                                                "displayName": "Bologna",
                                                "shortDisplayName": "Bologna",
                                            },
                                        },
                                        {
                                            "homeAway": "away",
                                            "team": {
                                                "id": "112",
                                                "displayName": "Lazio",
                                                "shortDisplayName": "Lazio",
                                            },
                                        },
                                    ],
                                }
                            ],
                        }
                    ]
                },
            )
        if path.endswith("/ita.1/summary"):
            assert request.url.params.get("event") == "401874927"
            return httpx.Response(
                200,
                json={
                    "header": {"id": "401874927"},
                    "boxscore": {"teams": []},
                    "injuries": [{"athlete": {"displayName": "Rotation Defender"}}],
                    "news": {"articles": [{"headline": "Bologna lineup context"}]},
                    "odds": [{"details": "Bologna win"}],
                },
            )
        if path.endswith("/ita.1/news"):
            return httpx.Response(
                200,
                json={
                    "articles": [
                        {
                            "headline": "Bologna prepares for Lazio",
                            "description": "Team news and tactical notes before the match.",
                            "published": "2026-08-24T08:00Z",
                        },
                        {
                            "headline": "Unrelated Serie A note",
                            "description": "Other teams.",
                        },
                    ]
                },
            )
        if path.endswith("/ita.1/teams/107/roster"):
            return httpx.Response(
                200,
                json={"athletes": [{"id": "7", "displayName": "Home Midfielder"}]},
            )
        if path.endswith("/ita.1/teams/112/roster"):
            return httpx.Response(
                200,
                json={"athletes": [{"id": "9", "displayName": "Away Striker"}]},
            )
        if path.endswith("/ita.1/teams/107/injuries") or path.endswith(
            "/ita.1/teams/112/injuries"
        ):
            return httpx.Response(
                200,
                json={"injuries": [{"status": "Questionable", "athlete": {"id": "4"}}]},
            )
        if path.endswith("/ita.1/teams/107/schedule") or path.endswith(
            "/ita.1/teams/112/schedule"
        ):
            return httpx.Response(200, json={"events": [{"id": "prev", "name": "Previous"}]})
        return httpx.Response(404, json={})

    async with httpx.AsyncClient(
        base_url="https://site.api.espn.com/apis/site/v2/sports/soccer",
        transport=httpx.MockTransport(handler),
    ) as client:
        provider = EspnSoccerProvider(client=client, league_paths=("ita.1",))
        evidence = await provider.collect(_fixture())

    assert evidence.provider == "espn_public_soccer"
    assert evidence.provider_fixture_id == "401874927"
    assert evidence.home_team_id == 107
    assert evidence.away_team_id == 112
    assert evidence.league_id == 12
    assert evidence.coverage["fixture"] is True
    assert evidence.coverage["summary"] is True
    assert evidence.coverage["news"] is True
    assert evidence.coverage["rosters"] is True
    assert evidence.coverage["injuries"] is True
    assert evidence.coverage["team_schedules"] is True
    assert "/apis/site/v2/sports/soccer/ita.1/summary" in seen_paths
    assert any(artifact.kind == "league_news" for artifact in evidence.artifacts)


@pytest.mark.asyncio
async def test_espn_soccer_returns_scan_artifacts_when_fixture_is_not_matched() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/ita.1/scoreboard"):
            return httpx.Response(
                200,
                json={
                    "events": [
                        {
                            "id": "different",
                            "date": "2026-08-24T16:30Z",
                            "competitions": [
                                {
                                    "competitors": [
                                        {"homeAway": "home", "team": {"displayName": "Milan"}},
                                        {"homeAway": "away", "team": {"displayName": "Inter"}},
                                    ]
                                }
                            ],
                        }
                    ]
                },
            )
        return httpx.Response(404, json={})

    async with httpx.AsyncClient(
        base_url="https://site.api.espn.com/apis/site/v2/sports/soccer",
        transport=httpx.MockTransport(handler),
    ) as client:
        provider = EspnSoccerProvider(client=client, league_paths=("ita.1",))
        evidence = await provider.collect(_fixture())

    assert evidence.provider_fixture_id.startswith("unmatched:")
    assert evidence.coverage["fixture"] is False
    assert evidence.coverage["scoreboard"] is True
    assert evidence.coverage["summary"] is False


@pytest.mark.asyncio
async def test_espn_soccer_falls_back_to_core_api_when_site_scoreboard_is_blocked() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/ita.1/scoreboard"):
            return httpx.Response(403, html="<h1>Access Denied</h1>")
        if path.endswith("/leagues/ita.1/events"):
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "$ref": "http://sports.core.api.espn.com/v2/sports/soccer/leagues/ita.1/events/401874927?lang=en&region=us"
                        }
                    ]
                },
            )
        if path.endswith("/leagues/ita.1/events/401874927"):
            return httpx.Response(
                200,
                json={
                    "id": "401874927",
                    "date": "2026-08-24T16:30Z",
                    "competitions": [
                        {
                            "competitors": [
                                {
                                    "homeAway": "home",
                                    "team": {
                                        "$ref": "http://sports.core.api.espn.com/v2/sports/soccer/leagues/ita.1/seasons/2026/teams/107?lang=en&region=us"
                                    },
                                },
                                {
                                    "homeAway": "away",
                                    "team": {
                                        "$ref": "http://sports.core.api.espn.com/v2/sports/soccer/leagues/ita.1/seasons/2026/teams/112?lang=en&region=us"
                                    },
                                },
                            ]
                        }
                    ],
                },
            )
        if path.endswith("/leagues/ita.1/seasons/2026/teams/107"):
            return httpx.Response(200, json={"id": "107", "displayName": "Bologna"})
        if path.endswith("/leagues/ita.1/seasons/2026/teams/112"):
            return httpx.Response(200, json={"id": "112", "displayName": "Lazio"})
        return httpx.Response(404, json={})

    async with httpx.AsyncClient(
        base_url="https://site.api.espn.com/apis/site/v2/sports/soccer",
        transport=httpx.MockTransport(handler),
    ) as client:
        provider = EspnSoccerProvider(client=client, league_paths=("ita.1",))
        evidence = await provider.collect(_fixture())

    assert evidence.provider_fixture_id == "401874927"
    assert evidence.home_team_id == 107
    assert evidence.away_team_id == 112
    assert evidence.coverage["fixture"] is True
    assert evidence.artifacts[0].endpoint.endswith("/leagues/ita.1/events")
