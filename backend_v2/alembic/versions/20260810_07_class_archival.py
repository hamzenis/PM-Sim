"""Add non-destructive class archival."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260810_07"
down_revision: str | None = "20260810_06"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("classes") as batch_op:
        batch_op.add_column(sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("classes") as batch_op:
        batch_op.drop_column("archived_at")
