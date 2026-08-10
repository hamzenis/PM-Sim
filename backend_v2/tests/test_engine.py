from app.simulation.engine import create_initial_state
from app.simulation.models import Difficulty, EmployeeType, TaskPool, Throughput


def test_initial_state_contains_complete_task_pool_and_budget() -> None:
    state = create_initial_state(
        total_tasks=400,
        difficulty_weights=(0.25, 0.50, 0.25),
        budget=250_000,
        working_days=60,
    )
    assert state.week == 0
    assert state.remaining_budget == 250_000
    assert state.remaining_working_days == 60
    assert state.tasks_todo == TaskPool(easy=100, medium=200, hard=100)
    assert state.tasks_completed.total == 0
    assert state.total_tasks == 400


def test_employee_type_has_throughput_for_each_difficulty() -> None:
    employee_type = EmployeeType(
        code="junior",
        name="Junior Developer",
        cost_per_day=100,
        throughput=Throughput(easy=4, medium=2, hard=0.5),
        error_rate=0.1,
    )
    assert employee_type.throughput.for_difficulty(Difficulty.EASY) == 4
    assert employee_type.throughput.for_difficulty(Difficulty.MEDIUM) == 2
    assert employee_type.throughput.for_difficulty(Difficulty.HARD) == 0.5
