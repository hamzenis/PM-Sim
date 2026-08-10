from dataclasses import dataclass, replace

from app.simulation.models import SimulationState, TaskPool
from app.simulation.randomness import RandomSource
from app.simulation.testing import sample_existing


@dataclass(frozen=True, slots=True)
class IntegrationTestResult:
    state: SimulationState
    tested: TaskPool
    passed: TaskPool
    returned_to_backlog: TaskPool


def apply_integration_testing(
    state: SimulationState,
    *,
    tested: TaskPool,
    random: RandomSource,
) -> IntegrationTestResult:
    """Integrate clean unit-tested work and return specification failures to the backlog."""
    eligible = state.tasks_unit_tested.minus(state.tasks_integration_tested).minus(state.known_bugs)
    if not eligible.contains(tested):
        raise ValueError("cannot integration test more clean eligible tasks than remain")

    failed = TaskPool(
        easy=sample_existing(
            successes=state.incorrect_specifications.easy,
            population=state.tasks_completed.easy,
            draws=tested.easy,
            random=random,
        ),
        medium=sample_existing(
            successes=state.incorrect_specifications.medium,
            population=state.tasks_completed.medium,
            draws=tested.medium,
            random=random,
        ),
        hard=sample_existing(
            successes=state.incorrect_specifications.hard,
            population=state.tasks_completed.hard,
            draws=tested.hard,
            random=random,
        ),
    )
    passed = tested.minus(failed)
    updated = replace(
        state,
        tasks_todo=state.tasks_todo.plus(failed),
        tasks_completed=state.tasks_completed.minus(failed),
        tasks_unit_tested=state.tasks_unit_tested.minus(failed),
        tasks_integration_tested=state.tasks_integration_tested.plus(passed),
        incorrect_specifications=state.incorrect_specifications.minus(failed),
    )
    return IntegrationTestResult(
        state=updated,
        tested=tested,
        passed=passed,
        returned_to_backlog=failed,
    )
