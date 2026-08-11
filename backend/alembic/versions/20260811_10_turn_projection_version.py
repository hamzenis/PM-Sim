"""Persist the exact run version returned by a weekly turn."""

import sqlalchemy as sa

from alembic import op

revision: str = "20260811_10"
down_revision: str | None = "20260811_09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "simulation_turns",
        sa.Column("resulting_run_version", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("simulation_turns", "resulting_run_version")
