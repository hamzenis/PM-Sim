from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import record_audit
from app.db.models import RevisionStatus, ScenarioRecord, ScenarioRevisionRecord
from app.scenarios.models import ScenarioDefinition


class ScenarioNotFoundError(LookupError):
    pass


class ScenarioRevisionNotFoundError(LookupError):
    pass


class ScenarioArchivedError(ValueError):
    pass


def create_scenario(
    session: Session,
    definition: ScenarioDefinition,
    *,
    owner_id: str,
) -> ScenarioRevisionRecord:
    """Create an owned scenario with its first draft revision."""
    now = datetime.now(UTC)
    scenario = ScenarioRecord(
        owner_id=owner_id,
        name=definition.name,
        created_at=now,
    )
    revision = _new_revision(scenario, definition, revision_number=1, now=now)
    session.add(scenario)
    session.flush()
    record_audit(
        session,
        actor_id=owner_id,
        action="scenario.created",
        target_type="scenario",
        target_id=scenario.id,
        details={"name": scenario.name, "revision_id": revision.id},
    )
    session.commit()
    session.refresh(revision)
    return revision


def create_revision(
    session: Session,
    *,
    scenario_id: str,
    owner_id: str,
    definition: ScenarioDefinition,
) -> ScenarioRevisionRecord:
    """Append a draft rather than editing a published revision in place."""
    scenario = get_scenario(session, scenario_id, owner_id=owner_id)
    if scenario.archived_at is not None:
        raise ScenarioArchivedError("scenario is archived")
    revision = _new_revision(
        scenario,
        definition,
        revision_number=scenario.revisions[-1].revision_number + 1,
        now=datetime.now(UTC),
    )
    session.add(revision)
    session.flush()
    record_audit(
        session,
        actor_id=owner_id,
        action="scenario.revision_created",
        target_type="scenario_revision",
        target_id=revision.id,
        details={"scenario_id": scenario.id, "revision_number": revision.revision_number},
    )
    session.commit()
    session.refresh(revision)
    return revision


def list_scenarios(session: Session, *, owner_id: str) -> list[ScenarioRecord]:
    statement = (
        select(ScenarioRecord)
        .where(
            ScenarioRecord.owner_id == owner_id,
            ScenarioRecord.archived_at.is_(None),
        )
        .order_by(ScenarioRecord.name, ScenarioRecord.id)
    )
    return list(session.scalars(statement))


def get_scenario(session: Session, scenario_id: str, *, owner_id: str) -> ScenarioRecord:
    scenario = session.get(ScenarioRecord, scenario_id)
    if scenario is None or scenario.owner_id != owner_id:
        raise ScenarioNotFoundError(scenario_id)
    return scenario


def publish_revision(
    session: Session,
    scenario_id: str,
    revision_number: int,
    *,
    owner_id: str,
) -> ScenarioRevisionRecord:
    scenario = get_scenario(session, scenario_id, owner_id=owner_id)
    if scenario.archived_at is not None:
        raise ScenarioArchivedError("scenario is archived")
    revision = next(
        (item for item in scenario.revisions if item.revision_number == revision_number),
        None,
    )
    if revision is None:
        raise ScenarioRevisionNotFoundError(f"{scenario_id}:{revision_number}")
    if revision.status == RevisionStatus.DRAFT:
        # Stored JSON is a persistence boundary: defensively apply today's complete schema
        # immediately before publication, even if the draft predates the running process.
        ScenarioDefinition.model_validate(revision.definition)
        revision.status = RevisionStatus.PUBLISHED
        revision.published_at = datetime.now(UTC)
        record_audit(
            session,
            actor_id=owner_id,
            action="scenario.revision_published",
            target_type="scenario_revision",
            target_id=revision.id,
            details={"scenario_id": scenario.id, "revision_number": revision.revision_number},
        )
        session.commit()
        session.refresh(revision)
    return revision


def archive_scenario(session: Session, scenario_id: str, *, owner_id: str) -> ScenarioRecord:
    scenario = get_scenario(session, scenario_id, owner_id=owner_id)
    if scenario.archived_at is None:
        scenario.archived_at = datetime.now(UTC)
        record_audit(
            session,
            actor_id=owner_id,
            action="scenario.archived",
            target_type="scenario",
            target_id=scenario.id,
            details={"name": scenario.name},
        )
        session.commit()
        session.refresh(scenario)
    return scenario


def _new_revision(
    scenario: ScenarioRecord,
    definition: ScenarioDefinition,
    *,
    revision_number: int,
    now: datetime,
) -> ScenarioRevisionRecord:
    return ScenarioRevisionRecord(
        scenario=scenario,
        revision_number=revision_number,
        schema_version=definition.schema_version,
        definition=definition.model_dump(mode="json"),
        created_at=now,
    )
