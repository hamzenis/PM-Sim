from app.simulation.models import ActivityAllocation, ActivityHours, WeeklyCapacity


class CapacityError(ValueError):
    """Raised when a weekly plan exceeds the team's finite capacity."""


def allocate_weekly_hours(
    capacity: WeeklyCapacity,
    requested: ActivityHours,
) -> ActivityHours:
    """Validate a plan in which all engineering activities share staff hours."""
    if requested.total > capacity.total_hours + 1e-9:
        raise CapacityError(
            f"requested {requested.total:g} hours but only {capacity.total_hours:g} are available"
        )
    return requested


def hours_from_allocation(
    capacity: WeeklyCapacity,
    allocation: ActivityAllocation,
    *,
    reserved_hours: float = 0,
) -> ActivityHours:
    """Turn student percentages into hours without creating extra capacity."""
    if reserved_hours < 0:
        raise ValueError("reserved hours cannot be negative")
    if reserved_hours > capacity.total_hours:
        raise CapacityError(
            f"reserved {reserved_hours:g} hours but only {capacity.total_hours:g} are available"
        )
    hours = capacity.total_hours - reserved_hours
    return ActivityHours(
        development=hours * allocation.development / 100,
        unit_testing=hours * allocation.unit_testing / 100,
        bug_fixing=hours * allocation.bug_fixing / 100,
        integration_testing=hours * allocation.integration_testing / 100,
    )
