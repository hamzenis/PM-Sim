import csv
import io
from dataclasses import asdict

import pytest

from app.batch.runner import (
    report_to_csv,
    report_to_dict,
    run_batch,
    run_simulation_batch,
    summarize_distribution,
)
from app.batch.strategies import TeamMemberCount, built_in_strategy
from app.scenarios.models import ScenarioDefinition
from app.scenarios.to_simulation import initial_state_from_scenario


def test_batch_uses_reproducible_consecutive_seeds() -> None:
    runs = run_batch(lambda seed: seed * 2, repetitions=3, initial_seed=10)
    assert [(run.seed, run.result) for run in runs] == [(10, 20), (11, 22), (12, 24)]


def test_optional_distribution_summary_uses_deterministic_nearest_ranks() -> None:
    assert asdict(summarize_distribution([9, 1, 5, 3, 7])) == {
        "mean": 5,
        "min": 1,
        "p10": 1,
        "median": 5,
        "p90": 9,
        "max": 9,
    }


def scenario() -> ScenarioDefinition:
    return ScenarioDefinition.model_validate(
        {
            "schema_version": 1,
            "name": "Batch",
            "authored_content": {"fragments": [], "questions": [], "events": [], "sequence": []},
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
    strategy = built_in_strategy("balanced", team_composition=(TeamMemberCount("developer", 3),))
    first = run_simulation_batch(scenario(), strategy=strategy, repetitions=4, initial_seed=20)
    second = run_simulation_batch(scenario(), strategy=strategy, repetitions=4, initial_seed=20)
    assert report_to_dict(first) == report_to_dict(second)
    assert [run.seed for run in first.runs] == [20, 21, 22, 23]
    assert first.summary.runs == 4
    assert 0 <= first.summary.completion_rate <= 1
    assert first.summary.average_elapsed_working_days > 0


def test_batch_report_can_be_exported_as_csv() -> None:
    strategy = built_in_strategy(
        "quality-first", team_composition=(TeamMemberCount("developer", 3),)
    )
    report = run_simulation_batch(scenario(), strategy=strategy, repetitions=2)
    rows = list(csv.DictReader(io.StringIO(report_to_csv(report))))
    assert len(rows) == 2
    assert rows[0]["strategy"] == "quality-first"
    assert {row["seed"] for row in rows} == {"0", "1"}


def test_unknown_strategy_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown strategy"):
        built_in_strategy("reckless", team_composition=(TeamMemberCount("developer", 3),))


def test_fixed_strategy_hires_mixed_team_in_configured_order() -> None:
    strategy = built_in_strategy(
        "balanced",
        team_composition=(TeamMemberCount("developer", 2), TeamMemberCount("tester", 1)),
    )
    decision = strategy.decide(initial_state_from_scenario(scenario()))
    assert [(hire.employee_type_code, hire.count) for hire in decision.hires] == [
        ("developer", 2),
        ("tester", 1),
    ]
