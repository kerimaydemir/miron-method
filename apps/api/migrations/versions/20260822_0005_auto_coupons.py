"""Add automatic coupon funnel and searchable case memory.

Revision ID: 20260822_0005
Revises: 20260822_0004
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260822_0005"
down_revision: str | None = "20260822_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE auto_coupon_runs (
      id uuid PRIMARY KEY,
      state text NOT NULL CHECK(state IN ('completed', 'settled')),
      source_mode text NOT NULL,
      run_json jsonb NOT NULL CHECK(octet_length(run_json::text) <= 1048576),
      actual_cost_usd numeric(12,6) NOT NULL CHECK(actual_cost_usd >= 0),
      created_at timestamptz NOT NULL,
      updated_at timestamptz NOT NULL
    );
    CREATE TABLE coupon_selections (
      auto_coupon_run_id uuid NOT NULL REFERENCES auto_coupon_runs(id),
      fixture_id uuid NOT NULL REFERENCES fixtures(id),
      analysis_run_id uuid NOT NULL REFERENCES analysis_runs(id),
      prediction_lock_id uuid NOT NULL REFERENCES prediction_locks(id),
      pick text NOT NULL CHECK(pick IN ('home', 'draw', 'away')),
      probability numeric(8,7) NOT NULL CHECK(probability > 0 AND probability < 1),
      model_fair_odds numeric(12,5) NOT NULL CHECK(model_fair_odds > 1),
      market_decimal_odds numeric(12,5),
      settlement_status text NOT NULL DEFAULT 'pending'
        CHECK(settlement_status IN ('pending', 'won', 'lost', 'void')),
      autopsy_id uuid REFERENCES autopsies(id),
      settled_at timestamptz,
      created_at timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY(auto_coupon_run_id, fixture_id),
      UNIQUE(prediction_lock_id)
    );
    CREATE TABLE case_memory_chunks (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      case_id uuid NOT NULL UNIQUE REFERENCES cases(id),
      fixture_id uuid NOT NULL REFERENCES fixtures(id),
      competition_key text NOT NULL,
      home_team text NOT NULL,
      away_team text NOT NULL,
      predicted_outcome text NOT NULL,
      realized_outcome text NOT NULL,
      result_verdict text NOT NULL,
      search_text text NOT NULL,
      case_json jsonb NOT NULL CHECK(octet_length(case_json::text) <= 262144),
      created_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE INDEX ix_coupon_selections_pending
      ON coupon_selections(settlement_status, fixture_id)
      WHERE settlement_status = 'pending';
    CREATE INDEX ix_case_memory_search
      ON case_memory_chunks USING gin(to_tsvector('simple', search_text));
    CREATE INDEX ix_case_memory_competition ON case_memory_chunks(competition_key, created_at DESC);
    """)


def downgrade() -> None:
    for table in ("case_memory_chunks", "coupon_selections", "auto_coupon_runs"):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
