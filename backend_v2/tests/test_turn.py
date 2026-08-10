from itertools import count

import pytest

from app.simulation.engine import create_initial_state
from app.simulation.models import (
    ActivityAllocation,
    EmployeeType,
    HireRequest,
    TaskPool,
    Throughput,
    WeeklyDecision,
)
from app.simulation.randomness import RecordedRandomSource
from app.simulation.turn import TurnRules, process_week


def developer_type() -> EmployeeType:
    return EmployeeType(
        code="developer",
        name="Developer",
        cost_per_day=100,
        throughput=Throughput(easy=4, medium=2, hard=1),
        error_rate=0,
        management_skill=1,
    )


def initial_state():
    return create_initial_state(
        total_tasks=40,
        difficulty_weights=(0.25, 0.5, 0.25),
        budget=10_000,
        working_days=7,
    )


def test_complete_development_week_updates_state_budget_time_and_events() -> None:
    ids = (f"employee-{number}" for number in count(1))
    result = process_week(
        initial_state(),
        decision=WeeklyDecision(
            allocation=ActivityAllocation(
                development=100,
                unit_testing=0,
                bug_fixing=0,
                integration_testing=0,
            ),
            hires=(HireRequest(employee_type_code="developer", count=1),),
        ),
        employee_types=(developer_type(),),
        rules=TurnRules(randomness="none"),
        random=RecordedRandomSource(probabilities=[0.99] * 20),
        new_employee_id=lambda: next(ids),
    )
    assert result.state.week == 1
    assert result.state.elapsed_working_days == 5
    assert result.state.remaining_working_days == 2
    assert result.state.remaining_budget == 9_500
    assert result.state.tasks_completed == TaskPool(easy=4, medium=4, hard=1)
    assert result.state.tasks_todo == TaskPool(easy=6, medium=16, hard=9)
    assert result.state.total_tasks == 40
    assert result.activity_hours.development == 40
    assert [event.kind for event in result.events] == [
        "staffing_changed",
        "tasks_unit_tested",
        "bugs_discovered",
        "bugs_fixed",
        "tasks_completed",
        "bugs_created",
        "incorrect_specifications_created",
        "tasks_integration_tested",
        "tasks_returned_to_backlog",
        "employee_dynamics_updated",
        "staff_cost_charged",
        "week_completed",
    ]


def test_final_week_uses_only_remaining_working_days() -> None:
    ids = iter(["employee"])
    first = process_week(
        initial_state(),
        decision=WeeklyDecision(
            allocation=ActivityAllocation(100, 0, 0, 0),
            hires=(HireRequest("developer", 1),),
        ),
        employee_types=(developer_type(),),
        rules=TurnRules(randomness="none"),
        random=RecordedRandomSource(probabilities=[0.99] * 20),
        new_employee_id=lambda: next(ids),
    )
    second = process_week(
        first.state,
        decision=WeeklyDecision(allocation=ActivityAllocation(100, 0, 0, 0)),
        employee_types=(developer_type(),),
        rules=TurnRules(randomness="none"),
        random=RecordedRandomSource(probabilities=[0.99] * 20),
        new_employee_id=lambda: "unused",
    )
    assert second.state.elapsed_working_days == 7
    assert second.state.remaining_working_days == 0
    assert second.state.remaining_budget == 9_300

    with pytest.raises(ValueError, match="deadline has already been reached"):
        process_week(
            second.state,
            decision=WeeklyDecision(allocation=ActivityAllocation(100, 0, 0, 0)),
            employee_types=(developer_type(),),
            rules=TurnRules(randomness="none"),
            random=RecordedRandomSource(),
            new_employee_id=lambda: "unused",
        )
