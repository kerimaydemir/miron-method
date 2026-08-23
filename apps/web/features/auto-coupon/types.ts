export type Pick = string;

export type LeaguePolicy = {
  key: string;
  name: string;
  country_code: string;
  openligadb_shortcut: string;
  football_data_code: string | null;
  odds_sport_key: string;
  prestige_weight: number;
};

export type Fixture = {
  id: string;
  sport_key: string;
  competition_key: string;
  competition_name: string;
  home_team: string;
  away_team: string;
  kickoff_at: string;
  venue_name: string | null;
  source_provider:
    | "mock_fixture"
    | "openligadb"
    | "football_data_org"
    | "the_odds_api"
    | "rapidapi_football";
  provider_fixture_id: string | null;
  status: "scheduled" | "live" | "finished";
  home_score: number | null;
  away_score: number | null;
  observed_at: string | null;
};

export type MarketOdds = {
  provider: "the_odds_api" | "rapidapi_football" | "api_football";
  observed_at: string;
  bookmaker_count: number;
  home_decimal: string;
  draw_decimal: string;
  away_decimal: string;
  fair_home_probability: string;
  fair_draw_probability: string;
  fair_away_probability: string;
};

export type AutoCandidate = {
  fixture: Fixture;
  league: LeaguePolicy;
  auto_score: number;
  market_odds: MarketOdds | null;
  memory_case_count: number;
  positive_factors: string[];
  risk_flags: string[];
};

export type FunnelDecision = {
  stage: "rough" | "critic";
  input_count: number;
  selected_fixture_ids: string[];
  eliminated_fixture_ids: string[];
  rationale: string;
  model_id: string;
};

export type CouponSelection = {
  fixture: Fixture;
  league: LeaguePolicy;
  analysis_run_id: string;
  lock_id: string;
  pick: Pick;
  market_key:
    | "h2h"
    | "draw_no_bet"
    | "btts"
    | "totals"
    | "alternate_totals"
    | "team_totals"
    | "alternate_team_totals";
  market_label: string;
  outcome_label: string;
  market_description: string | null;
  line: string | null;
  probability: string;
  model_fair_odds: string;
  market_decimal_odds: string | null;
  market_fair_probability: string | null;
  edge: string | null;
  bookmaker_count: number;
  price_observed_at: string | null;
  confidence: string;
  value_score: string;
  reason: string;
  uncertainty: string;
  rationale: {
    market_thesis: string;
    supporting_evidence: string[];
    counter_evidence: string[];
    price_rationale: string;
    invalidation_conditions: string[];
    model_disagreement: string;
    evidence_cutoff_at: string;
  } | null;
  settlement_status: "pending" | "won" | "lost" | "void";
  process_verdict:
    | "pending"
    | "sound_win"
    | "lucky_win"
    | "sound_but_unlucky_loss"
    | "bad_process_loss"
    | "insufficient_data";
};

export type CouponTicket = {
  kind: "single" | "double" | "treble";
  label: string;
  selection_fixture_ids: string[];
  combined_probability: string;
  combined_decimal_odds: string;
  odds_source: "bookmaker_average" | "model_fair_odds";
  risk_label: "düşük" | "orta" | "yüksek";
};

export type DailyPrediction = {
  prediction_id: string;
  fixture: Fixture;
  league: LeaguePolicy;
  pick: Pick;
  market_key:
    | "h2h"
    | "draw_no_bet"
    | "btts"
    | "totals"
    | "alternate_totals"
    | "team_totals"
    | "alternate_team_totals";
  market_label: string;
  outcome_label: string;
  market_description: string | null;
  line: string | null;
  probability: string;
  market_decimal_odds: string | null;
  market_fair_probability: string | null;
  bookmaker_count: number;
  confidence: string;
  score: string;
  tier: "journal_only" | "watchlist" | "coupon_candidate";
  reasons: string[];
  risks: string[];
  observed_at: string;
};

export type DailyReviewReport = {
  reviewed_at: string;
  total_predictions: number;
  settled_predictions: number;
  wins: number;
  losses: number;
  voids: number;
  hit_rate: string | null;
  average_odds: string | null;
  brier_score: string | null;
  equal_stake_roi: string | null;
  summary: string;
  items: Array<{
    prediction_id: string;
    fixture_id: string;
    pick: Pick;
    status: "won" | "lost" | "void";
    final_home_score: number;
    final_away_score: number;
    probability: string;
    market_decimal_odds: string | null;
    process_verdict:
      | "sound_win"
      | "lucky_win"
      | "sound_but_unlucky_loss"
      | "bad_process_loss"
      | "insufficient_data";
    explanation: string;
    lesson: string;
  }>;
};

export type AutoCouponRun = {
  schema_version: "auto-coupon.v1";
  run_id: string;
  state: "completed" | "settled";
  source_mode:
    | "bookmaker_live"
    | "fixture_live_model_odds"
    | "fixture_live_no_odds";
  observed_at: string;
  allowed_leagues: LeaguePolicy[];
  covered_league_keys: string[];
  initial_candidates: AutoCandidate[];
  rough_decision: FunnelDecision;
  critic_decision: FunnelDecision;
  daily_predictions: DailyPrediction[];
  selections: CouponSelection[];
  tickets: CouponTicket[];
  post_match_review: DailyReviewReport | null;
  rag_case_count: number;
  actual_cost_usd: string;
  notice: string;
};

export type AutoCouponReadiness = {
  ready: boolean;
  live_fixtures: boolean;
  live_bookmaker_odds: boolean;
  gemini_analysis: boolean;
  deep_structured_data: boolean;
  deep_analysis_ready: boolean;
  implemented_analysis_stages: string[];
  required_analysis_stages: string[];
  supported_market_keys: string[];
  blockers: string[];
  notice: string;
};

export type AutoCouponPerformance = {
  settled: number;
  wins: number;
  losses: number;
  voids: number;
  hit_rate: string | null;
  average_odds: string | null;
  average_predicted_probability: string | null;
  brier_score: string | null;
  equal_stake_roi: string | null;
  process_verdicts: Record<string, number>;
  by_market: Array<{
    market_key: string;
    settled: number;
    wins: number;
    losses: number;
    voids: number;
    hit_rate: string | null;
    average_odds: string | null;
    equal_stake_roi: string | null;
  }>;
  sample_size_status: "empty" | "early" | "monitor" | "meaningful";
  notice: string;
};
