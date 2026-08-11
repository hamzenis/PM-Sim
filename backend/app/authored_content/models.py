"""Runtime value objects for authored content.

This module is intentionally persistence- and simulation-agnostic.  Callers may map
these values to database rows, but the resolver can also be used by replay tooling.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal


class RuntimeStatus(StrEnum):
    PENDING = "pending"
    ACTIONABLE = "actionable"
    COMPLETED = "completed"


CheckpointKind = Literal["run_started", "before_week", "after_week", "run_finished"]


@dataclass(frozen=True, order=True)
class Checkpoint:
    """A canonical, totally ordered delivery checkpoint."""

    sort_key: tuple[int, int] = field(init=False, repr=False)
    kind: CheckpointKind
    week: int | None = None

    def __post_init__(self) -> None:
        if self.kind in {"before_week", "after_week"}:
            if not isinstance(self.week, int) or isinstance(self.week, bool) or self.week < 1:
                raise ValueError("week checkpoints require a positive integer week")
        elif self.week is not None:
            raise ValueError(f"{self.kind} does not accept a week")
        key = {
            "run_started": (0, 0),
            "before_week": (self.week or 0, 1),
            "after_week": (self.week or 0, 2),
            "run_finished": (2**63 - 1, 0),
        }[self.kind]
        object.__setattr__(self, "sort_key", key)

    @property
    def canonical(self) -> str:
        return self.kind if self.week is None else f"{self.kind}:{self.week}"

    @classmethod
    def parse(cls, value: str | Mapping[str, Any] | Checkpoint) -> Checkpoint:
        if isinstance(value, cls):
            return value
        if isinstance(value, Mapping):
            return cls(value["type"], value.get("week"))
        kind, separator, week = value.partition(":")
        return cls(kind, int(week) if separator else None)  # type: ignore[arg-type]


@dataclass(frozen=True)
class RuntimeEntry:
    id: str
    checkpoint: Checkpoint
    ordinal: int
    priority: int = 0
    required: bool = False
    kind: Literal["fragment", "question", "event"] = "event"
    depends_on: tuple[str, ...] = ()
    status: RuntimeStatus = RuntimeStatus.PENDING
    acknowledged: bool = False
    answer: Any = None
    definition: dict[str, Any] = field(default_factory=dict)

    @property
    def completed(self) -> bool:
        return self.status is RuntimeStatus.COMPLETED


@dataclass(frozen=True)
class Resolution:
    entries: tuple[RuntimeEntry, ...]

    @property
    def actionable(self) -> tuple[RuntimeEntry, ...]:
        return tuple(item for item in self.entries if item.status is RuntimeStatus.ACTIONABLE)
