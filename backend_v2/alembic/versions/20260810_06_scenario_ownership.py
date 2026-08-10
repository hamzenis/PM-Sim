"""Add scenario ownership and archival metadata."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260810_06"
down_revision: str | None = "20260810_05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("scenarios") as batch_op:
        batch_op.add_column(sa.Column("owner_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_foreign_key("fk_scenarios_owner_id", "users", ["owner_id"], ["id"])
        batch_op.create_index("ix_scenarios_owner_id", ["owner_id"])


def downgrade() -> None:
    with op.batch_alter_table("scenarios") as batch_op:
        batch_op.drop_index("ix_scenarios_owner_id")
        batch_op.drop_constraint("fk_scenarios_owner_id", type_="foreignkey")
        batch_op.drop_column("archived_at")
        batch_op.drop_column("owner_id")
