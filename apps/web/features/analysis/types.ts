export type StageView = {
  stage_id: string;
  name: string;
  status: string;
  summary: string;
  cost_usd: string;
};
export type OutcomeProbability = {
  outcome: "home" | "draw" | "away";
  probability: string;
  lower: string;
  upper: string;
};
export type AnalysisRun = {
  run_id: string;
  fixture_id: string;
  state: "LOCKING" | "LOCKED";
  cutoff_at: string;
  kickoff_at_snapshot: string;
  stages: StageView[];
  forecast: {
    outcome_probabilities: OutcomeProbability[];
    expected_home_goals: string;
    expected_away_goals: string;
    confidence: string;
    calibration_status: string;
    uncertainty_drivers: string[];
    decisive_evidence: string[];
    dissent_summary: string[];
    responsible_use_notice: string;
    analysis_provider: "mock" | "google_gemini";
    model_ids: string[];
  };
  actual_cost_usd: string;
  lock_id: string | null;
  lock_sha256: string | null;
};

export type StageDossier = {
  summary?: string;
  findings?: string[];
  evidence_refs?: string[];
  counterpoints?: string[];
  unknowns?: string[];
  team_news?: string[];
  coach_notes?: string[];
  likely_lineups?: string[];
  player_notes?: string[];
  citations?: string[];
};

export type AnalysisEvidenceDossier = {
  analysis_run_id: string;
  provider: string;
  observed_at: string;
  coverage: Record<string, boolean>;
  evidence_sha256: string;
  stage_outputs: Record<string, StageDossier>;
};
