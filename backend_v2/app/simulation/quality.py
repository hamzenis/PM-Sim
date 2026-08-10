from dataclasses import dataclass, replace

from app.simulation.models import Difficulty, EmployeeType, SimulationState, TaskPool
from app.simulation.randomness import RandomSource


@dataclass(frozen=True, slots=True)
class DifficultyProbabilities:
    easy: float
    medium: float
    hard: float

    def for_difficulty(self, difficulty: Difficulty) -> float:
        return {
            Difficulty.EASY: self.easy,
            Difficulty.MEDIUM: self.medium,
            Difficulty.HARD: self.hard,
        }[difficulty]


@dataclass(frozen=True, slots=True)
class DevelopmentResult:
    state: SimulationState
    completed: TaskPool
    bugs_created: TaskPool
    incorrect_specifications_created: TaskPool


def bug_probabilities(
    state: SimulationState,
    *,
    employee_types: tuple[EmployeeType, ...],
) -> DifficultyProbabilities:
    """Calculate team defect probabilities weighted by difficulty productivity."""
    types_by_code = {employee_type.code: employee_type for employee_type in employee_types}

    def for_difficulty(difficulty: Difficulty) -> float:
        weighted_probability = 0.0
        total_weight = 0.0
        for employee in state.employees:
            try:
                employee_type = types_by_code[employee.employee_type_code]
            except KeyError as error:
                raise ValueError(f"unknown employee type: {employee.employee_type_code}") from error
            weight = employee_type.throughput.for_difficulty(difficulty)
            probability = (employee_type.error_rate + employee.stress) / 3
            weighted_probability += weight * min(1, max(0, probability))
            total_weight += weight
        return weighted_probability / total_weight if total_weight else 0

    return DifficultyProbabilities(
        easy=for_difficulty(Difficulty.EASY),
        medium=for_difficulty(Difficulty.MEDIUM),
        hard=for_difficulty(Difficulty.HARD),
    )


def incorrect_specification_probability(
    state: SimulationState,
    *,
    employee_types: tuple[EmployeeType, ...],
) -> float:
    """Preserve the legacy weighted team-management calculation."""
    types_by_code = {employee_type.code: employee_type for employee_type in employee_types}
    weighted_quality = 0.0
    total_weight = 0.0
    for employee in state.employees:
        try:
            employee_type = types_by_code[employee.employee_type_code]
        except KeyError as error:
            raise ValueError(f"unknown employee type: {employee.employee_type_code}") from error
        weight = 1 + employee.experience + employee.motivation / 2
        weighted_quality += weight * employee_type.management_skill
        total_weight += weight
    management_quality = weighted_quality / total_weight if total_weight else 0
    return 1 - min(1, max(0, management_quality))


def apply_development_result(
    state: SimulationState,
    *,
    completed: TaskPool,
    defect_probabilities: DifficultyProbabilities,
    specification_failure_probability: float,
    random: RandomSource,
) -> DevelopmentResult:
    """Move completed work out of the backlog and record its hidden quality state."""
    if not 0 <= specification_failure_probability <= 1:
        raise ValueError("specification failure probability must be between zero and one")
    remaining = state.tasks_todo.minus(completed)
    bugs = _sample_task_pool(completed, defect_probabilities, random)
    specification_failures = _sample_uniform_pool(
        completed, specification_failure_probability, random
    )
    updated = replace(
        state,
        tasks_todo=remaining,
        tasks_completed=state.tasks_completed.plus(completed),
        undiscovered_bugs=state.undiscovered_bugs.plus(bugs),
        incorrect_specifications=state.incorrect_specifications.plus(specification_failures),
    )
    return DevelopmentResult(
        state=updated,
        completed=completed,
        bugs_created=bugs,
        incorrect_specifications_created=specification_failures,
    )


def _sample_task_pool(
    tasks: TaskPool,
    probabilities: DifficultyProbabilities,
    random: RandomSource,
) -> TaskPool:
    return TaskPool(
        easy=_successes(tasks.easy, probabilities.easy, random),
        medium=_successes(tasks.medium, probabilities.medium, random),
        hard=_successes(tasks.hard, probabilities.hard, random),
    )


def _sample_uniform_pool(tasks: TaskPool, probability: float, random: RandomSource) -> TaskPool:
    return TaskPool(
        easy=_successes(tasks.easy, probability, random),
        medium=_successes(tasks.medium, probability, random),
        hard=_successes(tasks.hard, probability, random),
    )


def _successes(count: int, probability: float, random: RandomSource) -> int:
    if not 0 <= probability <= 1:
        raise ValueError("task probability must be between zero and one")
    if probability == 0 or count == 0:
        return 0
    if probability == 1:
        return count
    return sum(random.probability(probability) for _ in range(count))
