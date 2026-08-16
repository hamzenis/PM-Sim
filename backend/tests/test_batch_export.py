import csv
import io
import json
import os

import pytest

from app.batch import BatchExportError, export_reports, reports_to_csv, reports_to_json
from app.batch.runner import run_simulation_batch
from app.batch.strategies import TeamMemberCount, built_in_strategy
from app.scenarios.models import ScenarioDefinition
from app.simulation.results import SimulationOutcome


def _scenario() -> ScenarioDefinition:
    return ScenarioDefinition.model_validate(
        {
            "schema_version": 1,
            "name": "Export ünicode",
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


def _report(strategy: str):
    return run_simulation_batch(
        _scenario(),
        strategy=built_in_strategy(strategy, team_composition=(TeamMemberCount("developer", 3),)),
        repetitions=2,
    )


def test_export_writes_one_format_to_stdout_and_rejects_two() -> None:
    report = _report("balanced")
    output = io.StringIO()
    export_reports(report, json_destination="-", stdout=output)
    assert json.loads(output.getvalue())[0]["strategy"] == "balanced"

    with pytest.raises(BatchExportError, match="both.*stdout"):
        export_reports(report, json_destination="-", csv_destination="-", stdout=output)


def test_csv_combines_multiple_strategies_with_stable_columns() -> None:
    rows = list(
        csv.DictReader(io.StringIO(reports_to_csv((_report("balanced"), _report("quality-first")))))
    )
    assert tuple(rows[0]) == (
        "run_number",
        "seed",
        "strategy",
        "outcome",
        "accepted_tasks",
        "rejected_tasks",
        "elapsed_working_days",
        "scheduled_working_days",
        "total_cost",
        "remaining_budget",
        "score",
        "known_bugs",
        "undiscovered_bugs",
    )
    assert [row["strategy"] for row in rows] == [
        "balanced",
        "balanced",
        "quality-first",
        "quality-first",
    ]


def test_export_refuses_overwrite_and_only_creates_requested_parents(tmp_path) -> None:
    report = _report("balanced")
    destination = tmp_path / "missing" / "report.json"
    with pytest.raises(BatchExportError, match="does not exist"):
        export_reports(report, json_destination=destination)
    assert not destination.parent.exists()

    export_reports(report, json_destination=destination, create_parents=True)
    with pytest.raises(BatchExportError, match="refusing to overwrite"):
        export_reports(report, json_destination=destination)
    export_reports(report, json_destination=destination, force=True)


def test_failed_atomic_replacement_preserves_existing_file(tmp_path, monkeypatch) -> None:
    destination = tmp_path / "report.json"
    destination.write_text("original", encoding="utf-8")

    def fail_replace(source, target):
        raise OSError("injected replacement failure")

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(BatchExportError, match="injected replacement failure"):
        export_reports(_report("balanced"), json_destination=destination, force=True)

    assert destination.read_text(encoding="utf-8") == "original"
    assert list(tmp_path.iterdir()) == [destination]


def test_json_round_trip_uses_enum_values_and_utf8(tmp_path) -> None:
    report = _report("quality-first")
    expected = json.loads(reports_to_json(report))
    destination = tmp_path / "report.json"
    export_reports(report, json_destination=destination)

    assert json.loads(destination.read_text(encoding="utf-8")) == expected
    assert expected[0]["runs"][0]["outcome"] == report.runs[0].result.outcome.value
    assert isinstance(report.runs[0].result.outcome, SimulationOutcome)
