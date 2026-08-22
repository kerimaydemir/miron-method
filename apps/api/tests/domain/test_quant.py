from decimal import Decimal

from app.domain.quant import (
    brier_score,
    elo_expected_score,
    multiplicative_fair_probabilities,
    poisson_three_way,
)


def test_poisson_probabilities_sum_to_one() -> None:
    result = poisson_three_way(Decimal("1.48"), Decimal("1.09"))
    assert abs(result.home + result.draw + result.away - Decimal("1")) <= Decimal(".000001")
    assert result.home > result.away


def test_market_margin_is_removed() -> None:
    probabilities = multiplicative_fair_probabilities(
        (Decimal("2.10"), Decimal("3.20"), Decimal("3.70"))
    )
    assert abs(sum(probabilities) - Decimal("1")) <= Decimal(".000001")


def test_elo_and_brier_are_deterministic() -> None:
    assert elo_expected_score(Decimal("1600"), Decimal("1500")) > Decimal(".5")
    assert brier_score((Decimal(".5"), Decimal(".3"), Decimal(".2")), 0) == Decimal(".38")
