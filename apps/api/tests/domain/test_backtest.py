from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

import pytest

from app.domain.backtest import (
    BacktestCase,
    TemporalFeature,
    assert_no_lookahead,
    evaluate_cases,
    shadow_variant,
    walk_forward_folds,
)


def make_case(day: int, feature_name: str = "elo") -> BacktestCase:
    kickoff = datetime(2026, 1, day, 18, tzinfo=UTC)
    cutoff = kickoff - timedelta(hours=24)
    return BacktestCase(
        fixture_id=uuid5(NAMESPACE_URL, f"backtest:{day}"),
        kickoff_at=kickoff,
        cutoff_at=cutoff,
        probabilities=(Decimal(".50"), Decimal(".30"), Decimal(".20")),
        realized_index=day % 3,
        features=(
            TemporalFeature(
                name=feature_name,
                value=Decimal("1510"),
                knowledge_time=cutoff - timedelta(minutes=1),
            ),
        ),
    )


def test_walk_forward_is_chronological_and_reports_proper_scores() -> None:
    cases = tuple(make_case(day) for day in range(1, 9))
    folds = walk_forward_folds(cases, min_train_size=4, test_size=2)
    assert len(folds) == 2
    assert all(fold.train[-1].kickoff_at < fold.test[0].kickoff_at for fold in folds)
    metrics = evaluate_cases(tuple(case for fold in folds for case in fold.test))
    assert metrics.case_count == 4
    assert metrics.mean_brier > 0
    assert metrics.mean_log_loss > 0


@pytest.mark.parametrize(
    "poisoned_name",
    (
        "final_score",
        "post_match_xg",
        "closing_odds_after_cutoff",
        "confirmed_lineup_after_cutoff",
        "future_elo",
        "case_outcome_text",
    ),
)
def test_named_leakage_sentinels_fail_closed(poisoned_name: str) -> None:
    with pytest.raises(ValueError, match="LEAKAGE_SENTINEL"):
        assert_no_lookahead(make_case(1, poisoned_name))


def test_future_knowledge_time_fails_closed() -> None:
    safe = make_case(1)
    poisoned = BacktestCase(
        fixture_id=safe.fixture_id,
        kickoff_at=safe.kickoff_at,
        cutoff_at=safe.cutoff_at,
        probabilities=safe.probabilities,
        realized_index=safe.realized_index,
        features=(
            TemporalFeature(
                name="injury_status",
                value="out",
                knowledge_time=safe.cutoff_at + timedelta(seconds=1),
            ),
        ),
    )
    with pytest.raises(ValueError, match="LOOKAHEAD_DETECTED"):
        assert_no_lookahead(poisoned)


def test_shadow_assignment_is_deterministic() -> None:
    fixture_id = make_case(1).fixture_id
    first = shadow_variant(fixture_id, "pilot.v1", ("control", "shadow"))
    assert first == shadow_variant(fixture_id, "pilot.v1", ("control", "shadow"))
