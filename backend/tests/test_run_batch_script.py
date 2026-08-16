import importlib.util
from pathlib import Path


def test_repository_batch_wrapper_forwards_arguments(monkeypatch) -> None:
    script_path = Path(__file__).parents[2] / "scripts" / "run_batch.py"
    spec = importlib.util.spec_from_file_location("run_batch", script_path)
    assert spec is not None
    assert spec.loader is not None
    run_batch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(run_batch)
    calls: list[list[str]] = []
    monkeypatch.setattr(
        run_batch, "_delegate", lambda arguments: calls.append(list(arguments)) or 7
    )

    arguments = ["--scenario", "scenario.json", "--repetitions", "3"]
    assert run_batch.main(arguments) == 7
    assert calls == [arguments]
