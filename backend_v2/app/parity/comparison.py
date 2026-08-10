from dataclasses import dataclass
from numbers import Real


@dataclass(frozen=True, slots=True)
class ParityDifference:
    path: str
    legacy: object
    rewritten: object


def compare_snapshots(
    legacy: object,
    rewritten: object,
    *,
    tolerance: float = 1e-9,
    ignored_paths: frozenset[str] = frozenset(),
) -> list[ParityDifference]:
    """Compare nested JSON-like snapshots and report every behavioral difference."""
    differences: list[ParityDifference] = []
    _compare(legacy, rewritten, "$", tolerance, ignored_paths, differences)
    return differences


def _compare(
    legacy: object,
    rewritten: object,
    path: str,
    tolerance: float,
    ignored_paths: frozenset[str],
    differences: list[ParityDifference],
) -> None:
    if path in ignored_paths:
        return
    if isinstance(legacy, dict) and isinstance(rewritten, dict):
        for key in sorted(set(legacy) | set(rewritten)):
            child = f"{path}.{key}"
            if key not in legacy or key not in rewritten:
                differences.append(ParityDifference(child, legacy.get(key), rewritten.get(key)))
            else:
                _compare(legacy[key], rewritten[key], child, tolerance, ignored_paths, differences)
        return
    if isinstance(legacy, list) and isinstance(rewritten, list):
        if len(legacy) != len(rewritten):
            differences.append(ParityDifference(f"{path}.length", len(legacy), len(rewritten)))
        for index, (legacy_item, rewritten_item) in enumerate(zip(legacy, rewritten, strict=False)):
            _compare(
                legacy_item,
                rewritten_item,
                f"{path}[{index}]",
                tolerance,
                ignored_paths,
                differences,
            )
        return
    if isinstance(legacy, bool) != isinstance(rewritten, bool):
        differences.append(ParityDifference(path, legacy, rewritten))
        return
    if _numbers_match(legacy, rewritten, tolerance):
        return
    if legacy != rewritten:
        differences.append(ParityDifference(path, legacy, rewritten))


def _numbers_match(left: object, right: object, tolerance: float) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return False
    if isinstance(left, Real) and isinstance(right, Real):
        return abs(float(left) - float(right)) <= tolerance
    return False
