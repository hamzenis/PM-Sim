from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuditLogRecord


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
