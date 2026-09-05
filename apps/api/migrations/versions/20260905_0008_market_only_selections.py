"""Allow honest market-only selections without fabricated analysis locks.

Revision ID: 20260905_0008
Revises: 20260822_0007
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260905_0008"
down_revision: str | None = "20260822_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
    ALTER TABLE coupon_selections
      ALTER COLUMN analysis_run_id DROP NOT NULL,
      ALTER COLUMN prediction_lock_id DROP NOT NULL;
    """)


def downgrade() -> None:
    op.execute("""
    DELETE FROM coupon_selections
    WHERE analysis_run_id IS NULL OR prediction_lock_id IS NULL;
    ALTER TABLE coupon_selections
      ALTER COLUMN analysis_run_id SET NOT NULL,
      ALTER COLUMN prediction_lock_id SET NOT NULL;
    """)
