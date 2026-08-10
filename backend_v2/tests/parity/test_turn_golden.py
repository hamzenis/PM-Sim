import json
from pathlib import Path

from app.parity.comparison import compare_snapshots
from app.parity.snapshots import turn_snapshot
from app.simulation.engine import create_initial_state
from app.simulation.models import (
    ActivityAllocation,
    EmployeeType,
    HireRequest,
    Throughput,
    WeeklyDecision,
)
from app.simulation.randomness import RecordedRandomSource
from app.simulation.turn import TurnRules, process_week

FIXTURE = Path(__file__).parent / "fixtures" / "simplified_turn_golden.json"


def test_approved_simplified_turn_matches_golden_contract() -> None:
    initial = create_initial_state(
        total_tasks=40,
        difficulty_weights=(0.25, 0.5, 0.25),
        budget=10_000,
        working_days=7,
    )
    decision = WeeklyDecision(
        allocation=ActivityAllocation(100, 0, 0, 0),
        hires=(HireRequest("developer", 1),),
    )
    result = process_week(
        initial,
        decision=decision,
        employee_types=(
            EmployeeType(
                code="developer",
                name="Developer",
                cost_per_day=100,
                throughput=Throughput(easy=4, medium=2, hard=1),
                error_rate=0,
                management_skill=1,
            ),
        ),
        rules=TurnRules(randomness="none"),
        random=RecordedRandomSource(probabilities=[0.99] * 20),
        new_employee_id=lambda: "employee-1",
    )
    actual = turn_snapshot(initial_state=initial, decision=decision, result=result)
    expected = json.loads(FIXTURE.read_text())
    assert compare_snapshots(expected, actual) == []
