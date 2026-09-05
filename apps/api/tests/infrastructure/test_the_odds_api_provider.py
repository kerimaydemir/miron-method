from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx
import pytest

from app.infrastructure.the_odds_api_provider import TheOddsApiProvider


@pytest.mark.asyncio
async def test_provider_uses_real_best_price_and_consensus_probability() -> None:
    kickoff = datetime.now(UTC) + timedelta(days=1)
    fresh_update = (datetime.now(UTC) - timedelta(minutes=1)).isoformat().replace(
        "+00:00", "Z"
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        is_wide = "/events/" in request.url.path
        if is_wide:
            assert "btts" in request.url.params["markets"]
            assert "totals" in request.url.params["markets"]
        else:
            assert request.url.params["markets"] == "h2h"
        extra_markets = (
            [
                {
                    "key": "btts",
                    "outcomes": [
                        {"name": "Yes", "price": 1.8},
                        {"name": "No", "price": 2.0},
                    ],
                },
                {
                    "key": "totals",
                    "outcomes": [
                        {"name": "Over", "price": 1.9, "point": 2.5},
                        {"name": "Under", "price": 1.9, "point": 2.5},
                    ],
                },
            ]
            if is_wide
            else []
        )
        payload = {
            "id": "event-1",
            "sport_key": "soccer_epl",
            "sport_title": "EPL",
            "commence_time": kickoff.isoformat().replace("+00:00", "Z"),
            "home_team": "Arsenal",
            "away_team": "Liverpool",
            "bookmakers": [
                {
                    "key": "book-a",
                    "last_update": fresh_update,
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Arsenal", "price": 2.0},
                                {"name": "Draw", "price": 4.0},
                                {"name": "Liverpool", "price": 4.0},
                            ],
                        },
                        *extra_markets,
                    ],
                },
                {
                    "key": "book-b",
                    "last_update": fresh_update,
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Arsenal", "price": 2.2},
                                {"name": "Draw", "price": 3.8},
                                {"name": "Liverpool", "price": 3.9},
                            ],
                        },
                        *extra_markets,
                    ],
                },
            ],
        }
        return httpx.Response(
            200,
            json=payload if is_wide else [payload],
        )

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://odds.test/v4"
    )
    provider = TheOddsApiProvider(
        api_key="test-key",
        base_url="https://odds.test/v4",
        refresh_seconds=300,
        wide_markets=("h2h", "btts", "totals"),
        client=client,
    )
    items = await provider.list_market_fixtures(
        start_utc=kickoff - timedelta(hours=6),
        end_utc=kickoff + timedelta(hours=6),
    )
    assert len(items) == 1
    fixture, market = items[0]
    assert fixture.source_provider == "the_odds_api"
    assert fixture.competition_name == "Premier League"
    assert market.bookmaker_count == 2
    assert market.home_decimal == Decimal("2.100")
    total = (
        market.fair_home_probability + market.fair_draw_probability + market.fair_away_probability
    )
    assert total == Decimal("1.000000")
    assert {item.market_key for item in market.quotes} == {"h2h"}
    assert len(market.quotes) == 6
    home_quote = max(
        (item for item in market.quotes if item.outcome_key == "home"),
        key=lambda item: item.decimal_odds,
    )
    assert home_quote.decimal_odds == Decimal("2.200")
    assert home_quote.bookmaker == "book-b"
    assert {item.bookmaker for item in market.quotes} == {"book-a", "book-b"}
    wide = await provider.wide_market_for(fixture.id)
    assert {item.market_key for item in wide.quotes} == {"h2h", "btts", "totals"}
    assert all(item.bookmaker_count == 2 for item in wide.quotes)
    assert {item.bookmaker for item in wide.quotes} == {"book-a", "book-b"}
    await client.aclose()
