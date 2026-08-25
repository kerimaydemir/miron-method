from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CanonicalFixture(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    sport_key: str = "football"
    competition_key: str
    competition_name: str
    home_team: str
    away_team: str
    kickoff_at: datetime
    venue_name: str | None = None
    source_provider: Literal[
        "mock_fixture",
        "openligadb",
        "football_data_org",
        "the_odds_api",
        "odds_api_io",
        "rapidapi_football",
        "api_football",
        "espn_core_odds",
    ] = "mock_fixture"
    provider_fixture_id: str | None = None
    status: Literal["scheduled", "live", "finished"] = "scheduled"
    home_score: int | None = Field(default=None, ge=0)
    away_score: int | None = Field(default=None, ge=0)
    observed_at: datetime | None = None

    @field_validator("kickoff_at")
    @classmethod
    def kickoff_is_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("kickoff_at must be timezone-aware")
        return value


class TriageFactors(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    coverage_score: Decimal = Field(ge=0, le=1)
    source_freshness_score: Decimal = Field(ge=0, le=1)
    competitive_relevance_score: Decimal = Field(ge=0, le=1)
    model_information_gain_score: Decimal = Field(ge=0, le=1)
    market_coverage_score: Decimal = Field(ge=0, le=1)
    lineup_uncertainty_resolvability: Decimal = Field(ge=0, le=1)
    user_interest_score: Decimal = Field(ge=0, le=1)
    historical_case_support: Decimal = Field(ge=0, le=1)
    kickoff_time_practicality: Decimal = Field(ge=0, le=1)
    estimated_cost_penalty: Decimal = Field(ge=0, le=1)
    unresolved_identity_penalty: Decimal = Field(ge=0, le=1)
    stale_data_penalty: Decimal = Field(ge=0, le=1)


class RankedFixture(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fixture: CanonicalFixture
    worthwhile_score: int = Field(ge=0, le=100)
    estimated_cost_usd: Decimal = Field(ge=0)
    positive_factors: tuple[str, ...]
    negative_factors: tuple[str, ...]
    coverage_label: str
    market_label: str
