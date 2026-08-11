from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser
from app.db.models import (
    ContentDeliveryRecord,
    ContentResponseRecord,
    ScenarioRevisionRecord,
    SimulationRunRecord,
    SimulationTurnRecord,
)
from app.db.session import get_session
from app.simulation.models import ActivityAllocation, HireRequest, WeeklyDecision
from app.simulations.service import (
    ConcurrentTurnError,
    ContentBlockingError,
    IdempotencyConflictError,
    SimulationRunError,
    complete_simulation_turn,
    get_simulation_run,
    list_simulation_runs,
    list_simulation_turns,
    start_simulation_run,
    submit_simulation_run,
)

router = APIRouter(prefix="/simulations", tags=["simulations"])
DatabaseSession = Annotated[Session, Depends(get_session)]
IdempotencyKey = Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=100)]


class StartSimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_revision_id: str
    class_id: str | None = None
    seed: int


class ActivityAllocationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    development: float = Field(ge=0, le=100)
    unit_testing: float = Field(ge=0, le=100)
    bug_fixing: float = Field(ge=0, le=100)
    integration_testing: float = Field(ge=0, le=100)


class HireRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_type_code: str = Field(min_length=1)
    count: int = Field(gt=0)


class CompleteTurnRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)
    allocation: ActivityAllocationRequest
    hires: list[HireRequestBody] = Field(default_factory=list)
    dismiss_employee_ids: list[str] = Field(default_factory=list)
    overtime_hours_per_employee: float = Field(default=0, ge=0)
    meeting_hours_per_employee: float = Field(default=0, ge=0)
    training_hours_per_employee: float = Field(default=0, ge=0)

    def to_domain(self) -> WeeklyDecision:
        return WeeklyDecision(
            allocation=ActivityAllocation(**self.allocation.model_dump()),
            hires=tuple(HireRequest(**hire.model_dump()) for hire in self.hires),
            dismiss_employee_ids=tuple(self.dismiss_employee_ids),
            overtime_hours_per_employee=self.overtime_hours_per_employee,
            meeting_hours_per_employee=self.meeting_hours_per_employee,
            training_hours_per_employee=self.training_hours_per_employee,
        )


class RunSummaryResponse(BaseModel):
    id: str
    scenario_revision_id: str
    class_id: str | None
    status: str
    current_week: int
    version: int
    started_at: datetime
    finished_at: datetime | None


class RunResponse(RunSummaryResponse):
    engine_version: str
    scenario_briefing: str
    state: dict[str, object]
    employee_types: list[dict[str, object]]
    final_result: dict[str, object] | None
    deliveries: list["StudentDeliveryResponse"]
    presentation: "StudentPresentationResponse"


class QuestionOptionResponse(BaseModel):
    id: str
    label: str


class QuestionSchemaResponse(BaseModel):
    answer_schema: str
    options: list[QuestionOptionResponse] = Field(default_factory=list)
    short_text_max_length: int | None = None


class LatestContentResponse(BaseModel):
    command_kind: str
    response_version: int
    value: dict[str, object]
    answered_at: datetime


class StudentDeliveryResponse(BaseModel):
    id: str
    sequence_entry_id: str
    sequence_ordinal: int
    kind: str
    status: str
    checkpoint: str
    title: str | None = None
    body: str | None = None
    prompt: str | None = None
    question: QuestionSchemaResponse | None = None
    required: bool
    latest_response: LatestContentResponse | None = None
    feedback: str | None = None
    visible: bool = True
    label: str | None = None


class StudentPresentationResponse(BaseModel):
    messages: list[str] = Field(default_factory=list)
    visible_fragment_ids: list[str] = Field(default_factory=list)
    visible_question_ids: list[str] = Field(default_factory=list)
    flags: dict[str, object] = Field(default_factory=dict)
    theme: str | None = None


class TurnResponse(BaseModel):
    run: RunResponse
    week_number: int
    events: list[dict[str, object]]
    replayed: bool


class SubmitRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)


class TurnHistoryResponse(BaseModel):
    week_number: int
    decision: dict[str, object]
    events: list[dict[str, object]]
    resulting_state: dict[str, object]
    submitted_at: datetime
    deliveries: list[StudentDeliveryResponse]


