import json
from pathlib import Path

from app.parity.legacy_math import (
    bug_probability,
    limit_score,
    management_skill,
    meetings_per_day,
    overtime_stress,
    quality_score,
    task_capacity,
    weekend_stress,
)

FIXTURE = Path(__file__).parent / "fixtures" / "legacy_math_golden.json"


def test_transcribed_legacy_formulas_match_characterization_fixture() -> None:
    actual = {
        "capacity_none": _capacity("none"),
        "capacity_semi": _capacity("semi"),
        "capacity_full": _capacity("full"),
        "bug_probability": bug_probability(error_rate=0.1, stress=0.2, error_adjustment=-0.15),
        "management_skill": management_skill([(0, 0.75, 50), (1, 0.5, 70)]),
        "meetings": meetings_per_day(meetings=7, days=3),
        "overtime_stress": overtime_stress(stress=0.2, overtime=2, increase_rate=0.05),
        "weekend_stress": weekend_stress(stress=0.1, reduction=0.15),
        "quality_score": quality_score(tasks=100, rejected=20, limit=100, exponent=1),
        "late_score": limit_score(actual=116, target=100, limit=100, exponent=1),
    }
    actual = json.loads(json.dumps(actual))
    expected = json.loads(FIXTURE.read_text())
    assert actual == expected


def _capacity(randomness: str) -> int:
    return task_capacity(
        hours=8,
        team_size=3,
        familiarity=0.2,
        motivation=0.75,
        stress=0.2,
        throughput=1,
        experience=0,
        randomness=randomness,
        poisson_value=6,
    )
