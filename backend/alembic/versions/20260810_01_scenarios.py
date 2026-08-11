"""Create scenarios and scenario revisions."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260810_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scenarios",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scenarios_name", "scenarios", ["name"])
    op.create_table(
        "scenario_revisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("scenario_id", sa.String(length=36), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("definition", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["scenario_id"], ["scenarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scenario_id", "revision_number", name="uq_scenario_revision_number"),
    )
    op.create_index("ix_scenario_revisions_scenario_id", "scenario_revisions", ["scenario_id"])


def downgrade() -> None:
    op.drop_index("ix_scenario_revisions_scenario_id", table_name="scenario_revisions")
    op.drop_table("scenario_revisions")
    op.drop_index("ix_scenarios_name", table_name="scenarios")
    op.drop_table("scenarios")
