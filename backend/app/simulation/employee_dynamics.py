from dataclasses import dataclass, replace
from statistics import mean

from app.simulation.models import Employee, EmployeeType, SimulationState


@dataclass(frozen=True, slots=True)
class EmployeeDynamicsRules:
    stress_overtime_increase: float = 0.05
    overtime_motivation_decrease: float = 0.02
    stress_weekend_reduction: float = 0.20
    solo_stress_increase: float = 0.05
    meeting_familiarity_increase: float = 0.05
    training_skill_increase_rate: float = 0.10
    training_motivation_boost: float = 0.10

    def __post_init__(self) -> None:
        values = (
            self.stress_overtime_increase,
            self.overtime_motivation_decrease,
            self.stress_weekend_reduction,
            self.solo_stress_increase,
            self.meeting_familiarity_increase,
            self.training_skill_increase_rate,
            self.training_motivation_boost,
        )
        if any(value < 0 for value in values):
            raise ValueError("employee dynamics rates cannot be negative")


def update_employee_dynamics(
    state: SimulationState,
    *,
    employee_types: tuple[EmployeeType, ...],
    overtime_hours_per_employee: float,
    meeting_hours_per_employee: float,
    training_hours_per_employee: float,
    rules: EmployeeDynamicsRules,
) -> SimulationState:
    """Apply weekly overtime, recovery, meetings, training, and solo-team effects."""
    if not state.employees:
        return state
    types_by_code = {employee_type.code: employee_type for employee_type in employee_types}
    effective_throughputs = [
        _average_throughput(types_by_code, employee) * (1 + employee.experience)
        for employee in state.employees
    ]
    team_average = mean(effective_throughputs)
    updated: list[Employee] = []
    for employee, effective_throughput in zip(state.employees, effective_throughputs, strict=True):
        positive_overtime = max(0, overtime_hours_per_employee)
        stress = employee.stress + positive_overtime * rules.stress_overtime_increase
        stress -= rules.stress_weekend_reduction
        if len(state.employees) == 1:
            stress += rules.solo_stress_increase

        motivation = employee.motivation - (positive_overtime * rules.overtime_motivation_decrease)
        experience = employee.experience
        if training_hours_per_employee > 0 and effective_throughput < team_average:
            gap = team_average - effective_throughput
            experience += (
                gap
                * rules.training_skill_increase_rate
                * training_hours_per_employee
                / (1 + employee.experience) ** 2
            )
            motivation += rules.training_motivation_boost * training_hours_per_employee

        familiarity = employee.familiarity + (
            meeting_hours_per_employee * rules.meeting_familiarity_increase
        )
        updated.append(
            replace(
                employee,
                stress=_bounded(stress),
                motivation=_bounded(motivation),
                familiarity=_bounded(familiarity),
                experience=experience,
            )
        )
    return replace(state, employees=tuple(updated))


def _average_throughput(
    types_by_code: dict[str, EmployeeType],
    employee: Employee,
) -> float:
    try:
        throughput = types_by_code[employee.employee_type_code].throughput
    except KeyError as error:
        raise ValueError(f"unknown employee type: {employee.employee_type_code}") from error
    return mean((throughput.easy, throughput.medium, throughput.hard))


def _bounded(value: float) -> float:
    return min(1, max(0, value))
