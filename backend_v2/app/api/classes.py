from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser, ProfessorUser
from app.classes.service import (
    ClassError,
    add_student,
    archive_class,
    assign_scenario,
    available_scenario_revisions,
    create_class,
    import_students,
    list_assigned_scenarios,
    list_professor_classes,
    list_students,
    remove_student,
    rename_class,
    reset_student_password,
    unassign_scenario,
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


class RenameClassRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str


class ImportStudentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=10, max_length=200)


class ImportStudentsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    students: list[ImportStudentRequest] = Field(min_length=1, max_length=100)


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    new_password: str = Field(min_length=10, max_length=200)


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


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    username: str


class AssignedScenarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    scenario_id: str
    revision_number: int
    status: str


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


@router.patch("/{class_id}", response_model=ClassResponse)
def rename_class_route(
    class_id: str,
    request: RenameClassRequest,
    session: DatabaseSession,
    professor: ProfessorUser,
) -> object:
    try:
        return rename_class(
            session,
            professor_id=professor.id,
            class_id=class_id,
            name=request.name,
        )
    except ClassError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/{class_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
def archive_class_route(
    class_id: str,
    session: DatabaseSession,
    professor: ProfessorUser,
) -> None:
    try:
        archive_class(session, professor_id=professor.id, class_id=class_id)
    except ClassError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/{class_id}/students", response_model=list[StudentResponse])
def list_students_route(
    class_id: str,
    session: DatabaseSession,
    professor: ProfessorUser,
) -> object:
    try:
        return list_students(session, professor_id=professor.id, class_id=class_id)
    except ClassError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post(
    "/{class_id}/students/import",
    response_model=list[StudentResponse],
    status_code=status.HTTP_201_CREATED,
)
def import_students_route(
    class_id: str,
    request: ImportStudentsRequest,
    session: DatabaseSession,
    professor: ProfessorUser,
) -> object:
    try:
        return import_students(
            session,
            professor_id=professor.id,
            class_id=class_id,
            students=[(student.username, student.password) for student in request.students],
        )
    except ClassError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.put(
    "/{class_id}/students/{student_id}/password",
    status_code=status.HTTP_204_NO_CONTENT,
)
def reset_student_password_route(
    class_id: str,
    student_id: str,
    request: ResetPasswordRequest,
    session: DatabaseSession,
    professor: ProfessorUser,
) -> None:
    try:
        reset_student_password(
            session,
            professor_id=professor.id,
            class_id=class_id,
            student_id=student_id,
            new_password=request.new_password,
        )
    except ClassError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete("/{class_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_student_route(
    class_id: str,
    student_id: str,
    session: DatabaseSession,
    professor: ProfessorUser,
) -> None:
    try:
        remove_student(
            session,
            professor_id=professor.id,
            class_id=class_id,
            student_id=student_id,
        )
    except ClassError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/{class_id}/scenarios", response_model=list[AssignedScenarioResponse])
def list_assigned_scenarios_route(
    class_id: str,
    session: DatabaseSession,
    professor: ProfessorUser,
) -> object:
    try:
        return list_assigned_scenarios(
            session,
            professor_id=professor.id,
            class_id=class_id,
        )
    except ClassError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete(
    "/{class_id}/scenarios/{scenario_revision_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unassign_scenario_route(
    class_id: str,
    scenario_revision_id: str,
    session: DatabaseSession,
    professor: ProfessorUser,
) -> None:
    try:
        unassign_scenario(
            session,
            professor_id=professor.id,
            class_id=class_id,
            scenario_revision_id=scenario_revision_id,
        )
    except ClassError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


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
