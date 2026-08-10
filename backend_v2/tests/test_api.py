from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_scenario_example_is_valid() -> None:
    response = client.post(
        "/api/scenarios/validate",
        json={
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
        },
    )
    assert response.status_code == 200
    assert response.json()["tasks"]["difficulty_distribution"] == {
        "easy": 0.25,
        "medium": 0.5,
        "hard": 0.25,
    }
