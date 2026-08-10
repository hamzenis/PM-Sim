import pytest

from app.simulation.capacity import CapacityError, allocate_weekly_hours, hours_from_allocation
from app.simulation.models import ActivityAllocation, ActivityHours, WeeklyCapacity


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


def test_meetings_and_training_reserve_time_before_percentage_allocation() -> None:
    hours = hours_from_allocation(
        WeeklyCapacity(employee_count=1),
        ActivityAllocation(50, 50, 0, 0),
        reserved_hours=10,
    )
    assert hours == ActivityHours(development=15, unit_testing=15)


def test_reserved_time_cannot_exceed_team_capacity() -> None:
    with pytest.raises(CapacityError, match="reserved 41 hours"):
        hours_from_allocation(
            WeeklyCapacity(employee_count=1),
            ActivityAllocation(100, 0, 0, 0),
            reserved_hours=41,
        )
