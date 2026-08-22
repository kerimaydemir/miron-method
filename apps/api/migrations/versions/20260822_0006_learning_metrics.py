"""Persist market rationale and post-match learning metrics.

Revision ID: 20260822_0006
Revises: 20260822_0005
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260822_0006"
down_revision: str | None = "20260822_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
    ALTER TABLE coupon_selections DROP CONSTRAINT coupon_selections_pick_check;
    ALTER TABLE coupon_selections
      ADD COLUMN market_key text NOT NULL DEFAULT 'h2h',
      ADD COLUMN market_label text NOT NULL DEFAULT 'Maç sonucu',
      ADD COLUMN outcome_label text NOT NULL DEFAULT '',
      ADD COLUMN line numeric(12,5),
      ADD COLUMN market_fair_probability numeric(8,7),
      ADD COLUMN edge numeric(9,8),
      ADD COLUMN bookmaker_count integer NOT NULL DEFAULT 0 CHECK(bookmaker_count >= 0),
      ADD COLUMN price_observed_at timestamptz,
      ADD COLUMN value_score numeric(7,2) NOT NULL DEFAULT 0 CHECK(value_score >= 0),
      ADD COLUMN rationale_json jsonb,
      ADD COLUMN process_verdict text NOT NULL DEFAULT 'pending'
        CHECK(process_verdict IN (
          'pending', 'sound_win', 'lucky_win', 'sound_but_unlucky_loss',
          'bad_process_loss', 'insufficient_data'
        )),
      ADD COLUMN final_home_score integer,
      ADD COLUMN final_away_score integer,
      ADD COLUMN post_match_json jsonb;
    CREATE INDEX ix_coupon_selections_market_settled
      ON coupon_selections(market_key, settlement_status, settled_at DESC);
    """)


def downgrade() -> None:
    op.execute("""
    DROP INDEX IF EXISTS ix_coupon_selections_market_settled;
    ALTER TABLE coupon_selections
      DROP COLUMN post_match_json,
      DROP COLUMN final_away_score,
      DROP COLUMN final_home_score,
      DROP COLUMN process_verdict,
      DROP COLUMN rationale_json,
      DROP COLUMN value_score,
      DROP COLUMN price_observed_at,
      DROP COLUMN bookmaker_count,
      DROP COLUMN edge,
      DROP COLUMN market_fair_probability,
      DROP COLUMN line,
      DROP COLUMN outcome_label,
      DROP COLUMN market_label,
      DROP COLUMN market_key;
    ALTER TABLE coupon_selections
      ADD CONSTRAINT coupon_selections_pick_check CHECK(pick IN ('home', 'draw', 'away'));
    """)
