"""Focused student commands for delivered authored content."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser
from app.api.simulations import RunResponse, _run_response
from app.db.session import get_session
from app.simulations.service import (
    ConcurrentTurnError,
    IdempotencyConflictError,
    SimulationRunError,
    content_command,
)

router = APIRouter(prefix="/simulations", tags=["simulation-content"])
DatabaseSession = Annotated[Session, Depends(get_session)]
IdempotencyKey = Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=100)]


class AnswerContentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(ge=1)
    answer: Any


class AcknowledgeContentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(ge=1)


def _command(
    session: Session,
    user: CurrentUser,
    run_id: str,
    entry_id: str,
    expected_version: int,
    key: str,
    kind: str,
    answer: Any = None,
) -> RunResponse:
    try:
        run, _ = content_command(
            session,
            run_id=run_id,
            user_id=user.id,
            sequence_entry_id=entry_id,
            expected_version=expected_version,
            idempotency_key=key,
            command_kind=kind,
            answer=answer,
        )
    except (ConcurrentTurnError, IdempotencyConflictError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except (SimulationRunError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return _run_response(session, run)


@router.post("/{run_id}/content/{entry_id}/answer", response_model=RunResponse)
def answer_content(
    run_id: str,
    entry_id: str,
    request: AnswerContentRequest,
    idempotency_key: IdempotencyKey,
    session: DatabaseSession,
    user: CurrentUser,
) -> RunResponse:
    return _command(
        session,
        user,
        run_id,
        entry_id,
        request.expected_version,
        idempotency_key,
        "answer",
        request.answer,
    )


@router.post("/{run_id}/content/{entry_id}/acknowledge", response_model=RunResponse)
def acknowledge_content(
    run_id: str,
    entry_id: str,
    request: AcknowledgeContentRequest,
    idempotency_key: IdempotencyKey,
    session: DatabaseSession,
    user: CurrentUser,
) -> RunResponse:
    return _command(
        session, user, run_id, entry_id, request.expected_version, idempotency_key, "acknowledge"
    )
