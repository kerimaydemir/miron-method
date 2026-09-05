from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.fixtures import CanonicalFixture

Pick = str
MarketKey = Literal[
    "h2h",
    "draw_no_bet",
    "double_chance",
    "btts",
    "totals",
    "alternate_totals",
    "team_totals",
    "alternate_team_totals",
    "spread",
    "odd_even",
    "first_half_h2h",
    "first_half_totals",
    "corners_spread",
    "cards_spread",
]


BookmakerSource = Literal[
    "the_odds_api",
    "odds_api_io",
    "rapidapi_football",
    "api_football",
    "espn_core_odds",
]


class MarketQuote(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: BookmakerSource = "the_odds_api"
    observed_at: datetime
    market_key: MarketKey
    market_label: str
    outcome_key: Literal[
        "home",
        "draw",
        "away",
        "over",
        "under",
        "yes",
        "no",
        "1x",
        "12",
        "x2",
        "odd",
        "even",
    ]
    outcome_label: str
    description: str | None = None
    point: Decimal | None = None
    decimal_odds: Decimal = Field(gt=1)
    fair_probability: Decimal = Field(gt=0, lt=1)
    bookmaker_count: int = Field(ge=1)
    bookmaker: str | None = None


class LeaguePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str
    name: str
    country_code: str
    openligadb_shortcut: str
    football_data_code: str | None = None
    odds_sport_key: str
    prestige_weight: int = Field(ge=0, le=10)


TOP_LEAGUES: tuple[LeaguePolicy, ...] = (
    LeaguePolicy(
        key="epl",
        name="Premier League",
        country_code="GB",
        openligadb_shortcut="pl1",
        football_data_code="PL",
        odds_sport_key="soccer_epl",
        prestige_weight=10,
    ),
    LeaguePolicy(
        key="laliga",
        name="LaLiga",
        country_code="ES",
        openligadb_shortcut="la1",
        football_data_code="PD",
        odds_sport_key="soccer_spain_la_liga",
        prestige_weight=10,
    ),
    LeaguePolicy(
        key="bundesliga",
        name="Bundesliga",
        country_code="DE",
        openligadb_shortcut="bl1",
        football_data_code="BL1",
        odds_sport_key="soccer_germany_bundesliga",
        prestige_weight=9,
    ),
    LeaguePolicy(
        key="serie_a",
        name="Serie A",
        country_code="IT",
        openligadb_shortcut="it1",
        football_data_code="SA",
        odds_sport_key="soccer_italy_serie_a",
        prestige_weight=9,
    ),
    LeaguePolicy(
        key="ligue_1",
        name="Ligue 1",
        country_code="FR",
        openligadb_shortcut="fr1",
        football_data_code="FL1",
        odds_sport_key="soccer_france_ligue_one",
        prestige_weight=8,
    ),
    LeaguePolicy(
        key="eredivisie",
        name="Eredivisie",
        country_code="NL",
        openligadb_shortcut="nl1",
        football_data_code="DED",
        odds_sport_key="soccer_netherlands_eredivisie",
        prestige_weight=7,
    ),
    LeaguePolicy(
        key="primeira",
        name="Primeira Liga",
        country_code="PT",
        openligadb_shortcut="pt1",
        football_data_code="PPL",
        odds_sport_key="soccer_portugal_primeira_liga",
        prestige_weight=7,
    ),
    LeaguePolicy(
        key="super_lig",
        name="Süper Lig",
        country_code="TR",
        openligadb_shortcut="tr1",
        football_data_code=None,
        odds_sport_key="soccer_turkey_super_league",
        prestige_weight=7,
    ),
    LeaguePolicy(
        key="championship",
        name="Championship",
        country_code="GB",
        openligadb_shortcut="eng2",
        football_data_code="ELC",
        odds_sport_key="soccer_efl_champ",
        prestige_weight=6,
    ),
    LeaguePolicy(
        key="mls",
        name="MLS",
        country_code="US",
        openligadb_shortcut="mls",
        football_data_code=None,
        odds_sport_key="soccer_usa_mls",
        prestige_weight=6,
    ),
)


def league_for_fixture(fixture: CanonicalFixture) -> LeaguePolicy | None:
    key_parts = fixture.competition_key.casefold().split(":")
    shortcut = key_parts[1] if len(key_parts) >= 3 else ""
    for league in TOP_LEAGUES:
        if (
            shortcut == league.openligadb_shortcut
            or fixture.competition_key.startswith(
                f"football-data:{(league.football_data_code or '').casefold()}:"
            )
            or fixture.competition_key == f"theodds:{league.odds_sport_key}"
            or fixture.competition_key == f"oddsapiio:{_ODDS_API_IO_LEAGUE_SLUGS[league.key]}"
            or fixture.competition_key.startswith(f"rapidapi:{league.key}:")
            or fixture.competition_key.startswith(f"api-football:{league.key}:")
            or fixture.competition_key.startswith(f"espn-core:{league.key}:")
        ):
            return league
    return None


_ODDS_API_IO_LEAGUE_SLUGS: dict[str, str] = {
    "epl": "england-premier-league",
    "laliga": "spain-laliga",
    "bundesliga": "germany-bundesliga",
    "serie_a": "italy-serie-a",
    "ligue_1": "france-ligue-1",
    "eredivisie": "netherlands-eredivisie",
    "primeira": "portugal-liga-portugal",
    "super_lig": "turkiye-super-lig",
    "championship": "england-championship",
    "mls": "usa-mls",
}


class MarketOdds(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: BookmakerSource = "the_odds_api"
    event_id: str | None = None
    observed_at: datetime
    bookmaker_count: int = Field(ge=1)
    home_decimal: Decimal = Field(gt=1)
    draw_decimal: Decimal = Field(gt=1)
    away_decimal: Decimal = Field(gt=1)
    fair_home_probability: Decimal = Field(gt=0, lt=1)
    fair_draw_probability: Decimal = Field(gt=0, lt=1)
    fair_away_probability: Decimal = Field(gt=0, lt=1)
    quotes: tuple[MarketQuote, ...] = ()

    @model_validator(mode="after")
    def fair_probabilities_sum_to_one(self) -> "MarketOdds":
        total = self.fair_home_probability + self.fair_draw_probability + self.fair_away_probability
        if abs(total - Decimal("1")) > Decimal(".000001"):
            raise ValueError("fair market probabilities must sum to one")
        return self


class AutoCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fixture: CanonicalFixture
    league: LeaguePolicy
    auto_score: int = Field(ge=0, le=100)
    market_odds: MarketOdds | None = None
    memory_case_count: int = Field(ge=0)
    positive_factors: tuple[str, ...]
    risk_flags: tuple[str, ...]


class FunnelDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    stage: Literal["rough", "critic"]
    input_count: int = Field(ge=0)
    selected_fixture_ids: tuple[UUID, ...]
    eliminated_fixture_ids: tuple[UUID, ...]
    rationale: str = Field(min_length=12, max_length=800)
    model_id: str


class DecisionRationale(BaseModel):
    """Immutable reasons captured before kickoff for later process auditing."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    market_thesis: str = Field(min_length=12, max_length=800)
    supporting_evidence: tuple[str, ...] = ()
    counter_evidence: tuple[str, ...] = ()
    price_rationale: str = Field(min_length=12, max_length=500)
    invalidation_conditions: tuple[str, ...] = ()
    model_disagreement: str = Field(min_length=8, max_length=500)
    evidence_cutoff_at: datetime


class CouponSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fixture: CanonicalFixture
    league: LeaguePolicy
    analysis_run_id: UUID | None
    lock_id: UUID | None
    pick: Pick
    market_key: MarketKey = "h2h"
    market_label: str = "Maç sonucu"
    outcome_label: str = ""
    market_description: str | None = None
    line: Decimal | None = None
    probability: Decimal = Field(gt=0, lt=1)
    model_fair_odds: Decimal = Field(gt=1)
    market_decimal_odds: Decimal | None = Field(default=None, gt=1)
    market_fair_probability: Decimal | None = Field(default=None, gt=0, lt=1)
    edge: Decimal | None = None
    bookmaker_count: int = Field(default=0, ge=0)
    bookmaker: str | None = None
    price_observed_at: datetime | None = None
    confidence: Decimal = Field(ge=0, le=1)
    value_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    reason: str = Field(min_length=8, max_length=500)
    uncertainty: str = Field(min_length=8, max_length=500)
    rationale: DecisionRationale | None = None
    settlement_status: Literal["pending", "won", "lost", "void"] = "pending"
    final_home_score: int | None = Field(default=None, ge=0)
    final_away_score: int | None = Field(default=None, ge=0)
    settlement_explanation: str | None = Field(default=None, min_length=8, max_length=900)
    process_verdict: Literal[
        "pending",
        "sound_win",
        "lucky_win",
        "sound_but_unlucky_loss",
        "bad_process_loss",
        "insufficient_data",
    ] = "pending"


class CouponTicket(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["single", "double", "treble"]
    label: str
    selection_fixture_ids: tuple[UUID, ...]
    combined_probability: Decimal = Field(gt=0, lt=1)
    combined_decimal_odds: Decimal = Field(gt=1)
    odds_source: Literal[
        "bookmaker_average",
        "bookmaker_consensus",
        "best_bookmaker_quotes",
        "model_fair_odds",
    ]
    risk_label: Literal["düşük", "orta", "yüksek"]


class DailyPrediction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    prediction_id: UUID
    fixture: CanonicalFixture
    league: LeaguePolicy
    pick: Pick
    market_key: MarketKey
    market_label: str
    outcome_label: str
    market_description: str | None = None
    line: Decimal | None = None
    probability: Decimal = Field(gt=0, lt=1)
    market_decimal_odds: Decimal | None = Field(default=None, gt=1)
    market_fair_probability: Decimal | None = Field(default=None, gt=0, lt=1)
    bookmaker_count: int = Field(ge=0)
    bookmaker: str | None = None
    confidence: Decimal = Field(ge=0, le=1)
    score: Decimal = Field(ge=0, le=100)
    tier: Literal["journal_only", "watchlist", "coupon_candidate"]
    reasons: tuple[str, ...] = Field(min_length=1)
    risks: tuple[str, ...] = Field(min_length=1)
    observed_at: datetime


class DailyPredictionReviewItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    prediction_id: UUID
    fixture_id: UUID
    pick: Pick
    status: Literal["won", "lost", "void"]
    final_home_score: int
    final_away_score: int
    probability: Decimal = Field(gt=0, lt=1)
    market_decimal_odds: Decimal | None = Field(default=None, gt=1)
    process_verdict: Literal[
        "sound_win",
        "lucky_win",
        "sound_but_unlucky_loss",
        "bad_process_loss",
        "insufficient_data",
    ]
    explanation: str = Field(min_length=12, max_length=900)
    lesson: str = Field(min_length=12, max_length=900)


class DailyReviewReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    reviewed_at: datetime
    total_predictions: int = Field(ge=0)
    settled_predictions: int = Field(ge=0)
    wins: int = Field(ge=0)
    losses: int = Field(ge=0)
    voids: int = Field(ge=0)
    hit_rate: Decimal | None = Field(default=None, ge=0, le=1)
    average_odds: Decimal | None = Field(default=None, gt=1)
    brier_score: Decimal | None = Field(default=None, ge=0, le=1)
    equal_stake_roi: Decimal | None = None
    summary: str = Field(min_length=12, max_length=1200)
    items: tuple[DailyPredictionReviewItem, ...] = ()


class AutoCouponRun(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["auto-coupon.v1"] = "auto-coupon.v1"
    run_id: UUID
    state: Literal["completed", "settled"]
    source_mode: Literal["bookmaker_live", "fixture_live_model_odds", "fixture_live_no_odds"]
    observed_at: datetime
    allowed_leagues: tuple[LeaguePolicy, ...] = TOP_LEAGUES
    covered_league_keys: tuple[str, ...]
    initial_candidates: tuple[AutoCandidate, ...]
    rough_decision: FunnelDecision
    critic_decision: FunnelDecision
    daily_predictions: tuple[DailyPrediction, ...] = ()
    selections: tuple[CouponSelection, ...]
    tickets: tuple[CouponTicket, ...]
    post_match_review: DailyReviewReport | None = None
    rag_case_count: int = Field(ge=0)
    actual_cost_usd: Decimal = Field(ge=0)
    notice: str = "Olasılıksal seçimdir; kesinlik veya bahis tavsiyesi değildir."


class MarketPerformance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    market_key: str
    settled: int = Field(ge=0)
    wins: int = Field(ge=0)
    losses: int = Field(ge=0)
    voids: int = Field(ge=0)
    hit_rate: Decimal | None = Field(default=None, ge=0, le=1)
    average_odds: Decimal | None = Field(default=None, gt=1)
    equal_stake_roi: Decimal | None = None


class CalibrationBand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str
    lower: Decimal = Field(ge=0, le=1)
    upper: Decimal = Field(ge=0, le=1)
    settled: int = Field(ge=0)
    wins: int = Field(ge=0)
    losses: int = Field(ge=0)
    hit_rate: Decimal | None = Field(default=None, ge=0, le=1)
    average_predicted_probability: Decimal | None = Field(default=None, ge=0, le=1)
    calibration_error: Decimal | None = Field(default=None, ge=0, le=1)


class AutoCouponPerformance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    settled: int = Field(ge=0)
    wins: int = Field(ge=0)
    losses: int = Field(ge=0)
    voids: int = Field(ge=0)
    hit_rate: Decimal | None = Field(default=None, ge=0, le=1)
    average_odds: Decimal | None = Field(default=None, gt=1)
    average_predicted_probability: Decimal | None = Field(default=None, ge=0, le=1)
    brier_score: Decimal | None = Field(default=None, ge=0, le=1)
    equal_stake_roi: Decimal | None = None
    process_verdicts: dict[str, int]
    by_market: tuple[MarketPerformance, ...]
    calibration: tuple[CalibrationBand, ...] = ()
    sample_size_status: Literal["empty", "early", "monitor", "meaningful"]
    notice: str


class AutoCouponReadiness(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ready: bool
    live_fixtures: bool
    live_bookmaker_odds: bool
    gemini_analysis: bool
    deep_structured_data: bool
    deep_analysis_ready: bool
    implemented_analysis_stages: tuple[str, ...]
    required_analysis_stages: tuple[str, ...]
    supported_market_keys: tuple[str, ...]
    blockers: tuple[str, ...]
    notice: str
