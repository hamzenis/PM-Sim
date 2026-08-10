from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.classes.service import user_can_access_revision
from app.db.models import (
    RevisionStatus,
    ScenarioRevisionRecord,
    SimulationRunRecord,
    SimulationTurnRecord,
    UserRecord,
)
from app.scenarios.models import ScenarioDefinition
from app.scenarios.to_simulation import (
    employee_types_from_scenario,
    initial_state_from_scenario,
    score_rules_from_scenario,
    turn_rules_from_scenario,
)
from app.simulation.models import WeeklyDecision
from app.simulation.randomness import SeededRandomSource
from app.simulation.results import SimulationOutcome, build_simulation_result, evaluate_outcome
from app.simulation.state_codec import state_from_dict, state_to_dict
from app.simulation.turn import process_week

ENGINE_VERSION = "0.1.0"


class SimulationRunError(ValueError):
    pass


class ConcurrentTurnError(SimulationRunError):
    pass


@dataclass(frozen=True, slots=True)
class CompletedTurn:
    run: SimulationRunRecord
    turn: SimulationTurnRecord
    replayed: bool = False


def list_simulation_runs(session: Session, user_id: str) -> list[SimulationRunRecord]:
    """Return only runs owned by the requesting student."""
    statement = (
        select(SimulationRunRecord)
        .where(SimulationRunRecord.user_id == user_id)
        .order_by(SimulationRunRecord.started_at.desc(), SimulationRunRecord.id)
    )
    return list(session.scalars(statement))


def get_simulation_run(
    session: Session,
    *,
    run_id: str,
    user_id: str,
) -> SimulationRunRecord:
    """Load an owned run without revealing whether another student's run exists."""
    run = session.get(SimulationRunRecord, run_id)
    if run is None or run.user_id != user_id:
        raise SimulationRunError("simulation run not found")
    return run


def start_simulation_run(
    session: Session,
    *,
    user_id: str,
    scenario_revision_id: str,
    seed: int,
) -> SimulationRunRecord:
    user = session.get(UserRecord, user_id)
    if user is None:
        raise SimulationRunError("user not found")
    revision = session.get(ScenarioRevisionRecord, scenario_revision_id)
    if revision is None or revision.status != RevisionStatus.PUBLISHED:
        raise SimulationRunError("a published scenario revision is required")
    if not user_can_access_revision(session, user.id, revision.id):
        raise SimulationRunError("scenario revision is not available to this user")
    scenario = ScenarioDefinition.model_validate(revision.definition)
    now = datetime.now(UTC)
    run = SimulationRunRecord(
        user_id=user.id,
        scenario_revision_id=revision.id,
        status=SimulationOutcome.ACTIVE,
        seed=seed,
        engine_version=ENGINE_VERSION,
        current_week=0,
        version=1,
        current_state=state_to_dict(initial_state_from_scenario(scenario)),
        started_at=now,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def complete_simulation_turn(
    session: Session,
    *,
    run_id: str,
    user_id: str,
    decision: WeeklyDecision,
    expected_version: int,
    idempotency_key: str,
) -> CompletedTurn:
    if not idempotency_key:
        raise SimulationRunError("idempotency key is required")
    existing = session.scalar(
        select(SimulationTurnRecord).where(
            SimulationTurnRecord.run_id == run_id,
            SimulationTurnRecord.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        run = session.get(SimulationRunRecord, run_id)
        if run is None or run.user_id != user_id:
            raise SimulationRunError("simulation run not found")
        return CompletedTurn(run=run, turn=existing, replayed=True)

    run = get_simulation_run(session, run_id=run_id, user_id=user_id)
    if run.status != SimulationOutcome.ACTIVE:
        raise SimulationRunError("simulation run is not active")
    if run.version != expected_version:
        raise ConcurrentTurnError("simulation run version has changed")

    revision = session.get(ScenarioRevisionRecord, run.scenario_revision_id)
    if revision is None:
        raise SimulationRunError("scenario revision not found")
    scenario = ScenarioDefinition.model_validate(revision.definition)
    turn_seed = run.seed + run.current_week
    result = process_week(
        state_from_dict(run.current_state),
        decision=decision,
        employee_types=employee_types_from_scenario(scenario),
        rules=turn_rules_from_scenario(scenario),
        random=SeededRandomSource(turn_seed),
        new_employee_id=lambda: str(uuid4()),
    )
    outcome = evaluate_outcome(result.state)
    now = datetime.now(UTC)
    state_data = state_to_dict(result.state)
    final_result = None
    finished_at = None
    if outcome is not SimulationOutcome.ACTIVE:
        final_result = asdict(
            build_simulation_result(result.state, rules=score_rules_from_scenario(scenario))
        )
        finished_at = now

    statement = (
        update(SimulationRunRecord)
        .where(
            SimulationRunRecord.id == run.id,
            SimulationRunRecord.user_id == user_id,
            SimulationRunRecord.version == expected_version,
        )
        .values(
            status=outcome,
            current_week=result.state.week,
            version=expected_version + 1,
            current_state=state_data,
            final_result=final_result,
            finished_at=finished_at,
        )
    )
    if session.execute(statement).rowcount != 1:
        session.rollback()
        raise ConcurrentTurnError("simulation run version has changed")

    turn = SimulationTurnRecord(
        run_id=run.id,
        week_number=result.state.week,
        turn_seed=turn_seed,
        idempotency_key=idempotency_key,
        decision=asdict(decision),
        resulting_state=state_data,
        events=[asdict(event) for event in result.events],
        submitted_at=now,
    )
    session.add(turn)
    session.commit()
    session.refresh(turn)
    updated_run = session.get(SimulationRunRecord, run.id)
    if updated_run is None:
        raise SimulationRunError("simulation run disappeared after update")
    return CompletedTurn(run=updated_run, turn=turn)
