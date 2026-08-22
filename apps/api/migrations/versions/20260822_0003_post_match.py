"""Add post-match result, autopsy, variance, lesson, and case memory.

Revision ID: 20260822_0003
Revises: 20260822_0002
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260822_0003"
down_revision: str | None = "20260822_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE match_results (
      id uuid PRIMARY KEY,
      fixture_id uuid NOT NULL REFERENCES fixtures(id),
      prediction_lock_id uuid NOT NULL REFERENCES prediction_locks(id),
      home_score integer NOT NULL CHECK(home_score BETWEEN 0 AND 30),
      away_score integer NOT NULL CHECK(away_score BETWEEN 0 AND 30),
      status text NOT NULL CHECK(status = 'final'),
      observed_at timestamptz NOT NULL,
      source text NOT NULL,
      result_version integer NOT NULL CHECK(result_version > 0),
      result_json jsonb NOT NULL CHECK(octet_length(result_json::text) <= 65536),
      created_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE(prediction_lock_id, result_version)
    );
    CREATE TABLE autopsies (
      id uuid PRIMARY KEY,
      prediction_lock_id uuid NOT NULL UNIQUE REFERENCES prediction_locks(id),
      analysis_run_id uuid NOT NULL REFERENCES analysis_runs(id),
      match_result_id uuid NOT NULL UNIQUE REFERENCES match_results(id),
      pre_match_lock_sha256 char(64) NOT NULL,
      brier_score numeric(12,8) NOT NULL CHECK(brier_score BETWEEN 0 AND 2),
      result_verdict text NOT NULL,
      process_verdict text NOT NULL,
      autopsy_json jsonb NOT NULL CHECK(octet_length(autopsy_json::text) <= 262144),
      created_at timestamptz NOT NULL
    );
    CREATE TABLE variance_attributions (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      autopsy_id uuid NOT NULL REFERENCES autopsies(id),
      category text NOT NULL,
      weight numeric(8,7) NOT NULL CHECK(weight BETWEEN 0 AND 1),
      rationale text NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE(autopsy_id, category)
    );
    CREATE TABLE lessons (
      id uuid PRIMARY KEY,
      autopsy_id uuid NOT NULL REFERENCES autopsies(id),
      status text NOT NULL CHECK(status IN ('candidate', 'validated', 'rejected')),
      scope text NOT NULL,
      statement text NOT NULL,
      confidence numeric(5,4) NOT NULL CHECK(confidence BETWEEN 0 AND 1),
      hindsight_safe boolean NOT NULL,
      supporting_lock_sha256 char(64) NOT NULL,
      created_at timestamptz NOT NULL,
      updated_at timestamptz NOT NULL,
      row_version bigint NOT NULL DEFAULT 0
    );
    CREATE TABLE cases (
      id uuid PRIMARY KEY,
      prediction_lock_id uuid NOT NULL UNIQUE REFERENCES prediction_locks(id),
      autopsy_id uuid NOT NULL UNIQUE REFERENCES autopsies(id),
      case_json jsonb NOT NULL CHECK(octet_length(case_json::text) <= 262144),
      created_at timestamptz NOT NULL
    );
    CREATE INDEX ix_match_results_fixture_observed ON match_results(fixture_id, observed_at);
    CREATE INDEX ix_lessons_status_scope ON lessons(status, scope);
    """)


def downgrade() -> None:
    for table in ("cases", "lessons", "variance_attributions", "autopsies", "match_results"):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
