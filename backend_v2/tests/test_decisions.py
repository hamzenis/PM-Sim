import pytest

from app.simulation.capacity import hours_from_allocation
from app.simulation.models import ActivityAllocation, WeeklyCapacity, WeeklyDecision


def test_student_percentages_become_shared_weekly_hours() -> None:
    allocation = ActivityAllocation(
        development=50,
        unit_testing=25,
        bug_fixing=15,
        integration_testing=10,
    )
    hours = hours_from_allocation(WeeklyCapacity(employee_count=2), allocation)
    assert hours.development == 40
    assert hours.unit_testing == 20
    assert hours.bug_fixing == 12
    assert hours.integration_testing == 8
    assert hours.total == 80


def test_percentages_must_total_100() -> None:
    with pytest.raises(ValueError, match="must total 100"):
        ActivityAllocation(
            development=50,
            unit_testing=20,
            bug_fixing=10,
            integration_testing=10,
        )


def test_duplicate_dismissals_are_rejected() -> None:
    allocation = ActivityAllocation(
        development=100,
        unit_testing=0,
        bug_fixing=0,
        integration_testing=0,
    )
    with pytest.raises(ValueError, match="cannot be dismissed more than once"):
        WeeklyDecision(allocation=allocation, dismiss_employee_ids=("one", "one"))


def test_meeting_and_training_hours_cannot_be_negative() -> None:
    allocation = ActivityAllocation(100, 0, 0, 0)
    with pytest.raises(ValueError, match="cannot be negative"):
        WeeklyDecision(allocation=allocation, meeting_hours_per_employee=-1)
