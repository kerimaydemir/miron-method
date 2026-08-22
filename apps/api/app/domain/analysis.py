from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

PRE_MATCH_STAGES: tuple[tuple[str, str], ...] = (
    ("S00", "Ön kontrol"),
    ("S01", "Güncel araştırma"),
    ("S02", "Kaynak doğrulama"),
    ("S03", "İddia normalizasyonu"),
    ("S04", "Çelişki ve güncellik"),
    ("S05", "İstatistik"),
    ("S06", "Oyuncu ve kadro"),
    ("S07", "Taktik"),
    ("S08", "Form"),
    ("S09", "Yorgunluk"),
    ("S10", "Kaleci"),
    ("S11", "Duran top"),
    ("S12", "Çevre"),
    ("S13", "İzole piyasa"),
    ("S14", "Piyasa hareketi açıklaması"),
    ("S15", "Quant modeller"),
    ("S16", "Tarihsel benzerlik"),
    ("S17", "Uzman eleştirmenler"),
    ("S18", "Kanıt denetimi"),
    ("S19", "Taktik sentezi"),
    ("S20", "Kadro sentezi"),
    ("S21", "Quant ve piyasa yorumu"),
    ("S22", "Ev galibiyeti steelman"),
    ("S23", "Beraberlik steelman"),
    ("S24", "Deplasman galibiyeti steelman"),
    ("S25", "Senaryo red team"),
    ("S26", "Senaryo motoru"),
    ("S27", "Chief Analyst"),
    ("S28", "Final Critic"),
    ("S29", "Chief revizyonu"),
    ("S30", "Prediction lock hazırlığı"),
)


class StageView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    stage_id: str
    name: str
    status: Literal["pending", "running", "completed", "degraded", "failed"]
    summary: str
    started_at: datetime
    completed_at: datetime | None
    cost_usd: Decimal = Field(ge=0)


class OutcomeProbability(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    outcome: Literal["home", "draw", "away"]
    probability: Decimal = Field(ge=0, le=1)
    lower: Decimal = Field(ge=0, le=1)
    upper: Decimal = Field(ge=0, le=1)


class FinalForecast(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["final-forecast.v1"] = "final-forecast.v1"
    fixture_id: UUID
    cutoff_at: datetime
    outcome_probabilities: tuple[OutcomeProbability, OutcomeProbability, OutcomeProbability]
    expected_home_goals: Decimal
    expected_away_goals: Decimal
    calibration_status: Literal["provisional"] = "provisional"
    confidence: Decimal = Field(ge=0, le=1)
    uncertainty_drivers: tuple[str, ...]
    decisive_evidence: tuple[str, ...]
    dissent_summary: tuple[str, ...]
    analysis_provider: Literal["mock", "google_gemini"] = "mock"
    model_ids: tuple[str, ...] = ()
    publish_status: Literal["degraded_publish"] = "degraded_publish"
    responsible_use_notice: str = (
        "Bu çıktı olasılıksal analizdir; kesinlik veya bahis tavsiyesi değildir."
    )

    @model_validator(mode="after")
    def probabilities_sum_to_one(self) -> "FinalForecast":
        if abs(
            sum(item.probability for item in self.outcome_probabilities) - Decimal("1")
        ) > Decimal(".000001"):
            raise ValueError("outcome probabilities must sum to one")
        return self


class AnalysisRunView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    run_id: UUID
    fixture_id: UUID
    state: Literal["LOCKING", "LOCKED"]
    cutoff_at: datetime
    kickoff_at_snapshot: datetime
    stages: tuple[StageView, ...]
    forecast: FinalForecast
    actual_cost_usd: Decimal
    correlation_id: UUID
    created_at: datetime
    lock_id: UUID | None = None
    lock_sha256: str | None = None


class AnalysisEvidenceDossier(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    analysis_run_id: UUID
    provider: str
    observed_at: datetime
    coverage: dict[str, bool]
    evidence: dict[str, object]
    evidence_sha256: str = Field(min_length=64, max_length=64)
    stage_outputs: dict[str, dict[str, object]]


class PredictionLockManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["prediction-lock.v1"] = "prediction-lock.v1"
    analysis_run_id: UUID
    fixture_id: UUID
    cutoff_at: datetime
    locked_at: datetime
    kickoff_at_snapshot: datetime
    forecast: FinalForecast


class PredictionLockView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    lock_id: UUID
    analysis_run_id: UUID
    manifest: PredictionLockManifest
    manifest_sha256: str = Field(min_length=64, max_length=64)
    object_uri: str
