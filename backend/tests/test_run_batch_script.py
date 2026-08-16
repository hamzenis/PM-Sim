import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def run_batch():
    script_path = Path(__file__).parents[2] / "scripts" / "run_batch.py"
    spec = importlib.util.spec_from_file_location("run_batch", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_repository_batch_wrapper_forwards_arguments(monkeypatch, run_batch) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(
        run_batch, "_delegate", lambda arguments: calls.append(list(arguments)) or 7
    )

    arguments = ["--scenario", "scenario.json", "--repetitions", "3", "--force"]
    assert run_batch.main(arguments) == 7
    assert calls == [arguments]


def _configuration(tmp_path: Path, scenarios: list[str] | None = None) -> Path:
    path = tmp_path / "experiment.json"
    path.write_text(
        json.dumps(
            {
                "scenarios": scenarios or ["one.json", "two.json"],
                "strategies": ["balanced", "quality-first"],
                "team_compositions": [
                    {
                        "name": "Two Developers",
                        "members": [{"employee_type_code": "developer", "count": 2}],
                    },
                    {
                        "name": "Mixed Team",
                        "members": [
                            {"employee_type_code": "developer", "count": 1},
                            {"employee_type_code": "tester", "count": 1},
                        ],
                    },
                ],
                "repetitions": 3,
                "initial_seed": 10,
                "output_root": "results",
            }
        ),
        encoding="utf-8",
    )
    for scenario in scenarios or ["one.json", "two.json"]:
        (tmp_path / scenario).write_text(f'{{"scenario": "{scenario}"}}', encoding="utf-8")
    return path


def _fake_backend(run_batch, monkeypatch, *, failing: str | None = None):
    calls = []

    class Config:
        def __init__(self, **values):
            self.__dict__.update(values)

    class Member:
        def __init__(self, employee_type_code, count):
            self.employee_type_code = employee_type_code
            self.count = count

    def execute(config):
        calls.append(config)
        if failing and config.scenario_path.name == failing:
            raise RuntimeError("broken scenario")
        return SimpleNamespace(
            reports=(config.scenario_path.name,), metadata=SimpleNamespace(pm_sim_version="0.1.0")
        )

    def export_reports(reports, *, json_destination, csv_destination, create_parents, force):
        json_destination.parent.mkdir(parents=True, exist_ok=True)
        json_destination.write_text(json.dumps(list(reports)), encoding="utf-8")
        csv_destination.write_text("scenario\n" + reports[0] + "\n", encoding="utf-8")

    def export_text(content, destination, *, create_parents, force):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

    def write_html_report(result, destination, *, create_parents, force):
        assert destination.parent.joinpath("results.json").is_file()
        assert destination.parent.joinpath("results.csv").is_file()
        destination.write_text("<html>report</html>", encoding="utf-8")

    monkeypatch.setattr(
        run_batch,
        "_backend_imports",
        lambda: (Config, Member, execute, export_reports, export_text, write_html_report),
    )
    return calls


def test_experiment_runs_scenario_composition_matrix_and_writes_manifest(
    tmp_path, monkeypatch, run_batch
) -> None:
    config = _configuration(tmp_path)
    calls = _fake_backend(run_batch, monkeypatch)

    assert run_batch.main(["--config", str(config)]) == 0

    assert len(calls) == 4
    manifest = json.loads((tmp_path / "results" / "manifest.json").read_text())
    assert manifest["package_version"] == "0.1.0"
    assert len(manifest["jobs"]) == 4
    assert {job["status"] for job in manifest["jobs"]} == {"success"}
    assert all(len(job["scenario_sha256"]) == 64 for job in manifest["jobs"])
    assert (tmp_path / "results" / "one" / "two-developers" / "results.json").is_file()
    assert (tmp_path / "results" / "two" / "mixed-team" / "results.csv").is_file()


def test_experiment_writes_html_after_json_and_csv(tmp_path, monkeypatch, run_batch) -> None:
    config = _configuration(tmp_path, ["one.json"])
    value = json.loads(config.read_text())
    value["output_formats"] = ["json", "csv", "html"]
    config.write_text(json.dumps(value), encoding="utf-8")
    _fake_backend(run_batch, monkeypatch)

    assert run_batch.main(["--config", str(config)]) == 0

    output = tmp_path / "results" / "one" / "two-developers"
    assert (output / "report.html").read_text() == "<html>report</html>"
    manifest = json.loads((tmp_path / "results" / "manifest.json").read_text())
    assert manifest["jobs"][0]["output_paths"]["html"].endswith("/report.html")


def test_experiment_continues_after_partial_failure(tmp_path, monkeypatch, run_batch) -> None:
    config = _configuration(tmp_path, ["bad.json", "good.json"])
    calls = _fake_backend(run_batch, monkeypatch, failing="bad.json")

    assert run_batch.main(["--config", str(config)]) == 1

    assert len(calls) == 4
    jobs = json.loads((tmp_path / "results" / "manifest.json").read_text())["jobs"]
    assert [job["status"] for job in jobs] == ["failed", "failed", "success", "success"]
    assert "broken scenario" in jobs[0]["error"]


def test_experiment_refuses_overwrite_unless_forced(tmp_path, monkeypatch, run_batch) -> None:
    config = _configuration(tmp_path, ["one.json"])
    _fake_backend(run_batch, monkeypatch)
    existing = tmp_path / "results" / "one" / "two-developers" / "results.json"
    existing.parent.mkdir(parents=True)
    existing.write_text("old", encoding="utf-8")

    with pytest.raises(SystemExit) as error:
        run_batch.main(["--config", str(config)])
    assert error.value.code == 2
    assert existing.read_text() == "old"

    assert run_batch.main(["--config", str(config), "--force"]) == 0
    assert existing.read_text() != "old"


def test_experiment_rejects_duplicate_filesystem_safe_output_paths(
    tmp_path, monkeypatch, run_batch
) -> None:
    config = _configuration(tmp_path, ["one.json"])
    value = json.loads(config.read_text())
    value["team_compositions"][1]["name"] = "Two@Developers"
    config.write_text(json.dumps(value), encoding="utf-8")
    _fake_backend(run_batch, monkeypatch)

    with pytest.raises(SystemExit) as error:
        run_batch.main(["--config", str(config)])
    assert error.value.code == 2
