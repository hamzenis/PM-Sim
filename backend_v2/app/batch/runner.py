from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BatchRun:
    run_number: int
    seed: int
    result: object


def run_batch[Result](
    run_once: Callable[[int], Result],
    *,
    repetitions: int,
    initial_seed: int = 0,
) -> list[BatchRun]:
    """Run one engine strategy repeatedly with reproducible consecutive seeds."""
    if repetitions < 1:
        raise ValueError("repetitions must be at least one")
    return [
        BatchRun(number, initial_seed + number, run_once(initial_seed + number))
        for number in range(repetitions)
    ]
