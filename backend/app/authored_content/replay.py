"""Read-only replay verification for authored-content audit records."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from .answers import AnswerError, normalize_answer
from .definitions import DefinitionLookups, referenced_definition, student_safe_snapshot
from .digests import definition_digest, projection_digest, response_request_digest
from .effects import apply_effect
from .models import Checkpoint
from .triggers import canonical_checkpoint
from .visibility import serialize_student


@dataclass(frozen=True)
class Divergence:
    category: str
    record: str
    expected: Any
    actual: Any


def verify_replay(
    definitions: DefinitionLookups,
    deliveries: Iterable[Mapping[str, Any]],
    responses: Iterable[Mapping[str, Any]] = (),
    effects: Iterable[Mapping[str, Any]] = (),
    *,
    initial_projection: Mapping[str, Any] | None = None,
    terminal: bool = False,
) -> tuple[Divergence, ...]:
    """Recompute the audit stream without accepting a session or updating a row."""
    differences: list[Divergence] = []
    sequence = {entry["id"]: (ordinal, entry) for ordinal, entry in enumerate(definitions.sequence)}
    completed: set[str] = set()
    prior_key: tuple[int, int, int, int] | None = None
    delivered_by_id: dict[str, Mapping[str, Any]] = {}
    for record in deliveries:
        entry_id = str(record["sequence_entry_id"])
        delivered_by_id[entry_id] = record
        if entry_id not in sequence:
            differences.append(Divergence("definition", entry_id, "known entry", "missing"))
            continue
        ordinal, entry = sequence[entry_id]
        checkpoint = Checkpoint.parse(entry["trigger"])
        key = (*checkpoint.sort_key, int(entry.get("priority", 0)), ordinal)
        if prior_key is not None and key < prior_key:
            differences.append(Divergence("ordering", entry_id, ">= previous order", key))
        prior_key = key
        expected_checkpoint = canonical_checkpoint(entry["trigger"])
        if record.get("canonical_checkpoint") != expected_checkpoint:
            differences.append(
                Divergence(
                    "checkpoint", entry_id, expected_checkpoint, record.get("canonical_checkpoint")
                )
            )
        missing = [
            dependency for dependency in entry.get("depends_on", []) if dependency not in completed
        ]
        if missing:
            differences.append(Divergence("dependencies", entry_id, "completed", missing))
        kind, definition = referenced_definition(definitions, entry)
        digest_snapshot = student_safe_snapshot(kind, definition)
        # Delivery persistence includes immutable sequence/visibility metadata in the
        # historical snapshot.  Replay must use that same canonical digest contract.
        digest_snapshot.update(
            {
                "kind": kind,
                "required": bool(entry.get("required", definition.get("required", False))),
                "visibility": entry.get("visibility", "default"),
                "professor_only": bool(definition.get("professor_only", False)),
            }
        )
        expected_digest = definition_digest(digest_snapshot)
        if record.get("definition_digest") != expected_digest:
            differences.append(
                Divergence(
                    "definition_digest", entry_id, expected_digest, record.get("definition_digest")
                )
            )
        if record.get("status") == "completed":
            completed.add(entry_id)

    for response in responses:
        entry_id = str(response["sequence_entry_id"])
        if entry_id not in sequence:
            differences.append(Divergence("response", entry_id, "known question", "missing"))
            continue
        _, entry = sequence[entry_id]
        kind, question = referenced_definition(definitions, entry)
        recorded_answer = response.get("normalized_answer")
        try:
            normalized = (
                normalize_answer(question, recorded_answer)
                if kind == "question"
                else {"acknowledged": True}
            )
        except (AnswerError, KeyError) as exc:
            differences.append(
                Divergence("normalized_response", entry_id, "valid normalized answer", str(exc))
            )
            continue
        if normalized != recorded_answer:
            differences.append(
                Divergence(
                    "normalized_response", entry_id, normalized, response.get("normalized_answer")
                )
            )
        request = response.get("request")
        if request is not None and response.get("request_digest") != response_request_digest(
            request
        ):
            differences.append(
                Divergence(
                    "response_request_digest",
                    entry_id,
                    response_request_digest(request),
                    response.get("request_digest"),
                )
            )

    projection = dict(initial_projection or {})
    for audit in effects:
        entry_id = str(audit["sequence_entry_id"])
        application = apply_effect(projection, audit["effect_payload"])
        if audit.get("before_projection_digest") != application.before_digest:
            differences.append(
                Divergence(
                    "projection_before",
                    entry_id,
                    application.before_digest,
                    audit.get("before_projection_digest"),
                )
            )
        if audit.get("after_projection_digest") != application.after_digest:
            differences.append(
                Divergence(
                    "projection_after",
                    entry_id,
                    application.after_digest,
                    audit.get("after_projection_digest"),
                )
            )
        projection = application.projection

    # Exercise the exact production visibility boundary and verify recorded student projections.
    for entry_id, record in delivered_by_id.items():
        if "student_projection" in record:
            actual = serialize_student([record], completed_ids=completed, terminal=terminal)
            if actual != record["student_projection"]:
                differences.append(
                    Divergence("visibility", entry_id, actual, record["student_projection"])
                )
        if record.get("turn_id") is not None and record.get("turn_run_id") not in (
            None,
            record.get("run_id"),
        ):
            differences.append(
                Divergence(
                    "turn_association", entry_id, record.get("run_id"), record.get("turn_run_id")
                )
            )
    # Explicit final digest catches projection tampering even with an empty audit list.
    _ = projection_digest(projection)
    return tuple(differences)
