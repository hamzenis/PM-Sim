#!/usr/bin/env python3
"""Run the backend batch CLI from the repository root.

Example: ``uv run --project backend python scripts/run_batch.py \
--scenario backend/scenario_examples/basic_project.json``
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPOSITORY_ROOT / "backend"


def _delegate(arguments: Sequence[str]) -> int:
    sys.path.insert(0, str(BACKEND_ROOT))
    from main import main as backend_main

    return backend_main(["batch", *arguments])


def main(argv: Sequence[str] | None = None) -> int:
    """Forward batch arguments to the canonical backend launcher."""
    return _delegate(sys.argv[1:] if argv is None else argv)


if __name__ == "__main__":
    raise SystemExit(main())
