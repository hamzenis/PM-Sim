from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import (
    Base,
    ClassMembershipRecord,
    ClassRecord,
    RevisionStatus,
    ScenarioAvailabilityRecord,
    ScenarioRecord,
    ScenarioRevisionRecord,
    UserRecord,
    UserRole,
)
from app.scenarios.models import ScenarioDefinition
from app.simulation.models import ActivityAllocation, HireRequest, WeeklyDecision
from app.simulations.service import (
    ConcurrentTurnError,
    SimulationRunError,
    complete_simulation_turn,
    get_simulation_run,
    list_simulation_runs,
    list_simulation_turns,
    start_simulation_run,
    submit_simulation_run,
)


@pytest.fixture
def session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as database_session:
        yield database_session


def scenario_definition() -> ScenarioDefinition:
    return ScenarioDefinition.model_validate(
        {
            "schema_version": 1,
            "name": "Service Test",
            "project": {"budget": 10_000, "working_days": 5},
            "tasks": {"total": 40},
            "employee_types": [
                {
                    "code": "developer",
                    "name": "Developer",
                    "cost_per_day": 100,
                    "throughput": {"easy": 4, "medium": 2, "hard": 1},
                    "error_rate": 0,
                    "management_skill": 1,
                }
            ],
            "rules": {"randomness": "none"},
        }
    )


def persisted_inputs(session: Session, *, published: bool = True):
    now = datetime.now(UTC)
    user = UserRecord(
        username="student",
        password_hash="not-used-in-this-service-test",
        role=UserRole.STUDENT,
        created_at=now,
    )
    professor = UserRecord(
        username="professor",
        password_hash="not-used-in-this-service-test",
        role=UserRole.PROFESSOR,
        created_at=now,
    )
    scenario = ScenarioRecord(name="Service Test", created_at=now)
    revision = ScenarioRevisionRecord(
        scenario=scenario,
        revision_number=1,
        schema_version=1,
        status=RevisionStatus.PUBLISHED if published else RevisionStatus.DRAFT,
        definition=scenario_definition().model_dump(mode="json"),
        created_at=now,
        published_at=now if published else None,
    )
    session.add_all([user, professor, scenario])
    session.commit()
    course_class = ClassRecord(name="Class", professor_id=professor.id, created_at=now)
    session.add(course_class)
    session.flush()
    session.add_all(
        [
            ClassMembershipRecord(
                class_id=course_class.id,
                user_id=user.id,
                created_at=now,
            ),
            ScenarioAvailabilityRecord(
                class_id=course_class.id,
                scenario_revision_id=revision.id,
                created_at=now,
            ),
        ]
    )
    session.commit()
    return user, revision


def development_decision() -> WeeklyDecision:
    return WeeklyDecision(
        allocation=ActivityAllocation(100, 0, 0, 0),
        hires=(HireRequest("developer", 1),),
    )


def test_run_requires_a_published_scenario_revision(session: Session) -> None:
    user, revision = persisted_inputs(session, published=False)
    with pytest.raises(SimulationRunError, match="published scenario"):
        start_simulation_run(
            session,
            user_id=user.id,
            scenario_revision_id=revision.id,
            seed=42,
        )


def test_run_requires_class_scenario_availability(session: Session) -> None:
    user, revision = persisted_inputs(session)
    availability = session.query(ScenarioAvailabilityRecord).one()
    session.delete(availability)
    session.commit()
    with pytest.raises(SimulationRunError, match="not available"):
        start_simulation_run(
            session,
            user_id=user.id,
            scenario_revision_id=revision.id,
            seed=42,
        )


def test_run_cannot_start_after_scenario_is_archived(session: Session) -> None:
    user, revision = persisted_inputs(session)
    revision.scenario.archived_at = datetime.now(UTC)
    session.commit()
    with pytest.raises(SimulationRunError, match="not available"):
        start_simulation_run(
            session,
            user_id=user.id,
            scenario_revision_id=revision.id,
            seed=42,
        )


