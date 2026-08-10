from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.scenarios.models import ScenarioDefinition
from app.scenarios.service import (
    ScenarioNotFoundError,
    ScenarioRevisionNotFoundError,
    create_scenario,
    get_scenario,
    list_scenarios,
    publish_revision,
)

router = APIRouter(prefix="/scenarios", tags=["scenarios"])
DatabaseSession = Annotated[Session, Depends(get_session)]


class RevisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    revision_number: int
    schema_version: int
    status: str
    definition: dict[str, object]
    created_at: datetime
    published_at: datetime | None


class ScenarioSummary(BaseModel):
    id: str
    name: str
    latest_revision: int
    latest_status: str


@router.post("/validate", response_model=ScenarioDefinition)
def validate_scenario(scenario: ScenarioDefinition) -> ScenarioDefinition:
    """Validate and normalize a scenario without persisting it."""
    return scenario


@router.post("", response_model=RevisionResponse, status_code=status.HTTP_201_CREATED)
def upload_scenario(
    scenario: ScenarioDefinition,
    session: DatabaseSession,
) -> object:
    return create_scenario(session, scenario)


@router.get("", response_model=list[ScenarioSummary])
def get_scenarios(session: DatabaseSession) -> list[ScenarioSummary]:
    return [
        ScenarioSummary(
            id=scenario.id,
            name=scenario.name,
            latest_revision=scenario.revisions[-1].revision_number,
            latest_status=scenario.revisions[-1].status,
        )
        for scenario in list_scenarios(session)
    ]


@router.get("/{scenario_id}", response_model=list[RevisionResponse])
def get_scenario_revisions(
    scenario_id: str,
    session: DatabaseSession,
) -> object:
    try:
        return get_scenario(session, scenario_id).revisions
    except ScenarioNotFoundError as error:
        raise HTTPException(status_code=404, detail="scenario not found") from error


@router.post(
    "/{scenario_id}/revisions/{revision_number}/publish",
    response_model=RevisionResponse,
)
def publish_scenario_revision(
    scenario_id: str,
    revision_number: int,
    session: DatabaseSession,
) -> object:
    try:
        return publish_revision(session, scenario_id, revision_number)
    except ScenarioRevisionNotFoundError as error:
        raise HTTPException(status_code=404, detail="scenario revision not found") from error
