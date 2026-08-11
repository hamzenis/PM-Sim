"""Bounded presentation projection effects; simulation state is not an input."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .digests import projection_digest

APPROVED_EFFECTS = frozenset(
    {
        "show_message",
        "show_fragment",
        "show_question",
        "set_presentation_flag",
        "set_presentation_theme",
    }
)


@dataclass(frozen=True)
class EffectApplication:
    projection: dict[str, Any]
    before_digest: str
    after_digest: str


def apply_effect(projection: Mapping[str, Any], effect: Mapping[str, Any]) -> EffectApplication:
    before = copy.deepcopy(dict(projection))
    after = copy.deepcopy(before)
    effect_type = effect.get("type")
    if effect_type not in APPROVED_EFFECTS:
        raise ValueError(f"unapproved presentation effect: {effect_type}")
    payload = effect.get("payload")
    if not isinstance(payload, Mapping):
        raise ValueError("effect payload must be an object")
    if effect_type == "show_message":
        after.setdefault("messages", []).append(payload["text"])
    elif effect_type == "show_fragment":
        after.setdefault("visible_fragment_ids", [])
        if payload["fragment_id"] not in after["visible_fragment_ids"]:
            after["visible_fragment_ids"].append(payload["fragment_id"])
    elif effect_type == "show_question":
        after.setdefault("visible_question_ids", [])
        if payload["question_id"] not in after["visible_question_ids"]:
            after["visible_question_ids"].append(payload["question_id"])
    elif effect_type == "set_presentation_flag":
        after.setdefault("flags", {})[payload["flag"]] = payload["value"]
    else:
        after["theme"] = payload["theme"]
    return EffectApplication(after, projection_digest(before), projection_digest(after))


def apply_effects(
    projection: Mapping[str, Any], effects: list[Mapping[str, Any]]
) -> tuple[dict[str, Any], tuple[EffectApplication, ...]]:
    current = dict(projection)
    audit = []
    for effect in effects:
        application = apply_effect(current, effect)
        current = application.projection
        audit.append(application)
    return current, tuple(audit)
