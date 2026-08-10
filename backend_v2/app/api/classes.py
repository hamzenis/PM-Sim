from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser, ProfessorUser
from app.classes.service import (
    ClassError,
    add_student,
    assign_scenario,
    available_scenario_revisions,
    create_class,
    list_professor_classes,
)
from app.db.session import get_session

router = APIRouter(prefix="/classes", tags=["classes"])
DatabaseSession = Annotated[Session, Depends(get_session)]


class CreateClassRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str


class AddStudentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str


class AssignScenarioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario_revision_id: str


class ClassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    professor_id: str


class AvailabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    scenario_revision_id: str
    created_at: datetime


@router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class_route(
    request: CreateClassRequest,
    session: DatabaseSession,
    professor: ProfessorUser,
) -> object:
    try:
        return create_class(session, professor_id=professor.id, name=request.name)
    except ClassError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("", response_model=list[ClassResponse])
def list_classes_route(session: DatabaseSession, professor: ProfessorUser) -> object:
    return list_professor_classes(session, professor.id)


@router.post("/{class_id}/students", status_code=status.HTTP_201_CREATED)
def add_student_route(
    class_id: str,
    request: AddStudentRequest,
    session: DatabaseSession,
    professor: ProfessorUser,
) -> dict[str, str]:
    try:
        membership = add_student(
            session,
            professor_id=professor.id,
            class_id=class_id,
            username=request.username,
        )
        return {"membership_id": membership.id}
    except ClassError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post(
    "/{class_id}/scenarios",
    response_model=AvailabilityResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_scenario_route(
    class_id: str,
    request: AssignScenarioRequest,
    session: DatabaseSession,
    professor: ProfessorUser,
) -> object:
    try:
        return assign_scenario(
            session,
            professor_id=professor.id,
            class_id=class_id,
            scenario_revision_id=request.scenario_revision_id,
        )
    except ClassError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/available-scenarios", response_model=list[dict[str, object]])
def available_scenarios_route(session: DatabaseSession, user: CurrentUser) -> object:
    return [
        {
            "id": revision.id,
            "revision_number": revision.revision_number,
            "definition": revision.definition,
        }
        for revision in available_scenario_revisions(session, user.id)
    ]
