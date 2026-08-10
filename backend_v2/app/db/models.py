from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def new_id() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class RevisionStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


class UserRole(StrEnum):
    STUDENT = "student"
    PROFESSOR = "professor"


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ScenarioRecord(Base):
    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(200), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    revisions: Mapped[list["ScenarioRevisionRecord"]] = relationship(
        back_populates="scenario",
        cascade="all, delete-orphan",
        order_by="ScenarioRevisionRecord.revision_number",
    )


class ScenarioRevisionRecord(Base):
    __tablename__ = "scenario_revisions"
    __table_args__ = (
        UniqueConstraint("scenario_id", "revision_number", name="uq_scenario_revision_number"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    scenario_id: Mapped[str] = mapped_column(
        ForeignKey("scenarios.id", ondelete="CASCADE"), index=True
    )
    revision_number: Mapped[int] = mapped_column(Integer)
    schema_version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default=RevisionStatus.DRAFT)
    definition: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    scenario: Mapped[ScenarioRecord] = relationship(back_populates="revisions")


class SimulationRunRecord(Base):
    __tablename__ = "simulation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    scenario_revision_id: Mapped[str] = mapped_column(
        ForeignKey("scenario_revisions.id"), index=True
    )
    status: Mapped[str] = mapped_column(String(30))
    seed: Mapped[int] = mapped_column(Integer)
    engine_version: Mapped[str] = mapped_column(String(30))
    current_week: Mapped[int] = mapped_column(Integer, default=0)
    version: Mapped[int] = mapped_column(Integer, default=1)
    current_state: Mapped[dict[str, object]] = mapped_column(JSON)
    final_result: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    turns: Mapped[list["SimulationTurnRecord"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="SimulationTurnRecord.week_number",
    )


class SimulationTurnRecord(Base):
    __tablename__ = "simulation_turns"
    __table_args__ = (
        UniqueConstraint("run_id", "week_number", name="uq_run_week_number"),
        UniqueConstraint("run_id", "idempotency_key", name="uq_run_idempotency_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("simulation_runs.id", ondelete="CASCADE"), index=True
    )
    week_number: Mapped[int] = mapped_column(Integer)
    turn_seed: Mapped[int] = mapped_column(Integer)
    idempotency_key: Mapped[str] = mapped_column(String(100))
    decision: Mapped[dict[str, object]] = mapped_column(JSON)
    resulting_state: Mapped[dict[str, object]] = mapped_column(JSON)
    events: Mapped[list[dict[str, object]]] = mapped_column(JSON)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    run: Mapped[SimulationRunRecord] = relationship(back_populates="turns")
