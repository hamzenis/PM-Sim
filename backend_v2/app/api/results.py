from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.auth import ProfessorUser
from app.api.classes import DatabaseSession
from app.db.models import SimulationRunRecord
from app.results.service import ProfessorResultError, get_class_run_audit, list_class_results

router = APIRouter(prefix="/classes", tags=["professor results"])


class ClassResultResponse(BaseModel):
    run_id: str
    student_id: str
    student_username: str
    scenario_revision_id: str
    status: str
    current_week: int
    finished_at: datetime | None
    final_result: dict[str, object] | None


class AuditTurnResponse(BaseModel):
    week_number: int
    turn_seed: int
    decision: dict[str, object]
    resulting_state: dict[str, object]
    events: list[dict[str, object]]
    submitted_at: datetime


class RunAuditResponse(ClassResultResponse):
    seed: int
    engine_version: str
    current_state: dict[str, object]
    turns: list[AuditTurnResponse]


@router.get("/{class_id}/results", response_model=list[ClassResultResponse])
def class_results(
    class_id: str,
    session: DatabaseSession,
    professor: ProfessorUser,
) -> list[ClassResultResponse]:
    try:
        results = list_class_results(session, class_id=class_id, professor_id=professor.id)
    except ProfessorResultError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return [
        _result_response(result.run, result.student.id, result.student.username)
        for result in results
    ]


@router.get("/{class_id}/results/{run_id}", response_model=RunAuditResponse)
def run_audit(
    class_id: str,
    run_id: str,
    session: DatabaseSession,
    professor: ProfessorUser,
) -> RunAuditResponse:
    try:
        result, turns = get_class_run_audit(
            session,
            class_id=class_id,
            run_id=run_id,
            professor_id=professor.id,
        )
    except ProfessorResultError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    summary = _result_response(result.run, result.student.id, result.student.username)
    return RunAuditResponse(
        **summary.model_dump(),
        seed=result.run.seed,
        engine_version=result.run.engine_version,
        current_state=result.run.current_state,
        turns=[
            AuditTurnResponse(
                week_number=turn.week_number,
                turn_seed=turn.turn_seed,
                decision=turn.decision,
                resulting_state=turn.resulting_state,
                events=turn.events,
                submitted_at=turn.submitted_at,
            )
            for turn in turns
        ],
    )


def _result_response(
    run: SimulationRunRecord, student_id: str, username: str
) -> ClassResultResponse:
    return ClassResultResponse(
        run_id=run.id,
        student_id=student_id,
        student_username=username,
        scenario_revision_id=run.scenario_revision_id,
        status=run.status,
        current_week=run.current_week,
        finished_at=run.finished_at,
        final_result=run.final_result,
    )
