"""Deterministic eligibility, dependency, and required-item resolution."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from .dependencies import completed_ids, dependencies_completed
from .models import Checkpoint, Resolution, RuntimeEntry, RuntimeStatus
from .triggers import is_eligible


def resolve(
    entries: Iterable[RuntimeEntry], reached: Checkpoint, *, terminal: bool = False
) -> Resolution:
    original = tuple(entries)
    completed = completed_ids(original)
    candidates = sorted(
        (
            entry
            for entry in original
            if not entry.completed
            and is_eligible(entry.checkpoint, reached, terminal=terminal)
            and dependencies_completed(entry, completed)
        ),
        key=lambda entry: (entry.priority, entry.ordinal),
    )
    earliest_required = next((entry.id for entry in candidates if entry.required), None)
    actionable = {
        entry.id for entry in candidates if not entry.required or entry.id == earliest_required
    }
    return Resolution(
        tuple(
            entry
            if entry.completed
            else replace(
                entry,
                status=RuntimeStatus.ACTIONABLE
                if entry.id in actionable
                else RuntimeStatus.PENDING,
            )
            for entry in original
        )
    )


def complete_delivery(
    entry: RuntimeEntry, *, acknowledged: bool = False, answered: object = None
) -> RuntimeEntry:
    """Apply atomic delivery semantics to one actionable item."""
    if entry.status is not RuntimeStatus.ACTIONABLE:
        raise ValueError("entry is not actionable")
    if entry.kind == "question":
        if answered is None:
            # Both required and optional questions remain answerable until answered.
            return entry
        return replace(entry, status=RuntimeStatus.COMPLETED, answer=answered)
    if entry.kind == "fragment" and entry.required and not acknowledged:
        return entry
    # Optional fragments, events, and acknowledged required fragments complete atomically.
    return replace(entry, status=RuntimeStatus.COMPLETED, acknowledged=acknowledged)
