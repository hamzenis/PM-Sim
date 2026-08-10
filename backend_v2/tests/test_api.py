from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.service import create_user
from app.db.models import Base, UserRole
from app.db.session import get_session
from app.main import app


@pytest.fixture
def client() -> Generator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_sessions = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)

    def override_session() -> Generator[Session]:
        with test_sessions() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as test_client:
        with test_sessions() as session:
            create_user(
                session,
                username="professor",
                password="professor-password",
                role=UserRole.PROFESSOR,
            )
            create_user(
                session,
                username="student",
                password="student-password",
                role=UserRole.STUDENT,
            )
        login = test_client.post(
            "/api/auth/login",
            json={"username": "professor", "password": "professor-password"},
        )
        assert login.status_code == 200
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def scenario_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "name": "Example",
        "project": {"budget": 1000, "working_days": 10},
        "tasks": {"total": 20},
        "employee_types": [
            {
                "code": "junior",
                "name": "Junior",
                "cost_per_day": 100,
                "throughput": {"easy": 4, "medium": 2, "hard": 1},
                "error_rate": 0.1,
            }
        ],
    }


def test_scenario_example_is_valid(client: TestClient) -> None:
    response = client.post(
        "/api/scenarios/validate",
        json=scenario_payload(),
    )
    assert response.status_code == 200
    assert response.json()["tasks"]["difficulty_distribution"] == {
        "easy": 0.25,
        "medium": 0.5,
        "hard": 0.25,
    }


def test_scenario_can_be_uploaded_listed_and_published(client: TestClient) -> None:
    upload = client.post("/api/scenarios", json=scenario_payload())
    assert upload.status_code == 201
    revision = upload.json()
    assert revision["revision_number"] == 1
    assert revision["status"] == "draft"

    scenarios = client.get("/api/scenarios")
    assert scenarios.status_code == 200
    scenario = scenarios.json()[0]
    assert scenario["name"] == "Example"
    assert scenario["latest_status"] == "draft"

    publish = client.post(f"/api/scenarios/{scenario['id']}/revisions/1/publish")
    assert publish.status_code == 200
    assert publish.json()["status"] == "published"
    assert publish.json()["published_at"] is not None

    revisions = client.get(f"/api/scenarios/{scenario['id']}")
    assert revisions.status_code == 200
    assert revisions.json()[0]["definition"]["tasks"]["total"] == 20


def test_missing_scenario_returns_not_found(client: TestClient) -> None:
    response = client.get("/api/scenarios/missing")
    assert response.status_code == 404
    assert response.json() == {"detail": "scenario not found"}


def test_professor_assigns_published_scenario_and_student_can_list_it(
    client: TestClient,
) -> None:
    revision = client.post("/api/scenarios", json=scenario_payload()).json()
    scenario_id = client.get("/api/scenarios").json()[0]["id"]
    client.post(f"/api/scenarios/{scenario_id}/revisions/1/publish")

    course_class = client.post("/api/classes", json={"name": "PM 2026"})
    assert course_class.status_code == 201
    class_id = course_class.json()["id"]
    assert (
        client.post(f"/api/classes/{class_id}/students", json={"username": "student"}).status_code
        == 201
    )
    assert (
        client.post(
            f"/api/classes/{class_id}/scenarios",
            json={"scenario_revision_id": revision["id"]},
        ).status_code
        == 201
    )

    client.post("/api/auth/logout")
    client.post(
        "/api/auth/login",
        json={"username": "student", "password": "student-password"},
    )
    available = client.get("/api/classes/available-scenarios")
    assert available.status_code == 200
    assert available.json()[0]["id"] == revision["id"]
