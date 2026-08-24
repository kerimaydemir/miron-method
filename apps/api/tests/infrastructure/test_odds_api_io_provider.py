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
                        "date": "2026-08-25T19:00:00Z",
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
        assert request.url.path.endswith("/odds/multi")
        assert request.url.params["bookmakers"] == "Bet365,Unibet"
        assert request.url.params["eventIds"] == "72221172"
        return httpx.Response(
            200,
            json=[
                {
                    "id": 72221172,
                    "home": "Fulham FC",
                    "away": "Chelsea FC",
                    "date": "2026-08-25T19:00:00Z",
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
                                "name": "Double Chance",
                                "updatedAt": "2026-08-23T21:20:47.591Z",
                                "odds": [{"1X": "2.050", "12": "1.220", "X2": "1.280"}],
                            },
                            {
                                "name": "Spread",
                                "updatedAt": "2026-08-23T21:21:47.591Z",
                                "odds": [{"hdp": -0.5, "home": "3.900", "away": "1.260"}],
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
                            {
                                "name": "Odd/Even",
                                "updatedAt": "2026-08-23T23:04:30.251Z",
                                "odds": [{"odd": "1.950", "even": "1.950"}],
                            },
                            {
                                "name": "ML HT",
                                "updatedAt": "2026-08-23T23:05:00.251Z",
                                "odds": [{"home": "4.600", "draw": "2.250", "away": "2.050"}],
                            },
                            {
                                "name": "Totals HT",
                                "updatedAt": "2026-08-23T23:05:30.251Z",
                                "odds": [{"hdp": 1.5, "over": "2.200", "under": "1.650"}],
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
                                "name": "Double Chance",
                                "updatedAt": "2026-08-23T21:22:47.591Z",
                                "odds": [{"1X": "2.000", "12": "1.250", "X2": "1.300"}],
                            },
                            {
                                "name": "Asian Handicap",
                                "updatedAt": "2026-08-23T21:23:47.591Z",
                                "odds": [{"hdp": -0.5, "home": "3.800", "away": "1.280"}],
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
                            {
                                "name": "Odd Even",
                                "updatedAt": "2026-08-23T23:05:30.251Z",
                                "odds": [{"odd": "1.900", "even": "2.000"}],
                            },
                            {
                                "name": "1st Half Moneyline",
                                "updatedAt": "2026-08-23T23:06:00.251Z",
                                "odds": [{"home": "4.500", "draw": "2.300", "away": "2.000"}],
                            },
                            {
                                "name": "1st Half Goals Over/Under",
                                "updatedAt": "2026-08-23T23:06:30.251Z",
                                "odds": [{"hdp": 1.5, "over": "2.300", "under": "1.600"}],
                            },
                        ],
                    },
                }
            ],
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
        start_utc=datetime(2026, 8, 25, tzinfo=UTC),
        end_utc=datetime(2026, 8, 26, tzinfo=UTC),
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
        "double_chance",
        "spread",
        "totals",
        "btts",
        "odd_even",
        "first_half_h2h",
        "first_half_totals",
    }
    quotes = {(item.market_key, item.outcome_key, item.point): item for item in market.quotes}
    assert quotes[("double_chance", "1x", None)].decimal_odds == Decimal("2.025")
    assert quotes[("spread", "home", Decimal("-0.5"))].market_label == "Handikap"
    assert quotes[("odd_even", "even", None)].outcome_label == "Çift"
    assert quotes[("first_half_h2h", "draw", None)].market_label == "İlk yarı sonucu"
    assert quotes[("first_half_totals", "over", Decimal("1.5"))].decimal_odds == Decimal("2.250")
    assert all(item.provider == "odds_api_io" for item in market.quotes)
    await client.aclose()


@pytest.mark.asyncio
async def test_provider_sanitizes_rate_limit_errors_without_leaking_key() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["apiKey"] == "sensitive-test-key"
        return httpx.Response(429, json={"message": "too many requests"})

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://odds-api-io.test/v3"
    )
    provider = OddsApiIoProvider(
        api_key="sensitive-test-key",
        base_url="https://odds-api-io.test/v3",
        refresh_seconds=300,
        bookmakers="Bet365,Unibet",
        events_per_league=1,
        client=client,
    )

    with pytest.raises(RuntimeError) as exc_info:
        await provider._fetch_league_events("england-premier-league")

    assert "sensitive-test-key" not in str(exc_info.value)
    assert str(exc_info.value) == "ODDS_API_IO_RATE_LIMITED"
    await client.aclose()
