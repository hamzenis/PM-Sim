from dataclasses import replace

import pytest

from app.simulation.engine import create_initial_state
from app.simulation.models import Employee, EmployeeType, TaskPool, Throughput
from app.simulation.productivity import (
    ExpectedTaskOutput,
    expected_development_output,
    member_efficiency,
    realize_task_output,
    team_efficiency,
)
from app.simulation.randomness import RecordedRandomSource


def junior_type() -> EmployeeType:
    return EmployeeType(
        code="junior",
        name="Junior",
        cost_per_day=100,
        throughput=Throughput(easy=4, medium=2, hard=1),
        error_rate=0.1,
    )


def project_state(*employees: Employee):
    initial = create_initial_state(
        total_tasks=400,
        difficulty_weights=(0.25, 0.5, 0.25),
        budget=100_000,
        working_days=60,
    )
    return replace(initial, employees=employees)


def test_member_efficiency_preserves_legacy_attribute_relationship() -> None:
    employee = Employee(
        id="one",
        employee_type_code="junior",
        familiarity=0.5,
        motivation=0.75,
        stress=0.2,
    )
    assert member_efficiency(employee) == pytest.approx(0.75)


def test_team_efficiency_decreases_as_communication_channels_grow() -> None:
    assert team_efficiency(1) == 1
    assert team_efficiency(5) < team_efficiency(2)
    assert team_efficiency(10) < team_efficiency(5)


def test_development_is_automatically_spread_across_backlog_difficulties() -> None:
    state = project_state(Employee(id="one", employee_type_code="junior"))
    output = expected_development_output(
        state,
        employee_types=(junior_type(),),
        development_hours=40,
    )
    # The employee receives 10/20/10 hours following the 25/50/25 backlog mix.
    assert output.easy == pytest.approx(3.875)
    assert output.medium == pytest.approx(3.875)
    assert output.hard == pytest.approx(0.96875)


def test_no_employees_produce_no_tasks() -> None:
    output = expected_development_output(
        project_state(),
        employee_types=(junior_type(),),
        development_hours=40,
    )
    assert output == ExpectedTaskOutput(easy=0, medium=0, hard=0)


def test_randomness_modes_convert_expected_output_to_discrete_tasks() -> None:
    expected = ExpectedTaskOutput(easy=4.4, medium=2.6, hard=1.2)
    available = TaskPool(easy=100, medium=100, hard=1)
    assert realize_task_output(
        expected,
        randomness="none",
        random=RecordedRandomSource(),
        available=available,
    ) == TaskPool(easy=4, medium=3, hard=1)
    assert realize_task_output(
        expected,
        randomness="full",
        random=RecordedRandomSource(poisson_values=[6, 2, 3]),
        available=available,
    ) == TaskPool(easy=6, medium=2, hard=1)
    assert realize_task_output(
        expected,
        randomness="semi",
        random=RecordedRandomSource(poisson_values=[6, 2, 0]),
        available=available,
    ) == TaskPool(easy=5, medium=2, hard=1)
