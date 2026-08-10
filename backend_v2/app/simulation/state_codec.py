from dataclasses import asdict

from app.simulation.models import Employee, SimulationState, TaskPool


def state_to_dict(state: SimulationState) -> dict[str, object]:
    """Convert immutable engine state to portable JSON-compatible data."""
    data = asdict(state)
    data["employees"] = list(data["employees"])
    return data


def state_from_dict(data: dict[str, object]) -> SimulationState:
    """Restore engine state while applying all domain validation again."""

    def task_pool(name: str) -> TaskPool:
        value = data.get(name)
        if not isinstance(value, dict):
            raise ValueError(f"{name} must be an object")
        return TaskPool(
            easy=_integer(value, "easy"),
            medium=_integer(value, "medium"),
            hard=_integer(value, "hard"),
        )

    employees_data = data.get("employees", [])
    if not isinstance(employees_data, list):
        raise ValueError("employees must be a list")
    employees = tuple(_employee(value) for value in employees_data)

    return SimulationState(
        week=_integer(data, "week"),
        elapsed_working_days=_integer(data, "elapsed_working_days"),
        remaining_working_days=_integer(data, "remaining_working_days"),
        initial_budget=_number(data, "initial_budget"),
        remaining_budget=_number(data, "remaining_budget"),
        tasks_todo=task_pool("tasks_todo"),
        tasks_completed=task_pool("tasks_completed"),
        tasks_unit_tested=task_pool("tasks_unit_tested"),
        tasks_integration_tested=task_pool("tasks_integration_tested"),
        known_bugs=task_pool("known_bugs"),
        undiscovered_bugs=task_pool("undiscovered_bugs"),
        incorrect_specifications=task_pool("incorrect_specifications"),
        employees=employees,
    )


def _employee(value: object) -> Employee:
    if not isinstance(value, dict):
        raise ValueError("each employee must be an object")
    return Employee(
        id=_string(value, "id"),
        employee_type_code=_string(value, "employee_type_code"),
        motivation=_number(value, "motivation"),
        stress=_number(value, "stress"),
        experience=_number(value, "experience"),
        familiarity=_number(value, "familiarity"),
    )


def _integer(data: dict[str, object], name: str) -> int:
    value = data.get(name)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    return value


def _number(data: dict[str, object], name: str) -> float:
    value = data.get(name)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{name} must be a number")
    return float(value)


def _string(data: dict[str, object], name: str) -> str:
    value = data.get(name)
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    return value
