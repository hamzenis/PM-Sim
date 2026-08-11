import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.authored_content.constants import EFFECT_PAYLOAD_MAX_BYTES
from app.scenarios.models import ScenarioDefinition


def example() -> dict[str, object]:
    return json.loads(Path("scenario_examples/authored_content_comprehensive.json").read_text())


def assert_invalid(definition: dict[str, object], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        ScenarioDefinition.model_validate(definition)


def test_comprehensive_authored_content_example_is_valid() -> None:
    content = ScenarioDefinition.model_validate(example()).authored_content
    assert len(content.questions) == 4
    assert content.events[-1].professor_only is True


@pytest.mark.parametrize("answer_schema", ["boolean", "short_text"])
def test_non_choice_questions_reject_options(answer_schema: str) -> None:
    definition = example()
    question = definition["authored_content"]["questions"][0]
    question["answer_schema"] = answer_schema
    assert_invalid(definition, "cannot have options")


def test_choice_question_requires_two_unique_options_and_valid_feedback() -> None:
    definition = example()
    definition["authored_content"]["questions"][0]["options"] = [
        {"id": "same", "label": "First"}, {"id": "same", "label": "Second"}
    ]
    assert_invalid(definition, "option IDs must be unique")

    definition = example()
    definition["authored_content"]["questions"][0]["feedback_by_option"] = {"missing": "No"}
    assert_invalid(definition, "must identify an option")


def test_scoring_and_answering_more_than_once_are_rejected() -> None:
    definition = example()
    definition["authored_content"]["questions"][0]["scoring"] = {"points": 1}
    assert_invalid(definition, "none_required")
    definition = example()
    definition["authored_content"]["questions"][0]["answer_once"] = False
    assert_invalid(definition, "literal_error")


@pytest.mark.parametrize("bad_reference", ["missing", None])
def test_sequence_requires_exactly_one_resolved_reference(bad_reference: str | None) -> None:
    definition = example()
    entry = definition["authored_content"]["sequence"][0]
    entry["fragment_id"] = bad_reference
    if bad_reference is None:
        assert_invalid(definition, "exactly one")
    else:
        assert_invalid(definition, "unresolved")


def test_duplicate_namespaces_and_repeated_references_are_rejected() -> None:
    definition = example()
    definition["authored_content"]["sequence"][0]["id"] = "briefing"
    assert_invalid(definition, "globally unique")
    definition = example()
    duplicate = copy.deepcopy(definition["authored_content"]["sequence"][0])
    duplicate["id"] = "another_entry"
    definition["authored_content"]["sequence"].append(duplicate)
    assert_invalid(definition, "referenced only once")


def test_dependency_resolution_self_cycle_and_checkpoint_ordering() -> None:
    definition = example()
    definition["authored_content"]["sequence"][0]["depends_on"] = ["missing"]
    assert_invalid(definition, "unknown dependency")
    definition = example()
    definition["authored_content"]["sequence"][0]["depends_on"] = ["s_briefing"]
    assert_invalid(definition, "cannot depend on itself")
    definition = example()
    definition["authored_content"]["sequence"][0]["depends_on"] = ["s_priority"]
    assert_invalid(definition, "acyclic")
    definition = example()
    definition["authored_content"]["sequence"][0]["depends_on"] = ["s_final"]
    assert_invalid(definition, "occurs after")


def test_invalid_trigger_unknown_effect_and_state_payload_are_rejected() -> None:
    definition = example()
    definition["authored_content"]["sequence"][0]["trigger"] = {"type": "during_week", "week": 1}
    assert_invalid(definition, "union_tag_invalid")
    definition = example()
    definition["authored_content"]["events"][0]["effects"][0] = {
        "type": "change_budget", "payload": {"budget": 10}
    }
    assert_invalid(definition, "union_tag_invalid")
    definition = example()
    definition["authored_content"]["events"][0]["effects"][0]["payload"]["budget"] = 10
    assert_invalid(definition, "extra_forbidden")


def test_effect_payload_is_bounded() -> None:
    definition = example()
    definition["authored_content"]["events"][0]["effects"][0]["payload"]["text"] = (
        "x" * (EFFECT_PAYLOAD_MAX_BYTES + 1)
    )
    assert_invalid(definition, "string_too_long")
