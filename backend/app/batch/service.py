"""Application-level orchestration for deterministic in-memory batch runs."""

import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from typing import Literal

from pydantic import ValidationError

from app.batch.runner import (
    SimulationBatchReport,
    report_to_csv,
    report_to_dict,
    run_simulation_batch,
)
from app.batch.strategies import built_in_strategy
from app.scenarios.models import ScenarioDefinition

OutputFormat = Literal["json", "csv"]
MAX_SEED = 2**32 - 1
BUILT_IN_STRATEGIES = frozenset(
    {"development-first", "balanced", "quality-first", "overtime-heavy"}
)


class BatchExecutionError(Exception):
    """Base class for expected batch execution failures."""


class BatchConfigurationError(BatchExecutionError):
    """The requested batch configuration is invalid."""


class ScenarioLoadError(BatchExecutionError):
    """A scenario could not be read or validated."""


class BatchOutputError(BatchExecutionError):
    """A requested report destination cannot be written."""


@dataclass(frozen=True, slots=True)
class LoadedScenario:
    definition: ScenarioDefinition
    source_path: Path
    sha256_digest: str
    employee_type_code: str | None


@dataclass(frozen=True, slots=True)
class BatchExecutionConfig:
    scenario_path: Path
    strategy_names: tuple[str, ...] = ("balanced",)
    repetitions: int = 100
    initial_seed: int = 0
    team_size: int = 3
    employee_type: str | None = None
    output_formats: tuple[OutputFormat, ...] = ("json",)
    output_directory: Path | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "scenario_path", Path(self.scenario_path))
        if self.output_directory is not None:
            object.__setattr__(self, "output_directory", Path(self.output_directory))
        if self.repetitions < 1:
            raise BatchConfigurationError("repetitions must be positive")
        if self.team_size < 1:
            raise BatchConfigurationError("team size must be positive")
        if not self.strategy_names:
            raise BatchConfigurationError("at least one strategy is required")
        if len(self.strategy_names) != len(set(self.strategy_names)):
            raise BatchConfigurationError("strategy names must be unique")
        unknown = set(self.strategy_names) - BUILT_IN_STRATEGIES
        if unknown:
            raise BatchConfigurationError(f"unknown strategy: {sorted(unknown)[0]}")
        if self.initial_seed < 0 or self.initial_seed > MAX_SEED:
            raise BatchConfigurationError(f"initial seed must be between 0 and {MAX_SEED}")
        if self.initial_seed + self.repetitions - 1 > MAX_SEED:
            raise BatchConfigurationError(f"seed range must end at or before {MAX_SEED}")
        if not self.output_formats:
            raise BatchConfigurationError("at least one output format is required")
        if len(self.output_formats) != len(set(self.output_formats)):
            raise BatchConfigurationError("output formats must be unique")
        unsupported = set(self.output_formats) - {"json", "csv"}
        if unsupported:
            raise BatchConfigurationError(f"unsupported output format: {sorted(unsupported)[0]}")
        if self.output_directory is not None:
            _validate_output_directory(self.output_directory)


@dataclass(frozen=True, slots=True)
class BatchProvenance:
    scenario_path: Path
    scenario_name: str
    strategy_names: tuple[str, ...]
    seeds: tuple[int, ...]
    team_size: int
    employee_type_code: str
    output_formats: tuple[OutputFormat, ...]


@dataclass(frozen=True, slots=True)
class BatchStrategyMetadata:
    name: str
    employee_type: str
    team_size: int
    allocation: dict[str, float]
    overtime_hours_per_employee: float


@dataclass(frozen=True, slots=True)
class BatchReportMetadata:
    """Report provenance; generated_at is the only non-deterministic envelope field."""

    schema_version: int
    pm_sim_package: str
    pm_sim_version: str
    generated_at: datetime
    scenario_name: str
    scenario_sha256: str
    initial_seed: int
    final_seed: int
    repetitions: int
    strategies: tuple[BatchStrategyMetadata, ...]


@dataclass(frozen=True, slots=True)
class BatchExecutionResult:
    reports: tuple[SimulationBatchReport, ...]
    provenance: BatchProvenance
    metadata: BatchReportMetadata


def load_scenario(path: Path | str) -> LoadedScenario:
    """Load validated JSON and infer an employee type only for a single-type scenario."""
    source = Path(path)
    try:
        scenario_bytes = source.read_bytes()
        definition = ScenarioDefinition.model_validate_json(scenario_bytes)
    except (OSError, ValidationError, ValueError) as error:
        raise ScenarioLoadError(f"could not load scenario '{source}': {error}") from error
    employee_type = (
        definition.employee_types[0].code if len(definition.employee_types) == 1 else None
    )
    return LoadedScenario(definition, source, sha256(scenario_bytes).hexdigest(), employee_type)


