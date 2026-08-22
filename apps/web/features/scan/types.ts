export type RankedFixture = {
  fixture: {
    id: string;
    competition_name: string;
    home_team: string;
    away_team: string;
    kickoff_at: string;
    source_provider: "mock_fixture" | "openligadb" | "football_data_org";
    provider_fixture_id: string | null;
    status: "scheduled" | "live" | "finished";
    home_score: number | null;
    away_score: number | null;
    observed_at: string | null;
  };
  worthwhile_score: number;
  estimated_cost_usd: string;
  positive_factors: string[];
  negative_factors: string[];
  coverage_label: string;
  market_label: string;
};

export type ScanResult = {
  scan_id: string;
  status: "completed";
  timezone: "Europe/Istanbul";
  local_dates: [string, string, string];
  candidates: RankedFixture[];
  source: string;
  source_observed_at: string | null;
};
