from dataclasses import dataclass
from enum import StrEnum

from app.simulation.models import SimulationState


class SimulationOutcome(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    SUBMITTED = "submitted"
    DEADLINE_REACHED = "deadline_reached"


@dataclass(frozen=True, slots=True)
class ScoreRules:
    quality_limit: int = 100
    time_limit: int = 100
    budget_limit: int = 100
    quality_exponent: float = 1
    time_exponent: float = 1
    budget_exponent: float = 1

    def __post_init__(self) -> None:
        if min(self.quality_limit, self.time_limit, self.budget_limit) < 0:
            raise ValueError("score limits cannot be negative")
        if min(self.quality_exponent, self.time_exponent, self.budget_exponent) < 0:
            raise ValueError("score exponents cannot be negative")


@dataclass(frozen=True, slots=True)
class SimulationScore:
    quality: int
    time: int
    budget: int
    total: int


@dataclass(frozen=True, slots=True)
class SimulationResult:
    outcome: SimulationOutcome
    accepted_tasks: int
    rejected_tasks: int
    elapsed_working_days: int
    total_cost: float
    remaining_budget: float
    score: SimulationScore


def evaluate_outcome(
    state: SimulationState,
    *,
    submitted: bool = False,
) -> SimulationOutcome:
    if state.tasks_integration_tested.total == state.total_tasks:
        return SimulationOutcome.COMPLETED
    if submitted:
        return SimulationOutcome.SUBMITTED
    if state.remaining_working_days == 0:
        return SimulationOutcome.DEADLINE_REACHED
    return SimulationOutcome.ACTIVE


def build_simulation_result(
    state: SimulationState,
    *,
    rules: ScoreRules,
    submitted: bool = False,
) -> SimulationResult:
    accepted = state.tasks_integration_tested.total
    rejected = state.total_tasks - accepted
    total_cost = state.initial_budget - state.remaining_budget
    scheduled_days = state.elapsed_working_days + state.remaining_working_days
    score = calculate_score(
        accepted_tasks=accepted,
        total_tasks=state.total_tasks,
        actual_days=state.elapsed_working_days,
        scheduled_days=scheduled_days,
        cost=total_cost,
        budget=state.initial_budget,
        rules=rules,
    )
    return SimulationResult(
        outcome=evaluate_outcome(state, submitted=submitted),
        accepted_tasks=accepted,
        rejected_tasks=rejected,
        elapsed_working_days=state.elapsed_working_days,
        total_cost=total_cost,
        remaining_budget=state.remaining_budget,
        score=score,
    )


def calculate_score(
    *,
    accepted_tasks: int,
    total_tasks: int,
    actual_days: int,
    scheduled_days: int,
    cost: float,
    budget: float,
    rules: ScoreRules,
) -> SimulationScore:
    quality = _quality_score(accepted_tasks, total_tasks, rules)
    time = _limit_score(actual_days, scheduled_days, rules.time_limit, rules.time_exponent)
    budget_score = _limit_score(cost, budget, rules.budget_limit, rules.budget_exponent)
    maximum = rules.quality_limit + rules.time_limit + rules.budget_limit
    total = round((quality + time + budget_score) / maximum * 100) if maximum else 0
    return SimulationScore(quality=quality, time=time, budget=budget_score, total=total)


def _quality_score(accepted: int, total: int, rules: ScoreRules) -> int:
    if total <= 0:
        return 0
    accepted_ratio = min(1, max(0, accepted / total))
    return int(accepted_ratio**rules.quality_exponent * rules.quality_limit)


def _limit_score(actual: float, target: float, limit: int, exponent: float) -> int:
    if target <= 0:
        return 0
    if actual <= target:
        return limit
    exceeded_percent = (actual / target - 1) * 100
    remaining_percent = max(0, 100 - exceeded_percent**exponent)
    return round(remaining_percent * limit / 100)
