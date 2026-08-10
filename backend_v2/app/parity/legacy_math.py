"""Pure-Python transcription of legacy formulas for characterization tests.

These functions intentionally reproduce legacy behavior, including unusual rounding.
They are evidence for parity work and are not used by the new simulation engine.
"""

from math import floor


def communication_channels(team_size: int) -> int:
    if team_size < 0:
        raise ValueError("team size cannot be negative")
    return team_size * (team_size - 1) // 2


def team_efficiency(team_size: int) -> float:
    return 1 / (1 + (communication_channels(team_size) / 20 - 0.05))


def member_efficiency(*, familiarity: float, motivation: float, stress: float) -> float:
    optimal_stress_contribution = 1 - abs(stress - 0.2)
    return (familiarity + motivation + optimal_stress_contribution) / 3


def task_capacity(
    *,
    hours: int,
    team_size: int,
    familiarity: float,
    motivation: float,
    stress: float,
    throughput: float,
    experience: float,
    randomness: str,
    poisson_value: int = 0,
) -> int:
    member = member_efficiency(
        familiarity=familiarity,
        motivation=motivation,
        stress=stress,
    )
    combined = (member + team_efficiency(team_size)) / 2
    mu = hours * combined * (throughput + experience)
    if randomness == "none":
        return round(mu * 0.2)
    if randomness == "semi":
        return round(((poisson_value + mu) / 2) * 0.2)
    if randomness == "full":
        return round(poisson_value * 0.2)
    raise ValueError(f"unknown randomness mode: {randomness}")


def solve_task_adjustments(
    *,
    development_quality: int,
    difficulty: int,
    motivation: float,
) -> tuple[float, float]:
    skill_match = development_quality - (difficulty / 3) * 100
    difficulty_adjustment = abs(skill_match) / 100 * 0.01
    motivation_change = round(0.005 - difficulty_adjustment, 4)
    return min(motivation + motivation_change, 1), min(0, skill_match / 100)


def bug_probability(*, error_rate: float, stress: float, error_adjustment: float) -> float:
    return (error_rate + stress - error_adjustment) / 3


def management_skill(
    members: list[tuple[float, float, int]],
) -> float:
    """Members contain (experience, motivation, management_quality_percent)."""
    if not members:
        return 0
    weighted_quality = 0.0
    total_weight = 0.0
    for experience, motivation, quality_percent in members:
        weight = 1 + experience + motivation / 2
        weighted_quality += weight * (quality_percent / 100)
        total_weight += weight
    return min(1, max(0, weighted_quality / total_weight)) if total_weight else 0


def meetings_per_day(*, meetings: int, days: int) -> tuple[int, ...]:
    per_day = floor(meetings / days)
    remainder = meetings % days
    return tuple(per_day + (1 if day < remainder else 0) for day in range(days))


def overtime_stress(*, stress: float, overtime: int, increase_rate: float) -> float:
    return max(0, min(1, stress + overtime * increase_rate))


def weekend_stress(*, stress: float, reduction: float) -> float:
    return max(0, stress - reduction)


def training_gain(
    *,
    member_throughput: float,
    team_mean_throughput: float,
    experience: float,
    increase_rate: float,
    motivation: float,
) -> tuple[float, float]:
    delta = team_mean_throughput - member_throughput * (1 + experience)
    if delta <= 0:
        return experience, motivation
    experience += delta * increase_rate / (1 + experience) ** 2
    return experience, min(1, motivation + 0.1)


def quality_score(*, tasks: int, rejected: int, limit: int, exponent: float) -> int:
    if tasks == 0:
        return 0
    return int((1 - rejected / tasks) ** exponent * limit)


def limit_score(*, actual: float, target: float, limit: int, exponent: float) -> float:
    if target == 0:
        return 0
    if actual <= target:
        return limit
    exceeded_percent = (actual / target - 1) * 100
    return max(0, int(100 - exceeded_percent**exponent)) * limit / 100
