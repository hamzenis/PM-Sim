import csv
import io

import pytest

from app.batch.runner import report_to_csv, report_to_dict, run_batch, run_simulation_batch
from app.batch.strategies import built_in_strategy
from app.scenarios.models import ScenarioDefinition


def test_batch_uses_reproducible_consecutive_seeds() -> None:
    runs = run_batch(lambda seed: seed * 2, repetitions=3, initial_seed=10)
    assert [(run.seed, run.result) for run in runs] == [(10, 20), (11, 22), (12, 24)]


def scenario() -> ScenarioDefinition:
    return ScenarioDefinition.model_validate(
        {
            "schema_version": 1,
            "name": "Batch",
            "project": {"budget": 20_000, "working_days": 20},
            "tasks": {"total": 40},
            "employee_types": [
                {
                    "code": "developer",
                    "name": "Developer",
                    "cost_per_day": 100,
                    "throughput": {"easy": 4, "medium": 2, "hard": 1},
                    "error_rate": 0.1,
                    "management_skill": 0.5,
                }
            ],
            "rules": {"randomness": "semi"},
        }
    )


def test_full_batch_is_deterministic_and_reports_aggregate_metrics() -> None:
    strategy = built_in_strategy("balanced", employee_type_code="developer")
    first = run_simulation_batch(scenario(), strategy=strategy, repetitions=4, initial_seed=20)
    second = run_simulation_batch(scenario(), strategy=strategy, repetitions=4, initial_seed=20)
    assert report_to_dict(first) == report_to_dict(second)
    assert [run.seed for run in first.runs] == [20, 21, 22, 23]
    assert first.summary.runs == 4
    assert 0 <= first.summary.completion_rate <= 1
    assert first.summary.average_elapsed_working_days > 0


def test_batch_report_can_be_exported_as_csv() -> None:
    strategy = built_in_strategy("quality-first", employee_type_code="developer")
    report = run_simulation_batch(scenario(), strategy=strategy, repetitions=2)
    rows = list(csv.DictReader(io.StringIO(report_to_csv(report))))
    assert len(rows) == 2
    assert rows[0]["strategy"] == "quality-first"
    assert {row["seed"] for row in rows} == {"0", "1"}


def test_unknown_strategy_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown strategy"):
        built_in_strategy("reckless", employee_type_code="developer")
