from dataclasses import dataclass
from enum import StrEnum


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass(frozen=True, slots=True)
class TaskPool:
    easy: int
    medium: int
    hard: int

    def __post_init__(self) -> None:
        if min(self.easy, self.medium, self.hard) < 0:
            raise ValueError("task counts cannot be negative")

    @property
    def total(self) -> int:
        return self.easy + self.medium + self.hard

    def plus(self, other: "TaskPool") -> "TaskPool":
        return TaskPool(
            easy=self.easy + other.easy,
            medium=self.medium + other.medium,
            hard=self.hard + other.hard,
        )

    def minus(self, other: "TaskPool") -> "TaskPool":
        return TaskPool(
            easy=self.easy - other.easy,
            medium=self.medium - other.medium,
            hard=self.hard - other.hard,
        )

    def contains(self, other: "TaskPool") -> bool:
        return self.easy >= other.easy and self.medium >= other.medium and self.hard >= other.hard


@dataclass(frozen=True, slots=True)
class Throughput:
    easy: float
    medium: float
    hard: float

    def __post_init__(self) -> None:
        if min(self.easy, self.medium, self.hard) < 0:
            raise ValueError("throughput cannot be negative")

    def for_difficulty(self, difficulty: Difficulty) -> float:
        return {
            Difficulty.EASY: self.easy,
            Difficulty.MEDIUM: self.medium,
            Difficulty.HARD: self.hard,
        }[difficulty]


@dataclass(frozen=True, slots=True)
class EmployeeType:
    code: str
    name: str
    cost_per_day: float
    throughput: Throughput
    error_rate: float
    management_skill: float = 0

    def __post_init__(self) -> None:
        if not self.code or not self.name:
            raise ValueError("employee type code and name are required")
        if self.cost_per_day < 0:
            raise ValueError("employee cost cannot be negative")
        if not 0 <= self.error_rate <= 1 or not 0 <= self.management_skill <= 1:
            raise ValueError("employee probabilities must be between zero and one")


@dataclass(frozen=True, slots=True)
class Employee:
    id: str
    employee_type_code: str
    motivation: float = 0.75
    stress: float = 0.10
    experience: float = 0
    familiarity: float = 0

    def __post_init__(self) -> None:
        if not self.id or not self.employee_type_code:
            raise ValueError("employee id and type are required")
        for name, value in (
            ("motivation", self.motivation),
            ("stress", self.stress),
            ("familiarity", self.familiarity),
        ):
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between zero and one")
        if self.experience < 0:
            raise ValueError("experience cannot be negative")


@dataclass(frozen=True, slots=True)
class SimulationState:
    week: int
    elapsed_working_days: int
    remaining_working_days: int
    initial_budget: float
    remaining_budget: float
    tasks_todo: TaskPool
    tasks_completed: TaskPool
    tasks_unit_tested: TaskPool
    tasks_integration_tested: TaskPool
    known_bugs: TaskPool
    undiscovered_bugs: TaskPool
    incorrect_specifications: TaskPool
    employees: tuple[Employee, ...] = ()

    def __post_init__(self) -> None:
        if self.week < 0 or self.elapsed_working_days < 0 or self.remaining_working_days < 0:
            raise ValueError("simulation time cannot be negative")
        if self.initial_budget < 0:
            raise ValueError("initial budget cannot be negative")
        if not self.tasks_completed.contains(self.tasks_unit_tested):
            raise ValueError("unit-tested tasks must be completed")
        if not self.tasks_unit_tested.contains(self.tasks_integration_tested):
            raise ValueError("integration-tested tasks must be unit tested")
        untested = self.tasks_completed.minus(self.tasks_unit_tested)
        tested_not_integrated = self.tasks_unit_tested.minus(self.tasks_integration_tested)
        if not untested.contains(self.undiscovered_bugs):
            raise ValueError("undiscovered bugs must belong to untested tasks")
        if not tested_not_integrated.contains(self.known_bugs):
            raise ValueError("known bugs must belong to unit-tested, unintegrated tasks")
        if not self.tasks_completed.contains(self.incorrect_specifications):
            raise ValueError("incorrect specifications cannot exceed completed tasks")

    @property
    def total_tasks(self) -> int:
        return self.tasks_todo.total + self.tasks_completed.total


@dataclass(frozen=True, slots=True)
class WeeklyCapacity:
    employee_count: int
    working_days: int = 5
    hours_per_day: int = 8
    overtime_hours_per_employee: float = 0

    def __post_init__(self) -> None:
        if self.employee_count < 0:
            raise ValueError("employee count cannot be negative")
        if self.working_days <= 0 or self.hours_per_day <= 0:
            raise ValueError("working days and hours per day must be positive")

    @property
    def total_hours(self) -> float:
        normal = self.employee_count * self.working_days * self.hours_per_day
        overtime = self.employee_count * self.overtime_hours_per_employee
        return max(0, normal + overtime)


@dataclass(frozen=True, slots=True)
class ActivityHours:
    development: float = 0
    unit_testing: float = 0
    bug_fixing: float = 0
    integration_testing: float = 0

    def __post_init__(self) -> None:
        values = (
            self.development,
            self.unit_testing,
            self.bug_fixing,
            self.integration_testing,
        )
        if min(values) < 0:
            raise ValueError("activity hours cannot be negative")

    @property
    def total(self) -> float:
        return self.development + self.unit_testing + self.bug_fixing + self.integration_testing


@dataclass(frozen=True, slots=True)
class ActivityAllocation:
    """Student-selected percentages of the team's available engineering time."""

    development: float
    unit_testing: float
    bug_fixing: float
    integration_testing: float

    def __post_init__(self) -> None:
        values = (
            self.development,
            self.unit_testing,
            self.bug_fixing,
            self.integration_testing,
        )
        if any(value < 0 or value > 100 for value in values):
            raise ValueError("activity percentages must be between zero and 100")
        if abs(sum(values) - 100) > 1e-9:
            raise ValueError("activity percentages must total 100")


@dataclass(frozen=True, slots=True)
class HireRequest:
    employee_type_code: str
    count: int

    def __post_init__(self) -> None:
        if not self.employee_type_code:
            raise ValueError("employee type code is required")
        if self.count <= 0:
            raise ValueError("hire count must be positive")


@dataclass(frozen=True, slots=True)
class WeeklyDecision:
    allocation: ActivityAllocation
    hires: tuple[HireRequest, ...] = ()
    dismiss_employee_ids: tuple[str, ...] = ()
    overtime_hours_per_employee: float = 0
    meeting_hours_per_employee: float = 0
    training_hours_per_employee: float = 0

    def __post_init__(self) -> None:
        if len(self.dismiss_employee_ids) != len(set(self.dismiss_employee_ids)):
            raise ValueError("an employee cannot be dismissed more than once")
        if self.meeting_hours_per_employee < 0 or self.training_hours_per_employee < 0:
            raise ValueError("meeting and training hours cannot be negative")
