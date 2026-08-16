#!/usr/bin/env python3
"""Run one backend batch command, or a configured matrix of experiments."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPOSITORY_ROOT / "backend"


def _backend_imports() -> tuple[Any, ...]:
    sys.path.insert(0, str(BACKEND_ROOT))
    from app.batch.export import export_reports, export_text
    from app.batch.html_report import write_html_report
    from app.batch.service import BatchExecutionConfig, execute_batch
    from app.batch.strategies import TeamMemberCount

    return (
        BatchExecutionConfig,
        TeamMemberCount,
        execute_batch,
        export_reports,
        export_text,
        write_html_report,
    )


def _delegate(arguments: Sequence[str]) -> int:
    sys.path.insert(0, str(BACKEND_ROOT))
    from main import main as backend_main

    return backend_main(["batch", *arguments])


def _safe_component(value: str) -> str:
    component = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip(".-_").lower()
    return component or "unnamed"


def _load_config(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not load experiment configuration '{path}': {error}") from error
    if not isinstance(value, dict):
        raise TypeError("experiment configuration must be a JSON object")
    required = {
        "scenarios",
        "strategies",
        "team_compositions",
        "repetitions",
        "initial_seed",
        "output_root",
    }
    missing = sorted(required - value.keys())
    unknown = sorted(value.keys() - required - {"output_formats"})
    if missing:
        raise ValueError(f"missing experiment configuration field: {missing[0]}")
    if unknown:
        raise ValueError(f"unknown experiment configuration field: {unknown[0]}")
    if not isinstance(value["scenarios"], list) or not value["scenarios"]:
        raise ValueError("scenarios must be a non-empty list")
    if not isinstance(value["strategies"], list) or not value["strategies"]:
        raise ValueError("strategies must be a non-empty list")
    if not isinstance(value["team_compositions"], list) or not value["team_compositions"]:
        raise ValueError("team_compositions must be a non-empty list")
    formats = value.setdefault("output_formats", ["json", "csv"])
    if (
        not isinstance(formats, list)
        or not formats
        or any(item not in {"json", "csv", "html"} for item in formats)
        or len(formats) != len(set(formats))
    ):
        raise ValueError("output_formats must contain unique json, csv, or html values")
    return value


def _resolve(base: Path, value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("scenario and output paths must be non-empty strings")
    path = Path(value)
    return path if path.is_absolute() else base / path


def _experiment(config_path: Path, *, force: bool) -> int:
    (
        BatchExecutionConfig,
        TeamMemberCount,
        execute_batch,
        export_reports,
        export_text,
        write_html_report,
    ) = _backend_imports()
    raw = _load_config(config_path)
    base = config_path.resolve().parent
    output_root = _resolve(base, raw["output_root"])
    jobs: list[dict[str, Any]] = []
    paths: set[Path] = set()

    for scenario_value in raw["scenarios"]:
        scenario_path = _resolve(base, scenario_value)
        scenario_key = _safe_component(scenario_path.stem)
        for composition in raw["team_compositions"]:
            if not isinstance(composition, dict) or set(composition) != {
                "name",
                "members",
            }:
                raise ValueError("each team composition requires only name and members")
            name = composition["name"]
            members = composition["members"]
            if not isinstance(name, str) or not name or not isinstance(members, list):
                raise ValueError("team composition name and members are invalid")
            output_directory = output_root / scenario_key / _safe_component(name)
            resolved_output = output_directory.resolve()
            if resolved_output in paths:
                raise ValueError(f"duplicate output path: {output_directory}")
            paths.add(resolved_output)
            jobs.append(
                {
                    "scenario_path": scenario_path,
                    "scenario": str(scenario_value),
                    "composition": composition,
                    "output_directory": output_directory,
                }
            )

    manifest_path = output_root / "manifest.json"
    artifacts = [manifest_path]
    for job in jobs:
        job_artifacts = [
            job["output_directory"] / "results.json",
            job["output_directory"] / "results.csv",
        ]
        if "html" in raw["output_formats"]:
            job_artifacts.append(job["output_directory"] / "report.html")
        artifacts.extend(job_artifacts)
    existing = [path for path in artifacts if path.exists()]
    if existing and not force:
        raise FileExistsError(f"refusing to overwrite existing file: {existing[0]}")

    started = datetime.now(UTC)
    manifest_jobs: list[dict[str, Any]] = []
    package_version = version("pm-sim-backend")
    failed = False
    for job in jobs:
        entry = {
            "scenario": job["scenario"],
            "scenario_sha256": None,
            "team_composition": job["composition"],
            "output_paths": {
                "json": str(job["output_directory"] / "results.json"),
                "csv": str(job["output_directory"] / "results.csv"),
            },
            "status": "failed",
        }
        try:
            scenario_bytes = job["scenario_path"].read_bytes()
            entry["scenario_sha256"] = sha256(scenario_bytes).hexdigest()
            members = tuple(
                TeamMemberCount(member["employee_type_code"], member["count"])
                for member in job["composition"]["members"]
            )
            result = execute_batch(
                BatchExecutionConfig(
                    scenario_path=job["scenario_path"],
                    team_composition=members,
                    strategy_names=tuple(raw["strategies"]),
                    repetitions=raw["repetitions"],
                    initial_seed=raw["initial_seed"],
                    output_formats=("json", "csv"),
                )
            )
            package_version = result.metadata.pm_sim_version
            export_reports(
                result.reports,
                json_destination=job["output_directory"] / "results.json",
                csv_destination=job["output_directory"] / "results.csv",
                create_parents=True,
                force=force,
            )
            if "html" in raw["output_formats"]:
                html_path = job["output_directory"] / "report.html"
                entry["output_paths"]["html"] = str(html_path)
                write_html_report(result, html_path, create_parents=True, force=force)
            entry["status"] = "success"
        # A single invalid scenario must not stop the remaining matrix.
        except Exception as error:  # noqa: BLE001
            failed = True
            entry["error"] = f"{type(error).__name__}: {error}"
        manifest_jobs.append(entry)

    manifest = {
        "started_at": started.isoformat(),
        "ended_at": datetime.now(UTC).isoformat(),
        "package": "pm-sim-backend",
        "package_version": package_version,
        "configuration": raw,
        "jobs": manifest_jobs,
    }
    export_text(
        json.dumps(manifest, indent=2) + "\n",
        manifest_path,
        create_parents=True,
        force=force,
    )
    return 1 if failed else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Preserve legacy forwarding unless the explicit experiment option is present."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if "--config" not in arguments:
        return _delegate(arguments)
    parser = argparse.ArgumentParser(description="Run a configured batch experiment matrix")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    try:
        options = parser.parse_args(arguments)
        return _experiment(options.config, force=options.force)
    except (TypeError, ValueError, FileExistsError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
