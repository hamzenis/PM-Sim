from collections.abc import Callable, Iterable
from dataclasses import replace

from app.simulation.models import Employee, EmployeeType, HireRequest, SimulationState


class StaffingError(ValueError):
    pass


def apply_staffing_changes(
    state: SimulationState,
    *,
    employee_types: Iterable[EmployeeType],
    hires: tuple[HireRequest, ...],
    dismiss_employee_ids: tuple[str, ...],
    new_employee_id: Callable[[], str],
) -> SimulationState:
    """Return a new state after validating and applying hiring and dismissal."""
    types_by_code = {employee_type.code: employee_type for employee_type in employee_types}
    employees_by_id = {employee.id: employee for employee in state.employees}

    missing_ids = sorted(set(dismiss_employee_ids) - employees_by_id.keys())
    if missing_ids:
        raise StaffingError(f"employees do not exist: {', '.join(missing_ids)}")

    remaining = [
        employee for employee in state.employees if employee.id not in dismiss_employee_ids
    ]
    additions: list[Employee] = []
    generated_ids = set(employees_by_id)
    for request in hires:
        if request.employee_type_code not in types_by_code:
            raise StaffingError(f"unknown employee type: {request.employee_type_code}")
        for _ in range(request.count):
            employee_id = new_employee_id()
            if not employee_id or employee_id in generated_ids:
                raise StaffingError("new employee IDs must be unique and non-empty")
            generated_ids.add(employee_id)
            additions.append(
                Employee(id=employee_id, employee_type_code=request.employee_type_code)
            )

    return replace(state, employees=tuple([*remaining, *additions]))


def weekly_staff_cost(
    employees: Iterable[Employee],
    *,
    employee_types: Iterable[EmployeeType],
    working_days: int,
) -> float:
    """Calculate salary cost for the employees present during a work week."""
    if working_days < 0:
        raise ValueError("working days cannot be negative")
    types_by_code = {employee_type.code: employee_type for employee_type in employee_types}
    total = 0.0
    for employee in employees:
        try:
            employee_type = types_by_code[employee.employee_type_code]
        except KeyError as error:
            raise StaffingError(f"unknown employee type: {employee.employee_type_code}") from error
        total += employee_type.cost_per_day * working_days
    return total
