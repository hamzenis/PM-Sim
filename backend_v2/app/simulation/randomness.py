from collections.abc import Iterable
from typing import Protocol


class RandomSource(Protocol):
    """Random values required by the engine, supplied by the caller."""

    def probability(self, chance: float) -> bool: ...

    def poisson(self, expected_value: float) -> int: ...


class RecordedRandomSource:
    """A finite random sequence for parity tests and replaying recorded calculations."""

    def __init__(
        self,
        *,
        probabilities: Iterable[float] = (),
        poisson_values: Iterable[int] = (),
    ) -> None:
        self._probabilities = iter(probabilities)
        self._poisson_values = iter(poisson_values)

    def probability(self, chance: float) -> bool:
        if not 0 <= chance <= 1:
            raise ValueError("probability must be between zero and one")
        try:
            value = next(self._probabilities)
        except StopIteration as error:
            raise RuntimeError("no recorded probability value remains") from error
        if not 0 <= value < 1:
            raise ValueError("recorded probability values must be in [0, 1)")
        return value < chance

    def poisson(self, expected_value: float) -> int:
        if expected_value < 0:
            raise ValueError("expected Poisson value cannot be negative")
        try:
            value = next(self._poisson_values)
        except StopIteration as error:
            raise RuntimeError("no recorded Poisson value remains") from error
        if value < 0:
            raise ValueError("recorded Poisson values cannot be negative")
        return value
