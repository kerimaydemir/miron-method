"""Persist real Gemini stage summaries.

Revision ID: 20260822_0004
Revises: 20260822_0003
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260822_0004"
down_revision: str | None = "20260822_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE stage_runs ADD COLUMN summary text NOT NULL "
        "DEFAULT 'Kesme zamanına uygun yapılandırılmış rapor tamamlandı.'"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE stage_runs DROP COLUMN IF EXISTS summary")
