from dataclasses import replace

import pytest

from app.simulation.employee_dynamics import EmployeeDynamicsRules, update_employee_dynamics
from app.simulation.engine import create_initial_state
from app.simulation.models import Employee, EmployeeType, Throughput


def employee_type(code: str, throughput: float) -> EmployeeType:
    return EmployeeType(
        code=code,
        name=code,
        cost_per_day=100,
        throughput=Throughput(throughput, throughput, throughput),
        error_rate=0,
    )


def state_with(*employees: Employee):
    return replace(
        create_initial_state(
            total_tasks=40,
            difficulty_weights=(0.25, 0.5, 0.25),
            budget=10_000,
            working_days=20,
        ),
        employees=employees,
    )


def test_overtime_recovery_and_solo_work_update_employee_wellbeing() -> None:
    state = state_with(Employee(id="one", employee_type_code="junior"))
    updated = update_employee_dynamics(
        state,
        employee_types=(employee_type("junior", 2),),
        overtime_hours_per_employee=2,
        meeting_hours_per_employee=0,
        training_hours_per_employee=0,
        rules=EmployeeDynamicsRules(),
    )
    employee = updated.employees[0]
    # 0.10 + 2*0.05 overtime - 0.20 recovery + 0.05 solo penalty.
    assert employee.stress == pytest.approx(0.05)
    assert employee.motivation == pytest.approx(0.71)


def test_meetings_improve_familiarity_and_training_helps_slower_employee() -> None:
    state = state_with(
        Employee(id="slow", employee_type_code="junior"),
        Employee(id="fast", employee_type_code="senior"),
    )
    updated = update_employee_dynamics(
        state,
        employee_types=(employee_type("junior", 1), employee_type("senior", 3)),
        overtime_hours_per_employee=0,
        meeting_hours_per_employee=2,
        training_hours_per_employee=1,
        rules=EmployeeDynamicsRules(),
    )
    slow, fast = updated.employees
    assert slow.familiarity == pytest.approx(0.1)
    assert fast.familiarity == pytest.approx(0.1)
    assert slow.experience == pytest.approx(0.1)
    assert slow.motivation == pytest.approx(0.85)
    assert fast.experience == 0
    assert fast.motivation == pytest.approx(0.75)
