"""Regenerate professor-review balancing evidence for scenario KT-1571220."""

import csv
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean

BACKEND = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BACKEND))

from app.batch.runner import run_simulation_batch  # noqa: E402
from app.scenarios.models import ScenarioDefinition  # noqa: E402
from app.simulation.models import (  # noqa: E402
    ActivityAllocation,
    HireRequest,
    SimulationState,
    WeeklyDecision,
)

SCENARIO_PATH = BACKEND / "scenario_examples/datawarehouse_migration_kt_1571220.json"
OUTPUT_DIR = Path(__file__).resolve().parent
INITIAL_SEED = 1_571_220
REPETITIONS = 200


@dataclass(frozen=True, slots=True)
class MixedTeamStrategy:
    name: str
    roster: dict[str, int]
    allocation: tuple[int, int, int, int]
    recovery_overtime: float = 0

    def decide(self, state: SimulationState) -> WeeklyDecision:
        hires = (
            tuple(HireRequest(code, count) for code, count in self.roster.items())
            if state.week == 0
            else ()
        )
        return WeeklyDecision(
            allocation=ActivityAllocation(*self.allocation),
            hires=hires,
            overtime_hours_per_employee=(self.recovery_overtime if state.week >= 4 else 0),
        )


STRATEGIES = (
    MixedTeamStrategy(
        "low-cost-staffing",
        {"junior_data_engineer": 3, "data_engineer": 1},
        (40, 25, 15, 20),
    ),
    MixedTeamStrategy(
        "senior-heavy-delivery",
        {"senior_data_engineer": 3, "data_architect": 1},
        (40, 25, 15, 20),
    ),
    MixedTeamStrategy(
        "specialist-balanced-staffing",
        {
            "data_engineer": 1,
            "senior_data_engineer": 1,
            "etl_migration_specialist": 1,
            "data_quality_test_engineer": 1,
        },
        (30, 30, 15, 25),
    ),
    MixedTeamStrategy(
        "development-first-allocation",
        {
            "data_engineer": 1,
            "senior_data_engineer": 1,
            "data_quality_test_engineer": 1,
            "migration_coordinator": 1,
        },
        (55, 20, 10, 15),
    ),
    MixedTeamStrategy(
        "quality-first-allocation",
        {
            "data_engineer": 1,
            "senior_data_engineer": 1,
            "data_quality_test_engineer": 1,
            "migration_coordinator": 1,
        },
        (25, 30, 20, 25),
    ),
    MixedTeamStrategy(
        "overtime-recovery-after-budget-shock",
        {
            "data_engineer": 1,
            "senior_data_engineer": 1,
            "data_quality_test_engineer": 1,
            "migration_coordinator": 1,
        },
        (35, 27, 13, 25),
        recovery_overtime=2,
    ),
)


def percentile(values: list[float], fraction: float) -> float:
    return sorted(values)[round((len(values) - 1) * fraction)]


def main() -> None:
    scenario_bytes = SCENARIO_PATH.read_bytes()
    # This exact API is the required pre-publication schema validation gate.
    intended = ScenarioDefinition.model_validate_json(scenario_bytes)
    reports: dict[str, object] = {
        "scenario": str(SCENARIO_PATH.relative_to(BACKEND)),
        "scenario_sha256": hashlib.sha256(scenario_bytes).hexdigest(),
        "engine_entry_point": "app.batch.runner.run_simulation_batch",
        "initial_seed": INITIAL_SEED,
        "repetitions_per_strategy": REPETITIONS,
        "seed_range": [INITIAL_SEED, INITIAL_SEED + REPETITIONS - 1],
        "strategies": [asdict(strategy) for strategy in STRATEGIES],
        "modes": {},
    }
    csv_rows: list[dict[str, object]] = []

    for randomness in ("none", "semi"):
        definition = intended.model_copy(
            update={"rules": intended.rules.model_copy(update={"randomness": randomness})}
        )
        mode_summaries: dict[str, object] = {}
        for strategy in STRATEGIES:
            report = run_simulation_batch(
                definition,
                strategy=strategy,
                repetitions=REPETITIONS,
                initial_seed=INITIAL_SEED,
            )
            runs = report.runs
            scores = [run.result.score.total for run in runs]
            accepted = [run.result.accepted_tasks for run in runs]
            rejected = [run.result.rejected_tasks for run in runs]
            costs = [run.result.total_cost for run in runs]
            days = [run.result.elapsed_working_days for run in runs]
            mode_summaries[strategy.name] = {
                "completion_rate": report.summary.completion_rate,
                "budget_exhaustion_rate_nominal_240000": report.summary.budget_exhaustion_rate,
                "effective_210000_ceiling_exceedance_rate": mean(cost > 210_000 for cost in costs),
                "accepted_tasks": {
                    "mean": mean(accepted),
                    "min": min(accepted),
                    "max": max(accepted),
                },
                "rejected_tasks": {
                    "mean": mean(rejected),
                    "min": min(rejected),
                    "max": max(rejected),
                },
                "total_cost": {"mean": mean(costs), "min": min(costs), "max": max(costs)},
                "elapsed_working_days": {"mean": mean(days), "min": min(days), "max": max(days)},
                "score_distribution": {
                    "mean": mean(scores),
                    "min": min(scores),
                    "p10": percentile(scores, 0.10),
                    "median": percentile(scores, 0.50),
                    "p90": percentile(scores, 0.90),
                    "max": max(scores),
                },
                "score_component_ranges": {
                    "quality": [
                        min(run.result.score.quality for run in runs),
                        max(run.result.score.quality for run in runs),
                    ],
                    "time": [
                        min(run.result.score.time for run in runs),
                        max(run.result.score.time for run in runs),
                    ],
                    "budget": [
                        min(run.result.score.budget for run in runs),
                        max(run.result.score.budget for run in runs),
                    ],
                },
            }
            for run in runs:
                csv_rows.append(
                    {
                        "randomness": randomness,
                        "strategy": strategy.name,
                        "run_number": run.run_number,
                        "seed": run.seed,
                        "outcome": run.result.outcome.value,
                        "accepted_tasks": run.result.accepted_tasks,
                        "rejected_tasks": run.result.rejected_tasks,
                        "elapsed_working_days": run.result.elapsed_working_days,
                        "total_cost": run.result.total_cost,
                        "nominal_budget_exhausted": run.final_state.remaining_budget < 0,
                        "effective_210000_ceiling_exceeded": run.result.total_cost > 210_000,
                        "quality_score": run.result.score.quality,
                        "time_score": run.result.score.time,
                        "budget_score": run.result.score.budget,
                        "total_score": run.result.score.total,
                    }
                )
        reports["modes"][randomness] = mode_summaries

    (OUTPUT_DIR / "batch-summary.json").write_text(json.dumps(reports, indent=2) + "\n")
    with (OUTPUT_DIR / "batch-runs.csv").open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)


if __name__ == "__main__":
    main()
