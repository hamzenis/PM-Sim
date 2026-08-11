"""Persist authored-content delivery, responses, and applied effects."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260811_09"
down_revision: str | None = "20260810_08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Deliberately nullable: pre-migration turns have no complete canonical request from
    # which a trustworthy digest can be reconstructed.
    op.add_column(
        "simulation_turns",
        sa.Column("request_digest", sa.String(length=64), nullable=True),
    )
    op.create_table(
        "content_delivery_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("sequence_entry_id", sa.String(length=100), nullable=False),
        sa.Column("canonical_checkpoint", sa.String(length=100), nullable=False),
        sa.Column("sequence_ordinal", sa.Integer(), nullable=False),
        sa.Column("definition_snapshot", sa.JSON(), nullable=False),
        sa.Column("definition_digest", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("turn_id", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["simulation_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["turn_id"], ["simulation_turns.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "sequence_entry_id", name="uq_content_delivery_entry"),
    )
    op.create_index(
        "ix_content_delivery_run_checkpoint",
        "content_delivery_records",
        ["run_id", "canonical_checkpoint"],
    )
    op.create_index(
        "ix_content_delivery_run_status", "content_delivery_records", ["run_id", "status"]
    )
    op.create_index("ix_content_delivery_records_turn_id", "content_delivery_records", ["turn_id"])
    op.create_table(
        "content_response_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("sequence_entry_id", sa.String(length=100), nullable=False),
        sa.Column("response_version", sa.Integer(), nullable=False),
        sa.Column("normalized_answer", sa.JSON(), nullable=False),
        sa.Column("command_kind", sa.String(length=30), nullable=False),
        sa.Column("request_digest", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=100), nullable=False),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["simulation_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "run_id", "sequence_entry_id", "response_version", name="uq_content_response_version"
        ),
        sa.UniqueConstraint("run_id", "idempotency_key", name="uq_content_response_idempotency"),
    )
    op.create_table(
        "applied_presentation_effect_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("sequence_entry_id", sa.String(length=100), nullable=False),
        sa.Column("effect_index", sa.Integer(), nullable=False),
        sa.Column("effect_payload", sa.JSON(), nullable=False),
        sa.Column("before_projection_digest", sa.String(length=64), nullable=False),
        sa.Column("after_projection_digest", sa.String(length=64), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("turn_id", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["simulation_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["turn_id"], ["simulation_turns.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "run_id", "sequence_entry_id", "effect_index", name="uq_applied_effect_index"
        ),
    )
    op.create_index(
        "ix_applied_presentation_effect_records_turn_id",
        "applied_presentation_effect_records",
        ["turn_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_applied_presentation_effect_records_turn_id",
        table_name="applied_presentation_effect_records",
    )
    op.drop_table("applied_presentation_effect_records")
    op.drop_table("content_response_records")
    op.drop_index("ix_content_delivery_records_turn_id", table_name="content_delivery_records")
    op.drop_index("ix_content_delivery_run_status", table_name="content_delivery_records")
    op.drop_index("ix_content_delivery_run_checkpoint", table_name="content_delivery_records")
    op.drop_table("content_delivery_records")
    op.drop_column("simulation_turns", "request_digest")
