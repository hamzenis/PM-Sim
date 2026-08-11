from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import (
    AppliedPresentationEffectRecord,
    Base,
    ContentDeliveryRecord,
    ContentResponseRecord,
    ScenarioRecord,
    ScenarioRevisionRecord,
    SimulationRunRecord,
    SimulationTurnRecord,
    UserRecord,
)
from app.db.session import create_database_engine

NOW = datetime(2026, 8, 11, tzinfo=UTC)
DIGEST = "a" * 64


@pytest.fixture
def session(tmp_path):
    engine = create_database_engine(f"sqlite:///{tmp_path / 'content.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = UserRecord(
            id="user", username="student", password_hash="hash", role="student", created_at=NOW
        )
        scenario = ScenarioRecord(id="scenario", name="Scenario", created_at=NOW)
        revision = ScenarioRevisionRecord(
            id="revision",
            scenario=scenario,
            revision_number=1,
            schema_version=1,
            status="published",
            definition={},
            created_at=NOW,
        )
        db.add_all([user, revision])
        db.commit()
        run = SimulationRunRecord(
            id="run",
            user_id=user.id,
            scenario_revision_id=revision.id,
            status="active",
            seed=7,
            engine_version="1",
            current_state={},
            started_at=NOW,
        )
        db.add(run)
        db.commit()
        yield db
    engine.dispose()


def delivery(**overrides):
    values = {
        "run_id": "run",
        "sequence_entry_id": "entry",
        "canonical_checkpoint": "week:1:start",
        "sequence_ordinal": 2,
        "definition_snapshot": {"prompt": ["immutable", {"nested": True}]},
        "definition_digest": DIGEST,
        "status": "delivered",
        "delivered_at": NOW,
    }
    values.update(overrides)
    return ContentDeliveryRecord(**values)


def response(**overrides):
    values = {
        "run_id": "run",
        "sequence_entry_id": "entry",
        "response_version": 1,
        "normalized_answer": {"selected": [1, 3], "acknowledged": True},
        "command_kind": "answer",
        "request_digest": DIGEST,
        "idempotency_key": "response-key",
        "answered_at": NOW,
    }
    values.update(overrides)
    return ContentResponseRecord(**values)


def effect(**overrides):
    values = {
        "run_id": "run",
        "sequence_entry_id": "entry",
        "effect_index": 0,
        "effect_payload": {"operation": "set", "value": {"risk": 4}},
        "before_projection_digest": "b" * 64,
        "after_projection_digest": "c" * 64,
        "applied_at": NOW,
    }
    values.update(overrides)
    return AppliedPresentationEffectRecord(**values)


@pytest.mark.parametrize(
    ("first", "duplicate"),
    [
        (delivery(), delivery()),
        (response(), response(idempotency_key="different")),
        (response(), response(sequence_entry_id="other", idempotency_key="response-key")),
        (effect(), effect()),
    ],
    ids=["delivery-entry", "response-version", "response-idempotency", "effect-index"],
)
def test_content_unique_constraints(session, first, duplicate) -> None:
    session.add(first)
    session.commit()
    session.add(duplicate)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


@pytest.mark.parametrize(
    "record", [delivery(run_id="missing"), response(run_id="missing"), effect(run_id="missing")]
)
def test_content_run_foreign_keys(session, record) -> None:
    session.add(record)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


@pytest.mark.parametrize("record", [delivery(turn_id="missing"), effect(turn_id="missing")])
def test_content_turn_foreign_keys(session, record) -> None:
    session.add(record)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_json_round_trip_and_response_versions_are_preserved(session) -> None:
    session.add_all(
        [
            delivery(),
            response(),
            response(
                response_version=2,
                idempotency_key="response-key-2",
                normalized_answer={"v": 2},
            ),
            effect(),
        ]
    )
    session.commit()
    session.expire_all()

    assert session.scalar(select(ContentDeliveryRecord)).definition_snapshot == {
        "prompt": ["immutable", {"nested": True}]
    }
    assert session.scalar(select(AppliedPresentationEffectRecord)).effect_payload == {
        "operation": "set",
        "value": {"risk": 4},
    }
    stored = session.scalars(
        select(ContentResponseRecord).order_by(ContentResponseRecord.response_version)
    ).all()
    assert [(item.response_version, item.normalized_answer) for item in stored] == [
        (1, {"selected": [1, 3], "acknowledged": True}),
        (2, {"v": 2}),
    ]


def test_legacy_turn_has_no_synthesized_digest_or_content_facts(session) -> None:
    session.add(
        SimulationTurnRecord(
            run_id="run",
            week_number=1,
            turn_seed=8,
            idempotency_key="legacy-key",
            decision={"budget": 1},
            resulting_state={},
            events=[],
            submitted_at=NOW,
        )
    )
    session.commit()

    turn = session.scalar(select(SimulationTurnRecord))
    assert turn.request_digest is None
    for model in (ContentDeliveryRecord, ContentResponseRecord, AppliedPresentationEffectRecord):
        assert session.scalar(select(func.count()).select_from(model)) == 0
