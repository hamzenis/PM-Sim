from collections.abc import Callable
from dataclasses import dataclass, replace

from app.simulation.capacity import hours_from_allocation
from app.simulation.employee_dynamics import EmployeeDynamicsRules, update_employee_dynamics
from app.simulation.integration import IntegrationTestResult, apply_integration_testing
from app.simulation.models import (
    ActivityHours,
    EmployeeType,
    SimulationState,
    TaskPool,
    WeeklyCapacity,
    WeeklyDecision,
)
from app.simulation.productivity import expected_output_for_tasks, realize_task_output
from app.simulation.quality import (
    DevelopmentResult,
    apply_development_result,
    bug_probabilities,
    incorrect_specification_probability,
)
from app.simulation.randomness import RandomSource
from app.simulation.results import SimulationOutcome, evaluate_outcome
from app.simulation.staffing import apply_staffing_changes, weekly_staff_cost
from app.simulation.testing import BugFixResult, UnitTestResult, apply_bug_fixes, apply_unit_testing


@dataclass(frozen=True, slots=True)
class TurnRules:
    randomness: str
    working_days_per_week: int = 5
    hours_per_day: int = 8
    employee_dynamics: EmployeeDynamicsRules = EmployeeDynamicsRules()

    def __post_init__(self) -> None:
        if self.randomness not in {"full", "semi", "none"}:
            raise ValueError(f"unknown randomness mode: {self.randomness}")
        if self.working_days_per_week <= 0 or self.hours_per_day <= 0:
            raise ValueError("working days and hours per day must be positive")


@dataclass(frozen=True, slots=True)
class SimulationEvent:
    kind: str
    values: dict[str, object]


@dataclass(frozen=True, slots=True)
class TurnResult:
    state: SimulationState
    activity_hours: ActivityHours
    meeting_hours: float
    training_hours: float
    events: tuple[SimulationEvent, ...]


def process_week(
    state: SimulationState,
    *,
    decision: WeeklyDecision,
    employee_types: tuple[EmployeeType, ...],
    rules: TurnRules,
    random: RandomSource,
    new_employee_id: Callable[[], str],
) -> TurnResult:
    """Execute one complete, immutable simulation week in the documented order."""
    if state.remaining_working_days == 0:
        raise ValueError("the simulation deadline has already been reached")

    working_days = min(rules.working_days_per_week, state.remaining_working_days)
    current = apply_staffing_changes(
        state,
        employee_types=employee_types,
        hires=decision.hires,
        dismiss_employee_ids=decision.dismiss_employee_ids,
        new_employee_id=new_employee_id,
    )
    capacity = WeeklyCapacity(
        employee_count=len(current.employees),
        working_days=working_days,
        hours_per_day=rules.hours_per_day,
        overtime_hours_per_employee=decision.overtime_hours_per_employee,
    )
    meeting_hours = len(current.employees) * decision.meeting_hours_per_employee
    training_hours = len(current.employees) * decision.training_hours_per_employee
    activity_hours = hours_from_allocation(
        capacity,
        decision.allocation,
        reserved_hours=meeting_hours + training_hours,
    )
    events: list[SimulationEvent] = [
        SimulationEvent(
            kind="staffing_changed",
            values={
                "hired": sum(request.count for request in decision.hires),
                "dismissed": len(decision.dismiss_employee_ids),
                "team_size": len(current.employees),
            },
        )
    ]

    unit_test_result = _unit_test(
        current, employee_types, activity_hours.unit_testing, rules, random
    )
    current = unit_test_result.state
    events.extend(
        (
            _pool_event("tasks_unit_tested", unit_test_result.tested),
            _pool_event("bugs_discovered", unit_test_result.bugs_discovered),
        )
    )

    bug_fix_result = _fix_bugs(current, employee_types, activity_hours.bug_fixing, rules, random)
    current = bug_fix_result.state
    events.append(_pool_event("bugs_fixed", bug_fix_result.bugs_fixed))

    development_result = _develop(
        current, employee_types, activity_hours.development, rules, random
    )
    current = development_result.state
    events.extend(
        (
            _pool_event("tasks_completed", development_result.completed),
            _pool_event("bugs_created", development_result.bugs_created),
            _pool_event(
                "incorrect_specifications_created",
                development_result.incorrect_specifications_created,
            ),
        )
    )

    integration_result = _integrate(
        current, employee_types, activity_hours.integration_testing, rules, random
    )
    current = integration_result.state
    events.extend(
        (
            _pool_event("tasks_integration_tested", integration_result.passed),
            _pool_event("tasks_returned_to_backlog", integration_result.returned_to_backlog),
        )
    )

    current = update_employee_dynamics(
        current,
        employee_types=employee_types,
        overtime_hours_per_employee=decision.overtime_hours_per_employee,
        meeting_hours_per_employee=decision.meeting_hours_per_employee,
        training_hours_per_employee=decision.training_hours_per_employee,
        rules=rules.employee_dynamics,
    )
    events.append(
        SimulationEvent(
            kind="employee_dynamics_updated",
            values={
                "overtime_hours_per_employee": decision.overtime_hours_per_employee,
                "meeting_hours_per_employee": decision.meeting_hours_per_employee,
                "training_hours_per_employee": decision.training_hours_per_employee,
            },
        )
    )

    staff_cost = weekly_staff_cost(
        current.employees,
        employee_types=employee_types,
        working_days=working_days,
    )
    current = replace(
        current,
        week=current.week + 1,
        elapsed_working_days=current.elapsed_working_days + working_days,
        remaining_working_days=current.remaining_working_days - working_days,
        remaining_budget=current.remaining_budget - staff_cost,
    )
    events.extend(
        (
            SimulationEvent(kind="staff_cost_charged", values={"amount": staff_cost}),
            SimulationEvent(
                kind="week_completed",
                values={"week": current.week, "working_days": working_days},
            ),
        )
    )
    outcome = evaluate_outcome(current)
    if outcome is not SimulationOutcome.ACTIVE:
        events.append(SimulationEvent(kind="simulation_finished", values={"outcome": outcome}))
    return TurnResult(
        state=current,
        activity_hours=activity_hours,
        meeting_hours=meeting_hours,
        training_hours=training_hours,
        events=tuple(events),
    )


