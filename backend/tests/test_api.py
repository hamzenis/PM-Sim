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
            create_user(
                session,
                username="other-professor",
                password="other-professor-password",
                role=UserRole.PROFESSOR,
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
    assert client.get("/health/ready").json() == {"status": "ready"}


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
    assert revision["scenario_id"] == scenario["id"]
    assert scenario["name"] == "Example"
    assert scenario["latest_status"] == "draft"

    publish = client.post(f"/api/scenarios/{scenario['id']}/revisions/1/publish")
    assert publish.status_code == 200
    assert publish.json()["status"] == "published"
    assert publish.json()["published_at"] is not None

    revisions = client.get(f"/api/scenarios/{scenario['id']}")
    assert revisions.status_code == 200
    assert revisions.json()[0]["definition"]["tasks"]["total"] == 20


def test_professor_audit_history_records_actions_and_supports_pagination(
    client: TestClient,
) -> None:
    client.post("/api/scenarios", json=scenario_payload())
    scenario_id = client.get("/api/scenarios").json()[0]["id"]
    client.post(f"/api/scenarios/{scenario_id}/revisions/1/publish")
    course_class = client.post("/api/classes", json={"name": "Audited"}).json()
    client.post(f"/api/classes/{course_class['id']}/students", json={"username": "student"})

    history = client.get("/api/audit?limit=2&offset=0")
    assert history.status_code == 200
    assert len(history.json()) == 2
    all_actions = {entry["action"] for entry in client.get("/api/audit?limit=20&offset=0").json()}
    assert {
        "scenario.created",
        "scenario.revision_published",
        "class.created",
        "class.student_added",
    } <= all_actions
    assert "password" not in str(history.json()).lower()

    client.post("/api/auth/logout")
    client.post(
        "/api/auth/login",
        json={"username": "student", "password": "student-password"},
    )
    assert client.get("/api/audit").status_code == 403


def test_missing_scenario_returns_not_found(client: TestClient) -> None:
    response = client.get("/api/scenarios/missing")
    assert response.status_code == 404
    assert response.json() == {"detail": "scenario not found"}


def test_scenario_revisions_are_append_only_owned_and_archivable(client: TestClient) -> None:
    first = client.post("/api/scenarios", json=scenario_payload()).json()
    scenario_id = client.get("/api/scenarios").json()[0]["id"]
    client.post(f"/api/scenarios/{scenario_id}/revisions/1/publish")
    revised_payload = scenario_payload()
    revised_payload["project"] = {"budget": 2000, "working_days": 15}
    second = client.post(
        f"/api/scenarios/{scenario_id}/revisions",
        json=revised_payload,
    )
    assert second.status_code == 201
    assert second.json()["revision_number"] == 2
    assert second.json()["status"] == "draft"
    revisions = client.get(f"/api/scenarios/{scenario_id}").json()
    assert revisions[0]["id"] == first["id"]
    assert revisions[0]["status"] == "published"
    assert revisions[1]["definition"]["project"]["budget"] == 2000

    client.post("/api/auth/logout")
    client.post(
        "/api/auth/login",
        json={
            "username": "other-professor",
            "password": "other-professor-password",
        },
    )
    assert client.get("/api/scenarios").json() == []
    assert client.get(f"/api/scenarios/{scenario_id}").status_code == 404
    assert (
        client.post(f"/api/scenarios/{scenario_id}/revisions", json=scenario_payload()).status_code
        == 404
    )

    client.post("/api/auth/logout")
    client.post(
        "/api/auth/login",
        json={"username": "professor", "password": "professor-password"},
    )
    assert client.post(f"/api/scenarios/{scenario_id}/archive").status_code == 204
    assert client.get("/api/scenarios").json() == []
    assert (
        client.post(f"/api/scenarios/{scenario_id}/revisions", json=scenario_payload()).status_code
        == 409
    )


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
    second_class = client.post("/api/classes", json={"name": "PM 2027"}).json()
    client.post(f"/api/classes/{second_class['id']}/students", json={"username": "student"})
    client.post(
        f"/api/classes/{second_class['id']}/scenarios",
        json={"scenario_revision_id": revision["id"]},
    )

    client.post("/api/auth/logout")
    client.post(
        "/api/auth/login",
        json={"username": "student", "password": "student-password"},
    )
    available = client.get("/api/classes/available-scenarios")
    assert available.status_code == 200
    assert available.json()[0]["id"] == revision["id"]
    assert available.json()[0]["class_id"] == class_id
    assert available.json()[0]["class_name"] == "PM 2026"
    assert available.json()[1]["class_id"] == second_class["id"]
    assert available.json()[1]["class_name"] == "PM 2027"


def test_professor_can_manage_class_members_assignments_and_archival(
    client: TestClient,
) -> None:
    revision = client.post("/api/scenarios", json=scenario_payload()).json()
    scenario_id = client.get("/api/scenarios").json()[0]["id"]
    client.post(f"/api/scenarios/{scenario_id}/revisions/1/publish")
    course_class = client.post("/api/classes", json={"name": "Before"}).json()
    class_id = course_class["id"]
    membership = client.post(f"/api/classes/{class_id}/students", json={"username": "student"})
    assert membership.status_code == 201
    client.post(
        f"/api/classes/{class_id}/scenarios",
        json={"scenario_revision_id": revision["id"]},
    )

    renamed = client.patch(f"/api/classes/{class_id}", json={"name": "After"})
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "After"
    students = client.get(f"/api/classes/{class_id}/students").json()
    assert students[0]["username"] == "student"
    actual_student_id = students[0]["id"]
    assignments = client.get(f"/api/classes/{class_id}/scenarios").json()
    assert assignments[0]["id"] == revision["id"]

    assert client.delete(f"/api/classes/{class_id}/students/{actual_student_id}").status_code == 204
    assert client.get(f"/api/classes/{class_id}/students").json() == []
    assert client.delete(f"/api/classes/{class_id}/scenarios/{revision['id']}").status_code == 204
    assert client.get(f"/api/classes/{class_id}/scenarios").json() == []
    assert client.post(f"/api/classes/{class_id}/archive").status_code == 204
    assert client.get("/api/classes").json() == []
    assert (
        client.post(f"/api/classes/{class_id}/students", json={"username": "student"}).status_code
        == 404
    )


def test_professor_can_import_students_transactionally_and_reset_passwords(
    client: TestClient,
) -> None:
    course_class = client.post("/api/classes", json={"name": "Imported"}).json()
    class_id = course_class["id"]
    imported = client.post(
        f"/api/classes/{class_id}/students/import",
        json={
            "students": [
                {"username": "Alice", "password": "alice-password"},
                {"username": "Bob", "password": "bob-password-1"},
            ]
        },
    )
    assert imported.status_code == 201
    assert [student["username"] for student in imported.json()] == ["alice", "bob"]
    alice_id = imported.json()[0]["id"]

    rejected = client.post(
        f"/api/classes/{class_id}/students/import",
        json={
            "students": [
                {"username": "Charlie", "password": "charlie-password"},
                {"username": "Charlie", "password": "another-password"},
            ]
        },
    )
    assert rejected.status_code == 409
    assert "unique" in rejected.json()["detail"]
    assert "charlie" not in {
        student["username"] for student in client.get(f"/api/classes/{class_id}/students").json()
    }

    reset = client.put(
        f"/api/classes/{class_id}/students/{alice_id}/password",
        json={"new_password": "alice-new-password"},
    )
    assert reset.status_code == 204
    client.post("/api/auth/logout")
    old_login = client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "alice-password"},
    )
    assert old_login.status_code == 401
    new_login = client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "alice-new-password"},
    )
    assert new_login.status_code == 200


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
    assert run["employee_types"][0]["code"] == "junior"
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
    assert history.json()[0]["state"]["week"] == 1
    assert "undiscovered_bugs" not in history.json()[0]["state"]
    assert "incorrect_specifications" not in history.json()[0]["state"]
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
