"""Persist full pre-match evidence and structured Gemini dossiers.

Revision ID: 20260822_0007
Revises: 20260822_0006
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260822_0007"
down_revision: str | None = "20260822_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE stage_runs ADD COLUMN output_json jsonb NOT NULL DEFAULT '{}'::jsonb")
    op.execute("""
    CREATE TABLE analysis_evidence_snapshots (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      analysis_run_id uuid NOT NULL UNIQUE REFERENCES analysis_runs(id),
      provider text NOT NULL,
      observed_at timestamptz NOT NULL,
      coverage_json jsonb NOT NULL,
      evidence_json jsonb NOT NULL,
      evidence_sha256 char(64) NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE UNIQUE INDEX ux_analysis_evidence_sha
      ON analysis_evidence_snapshots(analysis_run_id, evidence_sha256);

    CREATE FUNCTION forbid_analysis_evidence_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN RAISE EXCEPTION 'analysis_evidence_snapshots are immutable'; END; $$;
    CREATE TRIGGER analysis_evidence_no_update
      BEFORE UPDATE OR DELETE ON analysis_evidence_snapshots
      FOR EACH ROW EXECUTE FUNCTION forbid_analysis_evidence_mutation();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS analysis_evidence_no_update ON analysis_evidence_snapshots")
    op.execute("DROP FUNCTION IF EXISTS forbid_analysis_evidence_mutation")
    op.execute("DROP TABLE IF EXISTS analysis_evidence_snapshots")
    op.execute("ALTER TABLE stage_runs DROP COLUMN IF EXISTS output_json")
