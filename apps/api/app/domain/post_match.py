from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.analysis import PredictionLockView
from app.domain.quant import brier_score


class MatchResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fixture_id: UUID
    home_score: int = Field(ge=0, le=30)
    away_score: int = Field(ge=0, le=30)
    status: Literal["final"] = "final"
    observed_at: datetime
    source: str = Field(min_length=2, max_length=80)

    @model_validator(mode="after")
    def observed_at_has_timezone(self) -> "MatchResult":
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        return self


class VarianceAttribution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    category: Literal[
        "forecast_error",
        "scenario_miss",
        "data_miss",
        "execution_variance",
        "irreducible_variance",
        "unknown",
    ]
    weight: Decimal = Field(ge=0, le=1)
    rationale: str = Field(min_length=3, max_length=240)


class ValidatedLesson(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    lesson_id: UUID
    status: Literal["validated"] = "validated"
    scope: str = Field(min_length=3, max_length=120)
    statement: str = Field(min_length=12, max_length=400)
    confidence: Decimal = Field(ge=0, le=1)
    hindsight_safe: Literal[True] = True
    supporting_lock_sha256: str = Field(min_length=64, max_length=64)


class AutopsyView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["post-match-autopsy.v1"] = "post-match-autopsy.v1"
    autopsy_id: UUID
    lock_id: UUID
    analysis_run_id: UUID
    fixture_id: UUID
    pre_match_lock_sha256: str = Field(min_length=64, max_length=64)
    result: MatchResult
    realized_outcome: Literal["home", "draw", "away"]
    predicted_outcome: Literal["home", "draw", "away"] = "home"
    brier_score: Decimal = Field(ge=0, le=2)
    result_verdict: Literal["top_label_correct", "top_label_incorrect"]
    process_verdict: Literal["sound_but_uncertain", "needs_review"]
    pre_match_thesis: tuple[str, ...] = ()
    post_match_explanation: str = "Eski kayıt; ayrıntılı maç sonrası açıklama bulunmuyor."
    variance: tuple[VarianceAttribution, ...]
    lesson: ValidatedLesson
    created_at: datetime

    @model_validator(mode="after")
    def variance_is_complete(self) -> "AutopsyView":
        categories = [item.category for item in self.variance]
        if len(categories) != len(set(categories)):
            raise ValueError("variance categories must be unique")
        if abs(sum((item.weight for item in self.variance), Decimal("0")) - Decimal("1")) > Decimal(
            ".000001"
        ):
            raise ValueError("variance weights must sum to one")
        if "unknown" not in categories:
            raise ValueError("variance must preserve an unknown remainder")
        return self


def result_outcome(result: MatchResult) -> Literal["home", "draw", "away"]:
    if result.home_score > result.away_score:
        return "home"
    if result.home_score < result.away_score:
        return "away"
    return "draw"


def score_locked_forecast(lock: PredictionLockView, result: MatchResult) -> Decimal:
    items = lock.manifest.forecast.outcome_probabilities
    probabilities = (items[0].probability, items[1].probability, items[2].probability)
    outcome = result_outcome(result)
    return brier_score(probabilities, ("home", "draw", "away").index(outcome))


def validate_lesson_statement(statement: str) -> None:
    normalized = statement.casefold()
    forbidden = (
        "bilmeliydik",
        "kesinlikle olacaktı",
        "sonuca göre tahmin",
        "final skoru özellik",
        "gelecek verisi",
    )
    if any(fragment in normalized for fragment in forbidden):
        raise ValueError("LESSON_HINDSIGHT_REJECTED")
