from app.scenarios.models import ScenarioDefinition
from app.simulation.employee_dynamics import EmployeeDynamicsRules
from app.simulation.engine import create_initial_state
from app.simulation.models import EmployeeType, SimulationState, Throughput
from app.simulation.results import ScoreRules
from app.simulation.turn import TurnRules


def initial_state_from_scenario(scenario: ScenarioDefinition) -> SimulationState:
    distribution = scenario.tasks.difficulty_distribution
    return create_initial_state(
        total_tasks=scenario.tasks.total,
        difficulty_weights=(distribution.easy, distribution.medium, distribution.hard),
        budget=scenario.project.budget,
        working_days=scenario.project.working_days,
    )


def employee_types_from_scenario(scenario: ScenarioDefinition) -> tuple[EmployeeType, ...]:
    return tuple(
        EmployeeType(
            code=definition.code,
            name=definition.name,
            cost_per_day=definition.cost_per_day,
            throughput=Throughput(
                easy=definition.throughput.easy,
                medium=definition.throughput.medium,
                hard=definition.throughput.hard,
            ),
            error_rate=definition.error_rate,
            management_skill=definition.management_skill,
        )
        for definition in scenario.employee_types
    )


def turn_rules_from_scenario(scenario: ScenarioDefinition) -> TurnRules:
    rules = scenario.rules
    return TurnRules(
        randomness=rules.randomness,
        working_days_per_week=scenario.project.working_days_per_week,
        hours_per_day=scenario.project.hours_per_day,
        employee_dynamics=EmployeeDynamicsRules(
            stress_overtime_increase=rules.stress_overtime_increase,
            overtime_motivation_decrease=rules.overtime_motivation_decrease,
            stress_weekend_reduction=rules.stress_weekend_reduction,
            solo_stress_increase=rules.solo_stress_increase,
            meeting_familiarity_increase=rules.meeting_familiarity_increase,
            training_skill_increase_rate=rules.training_skill_increase_rate,
            training_motivation_boost=rules.training_motivation_boost,
        ),
    )


def score_rules_from_scenario(scenario: ScenarioDefinition) -> ScoreRules:
    scoring = scenario.scoring
    return ScoreRules(
        quality_limit=scoring.quality_limit,
        time_limit=scoring.time_limit,
        budget_limit=scoring.budget_limit,
        quality_exponent=scoring.quality_exponent,
        time_exponent=scoring.time_exponent,
        budget_exponent=scoring.budget_exponent,
    )
