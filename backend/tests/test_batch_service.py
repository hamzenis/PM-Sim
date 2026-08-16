import json
from dataclasses import replace
from hashlib import sha256

import pytest

from app.batch import (
    BatchConfigurationError,
    BatchExecutionConfig,
    BatchOutputError,
    ScenarioLoadError,
    execute_batch,
    execution_result_to_dict,
    load_scenario,
)


def scenario_payload(*, employee_codes: tuple[str, ...] = ("developer",)) -> dict[str, object]:
    return {
        "schema_version": 1,
        "name": "Service batch",
        "authored_content": {"fragments": [], "questions": [], "events": [], "sequence": []},
        "project": {"budget": 20_000, "working_days": 20},
        "tasks": {"total": 40},
        "employee_types": [
            {
                "code": code,
                "name": code.title(),
                "cost_per_day": 100,
                "throughput": {"easy": 4, "medium": 2, "hard": 1},
                "error_rate": 0.1,
                "management_skill": 0.5,
            }
            for code in employee_codes
        ],
        "rules": {"randomness": "semi"},
    }


def write_scenario(tmp_path, *, employee_codes=("developer",)):
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(scenario_payload(employee_codes=employee_codes)))
    return path


def test_load_scenario_validates_json_and_only_infers_unambiguous_employee_type(tmp_path) -> None:
    single = load_scenario(write_scenario(tmp_path))
    assert single.definition.name == "Service batch"
    assert single.employee_type_code == "developer"
    assert single.sha256_digest == sha256(single.source_path.read_bytes()).hexdigest()

    multiple_path = tmp_path / "multiple.json"
    multiple_path.write_text(json.dumps(scenario_payload(employee_codes=("developer", "tester"))))
    assert load_scenario(multiple_path).employee_type_code is None


def test_malformed_scenario_diagnostic_names_source(tmp_path) -> None:
    path = tmp_path / "broken-scenario.json"
    path.write_text('{"name":')
    with pytest.raises(ScenarioLoadError, match="broken-scenario.json"):
        load_scenario(path)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"repetitions": 0}, "repetitions"),
        ({"team_size": 0}, "team size"),
        ({"initial_seed": -1}, "initial seed"),
        ({"initial_seed": 2**32 - 1, "repetitions": 2}, "seed range"),
        ({"strategy_names": ("balanced", "balanced")}, "unique"),
    ],
)
def test_config_rejects_invalid_execution_values(tmp_path, changes, message) -> None:
    values = {"scenario_path": write_scenario(tmp_path), **changes}
    with pytest.raises(BatchConfigurationError, match=message):
        BatchExecutionConfig(**values)


def test_execute_batch_compares_strategies_over_identical_seed_range(tmp_path) -> None:
    config = BatchExecutionConfig(
        scenario_path=write_scenario(tmp_path),
        strategy_names=("balanced", "quality-first"),
        repetitions=3,
        initial_seed=12,
        team_size=2,
    )
    first = execute_batch(config)
    second = execute_batch(replace(config))

    assert [[run.seed for run in report.runs] for report in first.reports] == [
        [12, 13, 14],
        [12, 13, 14],
    ]
    assert first.reports == second.reports
    assert first.provenance.employee_type_code == "developer"


def test_report_metadata_tracks_exact_input_and_keeps_simulation_payload_deterministic(
    tmp_path,
) -> None:
    path = write_scenario(tmp_path)
    config = BatchExecutionConfig(scenario_path=path, repetitions=2, initial_seed=7, team_size=2)
    first = execute_batch(config)
    second = execute_batch(config)

    assert first.reports == second.reports
    metadata = execution_result_to_dict(first)["metadata"]
    assert metadata["scenario_name"] == "Service batch"
    assert metadata["scenario_sha256"] == sha256(path.read_bytes()).hexdigest()
    assert (metadata["initial_seed"], metadata["final_seed"], metadata["repetitions"]) == (7, 8, 2)
    assert metadata["schema_version"] == 1
    assert metadata["pm_sim_package"] == "pm-sim-backend"
    assert metadata["pm_sim_version"]
    assert metadata["generated_at"].endswith("+00:00")
    assert metadata["strategies"] == [
        {
            "name": "balanced",
            "employee_type": "developer",
            "team_size": 2,
            "allocation": {
                "development": 40,
                "unit_testing": 25,
                "bug_fixing": 15,
                "integration_testing": 20,
            },
            "overtime_hours_per_employee": 0,
        }
    ]

    path.write_text(json.dumps(scenario_payload()) + "\n")
    changed = execute_batch(config)
    assert changed.reports == first.reports
    assert changed.metadata.scenario_sha256 != first.metadata.scenario_sha256


def test_execute_batch_requires_known_explicit_type_when_scenario_is_ambiguous(tmp_path) -> None:
    path = write_scenario(tmp_path, employee_codes=("developer", "tester"))
    with pytest.raises(BatchConfigurationError, match="employee type is required"):
        execute_batch(BatchExecutionConfig(scenario_path=path))
    with pytest.raises(BatchConfigurationError, match="unknown employee type"):
        execute_batch(BatchExecutionConfig(scenario_path=path, employee_type="manager"))


def test_output_destination_is_validated_and_requested_reports_are_written(tmp_path) -> None:
    scenario = write_scenario(tmp_path)
    not_a_directory = tmp_path / "report.json"
    not_a_directory.write_text("occupied")
    with pytest.raises(BatchOutputError, match="not a directory"):
        BatchExecutionConfig(scenario_path=scenario, output_directory=not_a_directory)

    output = tmp_path / "reports"
    execute_batch(
        BatchExecutionConfig(
            scenario_path=scenario,
            repetitions=1,
            output_formats=("json", "csv"),
            output_directory=output,
        )
    )
    assert (output / "batch-report.json").is_file()
    assert (output / "batch-report-balanced.csv").is_file()
    assert (output / "batch-report-metadata.json").is_file()
    metadata = json.loads((output / "batch-report-metadata.json").read_text())
    assert metadata == json.loads((output / "batch-report.json").read_text())["metadata"]
