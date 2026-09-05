from datetime import UTC, date, datetime
from decimal import Decimal

from app.infrastructure.api_football_odds_provider import ApiFootballOddsProvider


def test_api_football_odds_normalizes_real_bookmaker_markets() -> None:
    values = [
        {"value": "Home", "odd": "2.40"},
        {"value": "Draw", "odd": "3.50"},
        {"value": "Away", "odd": "3.10"},
    ]
    record = {
        "league": {"id": 39},
        "fixture": {"id": 9876, "date": "2026-08-22T18:00:00+00:00"},
        "update": "2026-08-22T08:55:00+00:00",
        "bookmakers": [
            {
                "id": bookmaker_id,
                "name": f"Book {bookmaker_id}",
                "bets": [
                    {"name": "Match Winner", "values": values},
                    {
                        "name": "Goals Over/Under",
                        "values": [
                            {"value": "Over 2.5", "odd": "1.95"},
                            {"value": "Under 2.5", "odd": "1.90"},
                        ],
                    },
                ],
            }
            for bookmaker_id in (1, 2, 3)
        ],
    }
    detail = {
        "fixture": {
            "id": 9876,
            "date": "2026-08-22T18:00:00+00:00",
            "venue": {"name": "Test Stadium"},
        },
        "teams": {
            "home": {"id": 10, "name": "Arsenal"},
            "away": {"id": 20, "name": "Liverpool"},
        },
    }

    normalized = ApiFootballOddsProvider._normalize_record(
        record,
        detail,
        "epl",
        datetime(2026, 8, 22, 9, 0, tzinfo=UTC),
    )

    assert normalized is not None
    fixture, market = normalized
    assert fixture.source_provider == "api_football"
    assert fixture.home_team == "Arsenal"
    assert market.provider == "api_football"
    assert market.home_decimal == Decimal("2.400")
    assert {quote.market_key for quote in market.quotes} == {"h2h", "totals"}
    assert len(market.quotes) == 15
    assert all(quote.bookmaker_count == 3 for quote in market.quotes)
    assert all(quote.bookmaker is not None for quote in market.quotes)
    assert {quote.bookmaker for quote in market.quotes} == {"Book 1", "Book 2", "Book 3"}


def test_api_football_season_uses_start_year_but_keeps_mls_calendar_year() -> None:
    january = date(2027, 1, 15)

    assert ApiFootballOddsProvider._season_for_day(january, "epl") == 2026
    assert ApiFootballOddsProvider._season_for_day(january, "mls") == 2027
