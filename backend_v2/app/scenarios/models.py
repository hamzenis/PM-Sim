from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Probability = Annotated[float, Field(ge=0, le=1)]
NonNegative = Annotated[float, Field(ge=0)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectDefinition(StrictModel):
    budget: NonNegative
    working_days: int = Field(gt=0)
    hours_per_day: int = Field(default=8, gt=0, le=24)
    working_days_per_week: int = Field(default=5, gt=0, le=7)


class DifficultyDistribution(StrictModel):
    easy: Probability = 0.25
    medium: Probability = 0.50
    hard: Probability = 0.25

    @model_validator(mode="after")
    def totals_one(self) -> "DifficultyDistribution":
        if abs(self.easy + self.medium + self.hard - 1.0) > 1e-9:
            raise ValueError("task difficulty distribution must total 1.0")
        return self


class TaskDefinition(StrictModel):
    total: int = Field(gt=0)
    difficulty_distribution: DifficultyDistribution = Field(default_factory=DifficultyDistribution)


class ThroughputDefinition(StrictModel):
    """Tasks completed per eight productive hours."""

    easy: NonNegative
    medium: NonNegative
    hard: NonNegative


class EmployeeTypeDefinition(StrictModel):
    code: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=1)
    cost_per_day: NonNegative
    throughput: ThroughputDefinition
    error_rate: Probability
    management_skill: Probability = 0


class RuleDefinition(StrictModel):
    randomness: Literal["full", "semi", "none"] = "full"
    stress_overtime_increase: Probability = 0.05
    stress_weekend_reduction: Probability = 0.20
    integration_test_days: int = Field(default=1, ge=0)


class ScenarioDefinition(StrictModel):
    schema_version: Literal[1]
    name: str = Field(min_length=1)
    description: str = ""
    project: ProjectDefinition
    tasks: TaskDefinition
    employee_types: list[EmployeeTypeDefinition] = Field(min_length=1)
    rules: RuleDefinition = Field(default_factory=RuleDefinition)

    @model_validator(mode="after")
    def employee_codes_are_unique(self) -> "ScenarioDefinition":
        codes = [employee.code for employee in self.employee_types]
        if len(codes) != len(set(codes)):
            raise ValueError("employee type codes must be unique")
        return self
