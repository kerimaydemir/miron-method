from decimal import ROUND_HALF_UP, Decimal

from app.domain.fixtures import TriageFactors

POSITIVE_WEIGHTS: dict[str, Decimal] = {
    "coverage_score": Decimal("0.20"),
    "source_freshness_score": Decimal("0.15"),
    "competitive_relevance_score": Decimal("0.15"),
    "model_information_gain_score": Decimal("0.10"),
    "market_coverage_score": Decimal("0.10"),
    "lineup_uncertainty_resolvability": Decimal("0.10"),
    "user_interest_score": Decimal("0.10"),
    "historical_case_support": Decimal("0.05"),
    "kickoff_time_practicality": Decimal("0.05"),
}
NEGATIVE_WEIGHTS: dict[str, Decimal] = {
    "estimated_cost_penalty": Decimal("0.15"),
    "unresolved_identity_penalty": Decimal("0.10"),
    "stale_data_penalty": Decimal("0.10"),
}


def worthwhile_score(factors: TriageFactors) -> int:
    raw = sum(
        (getattr(factors, key) * weight for key, weight in POSITIVE_WEIGHTS.items()),
        start=Decimal("0"),
    )
    raw -= sum(
        (getattr(factors, key) * weight for key, weight in NEGATIVE_WEIGHTS.items()),
        start=Decimal("0"),
    )
    bounded = min(Decimal("1"), max(Decimal("0"), raw))
    return int((bounded * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
