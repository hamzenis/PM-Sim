from dataclasses import replace

from app.simulation.engine import create_initial_state
from app.simulation.models import TaskPool
from app.simulation.results import (
    ScoreRules,
    SimulationOutcome,
    build_simulation_result,
    calculate_score,
    evaluate_outcome,
)


def initial_state():
    return create_initial_state(
        total_tasks=40,
        difficulty_weights=(0.25, 0.5, 0.25),
        budget=10_000,
        working_days=20,
    )


def test_score_combines_quality_time_and_budget() -> None:
    score = calculate_score(
        accepted_tasks=32,
        total_tasks=40,
        actual_days=20,
        scheduled_days=20,
        cost=8_000,
        budget=10_000,
        rules=ScoreRules(),
    )
    assert score.quality == 80
    assert score.time == 100
    assert score.budget == 100
    assert score.total == 93


def test_budget_and_time_overruns_reduce_scores() -> None:
    score = calculate_score(
        accepted_tasks=40,
        total_tasks=40,
        actual_days=22,
        scheduled_days=20,
        cost=11_000,
        budget=10_000,
        rules=ScoreRules(),
    )
    assert score.quality == 100
    assert score.time == 90
    assert score.budget == 90
    assert score.total == 93


def test_outcome_distinguishes_completion_submission_and_deadline() -> None:
    state = initial_state()
    assert evaluate_outcome(state) is SimulationOutcome.ACTIVE
    assert evaluate_outcome(state, submitted=True) is SimulationOutcome.SUBMITTED
    deadline_outcome = evaluate_outcome(replace(state, remaining_working_days=0))
    assert deadline_outcome is SimulationOutcome.DEADLINE_REACHED

    completed = replace(
        state,
        tasks_todo=TaskPool(0, 0, 0),
        tasks_completed=TaskPool(10, 20, 10),
        tasks_unit_tested=TaskPool(10, 20, 10),
        tasks_integration_tested=TaskPool(10, 20, 10),
    )
    assert evaluate_outcome(completed) is SimulationOutcome.COMPLETED


def test_final_result_reports_accepted_rejected_cost_and_score() -> None:
    state = replace(
        initial_state(),
        elapsed_working_days=20,
        remaining_working_days=0,
        remaining_budget=2_000,
        tasks_todo=TaskPool(0, 0, 0),
        tasks_completed=TaskPool(10, 20, 10),
        tasks_unit_tested=TaskPool(8, 18, 9),
        tasks_integration_tested=TaskPool(8, 16, 8),
    )
    result = build_simulation_result(state, rules=ScoreRules())
    assert result.outcome is SimulationOutcome.DEADLINE_REACHED
    assert result.accepted_tasks == 32
    assert result.rejected_tasks == 8
    assert result.total_cost == 8_000
    assert result.score.total == 93
