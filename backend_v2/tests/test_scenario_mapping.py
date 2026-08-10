from pathlib import Path

from app.scenarios.models import ScenarioDefinition
from app.scenarios.to_simulation import turn_rules_from_scenario


def test_scenario_rules_map_to_framework_independent_turn_rules() -> None:
    definition = ScenarioDefinition.model_validate_json(
        Path("scenario_examples/basic_project.json").read_text()
    )
    rules = turn_rules_from_scenario(definition)
    assert rules.randomness == "full"
    assert rules.working_days_per_week == 5
    assert rules.hours_per_day == 8
    assert rules.employee_dynamics.stress_overtime_increase == 0.05
