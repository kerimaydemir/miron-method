from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pytest

from app.infrastructure.the_odds_api_provider import TheOddsApiProvider


@pytest.mark.asyncio
async def test_provider_normalizes_bookmaker_average_and_removes_overround() -> None:
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
            "commence_time": "2026-08-26T18:00:00Z",
            "home_team": "Arsenal",
            "away_team": "Liverpool",
            "bookmakers": [
                {
                    "key": "book-a",
                    "last_update": "2026-08-22T08:00:00Z",
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
                    "last_update": "2026-08-22T08:01:00Z",
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
        start_utc=datetime(2026, 8, 26, tzinfo=UTC),
        end_utc=datetime(2026, 8, 27, tzinfo=UTC),
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
    wide = await provider.wide_market_for(fixture.id)
    assert {item.market_key for item in wide.quotes} == {"h2h", "btts", "totals"}
    assert all(item.bookmaker_count == 2 for item in wide.quotes)
    await client.aclose()
