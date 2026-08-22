from datetime import UTC, datetime
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

import pytest

from app.application.post_match import PostMatchService
from app.domain.analysis import (
    FinalForecast,
    OutcomeProbability,
    PredictionLockManifest,
    PredictionLockView,
)
from app.domain.post_match import MatchResult, validate_lesson_statement


def locked_prediction() -> PredictionLockView:
    fixture_id = uuid5(NAMESPACE_URL, "post-match-fixture")
    run_id = uuid5(NAMESPACE_URL, "post-match-run")
    lock_id = uuid5(NAMESPACE_URL, "post-match-lock")
    cutoff = datetime(2026, 1, 1, 12, tzinfo=UTC)
    kickoff = datetime(2026, 1, 2, 18, tzinfo=UTC)
    forecast = FinalForecast(
        fixture_id=fixture_id,
        cutoff_at=cutoff,
        outcome_probabilities=(
            OutcomeProbability(
                outcome="home",
                probability=Decimal(".50"),
                lower=Decimal(".42"),
                upper=Decimal(".58"),
            ),
            OutcomeProbability(
                outcome="draw",
                probability=Decimal(".30"),
                lower=Decimal(".24"),
                upper=Decimal(".36"),
            ),
            OutcomeProbability(
                outcome="away",
                probability=Decimal(".20"),
                lower=Decimal(".14"),
                upper=Decimal(".26"),
            ),
        ),
        expected_home_goals=Decimal("1.5"),
        expected_away_goals=Decimal(".9"),
        confidence=Decimal(".64"),
        uncertainty_drivers=("lineup",),
        decisive_evidence=("elo",),
        dissent_summary=("draw",),
    )
    return PredictionLockView(
        lock_id=lock_id,
        analysis_run_id=run_id,
        manifest=PredictionLockManifest(
            analysis_run_id=run_id,
            fixture_id=fixture_id,
            cutoff_at=cutoff,
            locked_at=datetime(2026, 1, 2, 10, tzinfo=UTC),
            kickoff_at_snapshot=kickoff,
            forecast=forecast,
        ),
        manifest_sha256="a" * 64,
        object_uri="memory://lock.json",
    )


def test_post_match_separates_result_process_variance_and_lesson() -> None:
    lock = locked_prediction()
    now = datetime(2026, 1, 2, 21, tzinfo=UTC)
    service = PostMatchService(lambda: now)
    result = MatchResult(
        fixture_id=lock.manifest.fixture_id,
        home_score=2,
        away_score=1,
        observed_at=now,
        source="official-mock",
    )
    autopsy = service.ingest(lock, result)
    assert autopsy.result_verdict == "top_label_correct"
    assert autopsy.process_verdict == "sound_but_uncertain"
    assert sum((item.weight for item in autopsy.variance), Decimal("0")) == 1
    assert autopsy.variance[-1].category == "unknown"
    assert autopsy.lesson.hindsight_safe is True
    assert service.ingest(lock, result) == autopsy


def test_post_match_before_kickoff_and_hindsight_lesson_fail_closed() -> None:
    lock = locked_prediction()
    service = PostMatchService(lambda: datetime(2026, 1, 2, 17, tzinfo=UTC))
    result = MatchResult(
        fixture_id=lock.manifest.fixture_id,
        home_score=0,
        away_score=0,
        observed_at=datetime(2026, 1, 2, 17, tzinfo=UTC),
        source="official-mock",
    )
    with pytest.raises(ValueError, match="MATCH_NOT_STARTED"):
        service.ingest(lock, result)
    with pytest.raises(ValueError, match="LESSON_HINDSIGHT_REJECTED"):
        validate_lesson_statement("Bu sonucu kesinlikle olacaktı diye bilmeliydik.")
