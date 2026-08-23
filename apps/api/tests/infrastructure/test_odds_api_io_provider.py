from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pytest

from app.infrastructure.odds_api_io_provider import OddsApiIoProvider


@pytest.mark.asyncio
async def test_provider_filters_top_league_and_normalizes_richer_markets() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        if request.url.path.endswith("/events"):
            if request.url.params["league"] != "england-premier-league":
                return httpx.Response(200, json=[])
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 72221172,
                        "home": "Fulham FC",
                        "away": "Chelsea FC",
                        "date": "2026-08-24T19:00:00Z",
                        "status": "pending",
                        "sport": {"name": "Football", "slug": "football"},
                        "league": {
                            "name": "England - Premier League",
                            "slug": "england-premier-league",
                        },
                        "scores": {"home": 0, "away": 0},
                    }
                ],
            )
        assert request.url.path.endswith("/odds")
        assert request.url.params["bookmakers"] == "Bet365,Unibet"
        return httpx.Response(
            200,
            json={
                "id": 72221172,
                "home": "Fulham FC",
                "away": "Chelsea FC",
                "date": "2026-08-24T19:00:00Z",
                "status": "pending",
                "sport": {"name": "Football", "slug": "football"},
                "league": {
                    "name": "England - Premier League",
                    "slug": "england-premier-league",
                },
                "scores": {"home": 0, "away": 0},
                "bookmakers": {
                    "Bet365": [
                        {
                            "name": "ML",
                            "updatedAt": "2026-08-23T23:04:00.251Z",
                            "odds": [{"home": "3.900", "draw": "4.000", "away": "1.833"}],
                        },
                        {
                            "name": "Draw No Bet",
                            "updatedAt": "2026-08-23T21:11:47.591Z",
                            "odds": [{"home": "3.000", "away": "1.363"}],
                        },
                        {
                            "name": "Totals",
                            "updatedAt": "2026-08-23T22:51:31.254Z",
                            "odds": [{"hdp": 2.5, "over": "1.650", "under": "2.200"}],
                        },
                        {
                            "name": "Both Teams To Score",
                            "updatedAt": "2026-08-23T23:04:00.251Z",
                            "odds": [{"yes": "1.615", "no": "2.200"}],
                        },
                    ],
                    "Unibet": [
                        {
                            "name": "ML",
                            "updatedAt": "2026-08-23T23:05:00.251Z",
                            "odds": [{"home": "3.700", "draw": "4.100", "away": "1.900"}],
                        },
                        {
                            "name": "Draw No Bet",
                            "updatedAt": "2026-08-23T21:12:47.591Z",
                            "odds": [{"home": "2.900", "away": "1.400"}],
                        },
                        {
                            "name": "Goals Over/Under",
                            "updatedAt": "2026-08-23T22:52:31.254Z",
                            "odds": [{"hdp": 2.5, "over": "1.700", "under": "2.100"}],
                        },
                        {
                            "name": "Both Teams To Score",
                            "updatedAt": "2026-08-23T23:05:00.251Z",
                            "odds": [{"yes": "1.650", "no": "2.100"}],
                        },
                    ],
                },
            },
        )

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://odds-api-io.test/v3"
    )
    provider = OddsApiIoProvider(
        api_key="test-key",
        base_url="https://odds-api-io.test/v3",
        refresh_seconds=300,
        bookmakers="Bet365,Unibet",
        events_per_league=1,
        client=client,
    )
    items = await provider.list_market_fixtures(
        start_utc=datetime(2026, 8, 24, tzinfo=UTC),
        end_utc=datetime(2026, 8, 25, tzinfo=UTC),
    )
    assert len(items) == 1
    fixture, market = items[0]
    assert fixture.source_provider == "odds_api_io"
    assert fixture.competition_name == "Premier League"
    assert market.provider == "odds_api_io"
    assert market.bookmaker_count == 2
    assert market.home_decimal == Decimal("3.800")
    assert market.away_decimal == Decimal("1.867")
    assert (
        market.fair_home_probability + market.fair_draw_probability + market.fair_away_probability
    ) == Decimal("1.000000")
    assert {item.market_key for item in market.quotes} == {
        "h2h",
        "draw_no_bet",
        "totals",
        "btts",
    }
    assert all(item.provider == "odds_api_io" for item in market.quotes)
    await client.aclose()
