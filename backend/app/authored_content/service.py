"""Small transaction-friendly application service for authored-content commands."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .answers import normalize_answer
from .models import RuntimeEntry, RuntimeStatus
from .resolver import complete_delivery


def acknowledge(entry: RuntimeEntry) -> RuntimeEntry:
    if entry.kind != "fragment":
        raise ValueError("only fragments can be acknowledged")
    return complete_delivery(entry, acknowledged=True)


def answer(entry: RuntimeEntry, raw_answer: Any) -> RuntimeEntry:
    if entry.kind != "question":
        raise ValueError("only questions can be answered")
    normalized = normalize_answer(entry.definition, raw_answer, completed=entry.completed)
    return complete_delivery(entry, answered=normalized)


def deliver(entry: RuntimeEntry) -> RuntimeEntry:
    """Atomically deliver entries which require no student command."""
    if entry.status is not RuntimeStatus.ACTIONABLE:
        raise ValueError("entry is not actionable")
    if entry.kind == "event" or (entry.kind == "fragment" and not entry.required):
        return complete_delivery(entry)
    return replace(entry, status=RuntimeStatus.ACTIONABLE)
