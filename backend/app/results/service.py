from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import ProfessorContentAudit, load_professor_content_audit
from app.db.models import (
    ClassRecord,
    SimulationRunRecord,
    SimulationTurnRecord,
    UserRecord,
)
from app.simulation.results import SimulationOutcome


class ProfessorResultError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ProfessorRunResult:
    run: SimulationRunRecord
    student: UserRecord


@dataclass(frozen=True, slots=True)
class ProfessorRunAudit:
    result: ProfessorRunResult
    turns: tuple[SimulationTurnRecord, ...]
    content: ProfessorContentAudit


def list_class_results(
    session: Session,
    *,
    class_id: str,
    professor_id: str,
) -> list[ProfessorRunResult]:
    _owned_class(session, class_id=class_id, professor_id=professor_id)
    statement = (
        select(SimulationRunRecord, UserRecord)
        .join(UserRecord, UserRecord.id == SimulationRunRecord.user_id)
        .where(
            SimulationRunRecord.class_id == class_id,
            SimulationRunRecord.status != SimulationOutcome.ACTIVE,
        )
        .order_by(UserRecord.username, SimulationRunRecord.finished_at, SimulationRunRecord.id)
    )
    return [
        ProfessorRunResult(run=run, student=student) for run, student in session.execute(statement)
    ]


def get_class_run_audit(
    session: Session,
    *,
    class_id: str,
    run_id: str,
    professor_id: str,
) -> ProfessorRunAudit:
    _owned_class(session, class_id=class_id, professor_id=professor_id)
    row = session.execute(
        select(SimulationRunRecord, UserRecord)
        .join(UserRecord, UserRecord.id == SimulationRunRecord.user_id)
        .where(
            SimulationRunRecord.id == run_id,
            SimulationRunRecord.class_id == class_id,
        )
    ).one_or_none()
    if row is None:
        raise ProfessorResultError("simulation run not found")
    run, student = row
    turns = list(
        session.scalars(
            select(SimulationTurnRecord)
            .where(SimulationTurnRecord.run_id == run.id)
            .order_by(SimulationTurnRecord.week_number)
        )
    )
    # Authored facts are loaded only after the scoped professor/class/run query succeeds.
    content = load_professor_content_audit(session, run=run)
    return ProfessorRunAudit(
        result=ProfessorRunResult(run=run, student=student), turns=tuple(turns), content=content
    )


def _owned_class(session: Session, *, class_id: str, professor_id: str) -> ClassRecord:
    course_class = session.get(ClassRecord, class_id)
    if course_class is None or course_class.professor_id != professor_id:
        raise ProfessorResultError("class not found")
    return course_class
