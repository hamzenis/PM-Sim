import pytest

from app.simulation.capacity import CapacityError, allocate_weekly_hours
from app.simulation.models import ActivityHours, WeeklyCapacity


def test_activities_share_finite_weekly_capacity() -> None:
    capacity = WeeklyCapacity(employee_count=2)
    plan = ActivityHours(development=40, unit_testing=20, bug_fixing=20)
    assert allocate_weekly_hours(capacity, plan) == plan


def test_overallocated_week_is_rejected() -> None:
    with pytest.raises(CapacityError, match="only 40 are available"):
        allocate_weekly_hours(
            WeeklyCapacity(employee_count=1),
            ActivityHours(development=30, unit_testing=20),
        )
