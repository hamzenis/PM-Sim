import csv
import io
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from statistics import mean

from app.batch.strategies import DecisionStrategy
from app.scenarios.models import ScenarioDefinition
from app.scenarios.to_simulation import (
    employee_types_from_scenario,
    initial_state_from_scenario,
    score_rules_from_scenario,
    turn_rules_from_scenario,
)
from app.simulation.models import SimulationState
from app.simulation.randomness import SeededRandomSource
from app.simulation.results import (
    SimulationOutcome,
    SimulationResult,
    build_simulation_result,
    evaluate_outcome,
)
from app.simulation.turn import process_week


@dataclass(frozen=True, slots=True)
class BatchRun:
    run_number: int
    seed: int
    result: object


@dataclass(frozen=True, slots=True)
class SimulationBatchRun:
    run_number: int
    seed: int
    strategy: str
    result: SimulationResult
    final_state: SimulationState


@dataclass(frozen=True, slots=True)
class BatchSummary:
    runs: int
    completion_rate: float
    budget_exhaustion_rate: float
    average_score: float
    average_accepted_tasks: float
    average_elapsed_working_days: float
    average_total_cost: float
    average_known_bugs: float
    average_undiscovered_bugs: float


@dataclass(frozen=True, slots=True)
class SimulationBatchReport:
    strategy: str
    runs: tuple[SimulationBatchRun, ...]
    summary: BatchSummary


def run_batch[Result](
    run_once: Callable[[int], Result],
    *,
    repetitions: int,
    initial_seed: int = 0,
) -> list[BatchRun]:
    """Run one callable repeatedly with reproducible consecutive seeds."""
    if repetitions < 1:
        raise ValueError("repetitions must be at least one")
    return [
        BatchRun(number, initial_seed + number, run_once(initial_seed + number))
        for number in range(repetitions)
    ]


def run_simulation(
    scenario: ScenarioDefinition,
    *,
    strategy: DecisionStrategy,
    seed: int,
    run_number: int = 0,
) -> SimulationBatchRun:
    """Run a scenario entirely in memory until completion or its deadline."""
    state = initial_state_from_scenario(scenario)
    employee_types = employee_types_from_scenario(scenario)
    rules = turn_rules_from_scenario(scenario)
    next_employee_number = 0

    def employee_id() -> str:
        nonlocal next_employee_number
        identifier = f"batch-{run_number}-employee-{next_employee_number}"
        next_employee_number += 1
        return identifier

    while evaluate_outcome(state) is SimulationOutcome.ACTIVE:
        turn = process_week(
            state,
            decision=strategy.decide(state),
            employee_types=employee_types,
            rules=rules,
            random=SeededRandomSource(seed + state.week),
            new_employee_id=employee_id,
        )
        state = turn.state
    result = build_simulation_result(state, rules=score_rules_from_scenario(scenario))
    return SimulationBatchRun(
        run_number=run_number,
        seed=seed,
        strategy=strategy.name,
        result=result,
        final_state=state,
    )


def run_simulation_batch(
    scenario: ScenarioDefinition,
    *,
    strategy: DecisionStrategy,
    repetitions: int,
    initial_seed: int = 0,
) -> SimulationBatchReport:
    if repetitions < 1:
        raise ValueError("repetitions must be at least one")
    runs = tuple(
        run_simulation(
            scenario,
            strategy=strategy,
            seed=initial_seed + number,
            run_number=number,
        )
        for number in range(repetitions)
    )
    return SimulationBatchReport(
        strategy=strategy.name,
        runs=runs,
        summary=_summarize(runs),
    )


def report_to_dict(report: SimulationBatchReport) -> dict[str, object]:
    return {
        "strategy": report.strategy,
        "summary": asdict(report.summary),
        "runs": [_run_to_dict(run) for run in report.runs],
    }


def report_to_csv(report: SimulationBatchReport) -> str:
    output = io.StringIO()
    rows = [_run_to_dict(run) for run in report.runs]
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _summarize(runs: Iterable[SimulationBatchRun]) -> BatchSummary:
    values = tuple(runs)
    count = len(values)
    return BatchSummary(
        runs=count,
        completion_rate=sum(run.result.outcome == SimulationOutcome.COMPLETED for run in values)
        / count,
        budget_exhaustion_rate=sum(run.final_state.remaining_budget < 0 for run in values) / count,
        average_score=mean(run.result.score.total for run in values),
        average_accepted_tasks=mean(run.result.accepted_tasks for run in values),
        average_elapsed_working_days=mean(run.result.elapsed_working_days for run in values),
        average_total_cost=mean(run.result.total_cost for run in values),
        average_known_bugs=mean(run.final_state.known_bugs.total for run in values),
        average_undiscovered_bugs=mean(run.final_state.undiscovered_bugs.total for run in values),
    )


def _run_to_dict(run: SimulationBatchRun) -> dict[str, object]:
    return {
        "run_number": run.run_number,
        "seed": run.seed,
        "strategy": run.strategy,
        "outcome": run.result.outcome,
        "accepted_tasks": run.result.accepted_tasks,
        "rejected_tasks": run.result.rejected_tasks,
        "elapsed_working_days": run.result.elapsed_working_days,
        "scheduled_working_days": run.result.scheduled_working_days,
        "total_cost": run.result.total_cost,
        "remaining_budget": run.result.remaining_budget,
        "score": run.result.score.total,
        "known_bugs": run.final_state.known_bugs.total,
        "undiscovered_bugs": run.final_state.undiscovered_bugs.total,
    }
