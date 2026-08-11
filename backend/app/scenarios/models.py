import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.authored_content.constants import (
    AUTHORED_ID_PATTERN,
    EFFECT_PAYLOAD_MAX_BYTES,
    SHORT_TEXT_MAX_LENGTH,
)

Probability = Annotated[float, Field(ge=0, le=1)]
NonNegative = Annotated[float, Field(ge=0)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


AuthoredId = Annotated[str, Field(pattern=AUTHORED_ID_PATTERN)]
BoundedText = Annotated[str, Field(min_length=1, max_length=SHORT_TEXT_MAX_LENGTH)]


class RunStartedTrigger(StrictModel):
    type: Literal["run_started"]


class BeforeWeekTrigger(StrictModel):
    type: Literal["before_week"]
    week: int = Field(ge=1)


class AfterWeekTrigger(StrictModel):
    type: Literal["after_week"]
    week: int = Field(ge=1)


class RunFinishedTrigger(StrictModel):
    type: Literal["run_finished"]


AuthoredTrigger = Annotated[
    RunStartedTrigger | BeforeWeekTrigger | AfterWeekTrigger | RunFinishedTrigger,
    Field(discriminator="type"),
]


class _EffectPayload(StrictModel):
    @model_validator(mode="after")
    def enforce_payload_boundary(self) -> "_EffectPayload":
        encoded = json.dumps(self.model_dump(mode="json"), separators=(",", ":")).encode()
        if len(encoded) > EFFECT_PAYLOAD_MAX_BYTES:
            raise ValueError(f"effect payload exceeds {EFFECT_PAYLOAD_MAX_BYTES} bytes")
        forbidden = {
            "budget", "day", "week", "tasks", "employees", "quality", "score",
            "state", "simulation_state", "randomness", "outcome", "path", "command",
            "expression", "script", "code", "value_path", "target",
        }
        if forbidden.intersection(self.model_fields_set):
            raise ValueError("effect payload contains state or executable semantics")
        return self


class MessagePayload(_EffectPayload):
    text: BoundedText


class FragmentPresentationPayload(_EffectPayload):
    fragment_id: AuthoredId


class QuestionPresentationPayload(_EffectPayload):
    question_id: AuthoredId


class PresentationFlagPayload(_EffectPayload):
    flag: AuthoredId
    value: bool


class PresentationThemePayload(_EffectPayload):
    theme: AuthoredId


class ShowMessageEffect(StrictModel):
    type: Literal["show_message"]
    payload: MessagePayload


class ShowFragmentEffect(StrictModel):
    type: Literal["show_fragment"]
    payload: FragmentPresentationPayload


class ShowQuestionEffect(StrictModel):
    type: Literal["show_question"]
    payload: QuestionPresentationPayload


class SetPresentationFlagEffect(StrictModel):
    type: Literal["set_presentation_flag"]
    payload: PresentationFlagPayload


class SetPresentationThemeEffect(StrictModel):
    type: Literal["set_presentation_theme"]
    payload: PresentationThemePayload


PresentationEffect = Annotated[
    ShowMessageEffect | ShowFragmentEffect | ShowQuestionEffect | SetPresentationFlagEffect
    | SetPresentationThemeEffect,
    Field(discriminator="type"),
]


class NarrativeFragmentDefinition(StrictModel):
    id: AuthoredId
    title: BoundedText | None = None
    body: BoundedText
    required: bool = False


class QuestionOptionDefinition(StrictModel):
    id: AuthoredId
    label: BoundedText


class QuestionDefinition(StrictModel):
    id: AuthoredId
    prompt: BoundedText
    answer_schema: Literal["single_choice", "multiple_choice", "boolean", "short_text"]
    options: list[QuestionOptionDefinition] = Field(default_factory=list)
    feedback_by_option: dict[AuthoredId, BoundedText] = Field(default_factory=dict)
    scoring: None = None
    required: bool = True
    answer_once: Literal[True] = True
    short_text_max_length: int | None = Field(default=None, ge=1, le=SHORT_TEXT_MAX_LENGTH)

    @model_validator(mode="after")
    def validate_answer_shape(self) -> "QuestionDefinition":
        choice = self.answer_schema in {"single_choice", "multiple_choice"}
        if choice and len(self.options) < 2:
            raise ValueError("choice questions require at least two options")
        if not choice and self.options:
            raise ValueError("boolean and short-text questions cannot have options")
        ids = [option.id for option in self.options]
        if len(ids) != len(set(ids)):
            raise ValueError("question option IDs must be unique")
        if not set(self.feedback_by_option).issubset(ids):
            raise ValueError("feedback_by_option keys must identify an option")
        if self.short_text_max_length is not None and self.answer_schema != "short_text":
            raise ValueError("short_text_max_length is only valid for short text")
        return self


class AuthoredEventDefinition(StrictModel):
    id: AuthoredId
    effects: list[PresentationEffect] = Field(min_length=1)
    professor_only: bool = False


class SequenceEntryDefinition(StrictModel):
    id: AuthoredId
    trigger: AuthoredTrigger
    fragment_id: AuthoredId | None = None
    question_id: AuthoredId | None = None
    event_id: AuthoredId | None = None
    depends_on: list[AuthoredId] = Field(default_factory=list)

    @model_validator(mode="after")
    def exactly_one_reference(self) -> "SequenceEntryDefinition":
        if sum(ref is not None for ref in (self.fragment_id, self.question_id, self.event_id)) != 1:
            raise ValueError("sequence entries require exactly one object reference")
        if len(self.depends_on) != len(set(self.depends_on)):
            raise ValueError("entry dependencies must be unique")
        if self.id in self.depends_on:
            raise ValueError("an entry cannot depend on itself")
        return self


class AuthoredContentDefinition(StrictModel):
    fragments: list[NarrativeFragmentDefinition]
    questions: list[QuestionDefinition]
    events: list[AuthoredEventDefinition]
    sequence: list[SequenceEntryDefinition]

    @model_validator(mode="after")
    def validate_content_graph(self) -> "AuthoredContentDefinition":
        objects = [*self.fragments, *self.questions, *self.events]
        all_ids = [item.id for item in objects] + [entry.id for entry in self.sequence]
        if len(all_ids) != len(set(all_ids)):
            raise ValueError("authored object and entry IDs must be globally unique")
        object_ids = {item.id for item in objects}
        refs = [entry.fragment_id or entry.question_id or entry.event_id for entry in self.sequence]
        if any(ref not in object_ids for ref in refs):
            raise ValueError("sequence entry contains an unresolved object reference")
        if len(refs) != len(set(refs)):
            raise ValueError("authored objects may be referenced only once")
        entry_by_id = {entry.id: entry for entry in self.sequence}
        for entry in self.sequence:
            if any(dependency not in entry_by_id for dependency in entry.depends_on):
                raise ValueError("entry contains an unknown dependency")
            for dependency in entry.depends_on:
                if _checkpoint(entry_by_id[dependency].trigger) > _checkpoint(entry.trigger):
                    raise ValueError("dependency trigger occurs after dependent trigger")
        visiting: set[str] = set()
        visited: set[str] = set()
        def visit(entry_id: str) -> None:
            if entry_id in visiting:
                raise ValueError("entry dependencies must be acyclic")
            if entry_id in visited:
                return
            visiting.add(entry_id)
            for dependency in entry_by_id[entry_id].depends_on:
                visit(dependency)
            visiting.remove(entry_id)
            visited.add(entry_id)
        for entry_id in entry_by_id:
            visit(entry_id)
        return self


def _checkpoint(trigger: AuthoredTrigger) -> tuple[int, int]:
    if trigger.type == "run_started":
        return (0, 0)
    if trigger.type == "before_week":
        return (trigger.week, 0)
    if trigger.type == "after_week":
        return (trigger.week, 1)
    return (2**63, 0)


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
    overtime_motivation_decrease: Probability = 0.02
    solo_stress_increase: Probability = 0.05
    meeting_familiarity_increase: Probability = 0.05
    training_skill_increase_rate: NonNegative = 0.10
    training_motivation_boost: Probability = 0.10
    integration_test_days: int = Field(default=1, ge=0)


class ScoringDefinition(StrictModel):
    quality_limit: int = Field(default=100, ge=0)
    time_limit: int = Field(default=100, ge=0)
    budget_limit: int = Field(default=100, ge=0)
    quality_exponent: NonNegative = 1
    time_exponent: NonNegative = 1
    budget_exponent: NonNegative = 1


class ScenarioDefinition(StrictModel):
    schema_version: Literal[1]
    name: str = Field(min_length=1)
    description: str = Field(
        default="",
        description=(
            "Presentation-only scenario briefing shown to players before and during a run. "
            "It does not affect simulation behavior."
        ),
    )
    project: ProjectDefinition
    tasks: TaskDefinition
    employee_types: list[EmployeeTypeDefinition] = Field(min_length=1)
    rules: RuleDefinition = Field(default_factory=RuleDefinition)
    scoring: ScoringDefinition = Field(default_factory=ScoringDefinition)
    authored_content: AuthoredContentDefinition

    @model_validator(mode="after")
    def employee_codes_are_unique(self) -> "ScenarioDefinition":
        codes = [employee.code for employee in self.employee_types]
        if len(codes) != len(set(codes)):
            raise ValueError("employee type codes must be unique")
        return self
