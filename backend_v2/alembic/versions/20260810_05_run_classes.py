"""Associate new simulation runs with a class."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260810_05"
down_revision: str | None = "20260810_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("simulation_runs") as batch_op:
        batch_op.add_column(sa.Column("class_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key("fk_simulation_runs_class_id", "classes", ["class_id"], ["id"])
        batch_op.create_index("ix_simulation_runs_class_id", ["class_id"])


def downgrade() -> None:
    with op.batch_alter_table("simulation_runs") as batch_op:
        batch_op.drop_index("ix_simulation_runs_class_id")
        batch_op.drop_constraint("fk_simulation_runs_class_id", type_="foreignkey")
        batch_op.drop_column("class_id")
