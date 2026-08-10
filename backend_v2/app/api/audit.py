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


@router.get("", response_model=list[AuditResponse])
def get_audit_history(
    session: DatabaseSession,
    professor: ProfessorUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> object:
    return list_actor_audit(session, actor_id=professor.id, limit=limit, offset=offset)
