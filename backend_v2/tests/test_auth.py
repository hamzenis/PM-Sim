from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.auth import SESSION_COOKIE
from app.auth.service import (
    AuthenticationError,
    create_user,
    hash_password,
    token_hash,
    verify_password,
)
from app.db.models import AuthSessionRecord, Base, UserRole
from app.db.session import get_session
from app.main import app


@pytest.fixture
def auth_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)

    def override_session():
        with sessions() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with sessions() as session:
        create_user(
            session,
            username="student",
            password="student-password",
            role=UserRole.STUDENT,
        )
    with TestClient(app) as client:
        yield client, sessions
    app.dependency_overrides.clear()


def test_passwords_are_salted_and_verified() -> None:
    first = hash_password("long-enough-password")
    second = hash_password("long-enough-password")
    assert first != second
    assert verify_password("long-enough-password", first) is True
    assert verify_password("wrong-password", first) is False
    assert "long-enough-password" not in first


def test_short_password_is_rejected() -> None:
    with pytest.raises(AuthenticationError, match="at least 10"):
        hash_password("short")


def test_login_me_and_logout_cookie_flow(auth_client) -> None:
    client, _sessions = auth_client
    login = client.post(
        "/api/auth/login",
        json={"username": "student", "password": "student-password"},
    )
    assert login.status_code == 200
    assert login.json()["role"] == "student"
    assert SESSION_COOKIE in client.cookies
    assert client.get("/api/auth/me").json()["username"] == "student"

    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_invalid_login_does_not_disclose_which_credential_failed(auth_client) -> None:
    client, _sessions = auth_client
    response = client.post(
        "/api/auth/login",
        json={"username": "student", "password": "incorrect-password"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "invalid username or password"}


def test_student_cannot_access_professor_scenario_routes(auth_client) -> None:
    client, _sessions = auth_client
    client.post(
        "/api/auth/login",
        json={"username": "student", "password": "student-password"},
    )
    response = client.get("/api/scenarios")
    assert response.status_code == 403
    assert response.json() == {"detail": "professor role required"}


def test_expired_session_is_rejected_and_deleted(auth_client) -> None:
    client, sessions = auth_client
    client.cookies.set(SESSION_COOKIE, "expired-token")
    with sessions() as session:
        student_id = create_user(
            session,
            username="another-student",
            password="another-password",
            role=UserRole.STUDENT,
        ).id
        session.add(
            AuthSessionRecord(
                token_hash=token_hash("expired-token"),
                user_id=student_id,
                created_at=datetime.now(UTC) - timedelta(hours=9),
                expires_at=datetime.now(UTC) - timedelta(hours=1),
            )
        )
        session.commit()
    assert client.get("/api/auth/me").status_code == 401
