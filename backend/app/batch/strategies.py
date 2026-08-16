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
class TeamMemberCount:
    employee_type_code: str
    count: int

    def __post_init__(self) -> None:
        if not self.employee_type_code:
            raise ValueError("employee type code must not be empty")
        if self.count < 1:
            raise ValueError("employee count must be positive")


@dataclass(frozen=True, slots=True)
class FixedAllocationStrategy:
    name: str
    team_composition: tuple[TeamMemberCount, ...]
    allocation: ActivityAllocation
    overtime_hours_per_employee: float = 0

    def __post_init__(self) -> None:
        if not self.team_composition:
            raise ValueError("team composition must contain at least one employee")
        codes = [member.employee_type_code for member in self.team_composition]
        if len(codes) != len(set(codes)):
            raise ValueError("team composition employee type codes must be unique")

    def decide(self, state: SimulationState) -> WeeklyDecision:
        hires = ()
        if state.week == 0 and not state.employees:
            # Tuple order is part of the strategy input and is preserved for deterministic hiring.
            hires = tuple(
                HireRequest(member.employee_type_code, member.count)
                for member in self.team_composition
            )
        return WeeklyDecision(
            allocation=self.allocation,
            hires=hires,
            overtime_hours_per_employee=self.overtime_hours_per_employee,
        )


def built_in_strategy(
    name: str,
    *,
    team_composition: tuple[TeamMemberCount, ...],
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
        team_composition=team_composition,
        allocation=ActivityAllocation(
            development=development,
            unit_testing=unit_testing,
            bug_fixing=bug_fixing,
            integration_testing=integration_testing,
        ),
        overtime_hours_per_employee=overtime,
    )
