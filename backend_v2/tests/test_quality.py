from dataclasses import replace

import pytest

from app.simulation.engine import create_initial_state
from app.simulation.models import Employee, EmployeeType, TaskPool, Throughput
from app.simulation.quality import (
    DifficultyProbabilities,
    apply_development_result,
    bug_probabilities,
    incorrect_specification_probability,
)
from app.simulation.randomness import RecordedRandomSource


def employee_type(
    code: str,
    *,
    throughput: Throughput,
    error_rate: float,
    management_skill: float,
) -> EmployeeType:
    return EmployeeType(
        code=code,
        name=code,
        cost_per_day=100,
        throughput=throughput,
        error_rate=error_rate,
        management_skill=management_skill,
    )


def project_state(*employees: Employee):
    initial = create_initial_state(
        total_tasks=40,
        difficulty_weights=(0.25, 0.5, 0.25),
        budget=10_000,
        working_days=20,
    )
    return replace(initial, employees=employees)


def test_bug_probability_is_weighted_by_difficulty_productivity() -> None:
    fast = employee_type(
        "fast",
        throughput=Throughput(easy=9, medium=1, hard=1),
        error_rate=0.3,
        management_skill=0.5,
    )
    careful = employee_type(
        "careful",
        throughput=Throughput(easy=1, medium=9, hard=1),
        error_rate=0,
        management_skill=0.5,
    )
    state = project_state(
        Employee(id="one", employee_type_code="fast", stress=0),
        Employee(id="two", employee_type_code="careful", stress=0),
    )
    probabilities = bug_probabilities(state, employee_types=(fast, careful))
    assert probabilities.easy == pytest.approx(0.09)
    assert probabilities.medium == pytest.approx(0.01)
    assert probabilities.hard == pytest.approx(0.05)


def test_management_quality_controls_specification_failure_probability() -> None:
    lead = employee_type(
        "lead",
        throughput=Throughput(easy=1, medium=1, hard=1),
        error_rate=0,
        management_skill=0.8,
    )
    state = project_state(Employee(id="lead", employee_type_code="lead"))
    assert incorrect_specification_probability(state, employee_types=(lead,)) == pytest.approx(0.2)


def test_development_moves_tasks_and_records_hidden_quality() -> None:
    state = project_state(Employee(id="one", employee_type_code="developer"))
    completed = TaskPool(easy=2, medium=1, hard=0)
    # Six values: three bug checks followed by three specification checks.
    random = RecordedRandomSource(probabilities=[0.1, 0.9, 0.2, 0.8, 0.1, 0.7])
    result = apply_development_result(
        state,
        completed=completed,
        defect_probabilities=DifficultyProbabilities(easy=0.5, medium=0.5, hard=0.5),
        specification_failure_probability=0.5,
        random=random,
    )
    assert result.state.tasks_todo == TaskPool(easy=8, medium=19, hard=10)
    assert result.state.tasks_completed == completed
    assert result.bugs_created == TaskPool(easy=1, medium=1, hard=0)
    assert result.incorrect_specifications_created == TaskPool(easy=1, medium=0, hard=0)
    assert result.state.undiscovered_bugs == result.bugs_created
    assert result.state.incorrect_specifications == result.incorrect_specifications_created


def test_cannot_complete_more_tasks_than_remain() -> None:
    state = project_state()
    with pytest.raises(ValueError, match="task counts cannot be negative"):
        apply_development_result(
            state,
            completed=TaskPool(easy=11, medium=0, hard=0),
            defect_probabilities=DifficultyProbabilities(easy=0, medium=0, hard=0),
            specification_failure_probability=0,
            random=RecordedRandomSource(),
        )
