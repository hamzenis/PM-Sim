"""Create classes, memberships, and scenario availability."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260810_04"
down_revision: str | None = "20260810_03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "classes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("professor_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["professor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_classes_professor_id", "classes", ["professor_id"])
    op.create_table(
        "class_memberships",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("class_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("class_id", "user_id", name="uq_class_membership"),
    )
    op.create_index("ix_class_memberships_class_id", "class_memberships", ["class_id"])
    op.create_index("ix_class_memberships_user_id", "class_memberships", ["user_id"])
    op.create_table(
        "scenario_availability",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("class_id", sa.String(length=36), nullable=False),
        sa.Column("scenario_revision_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["scenario_revision_id"], ["scenario_revisions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("class_id", "scenario_revision_id", name="uq_class_scenario"),
    )
    op.create_index("ix_scenario_availability_class_id", "scenario_availability", ["class_id"])
    op.create_index(
        "ix_scenario_availability_scenario_revision_id",
        "scenario_availability",
        ["scenario_revision_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_scenario_availability_scenario_revision_id",
        table_name="scenario_availability",
    )
    op.drop_index("ix_scenario_availability_class_id", table_name="scenario_availability")
    op.drop_table("scenario_availability")
    op.drop_index("ix_class_memberships_user_id", table_name="class_memberships")
    op.drop_index("ix_class_memberships_class_id", table_name="class_memberships")
    op.drop_table("class_memberships")
    op.drop_index("ix_classes_professor_id", table_name="classes")
    op.drop_table("classes")
