from app.simulation.models import SimulationState, TaskPool
from app.simulation.tasks import distribute_tasks


def create_initial_state(
    *,
    total_tasks: int,
    difficulty_weights: tuple[float, float, float],
    budget: float,
    working_days: int,
) -> SimulationState:
    """Create the framework-independent state used at the start of every run."""
    tasks = distribute_tasks(
        total_tasks,
        easy=difficulty_weights[0],
        medium=difficulty_weights[1],
        hard=difficulty_weights[2],
    )
    empty = TaskPool(easy=0, medium=0, hard=0)
    return SimulationState(
        week=0,
        elapsed_working_days=0,
        remaining_working_days=working_days,
        initial_budget=budget,
        remaining_budget=budget,
        tasks_todo=tasks,
        tasks_completed=empty,
        tasks_unit_tested=empty,
        tasks_integration_tested=empty,
        known_bugs=empty,
        undiscovered_bugs=empty,
        incorrect_specifications=empty,
    )
