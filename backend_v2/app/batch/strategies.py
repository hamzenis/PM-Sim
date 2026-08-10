from dataclasses import dataclass
from typing import Protocol

from app.simulation.models import (
    ActivityAllocation,
    HireRequest,
    SimulationState,
    WeeklyDecision,
)


class DecisionStrategy(Protocol):
    """A deterministic policy used to choose one simulation week."""

    name: str

    def decide(self, state: SimulationState) -> WeeklyDecision: ...


@dataclass(frozen=True, slots=True)
class FixedAllocationStrategy:
    name: str
    employee_type_code: str
    allocation: ActivityAllocation
    initial_team_size: int = 3
    overtime_hours_per_employee: float = 0

    def __post_init__(self) -> None:
        if self.initial_team_size < 1:
            raise ValueError("initial team size must be positive")

    def decide(self, state: SimulationState) -> WeeklyDecision:
        hires = ()
        if state.week == 0 and not state.employees:
            hires = (HireRequest(self.employee_type_code, self.initial_team_size),)
        return WeeklyDecision(
            allocation=self.allocation,
            hires=hires,
            overtime_hours_per_employee=self.overtime_hours_per_employee,
        )


def built_in_strategy(
    name: str,
    *,
    employee_type_code: str,
    initial_team_size: int = 3,
) -> FixedAllocationStrategy:
    """Return one of the deliberately simple baseline comparison strategies."""
    allocations = {
        "development-first": (70, 15, 5, 10, 0),
        "balanced": (40, 25, 15, 20, 0),
        "quality-first": (25, 30, 20, 25, 0),
        "overtime-heavy": (40, 25, 15, 20, 8),
    }
    if name not in allocations:
        raise ValueError(f"unknown strategy: {name}")
    development, unit_testing, bug_fixing, integration_testing, overtime = allocations[name]
    return FixedAllocationStrategy(
        name=name,
        employee_type_code=employee_type_code,
        initial_team_size=initial_team_size,
        allocation=ActivityAllocation(
            development=development,
            unit_testing=unit_testing,
            bug_fixing=bug_fixing,
            integration_testing=integration_testing,
        ),
        overtime_hours_per_employee=overtime,
    )
