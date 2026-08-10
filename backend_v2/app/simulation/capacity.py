from app.simulation.models import ActivityHours, WeeklyCapacity


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
