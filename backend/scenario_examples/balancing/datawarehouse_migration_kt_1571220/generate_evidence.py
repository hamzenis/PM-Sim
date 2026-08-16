"""Regenerate professor-review balancing evidence for scenario KT-1571220."""

import csv
import io
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean

from app.batch import (
    BatchProvenance,
    execute_batch_strategies,
    export_text,
    load_scenario,
    summarize_distribution,
)
from app.simulation.models import (
    ActivityAllocation,
    HireRequest,
    SimulationState,
    WeeklyDecision,
)

BACKEND = Path(__file__).resolve().parents[3]
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


def generate_evidence() -> tuple[dict[str, object], list[dict[str, object]]]:
    loaded = load_scenario(SCENARIO_PATH)
    intended = loaded.definition
    provenance = BatchProvenance(
        scenario_path=loaded.source_path,
        scenario_name=intended.name,
        strategy_names=tuple(strategy.name for strategy in STRATEGIES),
        seeds=tuple(range(INITIAL_SEED, INITIAL_SEED + REPETITIONS)),
        team_size=4,
        employee_type_code="mixed",
        output_formats=("json", "csv"),
    )
    reports: dict[str, object] = {
        "scenario": str(provenance.scenario_path.relative_to(BACKEND)),
        "scenario_sha256": loaded.sha256_digest,
        "engine_entry_point": "app.batch.service.execute_batch_strategies",
        "initial_seed": provenance.seeds[0],
        "repetitions_per_strategy": REPETITIONS,
        "seed_range": [provenance.seeds[0], provenance.seeds[-1]],
        "strategies": [asdict(strategy) for strategy in STRATEGIES],
        "modes": {},
    }
    csv_rows: list[dict[str, object]] = []

    for randomness in ("none", "semi"):
        definition = intended.model_copy(
            update={"rules": intended.rules.model_copy(update={"randomness": randomness})}
        )
        mode_summaries: dict[str, object] = {}
        mode_reports = execute_batch_strategies(
            definition,
            strategies=STRATEGIES,
            repetitions=REPETITIONS,
            initial_seed=INITIAL_SEED,
        )
        for strategy, report in zip(STRATEGIES, mode_reports, strict=True):
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
                "score_distribution": asdict(summarize_distribution(scores)),
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
    return reports, csv_rows


def main() -> None:
    reports, csv_rows = generate_evidence()
    csv_output = io.StringIO(newline="")
    writer = csv.DictWriter(csv_output, fieldnames=list(csv_rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(csv_rows)

    export_text(json.dumps(reports, indent=2) + "\n", OUTPUT_DIR / "batch-summary.json", force=True)
    export_text(csv_output.getvalue(), OUTPUT_DIR / "batch-runs.csv", force=True)


if __name__ == "__main__":
    main()
