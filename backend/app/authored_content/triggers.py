"""Checkpoint parsing and eligibility."""

from .models import Checkpoint

RUN_STARTED = Checkpoint("run_started")
RUN_FINISHED = Checkpoint("run_finished")


def before_week(week: int) -> Checkpoint:
    return Checkpoint("before_week", week)


def after_week(week: int) -> Checkpoint:
    return Checkpoint("after_week", week)


def canonical_checkpoint(trigger: object) -> str:
    return Checkpoint.parse(trigger).canonical  # type: ignore[arg-type]


def is_eligible(trigger: object, reached: object, *, terminal: bool = False) -> bool:
    wanted = Checkpoint.parse(trigger)  # type: ignore[arg-type]
    current = Checkpoint.parse(reached)  # type: ignore[arg-type]
    if wanted.kind == "run_finished" and not terminal:
        return False
    return wanted.sort_key <= current.sort_key
