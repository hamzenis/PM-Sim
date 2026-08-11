from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.auth.service import AuthenticationError, change_password, login, logout, user_for_token
from app.config import settings
from app.db.models import UserRecord, UserRole
from app.db.session import get_session

SESSION_COOKIE = "pm_sim_session"

router = APIRouter(prefix="/auth", tags=["authentication"])
DatabaseSession = Annotated[Session, Depends(get_session)]
SessionCookie = Annotated[str | None, Cookie(alias=SESSION_COOKIE)]


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    role: str


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str
    new_password: str = Field(min_length=10, max_length=200)


def current_user(session: DatabaseSession, token: SessionCookie = None) -> UserRecord:
    user = user_for_token(session, token) if token else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication required",
        )
    return user


CurrentUser = Annotated[UserRecord, Depends(current_user)]


def professor_user(user: CurrentUser) -> UserRecord:
    if user.role != UserRole.PROFESSOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="professor role required")
    return user


ProfessorUser = Annotated[UserRecord, Depends(professor_user)]


@router.post("/login", response_model=UserResponse)
def login_route(credentials: LoginRequest, response: Response, session: DatabaseSession) -> object:
    try:
        authenticated = login(session, username=credentials.username, password=credentials.password)
    except AuthenticationError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)) from error
    response.set_cookie(
        SESSION_COOKIE,
        authenticated.token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        expires=authenticated.expires_at,
    )
    return authenticated.user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_route(
    response: Response,
    session: DatabaseSession,
    token: SessionCookie = None,
) -> None:
    if token:
        logout(session, token)
    response.delete_cookie(SESSION_COOKIE, httponly=True, samesite="lax")


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser) -> object:
    return user


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password_route(
    request: ChangePasswordRequest,
    response: Response,
    session: DatabaseSession,
    user: CurrentUser,
) -> None:
    try:
        change_password(
            session,
            user_id=user.id,
            current_password=request.current_password,
            new_password=request.new_password,
        )
    except AuthenticationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    response.delete_cookie(SESSION_COOKIE, httponly=True, samesite="lax")