@router.post("", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
def start_run(
    request: StartSimulationRequest,
    session: DatabaseSession,
    user: CurrentUser,
) -> RunResponse:
    try:
        run = start_simulation_run(
            session,
            user_id=user.id,
            scenario_revision_id=request.scenario_revision_id,
            seed=request.seed,
            class_id=request.class_id,
        )
    except SimulationRunError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return _run_response(session, run)


@router.get("", response_model=list[RunSummaryResponse])
def list_runs(session: DatabaseSession, user: CurrentUser) -> list[RunSummaryResponse]:
    return [_run_summary(run) for run in list_simulation_runs(session, user.id)]


@router.get("/{run_id}", response_model=RunResponse)
def get_run(run_id: str, session: DatabaseSession, user: CurrentUser) -> RunResponse:
    try:
        return _run_response(session, get_simulation_run(session, run_id=run_id, user_id=user.id))
    except SimulationRunError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/{run_id}/turns", response_model=list[TurnHistoryResponse])
def get_turn_history(
    run_id: str,
    session: DatabaseSession,
    user: CurrentUser,
) -> list[TurnHistoryResponse]:
    try:
        turns = list_simulation_turns(session, run_id=run_id, user_id=user.id)
    except SimulationRunError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return [_turn_history_response(turn) for turn in turns]


@router.post("/{run_id}/turns", response_model=TurnResponse)
def complete_turn(
    run_id: str,
    request: CompleteTurnRequest,
    idempotency_key: IdempotencyKey,
    session: DatabaseSession,
    user: CurrentUser,
) -> TurnResponse:
    try:
        completed = complete_simulation_turn(
            session,
            run_id=run_id,
            user_id=user.id,
            decision=request.to_domain(),
            expected_version=request.expected_version,
            idempotency_key=idempotency_key,
        )
    except (ConcurrentTurnError, IdempotencyConflictError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ContentBlockingError as error:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "content_blocked",
                "message": str(error),
                "blocking_entry": _delivery_response(session, error.delivery).model_dump(
                    mode="json"
                ),
            },
        ) from error
    except (SimulationRunError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    run_response = _run_response(session, completed.run)
    if completed.replayed:
        # Content-only commands may have advanced the live run since this turn.
        run_response = run_response.model_copy(
            update={
                "version": completed.projection_version,
                "current_week": completed.turn.week_number,
                "state": _student_state(completed.turn.resulting_state),
            }
        )
    return TurnResponse(
        run=run_response,
        week_number=completed.turn.week_number,
        events=_student_events(completed.turn.events),
        replayed=completed.replayed,
    )


@router.post("/{run_id}/submit", response_model=RunResponse)
def submit_run(
    run_id: str,
    request: SubmitRunRequest,
    session: DatabaseSession,
    user: CurrentUser,
) -> RunResponse:
    try:
        run = submit_simulation_run(
            session,
            run_id=run_id,
            user_id=user.id,
            expected_version=request.expected_version,
        )
    except ConcurrentTurnError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except SimulationRunError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return _run_response(session, run)


def _run_summary(run: SimulationRunRecord) -> RunSummaryResponse:
    return RunSummaryResponse(
        id=run.id,
        scenario_revision_id=run.scenario_revision_id,
        class_id=run.class_id,
        status=run.status,
        current_week=run.current_week,
        version=run.version,
        started_at=run.started_at,
        finished_at=run.finished_at,
    )


def _run_response(session: Session, run: SimulationRunRecord) -> RunResponse:
    summary = _run_summary(run)
    revision = session.get(ScenarioRevisionRecord, run.scenario_revision_id)
    employee_types = [] if revision is None else revision.definition.get("employee_types", [])
    scenario_briefing = "" if revision is None else str(revision.definition.get("description", ""))
    return RunResponse(
        **summary.model_dump(),
        engine_version=run.engine_version,
        scenario_briefing=scenario_briefing,
        state=_student_state(run.current_state),
        employee_types=employee_types,
        final_result=run.final_result,
        deliveries=_student_deliveries(session, run.id),
        presentation=_presentation_response(session, run.id),
    )


def _student_state(state: dict[str, object]) -> dict[str, object]:
    """Remove facts the player has not discovered through testing."""
    hidden = {"undiscovered_bugs", "incorrect_specifications"}
    return {name: value for name, value in state.items() if name not in hidden}


def _student_events(events: list[dict[str, object]]) -> list[dict[str, object]]:
    hidden_kinds = {"bugs_created", "incorrect_specifications_created"}
    return [event for event in events if event.get("kind") not in hidden_kinds]


def _turn_history_response(turn: SimulationTurnRecord) -> TurnHistoryResponse:
    session = Session.object_session(turn)
    return TurnHistoryResponse(
        week_number=turn.week_number,
        decision=turn.decision,
        events=_student_events(turn.events),
        resulting_state=_student_state(turn.resulting_state),
        submitted_at=turn.submitted_at,
        deliveries=[]
        if session is None
        else [
            _delivery_response(session, row)
            for row in turn.content_deliveries
            if not row.definition_snapshot.get("professor_only")
        ],
    )


def _delivery_response(session: Session, row: ContentDeliveryRecord) -> StudentDeliveryResponse:
    snapshot = row.definition_snapshot
    response = session.scalar(
        select(ContentResponseRecord)
        .where(
            ContentResponseRecord.run_id == row.run_id,
            ContentResponseRecord.sequence_entry_id == row.sequence_entry_id,
        )
        .order_by(ContentResponseRecord.response_version.desc())
    )
    question = None
    if snapshot.get("kind") == "question":
        question = QuestionSchemaResponse(
            answer_schema=str(snapshot["answer_schema"]),
            options=snapshot.get("options", []),
            short_text_max_length=snapshot.get("short_text_max_length"),
        )
    latest = (
        None
        if response is None
        else LatestContentResponse(
            command_kind=response.command_kind,
            response_version=response.response_version,
            value=response.normalized_answer,
            answered_at=response.answered_at,
        )
    )
    return StudentDeliveryResponse(
        id=row.id,
        sequence_entry_id=row.sequence_entry_id,
        sequence_ordinal=row.sequence_ordinal,
        kind=str(snapshot.get("kind", "event")),
        status=row.status,
        checkpoint=row.canonical_checkpoint,
        title=snapshot.get("title"),
        body=snapshot.get("body"),
        prompt=snapshot.get("prompt"),
        question=question,
        required=bool(snapshot.get("required", False)),
        latest_response=latest,
        label=snapshot.get("title") or snapshot.get("prompt"),
    )


def _student_deliveries(session: Session, run_id: str) -> list[StudentDeliveryResponse]:
    rows = session.scalars(
        select(ContentDeliveryRecord)
        .where(ContentDeliveryRecord.run_id == run_id)
        .order_by(ContentDeliveryRecord.sequence_ordinal)
    ).all()
    return [
        _delivery_response(session, row)
        for row in rows
        if not row.definition_snapshot.get("professor_only")
    ]


def _presentation_response(session: Session, run_id: str) -> StudentPresentationResponse:
    from app.simulations.service import _presentation

    return StudentPresentationResponse.model_validate(_presentation(session, run_id))
