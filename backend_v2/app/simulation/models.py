from dataclasses import dataclass


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
