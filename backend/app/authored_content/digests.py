"""One canonical JSON implementation for every authored-content digest."""

from __future__ import annotations

import hashlib
import json
import math
from decimal import Decimal
from typing import Any


def _normalize(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("canonical JSON does not support non-finite numbers")
        # JSON has one number type.  Normalize integral floats and spelling of -0.
        if value == 0:
            return 0
        return int(value) if value.is_integer() else float(Decimal(str(value)))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("canonical JSON does not support non-finite numbers")
        return int(value) if value == value.to_integral() else float(value)
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise TypeError("canonical JSON object keys must be strings")
        return {key: _normalize(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if hasattr(value, "model_dump"):
        return _normalize(value.model_dump(mode="json"))
    raise TypeError(f"unsupported canonical JSON value: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    return json.dumps(
        _normalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


# Named aliases deliberately share exactly the same canonicalization boundary.
definition_digest = sha256_digest
response_request_digest = sha256_digest
turn_request_digest = sha256_digest
projection_digest = sha256_digest
