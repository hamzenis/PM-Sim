"""The single student/professor serialization boundary."""

from __future__ import annotations

import copy
from collections.abc import Iterable, Mapping
from typing import Any

SENSITIVE_KEYS = frozenset(
    {
        "answer_key",
        "correct_answer",
        "scoring",
        "feedback_by_option",
        "definition_snapshot",
        "snapshot",
        "before_projection_digest",
        "after_projection_digest",
        "effect_payload",
        "run_state",
        "simulation_state",
        "random_seed",
        "hidden_simulation_fields",
    }
)


def visible_at(
    entry: Mapping[str, Any], completed_ids: set[str] | frozenset[str], *, terminal: bool
) -> bool:
    visibility = entry.get("visibility", "default")
    if visibility == "run_finished":
        return terminal
    if visibility == "after_acknowledgement":
        associated = entry.get("visibility_associated_entry_id")
        if not associated:
            raise ValueError("after_acknowledgement requires an explicit associated entry")
        # Title-only before completion; the entry itself remains visible.
        return True
    return True


def _strip(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _strip(item) for key, item in value.items() if key not in SENSITIVE_KEYS}
    if isinstance(value, list):
        return [_strip(item) for item in value]
    return copy.deepcopy(value)


def serialize_student(
    entries: Iterable[Mapping[str, Any]],
    *,
    completed_ids: set[str] | frozenset[str] = frozenset(),
    terminal: bool = False,
) -> list[dict[str, Any]]:
    result = []
    for source in entries:
        if source.get("professor_only") or source.get("future"):
            continue
        if not visible_at(source, completed_ids, terminal=terminal):
            continue
        item = _strip(dict(source))
        if source.get("hidden_body"):
            item.pop("body", None)
            item.pop("prompt", None)
        if source.get("visibility") == "after_acknowledgement":
            associated = source["visibility_associated_entry_id"]
            if associated not in completed_ids:
                item = {key: item[key] for key in ("id", "title") if key in item}
        result.append(item)
    return result


def serialize_professor(entries: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Professor output retains teaching data but not persistence/audit internals."""
    always_private = SENSITIVE_KEYS - {
        "answer_key",
        "correct_answer",
        "scoring",
        "feedback_by_option",
    }

    def clean(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: clean(item) for key, item in value.items() if key not in always_private}
        if isinstance(value, list):
            return [clean(item) for item in value]
        return copy.deepcopy(value)

    return [clean(dict(entry)) for entry in entries]
