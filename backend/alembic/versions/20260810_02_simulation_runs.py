"""Create users, simulation runs, and simulation turns."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260810_02"
down_revision: str | None = "20260810_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_table(
        "simulation_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("scenario_revision_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("engine_version", sa.String(length=30), nullable=False),
        sa.Column("current_week", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("current_state", sa.JSON(), nullable=False),
        sa.Column("final_result", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["scenario_revision_id"], ["scenario_revisions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_simulation_runs_user_id", "simulation_runs", ["user_id"])
    op.create_index(
        "ix_simulation_runs_scenario_revision_id",
        "simulation_runs",
        ["scenario_revision_id"],
    )
    op.create_table(
        "simulation_turns",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("turn_seed", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=100), nullable=False),
        sa.Column("decision", sa.JSON(), nullable=False),
        sa.Column("resulting_state", sa.JSON(), nullable=False),
        sa.Column("events", sa.JSON(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["simulation_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "idempotency_key", name="uq_run_idempotency_key"),
        sa.UniqueConstraint("run_id", "week_number", name="uq_run_week_number"),
    )
    op.create_index("ix_simulation_turns_run_id", "simulation_turns", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_simulation_turns_run_id", table_name="simulation_turns")
    op.drop_table("simulation_turns")
    op.drop_index("ix_simulation_runs_scenario_revision_id", table_name="simulation_runs")
    op.drop_index("ix_simulation_runs_user_id", table_name="simulation_runs")
    op.drop_table("simulation_runs")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
