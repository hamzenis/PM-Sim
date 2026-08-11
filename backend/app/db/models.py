from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
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


class AuthSessionRecord(Base):
    __tablename__ = "auth_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class AuditLogRecord(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    target_type: Mapped[str] = mapped_column(String(50), index=True)
    target_id: Mapped[str] = mapped_column(String(36), index=True)
    details: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class ClassRecord(Base):
    __tablename__ = "classes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(200))
    professor_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ClassMembershipRecord(Base):
    __tablename__ = "class_memberships"
    __table_args__ = (UniqueConstraint("class_id", "user_id", name="uq_class_membership"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    class_id: Mapped[str] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ScenarioRecord(Base):
    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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


class ScenarioAvailabilityRecord(Base):
    __tablename__ = "scenario_availability"
    __table_args__ = (
        UniqueConstraint("class_id", "scenario_revision_id", name="uq_class_scenario"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    class_id: Mapped[str] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"), index=True)
    scenario_revision_id: Mapped[str] = mapped_column(
        ForeignKey("scenario_revisions.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SimulationRunRecord(Base):
    __tablename__ = "simulation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    class_id: Mapped[str | None] = mapped_column(
        ForeignKey("classes.id"), index=True, nullable=True
    )
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
    content_deliveries: Mapped[list["ContentDeliveryRecord"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    content_responses: Mapped[list["ContentResponseRecord"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    applied_presentation_effects: Mapped[list["AppliedPresentationEffectRecord"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
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
    # NULL identifies turns written before canonical request digests were persisted.
    request_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    run: Mapped[SimulationRunRecord] = relationship(back_populates="turns")
    content_deliveries: Mapped[list["ContentDeliveryRecord"]] = relationship(
        back_populates="turn"
    )
    applied_presentation_effects: Mapped[list["AppliedPresentationEffectRecord"]] = relationship(
        back_populates="turn"
    )


class ContentDeliveryRecord(Base):
    __tablename__ = "content_delivery_records"
    __table_args__ = (
        UniqueConstraint("run_id", "sequence_entry_id", name="uq_content_delivery_entry"),
        Index("ix_content_delivery_run_checkpoint", "run_id", "canonical_checkpoint"),
        Index("ix_content_delivery_run_status", "run_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"))
    sequence_entry_id: Mapped[str] = mapped_column(String(100))
    canonical_checkpoint: Mapped[str] = mapped_column(String(100))
    sequence_ordinal: Mapped[int] = mapped_column(Integer)
    definition_snapshot: Mapped[dict[str, object]] = mapped_column(JSON)
    definition_digest: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(30))
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    turn_id: Mapped[str | None] = mapped_column(
        ForeignKey("simulation_turns.id", ondelete="SET NULL"), index=True, nullable=True
    )

    run: Mapped[SimulationRunRecord] = relationship(back_populates="content_deliveries")
    turn: Mapped[SimulationTurnRecord | None] = relationship(back_populates="content_deliveries")


class ContentResponseRecord(Base):
    __tablename__ = "content_response_records"
    __table_args__ = (
        UniqueConstraint(
            "run_id", "sequence_entry_id", "response_version", name="uq_content_response_version"
        ),
        UniqueConstraint("run_id", "idempotency_key", name="uq_content_response_idempotency"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"))
    sequence_entry_id: Mapped[str] = mapped_column(String(100))
    response_version: Mapped[int] = mapped_column(Integer)
    normalized_answer: Mapped[dict[str, object]] = mapped_column(JSON)
    command_kind: Mapped[str] = mapped_column(String(30))
    request_digest: Mapped[str] = mapped_column(String(64))
    idempotency_key: Mapped[str] = mapped_column(String(100))
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    run: Mapped[SimulationRunRecord] = relationship(back_populates="content_responses")


class AppliedPresentationEffectRecord(Base):
    __tablename__ = "applied_presentation_effect_records"
    __table_args__ = (
        UniqueConstraint(
            "run_id", "sequence_entry_id", "effect_index", name="uq_applied_effect_index"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"))
    sequence_entry_id: Mapped[str] = mapped_column(String(100))
    effect_index: Mapped[int] = mapped_column(Integer)
    effect_payload: Mapped[dict[str, object]] = mapped_column(JSON)
    before_projection_digest: Mapped[str] = mapped_column(String(64))
    after_projection_digest: Mapped[str] = mapped_column(String(64))
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    turn_id: Mapped[str | None] = mapped_column(
        ForeignKey("simulation_turns.id", ondelete="SET NULL"), index=True, nullable=True
    )

    run: Mapped[SimulationRunRecord] = relationship(back_populates="applied_presentation_effects")
    turn: Mapped[SimulationTurnRecord | None] = relationship(
        back_populates="applied_presentation_effects"
    )
