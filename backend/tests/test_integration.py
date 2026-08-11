from dataclasses import replace

import pytest

from app.simulation.engine import create_initial_state
from app.simulation.integration import apply_integration_testing
from app.simulation.models import TaskPool
from app.simulation.randomness import RecordedRandomSource


def integration_ready_state():
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
        tasks_unit_tested=TaskPool(easy=4, medium=3, hard=2),
        known_bugs=TaskPool(easy=1, medium=0, hard=0),
        incorrect_specifications=TaskPool(easy=2, medium=1, hard=0),
    )


def test_integration_returns_incorrect_work_to_backlog() -> None:
    state = integration_ready_state()
    result = apply_integration_testing(
        state,
        tested=TaskPool(easy=2, medium=2, hard=1),
        random=RecordedRandomSource(probabilities=[0.1, 0.9, 0.1, 0.9]),
    )
    assert result.returned_to_backlog == TaskPool(easy=1, medium=1, hard=0)
    assert result.passed == TaskPool(easy=1, medium=1, hard=1)
    assert result.state.tasks_todo == TaskPool(easy=7, medium=17, hard=8)
    assert result.state.tasks_completed == TaskPool(easy=3, medium=3, hard=2)
    assert result.state.tasks_unit_tested == TaskPool(easy=3, medium=2, hard=2)
    assert result.state.tasks_integration_tested == result.passed
    assert result.state.incorrect_specifications == TaskPool(easy=1, medium=0, hard=0)
    assert result.state.total_tasks == 40


def test_known_bug_tasks_are_not_eligible_for_integration() -> None:
    with pytest.raises(ValueError, match="clean eligible tasks"):
        apply_integration_testing(
            integration_ready_state(),
            tested=TaskPool(easy=4, medium=0, hard=0),
            random=RecordedRandomSource(),
        )


def test_already_integrated_tasks_cannot_be_integrated_twice() -> None:
    state = replace(
        integration_ready_state(),
        tasks_integration_tested=TaskPool(easy=1, medium=0, hard=0),
    )
    with pytest.raises(ValueError, match="clean eligible tasks"):
        apply_integration_testing(
            state,
            tested=TaskPool(easy=3, medium=0, hard=0),
            random=RecordedRandomSource(),
        )
