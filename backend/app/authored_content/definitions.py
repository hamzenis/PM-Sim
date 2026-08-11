"""Immutable authored-content definitions loaded only from a pinned revision."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from .digests import definition_digest


def _plain(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if not isinstance(value, dict):
        raise TypeError("pinned revision definition must be an object")
    return value


@dataclass(frozen=True)
class DefinitionLookups:
    revision_id: str
    digest: str
    fragments: Mapping[str, Mapping[str, Any]]
    questions: Mapping[str, Mapping[str, Any]]
    events: Mapping[str, Mapping[str, Any]]
    sequence: tuple[Mapping[str, Any], ...]


def from_pinned_revision(revision_id: str, revision_definition: Any) -> DefinitionLookups:
    """Build detached lookups from revision JSON, never from an authoring row."""
    if not revision_id:
        raise ValueError("a pinned scenario revision ID is required")
    root = _plain(revision_definition)
    content = root.get("authored_content", root)

    def deep_freeze(value: Any) -> Any:
        if isinstance(value, dict):
            return MappingProxyType({key: deep_freeze(item) for key, item in value.items()})
        if isinstance(value, list):
            return tuple(deep_freeze(item) for item in value)
        return value

    def freeze(items: list[dict[str, Any]]) -> Mapping[str, Mapping[str, Any]]:
        # model validation is expected at publication; copying detaches JSON ORM values.
        import copy

        values = {item["id"]: deep_freeze(copy.deepcopy(item)) for item in items}
        if len(values) != len(items):
            raise ValueError("definition IDs must be unique")
        return MappingProxyType(values)

    import copy

    sequence = tuple(deep_freeze(copy.deepcopy(item)) for item in content.get("sequence", []))
    return DefinitionLookups(
        revision_id=revision_id,
        digest=definition_digest(content),
        fragments=freeze(content.get("fragments", [])),
        questions=freeze(content.get("questions", [])),
        events=freeze(content.get("events", [])),
        sequence=sequence,
    )


def referenced_definition(
    lookups: DefinitionLookups, entry: Mapping[str, Any]
) -> tuple[str, Mapping[str, Any]]:
    for kind, lookup in (
        ("fragment", lookups.fragments),
        ("question", lookups.questions),
        ("event", lookups.events),
    ):
        object_id = entry.get(f"{kind}_id")
        if object_id is not None:
            try:
                return kind, lookup[object_id]
            except KeyError as exc:
                raise ValueError(f"unresolved {kind} definition: {object_id}") from exc
    raise ValueError("sequence entry must reference exactly one definition")


def student_safe_snapshot(kind: str, definition: Mapping[str, Any]) -> dict[str, Any]:
    """Canonical delivery snapshot; answer keys and teaching metadata never enter it."""
    allowed = {
        "fragment": {"id", "title", "body", "required"},
        "question": {
            "id",
            "prompt",
            "answer_schema",
            "options",
            "required",
            "answer_once",
            "short_text_max_length",
        },
        "event": {"id", "effects"},
    }[kind]

    def thaw(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {key: thaw(item) for key, item in value.items()}
        if isinstance(value, tuple):
            return [thaw(item) for item in value]
        return value

    return {key: thaw(definition[key]) for key in sorted(allowed & definition.keys())}
