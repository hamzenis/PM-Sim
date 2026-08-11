from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict

from app.api.auth import ProfessorUser
from app.api.classes import DatabaseSession
from app.audit.service import list_actor_audit

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    action: str
    target_type: str
    target_id: str
    details: dict[str, object]
    created_at: datetime


class ContentDeliveryAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class ContentResponseAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sequence_entry_id: str
    response_version: int
    command_kind: str
    normalized_answer: dict[str, object]
    answered_at: datetime
    request_digest: str
    idempotency_key_digest: str


class AppliedEffectAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sequence_entry_id: str
    effect_index: int
    effect_payload: dict[str, object]
    before_projection_digest: str
    after_projection_digest: str
    applied_at: datetime
    turn_id: str | None
    turn_week_number: int | None


class ReplayDivergenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: str
    record: str
    expected: object
    actual: object


class ProfessorContentAuditResponse(BaseModel):
    deliveries: list[ContentDeliveryAuditResponse]
    responses: list[ContentResponseAuditResponse]
    effects: list[AppliedEffectAuditResponse]
    digest_status: str
    divergences: list[ReplayDivergenceResponse]


@router.get("", response_model=list[AuditResponse])
def get_audit_history(
    session: DatabaseSession,
    professor: ProfessorUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> object:
    return list_actor_audit(session, actor_id=professor.id, limit=limit, offset=offset)
