from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

from app.application.auto_coupons import AutoCouponService
from app.domain.analysis import FinalForecast, OutcomeProbability
from app.domain.auto_coupon import MarketOdds, MarketQuote
from app.domain.fixtures import CanonicalFixture

NOW = datetime(2026, 8, 22, 9, 0, tzinfo=UTC)
FIXTURE = CanonicalFixture(
    id=uuid5(NAMESPACE_URL, "value-gate-fixture"),
    competition_key="rapidapi:epl:47",
    competition_name="Premier League",
    home_team="North London",
    away_team="Merseyside",
    kickoff_at=NOW + timedelta(hours=4),
)


def _forecast(home_probability: str) -> FinalForecast:
    home = Decimal(home_probability)
    draw = Decimal(".15")
    away = Decimal("1") - home - draw
    return FinalForecast(
        fixture_id=FIXTURE.id,
        cutoff_at=NOW,
        outcome_probabilities=(
            OutcomeProbability(outcome="home", probability=home, lower=home, upper=home),
            OutcomeProbability(outcome="draw", probability=draw, lower=draw, upper=draw),
            OutcomeProbability(outcome="away", probability=away, lower=away, upper=away),
        ),
        expected_home_goals=Decimal("2.10"),
        expected_away_goals=Decimal(".70"),
        confidence=Decimal(".80"),
        uncertainty_drivers=("Muhtemel on bir kesinleşmedi",),
        decisive_evidence=("Düzeltilmiş form üstünlüğü",),
        dissent_summary=("Erken gol senaryosu fiyatı değiştirebilir",),
        analysis_provider="google_gemini",
        model_ids=("gemini-test",),
    )


def _market(*, price: str, fair_probability: str = ".55") -> MarketOdds:
    quote = MarketQuote(
        observed_at=NOW,
        market_key="h2h",
        market_label="Maç sonucu",
        outcome_key="home",
        outcome_label="North London",
        decimal_odds=Decimal(price),
        fair_probability=Decimal(fair_probability),
        bookmaker_count=3,
    )
    return MarketOdds(
        observed_at=NOW,
        bookmaker_count=3,
        home_decimal=Decimal(price),
        draw_decimal=Decimal("4.20"),
        away_decimal=Decimal("5.00"),
        fair_home_probability=Decimal(fair_probability),
        fair_draw_probability=Decimal(".25"),
        fair_away_probability=Decimal("1") - Decimal(fair_probability) - Decimal(".25"),
        quotes=(quote,),
    )


def test_value_gate_rejects_probability_below_seventy_percent() -> None:
    selected = AutoCouponService._best_market_selection(
        _market(price="2.40"), _forecast(".69"), FIXTURE, NOW
    )

    assert selected is None


def test_value_gate_rejects_price_below_one_eighty() -> None:
    selected = AutoCouponService._best_market_selection(
        _market(price="1.79"), _forecast(".70"), FIXTURE, NOW
    )

    assert selected is None


def test_value_gate_has_no_two_forty_upper_cap() -> None:
    selected = AutoCouponService._best_market_selection(
        _market(price="6.50", fair_probability=".40"), _forecast(".72"), FIXTURE, NOW
    )

    assert selected is not None
    assert selected[0].decimal_odds == Decimal("6.50")
