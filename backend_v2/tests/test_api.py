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


def _assign_scenario_and_login_student(client: TestClient) -> str:
    revision = client.post("/api/scenarios", json=scenario_payload()).json()
    scenario_id = client.get("/api/scenarios").json()[0]["id"]
    assert client.post(f"/api/scenarios/{scenario_id}/revisions/1/publish").status_code == 200
    course_class = client.post("/api/classes", json={"name": "Simulation API"}).json()
    client.post(f"/api/classes/{course_class['id']}/students", json={"username": "student"})
    client.post(
        f"/api/classes/{course_class['id']}/scenarios",
        json={"scenario_revision_id": revision["id"]},
    )
    client.post("/api/auth/logout")
    login = client.post(
        "/api/auth/login",
        json={"username": "student", "password": "student-password"},
    )
    assert login.status_code == 200
    return revision["id"]


def test_student_can_start_read_and_complete_a_simulation_turn(client: TestClient) -> None:
    revision_id = _assign_scenario_and_login_student(client)
    started = client.post(
        "/api/simulations",
        json={"scenario_revision_id": revision_id, "seed": 123},
    )
    assert started.status_code == 201
    run = started.json()
    assert run["version"] == 1
    assert "undiscovered_bugs" not in run["state"]
    assert "incorrect_specifications" not in run["state"]

    assert client.get("/api/simulations").json()[0]["id"] == run["id"]
    assert client.get(f"/api/simulations/{run['id']}").status_code == 200

    decision = {
        "expected_version": 1,
        "allocation": {
            "development": 100,
            "unit_testing": 0,
            "bug_fixing": 0,
            "integration_testing": 0,
        },
        "hires": [{"employee_type_code": "junior", "count": 1}],
    }
    completed = client.post(
        f"/api/simulations/{run['id']}/turns",
        json=decision,
        headers={"Idempotency-Key": "week-1"},
    )
    assert completed.status_code == 200
    result = completed.json()
    assert result["run"]["current_week"] == 1
    assert result["run"]["version"] == 2
    assert result["replayed"] is False
    assert "bugs_created" not in {event["kind"] for event in result["events"]}

    history = client.get(f"/api/simulations/{run['id']}/turns")
    assert history.status_code == 200
    assert history.json()[0]["week_number"] == 1
    assert "bugs_created" not in {event["kind"] for event in history.json()[0]["events"]}

    replay = client.post(
        f"/api/simulations/{run['id']}/turns",
        json=decision,
        headers={"Idempotency-Key": "week-1"},
    )
    assert replay.status_code == 200
    assert replay.json()["replayed"] is True


def test_turn_api_requires_idempotency_and_rejects_stale_versions(client: TestClient) -> None:
    revision_id = _assign_scenario_and_login_student(client)
    run = client.post(
        "/api/simulations", json={"scenario_revision_id": revision_id, "seed": 1}
    ).json()
    decision = {
        "expected_version": 99,
        "allocation": {
            "development": 100,
            "unit_testing": 0,
            "bug_fixing": 0,
            "integration_testing": 0,
        },
    }
    missing_key = client.post(f"/api/simulations/{run['id']}/turns", json=decision)
    assert missing_key.status_code == 422
    stale = client.post(
        f"/api/simulations/{run['id']}/turns",
        json=decision,
        headers={"Idempotency-Key": "stale"},
    )
    assert stale.status_code == 409


def test_student_can_submit_a_run_and_cannot_take_more_turns(client: TestClient) -> None:
    revision_id = _assign_scenario_and_login_student(client)
    run = client.post(
        "/api/simulations", json={"scenario_revision_id": revision_id, "seed": 9}
    ).json()
    submitted = client.post(
        f"/api/simulations/{run['id']}/submit",
        json={"expected_version": 1},
    )
    assert submitted.status_code == 200
    result = submitted.json()
    assert result["status"] == "submitted"
    assert result["version"] == 2
    assert result["final_result"]["outcome"] == "submitted"

    replay = client.post(
        f"/api/simulations/{run['id']}/submit",
        json={"expected_version": 1},
    )
    assert replay.status_code == 200
    assert replay.json()["version"] == 2

    turn = client.post(
        f"/api/simulations/{run['id']}/turns",
        json={
            "expected_version": 2,
            "allocation": {
                "development": 100,
                "unit_testing": 0,
                "bug_fixing": 0,
                "integration_testing": 0,
            },
        },
        headers={"Idempotency-Key": "too-late"},
    )
    assert turn.status_code == 400
    assert turn.json()["detail"] == "simulation run is not active"


def test_professor_can_compare_final_results_and_inspect_full_audit(client: TestClient) -> None:
    revision = client.post("/api/scenarios", json=scenario_payload()).json()
    scenario_id = client.get("/api/scenarios").json()[0]["id"]
    client.post(f"/api/scenarios/{scenario_id}/revisions/1/publish")
    course_class = client.post("/api/classes", json={"name": "Results"}).json()
    client.post(f"/api/classes/{course_class['id']}/students", json={"username": "student"})
    client.post(
        f"/api/classes/{course_class['id']}/scenarios",
        json={"scenario_revision_id": revision["id"]},
    )
    client.post("/api/auth/logout")
    client.post(
        "/api/auth/login",
        json={"username": "student", "password": "student-password"},
    )
    run = client.post(
        "/api/simulations",
        json={
            "scenario_revision_id": revision["id"],
            "class_id": course_class["id"],
            "seed": 11,
        },
    ).json()
    decision = {
        "expected_version": 1,
        "allocation": {
            "development": 100,
            "unit_testing": 0,
            "bug_fixing": 0,
            "integration_testing": 0,
        },
        "hires": [{"employee_type_code": "junior", "count": 1}],
    }
    client.post(
        f"/api/simulations/{run['id']}/turns",
        json=decision,
        headers={"Idempotency-Key": "audit-week"},
    )
    client.post(f"/api/simulations/{run['id']}/submit", json={"expected_version": 2})

    client.post("/api/auth/logout")
    client.post(
        "/api/auth/login",
        json={"username": "professor", "password": "professor-password"},
    )
    results = client.get(f"/api/classes/{course_class['id']}/results")
    assert results.status_code == 200
    assert results.json()[0]["student_username"] == "student"
    assert results.json()[0]["final_result"]["outcome"] == "submitted"

    audit = client.get(f"/api/classes/{course_class['id']}/results/{run['id']}")
    assert audit.status_code == 200
    assert audit.json()["seed"] == 11
    assert audit.json()["turns"][0]["turn_seed"] == 11
    assert "undiscovered_bugs" in audit.json()["current_state"]
    assert client.get(f"/api/classes/missing/results/{run['id']}").status_code == 404
