from dataclasses import replace

import pytest

from app.simulation.engine import create_initial_state
from app.simulation.models import Employee
from app.simulation.state_codec import state_from_dict, state_to_dict


def state_with_employee():
    initial = create_initial_state(
        total_tasks=40,
        difficulty_weights=(0.25, 0.5, 0.25),
        budget=10_000,
        working_days=20,
    )
    return replace(
        initial,
        employees=(Employee(id="employee-1", employee_type_code="junior"),),
    )


def test_state_round_trip_preserves_domain_objects() -> None:
    state = state_with_employee()
    assert state_from_dict(state_to_dict(state)) == state


def test_state_restoration_rejects_invalid_nested_values() -> None:
    data = state_to_dict(state_with_employee())
    data["tasks_todo"]["easy"] = -1  # type: ignore[index]
    with pytest.raises(ValueError, match="task counts cannot be negative"):
        state_from_dict(data)


def test_state_restoration_rejects_ambiguous_number_types() -> None:
    data = state_to_dict(state_with_employee())
    data["week"] = True
    with pytest.raises(ValueError, match="week must be an integer"):
        state_from_dict(data)