def _capacity_for(
    state: SimulationState,
    employee_types: tuple[EmployeeType, ...],
    hours: float,
    available: TaskPool,
    rules: TurnRules,
    random: RandomSource,
) -> TaskPool:
    expected = expected_output_for_tasks(
        state,
        employee_types=employee_types,
        work_hours=hours,
        available=available,
    )
    return realize_task_output(
        expected,
        randomness=rules.randomness,
        random=random,
        available=available,
    )


def _fix_bugs(
    state: SimulationState,
    employee_types: tuple[EmployeeType, ...],
    hours: float,
    rules: TurnRules,
    random: RandomSource,
) -> BugFixResult:
    fixed = _capacity_for(state, employee_types, hours, state.known_bugs, rules, random)
    return apply_bug_fixes(state, fixed=fixed)


def _unit_test(
    state: SimulationState,
    employee_types: tuple[EmployeeType, ...],
    hours: float,
    rules: TurnRules,
    random: RandomSource,
) -> UnitTestResult:
    available = state.tasks_completed.minus(state.tasks_unit_tested)
    tested = _capacity_for(state, employee_types, hours, available, rules, random)
    return apply_unit_testing(state, tested=tested, random=random)


def _develop(
    state: SimulationState,
    employee_types: tuple[EmployeeType, ...],
    hours: float,
    rules: TurnRules,
    random: RandomSource,
) -> DevelopmentResult:
    completed = _capacity_for(state, employee_types, hours, state.tasks_todo, rules, random)
    return apply_development_result(
        state,
        completed=completed,
        defect_probabilities=bug_probabilities(state, employee_types=employee_types),
        specification_failure_probability=incorrect_specification_probability(
            state, employee_types=employee_types
        ),
        random=random,
    )


def _integrate(
    state: SimulationState,
    employee_types: tuple[EmployeeType, ...],
    hours: float,
    rules: TurnRules,
    random: RandomSource,
) -> IntegrationTestResult:
    available = state.tasks_unit_tested.minus(state.tasks_integration_tested).minus(
        state.known_bugs
    )
    tested = _capacity_for(state, employee_types, hours, available, rules, random)
    return apply_integration_testing(state, tested=tested, random=random)


def _pool_event(kind: str, pool: TaskPool) -> SimulationEvent:
    return SimulationEvent(
        kind=kind,
        values={"easy": pool.easy, "medium": pool.medium, "hard": pool.hard},
    )
