"""Application services for simulation runs.

The application-service boundary owns transactions: each command constructs every
row, uses ``flush`` only when generated identifiers are needed, and commits once.
"""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.authored_content.answers import normalize_answer
from app.authored_content.definitions import (
    from_pinned_revision,
    referenced_definition,
    student_safe_snapshot,
)
from app.authored_content.digests import (
    definition_digest,
    response_request_digest,
    turn_request_digest,
)
from app.authored_content.effects import apply_effects
from app.authored_content.models import Checkpoint, RuntimeEntry, RuntimeStatus
from app.authored_content.resolver import resolve
from app.classes.service import accessible_class_for_revision
from app.db.models import (
    AppliedPresentationEffectRecord,
    ContentDeliveryRecord,
    ContentResponseRecord,
    RevisionStatus,
    ScenarioRecord,
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


class IdempotencyConflictError(SimulationRunError):
    pass


class ContentBlockingError(SimulationRunError):
    """A required, already-delivered student item blocks progression."""

    def __init__(self, delivery: ContentDeliveryRecord):
        self.delivery = delivery
        super().__init__("required authored content must be completed")


@dataclass(frozen=True, slots=True)
class CompletedTurn:
    run: SimulationRunRecord
    turn: SimulationTurnRecord
    replayed: bool = False

    @property
    def projection_version(self) -> int:
        return self.turn.resulting_run_version or self.run.version


def list_simulation_runs(session: Session, user_id: str) -> list[SimulationRunRecord]:
    return list(
        session.scalars(
            select(SimulationRunRecord)
            .where(SimulationRunRecord.user_id == user_id)
            .order_by(SimulationRunRecord.started_at.desc(), SimulationRunRecord.id)
        )
    )


def get_simulation_run(session: Session, *, run_id: str, user_id: str) -> SimulationRunRecord:
    run = session.get(SimulationRunRecord, run_id)
    if run is None or run.user_id != user_id:
        raise SimulationRunError("simulation run not found")
    return run


def list_simulation_turns(
    session: Session, *, run_id: str, user_id: str
) -> list[SimulationTurnRecord]:
    get_simulation_run(session, run_id=run_id, user_id=user_id)
    return list(
        session.scalars(
            select(SimulationTurnRecord)
            .where(SimulationTurnRecord.run_id == run_id)
            .order_by(SimulationTurnRecord.week_number)
        )
    )


def _scenario(
    session: Session, run: SimulationRunRecord
) -> tuple[ScenarioRevisionRecord, ScenarioDefinition]:
    revision = session.get(ScenarioRevisionRecord, run.scenario_revision_id)
    if revision is None:
        raise SimulationRunError("scenario revision not found")
    return revision, ScenarioDefinition.model_validate(revision.definition)


def _entries(
    revision: ScenarioRevisionRecord, deliveries: list[ContentDeliveryRecord]
) -> list[RuntimeEntry]:
    lookups = from_pinned_revision(revision.id, revision.definition)
    rows = {row.sequence_entry_id: row for row in deliveries}
    result = []
    for ordinal, sequence in enumerate(lookups.sequence):
        kind, definition = referenced_definition(lookups, sequence)
        row = rows.get(sequence["id"])
        trigger = sequence["trigger"]
        checkpoint = Checkpoint.parse({"type": trigger["type"], "week": trigger.get("week")})
        result.append(
            RuntimeEntry(
                id=sequence["id"],
                checkpoint=checkpoint,
                ordinal=ordinal,
                priority=sequence.get("priority", 0),
                required=bool(definition.get("required", False)),
                kind=kind,
                depends_on=tuple(sequence.get("depends_on", ())),
                status=RuntimeStatus(row.status) if row else RuntimeStatus.PENDING,
                definition=dict(definition),
            )
        )
    return result


def _presentation(session: Session, run_id: str) -> dict[str, Any]:
    projection: dict[str, Any] = {}
    effects = session.scalars(
        select(AppliedPresentationEffectRecord)
        .where(AppliedPresentationEffectRecord.run_id == run_id)
        .order_by(AppliedPresentationEffectRecord.applied_at, AppliedPresentationEffectRecord.id)
    ).all()
    for effect in effects:
        projection, _ = apply_effects(projection, [effect.effect_payload])
    return projection


def _resolve_content(
    session: Session,
    run: SimulationRunRecord,
    revision: ScenarioRevisionRecord,
    checkpoint: Checkpoint,
    *,
    turn: SimulationTurnRecord | None = None,
    terminal: bool = False,
) -> None:
    """Resolve a checkpoint, auto-completing events/optional fragments to a fixpoint."""
    while True:
        deliveries = list(
            session.scalars(
                select(ContentDeliveryRecord).where(ContentDeliveryRecord.run_id == run.id)
            )
        )
        by_id = {row.sequence_entry_id: row for row in deliveries}
        resolution = resolve(_entries(revision, deliveries), checkpoint, terminal=terminal)
        fresh = [entry for entry in resolution.actionable if entry.id not in by_id]
        if not fresh:
            return
        progressed = False
        for entry in fresh:
            snapshot = student_safe_snapshot(entry.kind, entry.definition)
            # Sequence metadata is safe and needed for student ordering/visibility.
            sequence = next(
                item
                for item in from_pinned_revision(revision.id, revision.definition).sequence
                if item["id"] == entry.id
            )
            snapshot.update(
                {
                    "kind": entry.kind,
                    "required": entry.required,
                    "visibility": sequence.get("visibility", "default"),
                    "professor_only": bool(entry.definition.get("professor_only", False)),
                }
            )
            row = ContentDeliveryRecord(
                run_id=run.id,
                sequence_entry_id=entry.id,
                canonical_checkpoint=entry.checkpoint.canonical,
                sequence_ordinal=entry.ordinal,
                definition_snapshot=snapshot,
                definition_digest=definition_digest(snapshot),
                status=RuntimeStatus.ACTIONABLE,
                delivered_at=datetime.now(UTC),
                turn_id=turn.id if turn else None,
            )
            session.add(row)
            if entry.kind == "event" or (entry.kind == "fragment" and not entry.required):
                row.status = RuntimeStatus.COMPLETED
                row.completed_at = datetime.now(UTC)
                effects = (
                    []
                    if entry.definition.get("professor_only")
                    else entry.definition.get("effects", [])
                )
                before = _presentation(session, run.id)
                after, audits = apply_effects(before, effects)
                del after
                for index, (effect, audit) in enumerate(zip(effects, audits, strict=True)):
                    session.add(
                        AppliedPresentationEffectRecord(
                            run_id=run.id,
                            sequence_entry_id=entry.id,
                            effect_index=index,
                            effect_payload={
                                "type": effect["type"],
                                "payload": dict(effect["payload"]),
                            },
                            before_projection_digest=audit.before_digest,
                            after_projection_digest=audit.after_digest,
                            applied_at=datetime.now(UTC),
                            turn_id=turn.id if turn else None,
                        )
                    )
                progressed = True
        session.flush()
        if not progressed:
            return


def _blocking_delivery(session: Session, run_id: str) -> ContentDeliveryRecord | None:
    rows = session.scalars(
        select(ContentDeliveryRecord)
        .where(
            ContentDeliveryRecord.run_id == run_id,
            ContentDeliveryRecord.status == RuntimeStatus.ACTIONABLE,
        )
        .order_by(ContentDeliveryRecord.sequence_ordinal)
    ).all()
    return next((row for row in rows if row.definition_snapshot.get("required")), None)


def submit_simulation_run(
    session: Session, *, run_id: str, user_id: str, expected_version: int
) -> SimulationRunRecord:
    run = get_simulation_run(session, run_id=run_id, user_id=user_id)
    if run.status != SimulationOutcome.ACTIVE:
        return run
    if run.version != expected_version:
        raise ConcurrentTurnError("simulation run version has changed")
    revision, scenario = _scenario(session, run)
    now = datetime.now(UTC)
    run.status, run.version, run.finished_at = (
        SimulationOutcome.SUBMITTED,
        expected_version + 1,
        now,
    )
    run.final_result = asdict(
        build_simulation_result(
            state_from_dict(run.current_state),
            rules=score_rules_from_scenario(scenario),
            submitted=True,
        )
    )
    _resolve_content(session, run, revision, Checkpoint("run_finished"), terminal=True)
    session.commit()
    return run


def start_simulation_run(
    session: Session,
    *,
    user_id: str,
    scenario_revision_id: str,
    seed: int,
    class_id: str | None = None,
) -> SimulationRunRecord:
    user = session.get(UserRecord, user_id)
    revision = session.get(ScenarioRevisionRecord, scenario_revision_id)
    if user is None:
        raise SimulationRunError("user not found")
    if revision is None or revision.status != RevisionStatus.PUBLISHED:
        raise SimulationRunError("a published scenario revision is required")
    scenario_record = session.get(ScenarioRecord, revision.scenario_id)
    if scenario_record is None or scenario_record.archived_at is not None:
        raise SimulationRunError("scenario is not available")
    available = accessible_class_for_revision(
        session, user_id=user.id, revision_id=revision.id, class_id=class_id
    )
    if available is None:
        raise SimulationRunError("scenario revision is not available to this user")
    scenario = ScenarioDefinition.model_validate(revision.definition)
    run = SimulationRunRecord(
        user_id=user.id,
        class_id=available,
        scenario_revision_id=revision.id,
        status=SimulationOutcome.ACTIVE,
        seed=seed,
        engine_version=ENGINE_VERSION,
        current_week=0,
        version=1,
        current_state=state_to_dict(initial_state_from_scenario(scenario)),
        started_at=datetime.now(UTC),
    )
    session.add(run)
    session.flush()
    _resolve_content(session, run, revision, Checkpoint("run_started"))
    session.commit()
    return run


def canonical_turn_request(decision: WeeklyDecision, expected_version: int) -> dict[str, Any]:
    """Canonical policy: staffing collections are sets; allocation numbers retain value."""
    raw = asdict(decision)
    hires: dict[str, int] = {}
    for hire in raw["hires"]:
        hires[hire["employee_type_code"]] = hires.get(hire["employee_type_code"], 0) + hire["count"]
    raw["hires"] = [{"employee_type_code": key, "count": hires[key]} for key in sorted(hires)]
    raw["dismiss_employee_ids"] = sorted(set(raw["dismiss_employee_ids"]))
    return {"expected_version": expected_version, "decision": raw}


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
    digest = turn_request_digest(canonical_turn_request(decision, expected_version))
    existing = session.scalar(
        select(SimulationTurnRecord).where(
            SimulationTurnRecord.run_id == run_id,
            SimulationTurnRecord.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        run = get_simulation_run(session, run_id=run_id, user_id=user_id)
        if existing.request_digest != digest:
            raise IdempotencyConflictError("idempotency key was reused with a different request")
        return CompletedTurn(run=run, turn=existing, replayed=True)
    run = get_simulation_run(session, run_id=run_id, user_id=user_id)
    if run.status != SimulationOutcome.ACTIVE:
        raise SimulationRunError("simulation run is not active")
    if run.version != expected_version:
        raise ConcurrentTurnError("simulation run version has changed")
    revision, scenario = _scenario(session, run)
    next_week = run.current_week + 1
    _resolve_content(session, run, revision, Checkpoint("before_week", next_week))
    blocker = _blocking_delivery(session, run.id)
    if blocker:
        # Resolving the gate is itself the complete (blocked) command outcome.
        session.commit()
        raise ContentBlockingError(blocker)
    turn_seed = run.seed + run.current_week
    employee_sequence = iter(range(sum(hire.count for hire in decision.hires)))
    result = process_week(
        state_from_dict(run.current_state),
        decision=decision,
        employee_types=employee_types_from_scenario(scenario),
        rules=turn_rules_from_scenario(scenario),
        random=SeededRandomSource(turn_seed),
        # Employee identity is part of simulation state, so derive it from simulation
        # inputs rather than process entropy.  Authored-content-only revisions can then
        # be proven bit-for-bit neutral to the simulation track.
        new_employee_id=lambda: str(
            uuid5(NAMESPACE_URL, f"pm-sim:{turn_seed}:{next(employee_sequence)}")
        ),
    )
    outcome, now, state_data = (
        evaluate_outcome(result.state),
        datetime.now(UTC),
        state_to_dict(result.state),
    )
    turn = SimulationTurnRecord(
        run_id=run.id,
        week_number=result.state.week,
        turn_seed=turn_seed,
        idempotency_key=idempotency_key,
        request_digest=digest,
        resulting_run_version=expected_version + 1,
        decision=asdict(decision),
        resulting_state=state_data,
        events=[asdict(event) for event in result.events],
        submitted_at=now,
    )
    session.add(turn)
    session.flush()
    _resolve_content(session, run, revision, Checkpoint("after_week", result.state.week), turn=turn)
    if outcome is not SimulationOutcome.ACTIVE:
        _resolve_content(
            session, run, revision, Checkpoint("run_finished"), turn=turn, terminal=True
        )
    run.status, run.current_week, run.version, run.current_state = (
        outcome,
        result.state.week,
        expected_version + 1,
        state_data,
    )
    if outcome is not SimulationOutcome.ACTIVE:
        run.final_result, run.finished_at = (
            asdict(
                build_simulation_result(result.state, rules=score_rules_from_scenario(scenario))
            ),
            now,
        )
    session.commit()
    return CompletedTurn(run=run, turn=turn)


def content_command(
    session: Session,
    *,
    run_id: str,
    user_id: str,
    sequence_entry_id: str,
    expected_version: int,
    idempotency_key: str,
    command_kind: str,
    answer: Any = None,
) -> tuple[SimulationRunRecord, bool]:
    request = {
        "command_kind": command_kind,
        "sequence_entry_id": sequence_entry_id,
        "expected_version": expected_version,
    }
    if command_kind == "answer":
        request["answer"] = answer
    digest = response_request_digest(request)
    prior = session.scalar(
        select(ContentResponseRecord).where(
            ContentResponseRecord.run_id == run_id,
            ContentResponseRecord.idempotency_key == idempotency_key,
        )
    )
    if prior:
        prior_run = get_simulation_run(session, run_id=run_id, user_id=user_id)
        if prior.request_digest != digest:
            raise IdempotencyConflictError("idempotency key was reused with a different request")
        return prior_run, True
    run = get_simulation_run(session, run_id=run_id, user_id=user_id)
    if run.version != expected_version:
        raise ConcurrentTurnError("simulation run version has changed")
    delivery = session.scalar(
        select(ContentDeliveryRecord).where(
            ContentDeliveryRecord.run_id == run.id,
            ContentDeliveryRecord.sequence_entry_id == sequence_entry_id,
        )
    )
    if delivery is None or delivery.status != RuntimeStatus.ACTIONABLE:
        raise SimulationRunError("content entry is not delivered and actionable")
    snapshot = delivery.definition_snapshot
    if command_kind == "answer":
        if snapshot.get("kind") != "question":
            raise SimulationRunError("only questions can be answered")
        normalized = normalize_answer(snapshot, answer)
        payload = {"answer": normalized}
    else:
        if snapshot.get("kind") != "fragment" or not snapshot.get("required"):
            raise SimulationRunError("only required fragments can be acknowledged")
        payload = {"acknowledged": True}
    session.add(
        ContentResponseRecord(
            run_id=run.id,
            sequence_entry_id=sequence_entry_id,
            response_version=1,
            normalized_answer=payload,
            command_kind=command_kind,
            request_digest=digest,
            idempotency_key=idempotency_key,
            answered_at=datetime.now(UTC),
        )
    )
    delivery.status, delivery.completed_at = RuntimeStatus.COMPLETED, datetime.now(UTC)
    revision, _ = _scenario(session, run)
    checkpoint = Checkpoint.parse(delivery.canonical_checkpoint)
    _resolve_content(session, run, revision, checkpoint)
    run.version = expected_version + 1
    session.commit()
    return run, False
