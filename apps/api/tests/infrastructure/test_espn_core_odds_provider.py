from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pytest

from app.domain.auto_coupon import league_for_fixture
from app.infrastructure.espn_core_odds_provider import EspnCoreOddsProvider


@pytest.mark.asyncio
async def test_espn_core_odds_provider_collects_no_key_market_quotes() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/leagues/esp.1/events"):
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "$ref": "http://sports.core.api.espn.com/v2/sports/soccer/leagues/esp.1/events/401882909?lang=en&region=us"
                        }
                    ]
                },
            )
        if path.endswith("/leagues/esp.1/events/401882909"):
            return httpx.Response(
                200,
                json={
                    "id": "401882909",
                    "date": "2026-08-26T17:30Z",
                    "competitions": [
                        {
                            "id": "401882909",
                            "venue": {"fullName": "El Sadar"},
                            "competitors": [
                                {
                                    "homeAway": "home",
                                    "team": {
                                        "$ref": "http://sports.core.api.espn.com/v2/sports/soccer/leagues/esp.1/seasons/2026/teams/97?lang=en&region=us"
                                    },
                                },
                                {
                                    "homeAway": "away",
                                    "team": {
                                        "$ref": "http://sports.core.api.espn.com/v2/sports/soccer/leagues/esp.1/seasons/2026/teams/1538?lang=en&region=us"
                                    },
                                },
                            ],
                            "odds": {
                                "$ref": "http://sports.core.api.espn.com/v2/sports/soccer/leagues/esp.1/events/401882909/competitions/401882909/odds?lang=en&region=us"
                            },
                        }
                    ],
                },
            )
        if path.endswith("/teams/97"):
            return httpx.Response(200, json={"id": "97", "displayName": "Osasuna"})
        if path.endswith("/teams/1538"):
            return httpx.Response(200, json={"id": "1538", "displayName": "Levante"})
        if path.endswith("/competitions/401882909/odds"):
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "provider": {"name": "DraftKings"},
                            "overUnder": 2.5,
                            "overOdds": 115,
                            "underOdds": -145,
                            "homeTeamOdds": {
                                "current": {
                                    "moneyLine": {"decimal": 1.90},
                                    "spread": {"decimal": 1.80},
                                    "pointSpread": {"alternateDisplayValue": "-0.5"},
                                }
                            },
                            "awayTeamOdds": {
                                "current": {
                                    "moneyLine": {"decimal": 4.40},
                                    "spread": {"decimal": 1.90},
                                    "pointSpread": {"alternateDisplayValue": "+0.5"},
                                }
                            },
                            "drawOdds": {"moneyLine": 240},
                        }
                    ]
                },
            )
        return httpx.Response(404, json={})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = EspnCoreOddsProvider(client=client, league_paths=("esp.1",))
        pairs = await provider.list_market_fixtures(
            start_utc=datetime(2026, 8, 26, 15, tzinfo=UTC),
            end_utc=datetime(2026, 8, 26, 22, tzinfo=UTC),
        )

    assert len(pairs) == 1
    fixture, market = pairs[0]
    assert fixture.source_provider == "espn_core_odds"
    assert fixture.provider_fixture_id == "401882909"
    assert league_for_fixture(fixture).name == "LaLiga"  # type: ignore[union-attr]
    assert market.provider == "espn_core_odds"
    assert market.bookmaker_count == 1
    assert {quote.market_key for quote in market.quotes} == {"h2h", "spread", "totals"}
    assert market.home_decimal == Decimal("1.9")
    assert any(quote.market_key == "totals" and quote.outcome_key == "over" for quote in market.quotes)
