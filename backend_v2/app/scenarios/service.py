from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import RevisionStatus, ScenarioRecord, ScenarioRevisionRecord
from app.scenarios.models import ScenarioDefinition


class ScenarioNotFoundError(LookupError):
    pass


class ScenarioRevisionNotFoundError(LookupError):
    pass


def create_scenario(session: Session, definition: ScenarioDefinition) -> ScenarioRevisionRecord:
    """Create a scenario with its first immutable-input draft revision."""
    now = datetime.now(UTC)
    scenario = ScenarioRecord(name=definition.name, created_at=now)
    revision = ScenarioRevisionRecord(
        scenario=scenario,
        revision_number=1,
        schema_version=definition.schema_version,
        definition=definition.model_dump(mode="json"),
        created_at=now,
    )
    session.add(scenario)
    session.commit()
    session.refresh(revision)
    return revision


def list_scenarios(session: Session) -> list[ScenarioRecord]:
    statement = select(ScenarioRecord).order_by(ScenarioRecord.name, ScenarioRecord.id)
    return list(session.scalars(statement))


def get_scenario(session: Session, scenario_id: str) -> ScenarioRecord:
    scenario = session.get(ScenarioRecord, scenario_id)
    if scenario is None:
        raise ScenarioNotFoundError(scenario_id)
    return scenario


def publish_revision(
    session: Session,
    scenario_id: str,
    revision_number: int,
) -> ScenarioRevisionRecord:
    statement = select(ScenarioRevisionRecord).where(
        ScenarioRevisionRecord.scenario_id == scenario_id,
        ScenarioRevisionRecord.revision_number == revision_number,
    )
    revision = session.scalar(statement)
    if revision is None:
        raise ScenarioRevisionNotFoundError(f"{scenario_id}:{revision_number}")
    if revision.status == RevisionStatus.DRAFT:
        revision.status = RevisionStatus.PUBLISHED
        revision.published_at = datetime.now(UTC)
        session.commit()
        session.refresh(revision)
    return revision
