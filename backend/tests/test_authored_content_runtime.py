import pytest

from app.authored_content.answers import AnswerError, normalize_answer
from app.authored_content.definitions import (
    from_pinned_revision,
    referenced_definition,
    student_safe_snapshot,
)
from app.authored_content.digests import canonical_json, definition_digest
from app.authored_content.effects import apply_effect
from app.authored_content.models import Checkpoint, RuntimeEntry, RuntimeStatus
from app.authored_content.replay import verify_replay
from app.authored_content.resolver import complete_delivery, resolve
from app.authored_content.visibility import serialize_student


def entry(id, *, ordinal, required=False, priority=0, depends_on=(), kind="event", checkpoint=None):
    return RuntimeEntry(
        id,
        checkpoint or Checkpoint("run_started"),
        ordinal,
        priority,
        required,
        kind,
        tuple(depends_on),
    )


def test_checkpoints_and_deterministic_required_resolution():
    assert Checkpoint.parse("before_week:2") < Checkpoint.parse("after_week:2")
    optional = entry("optional", ordinal=2)
    later = entry("later", ordinal=1, required=True, priority=2)
    first = entry("first", ordinal=4, required=True, priority=1)
    result = resolve([optional, later, first], Checkpoint("run_started"))
    assert [item.id for item in result.actionable] == ["optional", "first"]


def test_dependencies_and_delivery_semantics():
    dependent = entry("b", ordinal=1, depends_on=("a",))
    assert not resolve([entry("a", ordinal=0), dependent], Checkpoint("run_started")).actionable[1:]
    required = entry("f", ordinal=0, required=True, kind="fragment")
    required = resolve([required], Checkpoint("run_started")).actionable[0]
    assert complete_delivery(required).status == RuntimeStatus.ACTIONABLE
    assert complete_delivery(required, acknowledged=True).completed
    event = resolve([entry("e", ordinal=0)], Checkpoint("run_started")).actionable[0]
    assert complete_delivery(event).completed


@pytest.mark.parametrize(
    ("schema", "raw", "expected"),
    [
        ("single_choice", "b", "b"),
        ("multiple_choice", ["b", "a"], ["a", "b"]),
        ("boolean", False, False),
        ("short_text", "  raw text  ", "  raw text  "),
    ],
)
def test_all_answer_forms(schema, raw, expected):
    question = {
        "answer_schema": schema,
        "required": True,
        "options": [{"id": "a"}, {"id": "b"}],
        "short_text_max_length": 20,
    }
    assert normalize_answer(question, raw) == expected


def test_answers_are_strict_and_answer_once():
    question = {"answer_schema": "boolean", "required": True, "options": []}
    with pytest.raises(AnswerError):
        normalize_answer(question, 1)
    with pytest.raises(AnswerError, match="already"):
        normalize_answer(question, True, completed=True)


def test_canonical_digests_and_bounded_effects():
    assert canonical_json({"z": -0.0, "a": [True, None]}) == '{"a":[true,null],"z":0}'
    assert definition_digest({"a": 1, "b": 2}) == definition_digest({"b": 2.0, "a": 1})
    result = apply_effect(
        {}, {"type": "set_presentation_flag", "payload": {"flag": "x", "value": True}}
    )
    assert result.projection == {"flags": {"x": True}}
    with pytest.raises(ValueError, match="unapproved"):
        apply_effect({}, {"type": "change_budget", "payload": {"budget": 1}})


def test_student_visibility_is_title_only_and_filters_internals():
    content = {
        "id": "later",
        "title": "Later",
        "body": "secret",
        "visibility": "after_acknowledgement",
        "visibility_associated_entry_id": "required",
        "definition_snapshot": {"answer_key": "x"},
    }
    assert serialize_student([content]) == [{"id": "later", "title": "Later"}]
    visible = serialize_student([content], completed_ids={"required"})[0]
    assert visible["body"] == "secret"
    assert "definition_snapshot" not in visible


def test_run_finished_requires_terminal_status():
    item = {"id": "final", "visibility": "run_finished"}
    assert serialize_student([item], terminal=False) == []
    assert serialize_student([item], terminal=True)


def test_replay_reports_definition_and_checkpoint_divergence():
    lookups = from_pinned_revision(
        "revision-1",
        {
            "fragments": [{"id": "brief", "body": "Brief", "required": False}],
            "questions": [],
            "events": [],
            "sequence": [
                {"id": "entry", "trigger": {"type": "run_started"}, "fragment_id": "brief"}
            ],
        },
    )
    differences = verify_replay(
        lookups,
        [
            {
                "sequence_entry_id": "entry",
                "canonical_checkpoint": "after_week:1",
                "definition_digest": "bad",
                "status": "completed",
            }
        ],
    )
    assert {item.category for item in differences} == {"checkpoint", "definition_digest"}


def test_pinned_definition_lookups_are_deeply_immutable():
    lookups = from_pinned_revision(
        "revision-1",
        {
            "fragments": [],
            "questions": [
                {
                    "id": "q",
                    "prompt": "Pick",
                    "answer_schema": "single_choice",
                    "options": [{"id": "a", "label": "A"}],
                }
            ],
            "events": [],
            "sequence": [{"id": "entry", "trigger": {"type": "run_started"}, "question_id": "q"}],
        },
    )
    with pytest.raises(TypeError):
        lookups.questions["q"]["prompt"] = "changed"
    kind, definition = referenced_definition(lookups, lookups.sequence[0])
    assert student_safe_snapshot(kind, definition)["options"] == [{"id": "a", "label": "A"}]
