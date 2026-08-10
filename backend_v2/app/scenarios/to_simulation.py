from app.scenarios.models import ScenarioDefinition
from app.simulation.engine import create_initial_state
from app.simulation.models import EmployeeType, SimulationState, Throughput


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
