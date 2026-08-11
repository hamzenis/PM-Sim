"""Pure dependency predicates used by live resolution and replay."""

from collections.abc import Iterable, Mapping

from .models import RuntimeEntry, RuntimeStatus


def completed_ids(entries: Iterable[RuntimeEntry]) -> frozenset[str]:
    return frozenset(entry.id for entry in entries if entry.status is RuntimeStatus.COMPLETED)


def dependencies_completed(
    entry: RuntimeEntry, statuses: Mapping[str, RuntimeStatus] | set[str] | frozenset[str]
) -> bool:
    completed = (
        statuses
        if isinstance(statuses, (set, frozenset))
        else {
            key
            for key, value in statuses.items()
            if value is RuntimeStatus.COMPLETED or value == "completed"
        }
    )
    return all(dependency in completed for dependency in entry.depends_on)
