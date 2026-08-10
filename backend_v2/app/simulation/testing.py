from dataclasses import dataclass, replace

from app.simulation.models import SimulationState, TaskPool
from app.simulation.randomness import RandomSource


@dataclass(frozen=True, slots=True)
class UnitTestResult:
    state: SimulationState
    tested: TaskPool
    bugs_discovered: TaskPool


@dataclass(frozen=True, slots=True)
class BugFixResult:
    state: SimulationState
    bugs_fixed: TaskPool


def apply_unit_testing(
    state: SimulationState,
    *,
    tested: TaskPool,
    random: RandomSource,
) -> UnitTestResult:
    """Test completed work and reveal all defects present in the sampled tasks."""
    eligible = state.tasks_completed.minus(state.tasks_unit_tested)
    if not eligible.contains(tested):
        raise ValueError("cannot unit test more eligible tasks than remain")

    discovered = TaskPool(
        easy=sample_existing(
            successes=state.undiscovered_bugs.easy,
            population=eligible.easy,
            draws=tested.easy,
            random=random,
        ),
        medium=sample_existing(
            successes=state.undiscovered_bugs.medium,
            population=eligible.medium,
            draws=tested.medium,
            random=random,
        ),
        hard=sample_existing(
            successes=state.undiscovered_bugs.hard,
            population=eligible.hard,
            draws=tested.hard,
            random=random,
        ),
    )
    updated = replace(
        state,
        tasks_unit_tested=state.tasks_unit_tested.plus(tested),
        undiscovered_bugs=state.undiscovered_bugs.minus(discovered),
        known_bugs=state.known_bugs.plus(discovered),
    )
    return UnitTestResult(state=updated, tested=tested, bugs_discovered=discovered)


def apply_bug_fixes(state: SimulationState, *, fixed: TaskPool) -> BugFixResult:
    """Fix known defects without allowing undiscovered defects to be selected."""
    if not state.known_bugs.contains(fixed):
        raise ValueError("cannot fix more known bugs than remain")
    updated = replace(state, known_bugs=state.known_bugs.minus(fixed))
    return BugFixResult(state=updated, bugs_fixed=fixed)


def sample_existing(
    *,
    successes: int,
    population: int,
    draws: int,
    random: RandomSource,
) -> int:
    """Sample anonymously without replacement, equivalent to a hypergeometric draw."""
    if successes > population or draws > population:
        raise ValueError("invalid anonymous task population")
    discovered = 0
    remaining_successes = successes
    remaining_population = population
    for draw_index in range(draws):
        if remaining_successes == 0:
            break
        if remaining_successes == remaining_population:
            discovered += min(remaining_successes, draws - draw_index)
            break
        if random.probability(remaining_successes / remaining_population):
            discovered += 1
            remaining_successes -= 1
        remaining_population -= 1
    return discovered
