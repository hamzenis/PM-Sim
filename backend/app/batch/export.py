"""Format-neutral serialization and safe output for batch reports."""

import csv
import io
import json
import os
import sys
import tempfile
from collections.abc import Iterable, Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import TextIO

from app.batch.runner import SimulationBatchReport, SimulationBatchRun

ExportDestination = Path | str

CSV_FIELDS = (
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


class BatchExportError(Exception):
    """A batch report could not be serialized or written safely."""


def reports_to_dict(
    reports: SimulationBatchReport | Iterable[SimulationBatchReport],
) -> list[dict[str, object]]:
    """Return reports as JSON-compatible values in a stable field order."""
    return [_report_to_dict(report) for report in _coerce_reports(reports)]


def reports_to_json(
    reports: SimulationBatchReport | Iterable[SimulationBatchReport],
) -> str:
    """Serialize one or more reports as UTF-8 JSON text."""
    return json.dumps(reports_to_dict(reports), ensure_ascii=False, indent=2) + "\n"


def reports_to_csv(
    reports: SimulationBatchReport | Iterable[SimulationBatchReport],
) -> str:
    """Serialize all strategy runs into one consistently shaped CSV document."""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for report in _coerce_reports(reports):
        for run in report.runs:
            writer.writerow(_run_to_dict(run, strategy=report.strategy))
    return output.getvalue()


def export_reports(
    reports: SimulationBatchReport | Iterable[SimulationBatchReport],
    *,
    json_destination: ExportDestination | None = None,
    csv_destination: ExportDestination | None = None,
    create_parents: bool = False,
    force: bool = False,
    stdout: TextIO | None = None,
) -> None:
    """Write requested formats, using ``-`` for stdout and atomic file replacement."""
    destinations = tuple(
        destination
        for destination in (json_destination, csv_destination)
        if destination is not None
    )
    if sum(os.fspath(destination) == "-" for destination in destinations) > 1:
        raise BatchExportError("JSON and CSV cannot both be written to stdout")

    values = _coerce_reports(reports)
    outputs = (
        (json_destination, reports_to_json(values)),
        (csv_destination, reports_to_csv(values)),
    )
    stream = stdout if stdout is not None else sys.stdout
    for destination, content in outputs:
        if destination is None:
            continue
        if os.fspath(destination) == "-":
            stream.write(content)
            continue
        _atomic_write(Path(destination), content, create_parents=create_parents, force=force)


def export_text(
    content: str,
    destination: ExportDestination,
    *,
    create_parents: bool = False,
    force: bool = False,
) -> None:
    """Atomically export caller-defined text while retaining its external schema."""
    _atomic_write(Path(destination), content, create_parents=create_parents, force=force)


def _coerce_reports(
    reports: SimulationBatchReport | Iterable[SimulationBatchReport],
) -> tuple[SimulationBatchReport, ...]:
    values = (reports,) if isinstance(reports, SimulationBatchReport) else tuple(reports)
    if not values:
        raise ValueError("at least one batch report is required")
    if not all(isinstance(report, SimulationBatchReport) for report in values):
        raise TypeError("reports must contain only SimulationBatchReport values")
    return values


def _report_to_dict(report: SimulationBatchReport) -> dict[str, object]:
    return {
        "strategy": report.strategy,
        "summary": _json_value(report.summary),
        "runs": [_run_to_dict(run, strategy=report.strategy) for run in report.runs],
    }


def _run_to_dict(run: SimulationBatchRun, *, strategy: str) -> dict[str, object]:
    result = run.result
    final_state = run.final_state
    values = {
        "run_number": run.run_number,
        "seed": run.seed,
        "strategy": strategy,
        "outcome": result.outcome,
        "accepted_tasks": result.accepted_tasks,
        "rejected_tasks": result.rejected_tasks,
        "elapsed_working_days": result.elapsed_working_days,
        "scheduled_working_days": result.scheduled_working_days,
        "total_cost": result.total_cost,
        "remaining_budget": result.remaining_budget,
        "score": result.score.total,
        "known_bugs": final_state.known_bugs.total,
        "undiscovered_bugs": final_state.undiscovered_bugs.total,
    }
    return {name: _json_value(values[name]) for name in CSV_FIELDS}


def _json_value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    return value


def _atomic_write(path: Path, content: str, *, create_parents: bool, force: bool) -> None:
    parent = path.parent
    if create_parents:
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise BatchExportError(
                f"could not create output directory '{parent}': {error}"
            ) from error
    if not parent.is_dir():
        raise BatchExportError(f"output directory does not exist: {parent}")
    if path.exists() and not force:
        raise BatchExportError(f"refusing to overwrite existing file: {path}")

    temporary: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=parent)
        temporary = Path(temporary_name)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        temporary = None
    except OSError as error:
        raise BatchExportError(f"could not write report '{path}': {error}") from error
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
