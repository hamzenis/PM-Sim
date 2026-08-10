from dataclasses import replace

import pytest

from app.simulation.engine import create_initial_state
from app.simulation.models import TaskPool
from app.simulation.randomness import RecordedRandomSource
from app.simulation.testing import apply_bug_fixes, apply_unit_testing


def developed_state():
    initial = create_initial_state(
        total_tasks=40,
        difficulty_weights=(0.25, 0.5, 0.25),
        budget=10_000,
        working_days=20,
    )
    return replace(
        initial,
        tasks_todo=TaskPool(easy=6, medium=16, hard=8),
        tasks_completed=TaskPool(easy=4, medium=4, hard=2),
        undiscovered_bugs=TaskPool(easy=2, medium=1, hard=0),
    )


def test_unit_testing_discovers_bugs_without_replacement() -> None:
    state = developed_state()
    result = apply_unit_testing(
        state,
        tested=TaskPool(easy=2, medium=2, hard=1),
        random=RecordedRandomSource(probabilities=[0.1, 0.9, 0.1, 0.9]),
    )
    assert result.tested == TaskPool(easy=2, medium=2, hard=1)
    assert result.bugs_discovered == TaskPool(easy=1, medium=1, hard=0)
    assert result.state.tasks_unit_tested == result.tested
    assert result.state.known_bugs == result.bugs_discovered
    assert result.state.undiscovered_bugs == TaskPool(easy=1, medium=0, hard=0)


def test_already_tested_tasks_cannot_be_tested_twice() -> None:
    state = replace(developed_state(), tasks_unit_tested=TaskPool(easy=4, medium=0, hard=0))
    with pytest.raises(ValueError, match="more eligible tasks"):
        apply_unit_testing(
            state,
            tested=TaskPool(easy=1, medium=0, hard=0),
            random=RecordedRandomSource(),
        )


def test_only_known_bugs_can_be_fixed() -> None:
    state = replace(
        developed_state(),
        known_bugs=TaskPool(easy=1, medium=1, hard=0),
        undiscovered_bugs=TaskPool(easy=1, medium=0, hard=0),
    )
    result = apply_bug_fixes(state, fixed=TaskPool(easy=1, medium=0, hard=0))
    assert result.state.known_bugs == TaskPool(easy=0, medium=1, hard=0)
    assert result.state.undiscovered_bugs == TaskPool(easy=1, medium=0, hard=0)

    with pytest.raises(ValueError, match="more known bugs"):
        apply_bug_fixes(result.state, fixed=TaskPool(easy=1, medium=0, hard=0))
