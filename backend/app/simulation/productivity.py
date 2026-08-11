from dataclasses import dataclass
from math import floor

from app.simulation.models import Difficulty, Employee, EmployeeType, SimulationState, TaskPool
from app.simulation.randomness import RandomSource


@dataclass(frozen=True, slots=True)
class ExpectedTaskOutput:
    easy: float
    medium: float
    hard: float


def member_efficiency(employee: Employee, *, ideal_stress: float = 0.2) -> float:
    """Calculate the established familiarity, motivation, and stress relationship."""
    stress_contribution = 1 - abs(employee.stress - ideal_stress)
    return max(
        0,
        min(1, (employee.familiarity + employee.motivation + stress_contribution) / 3),
    )


def team_efficiency(team_size: int) -> float:
    """Model communication overhead using the communication-channel curve."""
    if team_size < 0:
        raise ValueError("team size cannot be negative")
    channels = team_size * (team_size - 1) / 2
    return min(1, 1 / (1 + channels / 20 - 0.05))


def expected_development_output(
    state: SimulationState,
    *,
    employee_types: tuple[EmployeeType, ...],
    development_hours: float,
) -> ExpectedTaskOutput:
    """Automatically spread development time across the remaining difficulty mix."""
    return expected_output_for_tasks(
        state,
        employee_types=employee_types,
        work_hours=development_hours,
        available=state.tasks_todo,
    )


def expected_output_for_tasks(
    state: SimulationState,
    *,
    employee_types: tuple[EmployeeType, ...],
    work_hours: float,
    available: TaskPool,
) -> ExpectedTaskOutput:
    """Spread team time across an anonymous pool and calculate expected actions."""
    if work_hours < 0:
        raise ValueError("work hours cannot be negative")
    if not state.employees or work_hours == 0 or available.total == 0:
        return ExpectedTaskOutput(easy=0, medium=0, hard=0)

    types_by_code = {employee_type.code: employee_type for employee_type in employee_types}
    hours_per_employee = work_hours / len(state.employees)
    difficulty_shares = {
        Difficulty.EASY: available.easy / available.total,
        Difficulty.MEDIUM: available.medium / available.total,
        Difficulty.HARD: available.hard / available.total,
    }
    output = {difficulty: 0.0 for difficulty in Difficulty}
    communication_efficiency = team_efficiency(len(state.employees))

    for employee in state.employees:
        try:
            employee_type = types_by_code[employee.employee_type_code]
        except KeyError as error:
            raise ValueError(f"unknown employee type: {employee.employee_type_code}") from error
        combined_efficiency = (member_efficiency(employee) + communication_efficiency) / 2
        experience_multiplier = 1 + employee.experience
        for difficulty in Difficulty:
            difficulty_hours = hours_per_employee * difficulty_shares[difficulty]
            base_tasks = difficulty_hours / 8 * employee_type.throughput.for_difficulty(difficulty)
            output[difficulty] += base_tasks * combined_efficiency * experience_multiplier

    return ExpectedTaskOutput(
        easy=output[Difficulty.EASY],
        medium=output[Difficulty.MEDIUM],
        hard=output[Difficulty.HARD],
    )


def realize_task_output(
    expected: ExpectedTaskOutput,
    *,
    randomness: str,
    random: RandomSource,
    available: TaskPool,
) -> TaskPool:
    """Convert expected productivity to discrete tasks using the scenario random mode."""
    if randomness not in {"full", "semi", "none"}:
        raise ValueError(f"unknown randomness mode: {randomness}")

    def realize(value: float, maximum: int) -> int:
        if value <= 0 or maximum == 0:
            return 0
        if randomness == "none":
            completed = _round_half_up(value)
        else:
            sampled = random.poisson(value)
            completed = sampled if randomness == "full" else _round_half_up((sampled + value) / 2)
        return min(maximum, completed)

    return TaskPool(
        easy=realize(expected.easy, available.easy),
        medium=realize(expected.medium, available.medium),
        hard=realize(expected.hard, available.hard),
    )


def _round_half_up(value: float) -> int:
    return floor(value + 0.5)