def execute_batch(config: BatchExecutionConfig) -> BatchExecutionResult:
    """Execute every strategy against the same consecutive deterministic seeds."""
    loaded = load_scenario(config.scenario_path)
    known_employee_types = {item.code for item in loaded.definition.employee_types}
    employee_type = config.employee_type or loaded.employee_type_code
    if employee_type is None:
        raise BatchConfigurationError(
            "employee type is required when the scenario defines multiple employee types"
        )
    if employee_type not in known_employee_types:
        raise BatchConfigurationError(f"unknown employee type: {employee_type}")

    strategies = tuple(
        built_in_strategy(
            name,
            employee_type_code=employee_type,
            initial_team_size=config.team_size,
        )
        for name in config.strategy_names
    )
    reports = tuple(
        run_simulation_batch(
            loaded.definition,
            strategy=strategy,
            repetitions=config.repetitions,
            initial_seed=config.initial_seed,
        )
        for strategy in strategies
    )
    result = BatchExecutionResult(
        reports=reports,
        provenance=BatchProvenance(
            scenario_path=loaded.source_path,
            scenario_name=loaded.definition.name,
            strategy_names=config.strategy_names,
            seeds=tuple(range(config.initial_seed, config.initial_seed + config.repetitions)),
            team_size=config.team_size,
            employee_type_code=employee_type,
            output_formats=config.output_formats,
        ),
        metadata=BatchReportMetadata(
            schema_version=1,
            pm_sim_package="pm-sim-backend",
            pm_sim_version=version("pm-sim-backend"),
            generated_at=datetime.now(UTC),
            scenario_name=loaded.definition.name,
            scenario_sha256=loaded.sha256_digest,
            initial_seed=config.initial_seed,
            final_seed=config.initial_seed + config.repetitions - 1,
            repetitions=config.repetitions,
            strategies=tuple(
                BatchStrategyMetadata(
                    name=strategy.name,
                    employee_type=strategy.employee_type_code,
                    team_size=strategy.initial_team_size,
                    allocation=asdict(strategy.allocation),
                    overtime_hours_per_employee=strategy.overtime_hours_per_employee,
                )
                for strategy in strategies
            ),
        ),
    )
    if config.output_directory is not None:
        _write_reports(result, config.output_directory, config.output_formats)
    return result


def execution_result_to_dict(result: BatchExecutionResult) -> dict[str, object]:
    return {
        "metadata": {
            **{
                key: value
                for key, value in asdict(result.metadata).items()
                if key not in {"generated_at", "strategies"}
            },
            "generated_at": result.metadata.generated_at.isoformat(),
            "strategies": [asdict(strategy) for strategy in result.metadata.strategies],
        },
        "provenance": {
            "scenario_path": str(result.provenance.scenario_path),
            "scenario_name": result.provenance.scenario_name,
            "strategy_names": list(result.provenance.strategy_names),
            "seeds": list(result.provenance.seeds),
            "team_size": result.provenance.team_size,
            "employee_type_code": result.provenance.employee_type_code,
            "output_formats": list(result.provenance.output_formats),
        },
        "reports": [report_to_dict(report) for report in result.reports],
    }


def _validate_output_directory(destination: Path) -> None:
    existing = destination if destination.exists() else destination.parent
    if destination.exists() and not destination.is_dir():
        raise BatchOutputError(f"output destination is not a directory: {destination}")
    if not existing.exists() or not existing.is_dir() or not os.access(existing, os.W_OK):
        raise BatchOutputError(f"output destination is not writable: {destination}")


def _write_reports(
    result: BatchExecutionResult, destination: Path, formats: tuple[OutputFormat, ...]
) -> None:
    try:
        destination.mkdir(exist_ok=True)
        if "json" in formats:
            (destination / "batch-report.json").write_text(
                json.dumps(execution_result_to_dict(result), indent=2) + "\n", encoding="utf-8"
            )
        if "csv" in formats:
            (destination / "batch-report-metadata.json").write_text(
                json.dumps(execution_result_to_dict(result)["metadata"], indent=2) + "\n",
                encoding="utf-8",
            )
            for report in result.reports:
                (destination / f"batch-report-{report.strategy}.csv").write_text(
                    report_to_csv(report), encoding="utf-8"
                )
    except OSError as error:
        raise BatchOutputError(f"could not write reports to '{destination}': {error}") from error
