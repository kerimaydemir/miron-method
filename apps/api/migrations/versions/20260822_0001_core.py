"""Create canonical discovery, workflow, audit, and lock core.

Revision ID: 20260822_0001
Revises: None
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260822_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("""
    CREATE TABLE sports (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      sport_key text NOT NULL UNIQUE,
      plugin_key text NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now(),
      row_version bigint NOT NULL DEFAULT 0
    );
    CREATE TABLE competitions (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), sport_id uuid NOT NULL REFERENCES sports(id),
      competition_key text NOT NULL, name text NOT NULL, country_code char(2),
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), row_version bigint NOT NULL DEFAULT 0,
      UNIQUE (sport_id, competition_key)
    );
    CREATE TABLE teams (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), sport_id uuid NOT NULL REFERENCES sports(id),
      name text NOT NULL, country_code char(2),
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), row_version bigint NOT NULL DEFAULT 0
    );
    CREATE TABLE team_aliases (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), team_id uuid NOT NULL REFERENCES teams(id), provider_id text NOT NULL,
      alias_nfkc text NOT NULL, effective_start timestamptz, effective_end timestamptz, confidence numeric(5,4) NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now(), CHECK (confidence BETWEEN 0 AND 1), UNIQUE(provider_id, alias_nfkc, effective_start)
    );
    CREATE TABLE fixtures (
      id uuid PRIMARY KEY, sport_id uuid NOT NULL REFERENCES sports(id), competition_id uuid NOT NULL REFERENCES competitions(id),
      home_team_id uuid NOT NULL REFERENCES teams(id), away_team_id uuid NOT NULL REFERENCES teams(id), kickoff_at timestamptz NOT NULL,
      status text NOT NULL DEFAULT 'scheduled', current_version integer NOT NULL DEFAULT 1,
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), row_version bigint NOT NULL DEFAULT 0,
      CHECK (home_team_id <> away_team_id)
    );
    CREATE TABLE fixture_versions (
      fixture_id uuid NOT NULL REFERENCES fixtures(id), version integer NOT NULL, kickoff_at timestamptz NOT NULL, status text NOT NULL,
      observed_at timestamptz NOT NULL, source_snapshot_id uuid, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(fixture_id, version)
    );
    CREATE TABLE scan_runs (
      id uuid PRIMARY KEY, timezone text NOT NULL CHECK(timezone = 'Europe/Istanbul'), start_utc timestamptz NOT NULL,
      end_exclusive_utc timestamptz NOT NULL, local_dates date[] NOT NULL, state text NOT NULL, correlation_id uuid NOT NULL,
      config_version text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), CHECK(cardinality(local_dates) = 3),
      CHECK(end_exclusive_utc > start_utc)
    );
    CREATE TABLE scan_candidates (
      scan_run_id uuid NOT NULL REFERENCES scan_runs(id), fixture_id uuid NOT NULL REFERENCES fixtures(id), rank integer NOT NULL,
      worthwhile_score integer NOT NULL CHECK(worthwhile_score BETWEEN 0 AND 100), factor_json jsonb NOT NULL,
      fixture_version integer NOT NULL, estimated_cost_usd numeric(12,6) NOT NULL CHECK(estimated_cost_usd >= 0),
      created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(scan_run_id, fixture_id), UNIQUE(scan_run_id, rank)
    );
    CREATE TABLE config_snapshots (
      id uuid PRIMARY KEY, schema_version text NOT NULL, config_json jsonb NOT NULL, sha256 char(64) NOT NULL UNIQUE,
      created_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE analysis_runs (
      id uuid PRIMARY KEY, fixture_id uuid NOT NULL REFERENCES fixtures(id), state text NOT NULL, cutoff_at timestamptz NOT NULL,
      kickoff_at_snapshot timestamptz NOT NULL, config_snapshot_id uuid NOT NULL REFERENCES config_snapshots(id),
      prompt_bundle_version text NOT NULL, reserved_cost_usd numeric(12,6) NOT NULL DEFAULT 0, actual_cost_usd numeric(12,6) NOT NULL DEFAULT 0,
      degraded_reasons jsonb NOT NULL DEFAULT '[]', correlation_id uuid NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now(), row_version bigint NOT NULL DEFAULT 0,
      CHECK(cutoff_at <= kickoff_at_snapshot), CHECK(reserved_cost_usd >= 0), CHECK(actual_cost_usd >= 0)
    );
    CREATE TABLE run_state_transitions (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), analysis_run_id uuid NOT NULL REFERENCES analysis_runs(id),
      from_state text, to_state text NOT NULL, reason_code text NOT NULL, actor_type text NOT NULL, actor_id text NOT NULL,
      occurred_at timestamptz NOT NULL, correlation_id uuid NOT NULL, prior_state_json jsonb,
      UNIQUE(analysis_run_id, to_state, occurred_at, reason_code)
    );
    CREATE TABLE stage_runs (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), analysis_run_id uuid NOT NULL REFERENCES analysis_runs(id), stage_id text NOT NULL,
      attempt integer NOT NULL DEFAULT 1, status text NOT NULL, input_hash char(64) NOT NULL, output_hash char(64),
      started_at timestamptz, completed_at timestamptz, error_code text, cost_usd numeric(12,6) NOT NULL DEFAULT 0,
      UNIQUE(analysis_run_id, stage_id, attempt), CHECK(cost_usd >= 0)
    );
    CREATE TABLE forecast_versions (
      id uuid PRIMARY KEY, analysis_run_id uuid NOT NULL REFERENCES analysis_runs(id), version integer NOT NULL,
      forecast_json jsonb NOT NULL, forecast_sha256 char(64) NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE(analysis_run_id, version), UNIQUE(analysis_run_id, forecast_sha256)
    );
    CREATE TABLE prediction_locks (
      id uuid PRIMARY KEY, analysis_run_id uuid NOT NULL UNIQUE REFERENCES analysis_runs(id),
      forecast_version_id uuid NOT NULL UNIQUE REFERENCES forecast_versions(id), cutoff_at timestamptz NOT NULL,
      locked_at timestamptz NOT NULL, kickoff_at_snapshot timestamptz NOT NULL, manifest_json jsonb NOT NULL,
      manifest_sha256 char(64) NOT NULL UNIQUE, signature text, object_uri text NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now(), CHECK(locked_at < kickoff_at_snapshot)
    );
    CREATE TABLE idempotency_records (
      workspace_id text NOT NULL, route text NOT NULL, caller_key text NOT NULL, request_hash char(64) NOT NULL,
      status text NOT NULL, resource_id uuid, response_json jsonb, created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(workspace_id, route, caller_key)
    );
    CREATE TABLE audit_events (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), event_name text NOT NULL, actor_type text NOT NULL, actor_id text NOT NULL,
      analysis_run_id uuid REFERENCES analysis_runs(id), correlation_id uuid NOT NULL, reason_code text NOT NULL,
      prior_state jsonb, new_state jsonb, occurred_at timestamptz NOT NULL, metadata jsonb NOT NULL DEFAULT '{}'
    );
    CREATE TABLE outbox_events (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), aggregate_type text NOT NULL, aggregate_id uuid NOT NULL,
      event_type text NOT NULL, payload jsonb NOT NULL, occurred_at timestamptz NOT NULL, published_at timestamptz,
      attempt_count integer NOT NULL DEFAULT 0
    );
    CREATE INDEX ix_fixtures_kickoff ON fixtures(kickoff_at, competition_id);
    CREATE INDEX ix_scan_candidates_rank ON scan_candidates(scan_run_id, rank);
    CREATE INDEX ix_stage_runs_run_status ON stage_runs(analysis_run_id, status);
    CREATE INDEX ix_audit_events_run_time ON audit_events(analysis_run_id, occurred_at);
    CREATE INDEX ix_outbox_unpublished ON outbox_events(occurred_at) WHERE published_at IS NULL;
    """)
    op.execute("""
    CREATE FUNCTION forbid_prediction_lock_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN RAISE EXCEPTION 'prediction_locks are immutable'; END; $$;
    CREATE TRIGGER prediction_locks_no_update BEFORE UPDATE OR DELETE ON prediction_locks
    FOR EACH ROW EXECUTE FUNCTION forbid_prediction_lock_mutation();

    CREATE FUNCTION forbid_state_transition_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN RAISE EXCEPTION 'run_state_transitions are append-only'; END; $$;
    CREATE TRIGGER run_state_transitions_no_update BEFORE UPDATE OR DELETE ON run_state_transitions
    FOR EACH ROW EXECUTE FUNCTION forbid_state_transition_mutation();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS run_state_transitions_no_update ON run_state_transitions")
    op.execute("DROP FUNCTION IF EXISTS forbid_state_transition_mutation")
    op.execute("DROP TRIGGER IF EXISTS prediction_locks_no_update ON prediction_locks")
    op.execute("DROP FUNCTION IF EXISTS forbid_prediction_lock_mutation")
    for table in (
        "outbox_events",
        "audit_events",
        "idempotency_records",
        "prediction_locks",
        "forecast_versions",
        "stage_runs",
        "run_state_transitions",
        "analysis_runs",
        "config_snapshots",
        "scan_candidates",
        "scan_runs",
        "fixture_versions",
        "fixtures",
        "team_aliases",
        "teams",
        "competitions",
        "sports",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
