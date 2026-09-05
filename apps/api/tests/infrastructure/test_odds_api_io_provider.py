from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest

from app.domain.fixtures import CanonicalFixture
from app.infrastructure.odds_api_io_provider import OddsApiIoProvider


@pytest.mark.asyncio
async def test_provider_filters_top_league_and_normalizes_richer_markets() -> None:
    observed_at = datetime.now(UTC)
    kickoff_at = observed_at + timedelta(days=1)
    kickoff_text = kickoff_at.isoformat().replace("+00:00", "Z")
    fresh_update = (observed_at - timedelta(minutes=5)).isoformat().replace(
        "+00:00", "Z"
    )

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
                        "date": kickoff_text,
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
                    "date": kickoff_text,
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
                                "updatedAt": fresh_update,
                                "odds": [{"home": "3.900", "draw": "4.000", "away": "1.833"}],
                            },
                            {
                                "name": "Draw No Bet",
                                "updatedAt": fresh_update,
                                "odds": [{"home": "3.000", "away": "1.363"}],
                            },
                            {
                                "name": "Double Chance",
                                "updatedAt": fresh_update,
                                "odds": [{"1X": "2.050", "12": "1.220", "X2": "1.280"}],
                            },
                            {
                                "name": "Spread",
                                "updatedAt": fresh_update,
                                "odds": [{"hdp": -0.5, "home": "3.900", "away": "1.260"}],
                            },
                            {
                                "name": "Totals",
                                "updatedAt": fresh_update,
                                "odds": [{"hdp": 2.5, "over": "1.650", "under": "2.200"}],
                            },
                            {
                                "name": "Both Teams To Score",
                                "updatedAt": fresh_update,
                                "odds": [{"yes": "1.615", "no": "2.200"}],
                            },
                            {
                                "name": "Odd/Even",
                                "updatedAt": fresh_update,
                                "odds": [{"odd": "1.950", "even": "1.950"}],
                            },
                            {
                                "name": "ML HT",
                                "updatedAt": fresh_update,
                                "odds": [{"home": "4.600", "draw": "2.250", "away": "2.050"}],
                            },
                            {
                                "name": "Totals HT",
                                "updatedAt": fresh_update,
                                "odds": [{"hdp": 1.5, "over": "2.200", "under": "1.650"}],
                            },
                        ],
                        "Unibet": [
                            {
                                "name": "ML",
                                "updatedAt": fresh_update,
                                "odds": [{"home": "3.700", "draw": "4.100", "away": "1.900"}],
                            },
                            {
                                "name": "Draw No Bet",
                                "updatedAt": fresh_update,
                                "odds": [{"home": "2.900", "away": "1.400"}],
                            },
                            {
                                "name": "Double Chance",
                                "updatedAt": fresh_update,
                                "odds": [{"1X": "2.000", "12": "1.250", "X2": "1.300"}],
                            },
                            {
                                "name": "Asian Handicap",
                                "updatedAt": fresh_update,
                                "odds": [{"hdp": -0.5, "home": "3.800", "away": "1.280"}],
                            },
                            {
                                "name": "Goals Over/Under",
                                "updatedAt": fresh_update,
                                "odds": [{"hdp": 2.5, "over": "1.700", "under": "2.100"}],
                            },
                            {
                                "name": "Both Teams To Score",
                                "updatedAt": fresh_update,
                                "odds": [{"yes": "1.650", "no": "2.100"}],
                            },
                            {
                                "name": "Odd Even",
                                "updatedAt": fresh_update,
                                "odds": [{"odd": "1.900", "even": "2.000"}],
                            },
                            {
                                "name": "1st Half Moneyline",
                                "updatedAt": fresh_update,
                                "odds": [{"home": "4.500", "draw": "2.300", "away": "2.000"}],
                            },
                            {
                                "name": "1st Half Goals Over/Under",
                                "updatedAt": fresh_update,
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
        start_utc=kickoff_at - timedelta(hours=1),
        end_utc=kickoff_at + timedelta(hours=1),
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
    assert quotes[("double_chance", "1x", None)].decimal_odds == Decimal("2.050")
    assert quotes[("spread", "home", Decimal("-0.5"))].market_label == "Handikap"
    assert quotes[("spread", "away", Decimal("0.5"))].decimal_odds == Decimal("1.280")
    assert quotes[("odd_even", "even", None)].outcome_label == "Çift"
    assert quotes[("first_half_h2h", "draw", None)].market_label == "İlk yarı sonucu"
    assert quotes[("first_half_totals", "over", Decimal("1.5"))].decimal_odds == Decimal("2.300")
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


def test_normalizer_counts_unique_complete_fresh_bookmakers_only() -> None:
    observed_at = datetime(2026, 9, 5, 10, 0, tzinfo=UTC)
    kickoff_at = observed_at + timedelta(hours=5)
    fresh = (observed_at - timedelta(minutes=2)).isoformat().replace("+00:00", "Z")
    stale = (observed_at - timedelta(hours=7)).isoformat().replace("+00:00", "Z")

    def moneyline(updated: str | None) -> list[dict[str, object]]:
        return [
            {
                "name": "ML",
                "updatedAt": updated,
                "odds": [{"home": "2.20", "draw": "3.20", "away": "3.30"}],
            }
        ]
    payload = {
        "id": 991122,
        "home": "Arsenal",
        "away": "Liverpool",
        "date": kickoff_at.isoformat().replace("+00:00", "Z"),
        "status": "pending",
        "sport": {"name": "Football", "slug": "football"},
        "league": {"name": "England", "slug": "england-premier-league"},
        "bookmakers": {
            "Bet365": moneyline(fresh),
            " bet365 ": moneyline(fresh),
            "Stale Book": moneyline(stale),
            "Missing Timestamp": moneyline(None),
            "Incomplete": [
                {
                    "name": "ML",
                    "updatedAt": fresh,
                    "odds": [{"home": "2.10", "away": "3.40"}],
                }
            ],
        },
    }

    normalized = OddsApiIoProvider._normalize_event(payload, observed_at)

    assert normalized is not None
    _, market = normalized
    assert market.bookmaker_count == 1
    assert all(quote.bookmaker_count == 1 for quote in market.quotes)
    assert all(quote.bookmaker == "Bet365" for quote in market.quotes)


@pytest.mark.asyncio
async def test_refresh_result_uses_settled_status() -> None:
    observed_at = datetime.now(UTC)
    kickoff_at = observed_at + timedelta(days=1)
    kickoff_text = kickoff_at.isoformat().replace("+00:00", "Z")
    fresh_update = (observed_at - timedelta(minutes=5)).isoformat().replace(
        "+00:00", "Z"
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/events") and request.url.params["status"] == "pending":
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 72478464,
                        "home": "Valencia CF",
                        "away": "Real Betis Seville",
                        "date": kickoff_text,
                        "status": "pending",
                        "sport": {"name": "Football", "slug": "football"},
                        "league": {"name": "Spain - LaLiga", "slug": "spain-laliga"},
                        "scores": {"home": 0, "away": 0},
                    }
                ],
            )
        if request.url.path.endswith("/odds/multi"):
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 72478464,
                        "home": "Valencia CF",
                        "away": "Real Betis Seville",
                        "date": kickoff_text,
                        "status": "pending",
                        "sport": {"name": "Football", "slug": "football"},
                        "league": {"name": "Spain - LaLiga", "slug": "spain-laliga"},
                        "scores": {"home": 0, "away": 0},
                        "bookmakers": {
                            "Bet365": [
                                {
                                    "name": "ML",
                                    "updatedAt": fresh_update,
                                    "odds": [{"home": "2.1", "draw": "3.1", "away": "3.4"}],
                                }
                            ]
                        },
                    }
                ],
            )
        assert request.url.path.endswith("/events")
        assert request.url.params["status"] == "settled"
        return httpx.Response(
            200,
            json=[
                {
                    "id": 72478464,
                    "home": "Valencia CF",
                    "away": "Real Betis Seville",
                    "date": kickoff_text,
                    "status": "settled",
                    "sport": {"name": "Football", "slug": "football"},
                    "league": {"name": "Spain - LaLiga", "slug": "spain-laliga"},
                    "scores": {"home": 0, "away": 1},
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
        start_utc=kickoff_at - timedelta(hours=1),
        end_utc=kickoff_at + timedelta(hours=1),
    )

    refreshed = await provider.refresh_result(items[0][0].id)

    assert refreshed.status == "finished"
    assert refreshed.home_score == 0
    assert refreshed.away_score == 1
    await client.aclose()


@pytest.mark.asyncio
async def test_refresh_fixture_result_uses_snapshot_league_slug() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/events")
        assert request.url.params["status"] == "settled"
        assert request.url.params["league"] == "spain-laliga"
        return httpx.Response(
            200,
            json=[
                {
                    "id": 72478464,
                    "home": "Valencia CF",
                    "away": "Real Betis Seville",
                    "date": "2026-08-25T19:00:00Z",
                    "status": "settled",
                    "sport": {"name": "Football", "slug": "football"},
                    "league": {"name": "Spain - LaLiga", "slug": "spain-laliga"},
                    "scores": {"home": 0, "away": 1},
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
    fixture = CanonicalFixture(
        id=uuid4(),
        competition_key="oddsapiio:spain-laliga",
        competition_name="LaLiga",
        home_team="Valencia CF",
        away_team="Real Betis Seville",
        kickoff_at=datetime(2026, 8, 25, 19, tzinfo=UTC),
        source_provider="odds_api_io",
        provider_fixture_id="72478464",
    )

    refreshed = await provider.refresh_fixture_result(fixture)

    assert refreshed.status == "finished"
    assert refreshed.home_score == 0
    assert refreshed.away_score == 1
    await client.aclose()
