from app.authored_content.digests import turn_request_digest
from app.simulation.models import ActivityAllocation, HireRequest, WeeklyDecision
from app.simulations.service import canonical_turn_request


def _decision(*, hires=(), dismissals=()) -> WeeklyDecision:
    return WeeklyDecision(
        allocation=ActivityAllocation(50.0, 20.0, 20.0, 10.0),
        hires=hires,
        dismiss_employee_ids=dismissals,
    )


def test_turn_digest_treats_staffing_as_order_insensitive_sets() -> None:
    first = _decision(
        hires=(HireRequest("developer", 1), HireRequest("tester", 2)),
        dismissals=("b", "a"),
    )
    reordered = _decision(
        hires=(HireRequest("tester", 2), HireRequest("developer", 1)),
        dismissals=("a", "b"),
    )
    assert turn_request_digest(canonical_turn_request(first, 4)) == turn_request_digest(
        canonical_turn_request(reordered, 4)
    )


def test_turn_digest_includes_expected_version_and_semantic_numbers() -> None:
    decision = _decision()
    assert turn_request_digest(canonical_turn_request(decision, 4)) != turn_request_digest(
        canonical_turn_request(decision, 5)
    )
    changed = WeeklyDecision(
        allocation=ActivityAllocation(49.5, 20.5, 20.0, 10.0),
    )
    assert turn_request_digest(canonical_turn_request(decision, 4)) != turn_request_digest(
        canonical_turn_request(changed, 4)
    )
