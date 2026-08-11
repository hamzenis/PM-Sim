from dataclasses import replace
from itertools import count

import pytest

from app.simulation.engine import create_initial_state
from app.simulation.models import Employee, EmployeeType, HireRequest, Throughput
from app.simulation.staffing import StaffingError, apply_staffing_changes, weekly_staff_cost


def employee_type(code: str = "junior", cost_per_day: float = 100) -> EmployeeType:
    return EmployeeType(
        code=code,
        name=code.title(),
        cost_per_day=cost_per_day,
        throughput=Throughput(easy=4, medium=2, hard=1),
        error_rate=0.1,
    )


def state_with_employee():
    state = create_initial_state(
        total_tasks=20,
        difficulty_weights=(0.25, 0.5, 0.25),
        budget=10_000,
        working_days=20,
    )
    return replace(
        state,
        employees=(Employee(id="existing", employee_type_code="junior"),),
    )


def test_staff_can_be_hired_and_dismissed_immutably() -> None:
    ids = (f"new-{number}" for number in count(1))
    original = state_with_employee()
    updated = apply_staffing_changes(
        original,
        employee_types=[employee_type()],
        hires=(HireRequest(employee_type_code="junior", count=2),),
        dismiss_employee_ids=("existing",),
        new_employee_id=lambda: next(ids),
    )
    assert [employee.id for employee in updated.employees] == ["new-1", "new-2"]
    assert [employee.id for employee in original.employees] == ["existing"]


def test_unknown_employee_type_cannot_be_hired() -> None:
    with pytest.raises(StaffingError, match="unknown employee type: missing"):
        apply_staffing_changes(
            state_with_employee(),
            employee_types=[employee_type()],
            hires=(HireRequest(employee_type_code="missing", count=1),),
            dismiss_employee_ids=(),
            new_employee_id=lambda: "new",
        )


def test_weekly_cost_uses_daily_rate_and_working_days() -> None:
    employees = (
        Employee(id="one", employee_type_code="junior"),
        Employee(id="two", employee_type_code="senior"),
    )
    assert (
        weekly_staff_cost(
            employees,
            employee_types=[employee_type(), employee_type("senior", 250)],
            working_days=5,
        )
        == 1_750
    )
