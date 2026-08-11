from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.authored_content.definitions import from_pinned_revision
from app.authored_content.replay import Divergence, verify_replay
from app.db.models import (
    AppliedPresentationEffectRecord,
    AuditLogRecord,
    ContentDeliveryRecord,
    ContentResponseRecord,
    ScenarioRevisionRecord,
    SimulationRunRecord,
    SimulationTurnRecord,
)


@dataclass(frozen=True, slots=True)
class ProfessorContentDelivery:
    id: str
    sequence_entry_id: str
    sequence_ordinal: int
    checkpoint: str
    visibility: str
    hidden_from_students: bool
    definition_digest: str
    definition_snapshot: dict[str, object]
    status: str
    delivered_at: datetime
    completed_at: datetime | None
    turn_id: str | None
    turn_week_number: int | None


@dataclass(frozen=True, slots=True)
class ProfessorContentResponse:
    id: str
    sequence_entry_id: str
    response_version: int
    command_kind: str
    normalized_answer: dict[str, object]
    answered_at: datetime
    request_digest: str
    idempotency_key_digest: str


@dataclass(frozen=True, slots=True)
class ProfessorAppliedEffect:
    id: str
    sequence_entry_id: str
    effect_index: int
    effect_payload: dict[str, object]
    before_projection_digest: str
    after_projection_digest: str
    applied_at: datetime
    turn_id: str | None
    turn_week_number: int | None


@dataclass(frozen=True, slots=True)
class ProfessorContentAudit:
    deliveries: tuple[ProfessorContentDelivery, ...]
    responses: tuple[ProfessorContentResponse, ...]
    effects: tuple[ProfessorAppliedEffect, ...]
    digest_status: str
    divergences: tuple[Divergence, ...]


def load_professor_content_audit(
    session: Session, *, run: SimulationRunRecord
) -> ProfessorContentAudit:
    """Load authored facts for an already-authorized run and verify them read-only.

    Callers must obtain ``run`` through the professor/class/run ownership query.  Taking a
    run rather than a delivery/response identifier deliberately prevents unscoped lookup paths.
    """
    turns = {
        turn.id: turn.week_number
        for turn in session.scalars(
            select(SimulationTurnRecord).where(SimulationTurnRecord.run_id == run.id)
        )
    }
    delivery_rows = list(
        session.scalars(
            select(ContentDeliveryRecord)
            .where(ContentDeliveryRecord.run_id == run.id)
            .order_by(ContentDeliveryRecord.sequence_ordinal, ContentDeliveryRecord.id)
        )
    )
    response_rows = list(
        session.scalars(
            select(ContentResponseRecord)
            .where(ContentResponseRecord.run_id == run.id)
            .order_by(
                ContentResponseRecord.sequence_entry_id,
                ContentResponseRecord.response_version,
                ContentResponseRecord.answered_at,
                ContentResponseRecord.id,
            )
        )
    )
    effect_rows = list(
        session.scalars(
            select(AppliedPresentationEffectRecord)
            .where(AppliedPresentationEffectRecord.run_id == run.id)
            .order_by(
                AppliedPresentationEffectRecord.applied_at,
                AppliedPresentationEffectRecord.sequence_entry_id,
                AppliedPresentationEffectRecord.effect_index,
            )
        )
    )
    deliveries = tuple(
        ProfessorContentDelivery(
            id=row.id,
            sequence_entry_id=row.sequence_entry_id,
            sequence_ordinal=row.sequence_ordinal,
            checkpoint=row.canonical_checkpoint,
            visibility=str(row.definition_snapshot.get("visibility", "default")),
            hidden_from_students=bool(row.definition_snapshot.get("professor_only", False)),
            definition_digest=row.definition_digest,
            definition_snapshot=row.definition_snapshot,
            status=row.status,
            delivered_at=row.delivered_at,
            completed_at=row.completed_at,
            turn_id=row.turn_id,
            turn_week_number=turns.get(row.turn_id),
        )
        for row in delivery_rows
    )
    responses = tuple(
        ProfessorContentResponse(
            id=row.id,
            sequence_entry_id=row.sequence_entry_id,
            response_version=row.response_version,
            command_kind=row.command_kind,
            normalized_answer=row.normalized_answer,
            answered_at=row.answered_at,
            request_digest=row.request_digest,
            idempotency_key_digest=sha256(row.idempotency_key.encode()).hexdigest(),
        )
        for row in response_rows
    )
    effects = tuple(
        ProfessorAppliedEffect(
            id=row.id,
            sequence_entry_id=row.sequence_entry_id,
            effect_index=row.effect_index,
            effect_payload=row.effect_payload,
            before_projection_digest=row.before_projection_digest,
            after_projection_digest=row.after_projection_digest,
            applied_at=row.applied_at,
            turn_id=row.turn_id,
            turn_week_number=turns.get(row.turn_id),
        )
        for row in effect_rows
    )
    revision = session.get(ScenarioRevisionRecord, run.scenario_revision_id)
    divergences: tuple[Divergence, ...]
    if revision is None:
        divergences = (Divergence("revision", run.scenario_revision_id, "present", "missing"),)
    else:
        definitions = from_pinned_revision(revision.id, revision.definition)
        divergences = verify_replay(
            definitions,
            [_delivery_verifier_record(row, turns) for row in delivery_rows],
            [_response_verifier_record(row) for row in response_rows],
            [_effect_verifier_record(row) for row in effect_rows],
            terminal=run.status != "active",
        )
    return ProfessorContentAudit(
        deliveries, responses, effects, "diverged" if divergences else "verified", divergences
    )


def _delivery_verifier_record(row: ContentDeliveryRecord, turns: dict[str, int]) -> dict[str, Any]:
    return {
        "run_id": row.run_id,
        "sequence_entry_id": row.sequence_entry_id,
        "canonical_checkpoint": row.canonical_checkpoint,
        "definition_digest": row.definition_digest,
        "status": row.status,
        "turn_id": row.turn_id,
        "turn_run_id": row.run_id if row.turn_id in turns else None,
    }


def _response_verifier_record(row: ContentResponseRecord) -> dict[str, Any]:
    return {
        "sequence_entry_id": row.sequence_entry_id,
        "normalized_answer": (
            row.normalized_answer.get("answer", row.normalized_answer)
            if row.command_kind == "answer"
            else row.normalized_answer
        ),
        "command_kind": row.command_kind,
        "request_digest": row.request_digest,
    }


def _effect_verifier_record(row: AppliedPresentationEffectRecord) -> dict[str, Any]:
    return {
        "sequence_entry_id": row.sequence_entry_id,
        "effect_payload": row.effect_payload,
        "before_projection_digest": row.before_projection_digest,
        "after_projection_digest": row.after_projection_digest,
    }


def record_audit(
    session: Session,
    *,
    actor_id: str,
    action: str,
    target_type: str,
    target_id: str,
    details: dict[str, object] | None = None,
) -> AuditLogRecord:
    """Stage an immutable audit record in the caller's current transaction."""
    record = AuditLogRecord(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details or {},
        created_at=datetime.now(UTC),
    )
    session.add(record)
    return record


def list_actor_audit(
    session: Session,
    *,
    actor_id: str,
    limit: int = 50,
    offset: int = 0,
) -> list[AuditLogRecord]:
    if not 1 <= limit <= 200:
        raise ValueError("limit must be between 1 and 200")
    if offset < 0:
        raise ValueError("offset cannot be negative")
    statement = (
        select(AuditLogRecord)
        .where(AuditLogRecord.actor_id == actor_id)
        .order_by(AuditLogRecord.created_at.desc(), AuditLogRecord.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(session.scalars(statement))