def test_runs_are_listed_and_read_only_for_their_owner(session: Session) -> None:
    user, revision = persisted_inputs(session)
    run = start_simulation_run(session, user_id=user.id, scenario_revision_id=revision.id, seed=3)
    assert list_simulation_runs(session, user.id) == [run]
    assert get_simulation_run(session, run_id=run.id, user_id=user.id) == run
    with pytest.raises(SimulationRunError, match="not found"):
        get_simulation_run(session, run_id=run.id, user_id="another-user")


def test_student_can_submit_an_active_run_once(session: Session) -> None:
    user, revision = persisted_inputs(session)
    run = start_simulation_run(session, user_id=user.id, scenario_revision_id=revision.id, seed=3)
    submitted = submit_simulation_run(
        session,
        run_id=run.id,
        user_id=user.id,
        expected_version=1,
    )
    assert submitted.status == "submitted"
    assert submitted.version == 2
    assert submitted.finished_at is not None
    assert submitted.final_result["outcome"] == "submitted"

    replay = submit_simulation_run(
        session,
        run_id=run.id,
        user_id=user.id,
        expected_version=1,
    )
    assert replay.version == 2
    with pytest.raises(SimulationRunError, match="not active"):
        complete_simulation_turn(
            session,
            run_id=run.id,
            user_id=user.id,
            decision=development_decision(),
            expected_version=2,
            idempotency_key="after-submit",
        )


def test_turn_history_requires_run_ownership(session: Session) -> None:
    user, revision = persisted_inputs(session)
    run = start_simulation_run(session, user_id=user.id, scenario_revision_id=revision.id, seed=3)
    complete_simulation_turn(
        session,
        run_id=run.id,
        user_id=user.id,
        decision=development_decision(),
        expected_version=1,
        idempotency_key="history",
    )
    assert [
        turn.week_number for turn in list_simulation_turns(session, run_id=run.id, user_id=user.id)
    ] == [1]
    with pytest.raises(SimulationRunError, match="not found"):
        list_simulation_turns(session, run_id=run.id, user_id="another-user")


def test_turn_is_persisted_with_state_events_seed_and_optimistic_version(session: Session) -> None:
    user, revision = persisted_inputs(session)
    run = start_simulation_run(session, user_id=user.id, scenario_revision_id=revision.id, seed=42)
    completed = complete_simulation_turn(
        session,
        run_id=run.id,
        user_id=user.id,
        decision=development_decision(),
        expected_version=1,
        idempotency_key="week-one",
    )
    assert completed.run.current_week == 1
    assert completed.run.version == 2
    assert completed.run.status == "deadline_reached"
    assert completed.run.final_result is not None
    assert completed.turn.turn_seed == 42
    assert completed.turn.decision["allocation"]["development"] == 100
    assert completed.turn.events[-1]["kind"] == "simulation_finished"


def test_idempotency_replays_the_existing_turn_without_processing_again(session: Session) -> None:
    user, revision = persisted_inputs(session)
    run = start_simulation_run(session, user_id=user.id, scenario_revision_id=revision.id, seed=7)
    first = complete_simulation_turn(
        session,
        run_id=run.id,
        user_id=user.id,
        decision=development_decision(),
        expected_version=1,
        idempotency_key="same-request",
    )
    replay = complete_simulation_turn(
        session,
        run_id=run.id,
        user_id=user.id,
        decision=development_decision(),
        expected_version=1,
        idempotency_key="same-request",
    )
    assert replay.replayed is True
    assert replay.turn.id == first.turn.id
    assert replay.run.version == 2


def test_stale_run_version_is_rejected(session: Session) -> None:
    user, revision = persisted_inputs(session)
    run = start_simulation_run(session, user_id=user.id, scenario_revision_id=revision.id, seed=7)
    with pytest.raises(ConcurrentTurnError, match="version has changed"):
        complete_simulation_turn(
            session,
            run_id=run.id,
            user_id=user.id,
            decision=development_decision(),
            expected_version=99,
            idempotency_key="stale",
        )
