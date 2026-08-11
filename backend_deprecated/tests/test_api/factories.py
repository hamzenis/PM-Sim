from copy import deepcopy


_BASE_DATA = {
    "user_data": {
        "username": "testuser",
        "password": "secretpass123",
        "staff": True,
        "is_staff": True,
    },
    "management_goal": {
        "budget": 250000,
        "duration": 60,
        "easy_tasks": 120,
        "medium_tasks": 250,
        "hard_tasks": 150,
        "tasks_predecessor_p": 0.2,
    },
    "template_scenario": {
        "name": "Test Scenario",
        "story": "A test story for the test scenario",
    },
    "config_data": {
        "name": "test_conf_low_stress",
        "stress_weekend_reduction": -0.2,
        "stress_overtime_increase": 0.05,
        "stress_error_increase": 0.02,
        "done_tasks_per_meeting": 50,
        "train_skill_increase_rate": 0.01,
        "cost_member_team_event": 500,
        "randomness": "full",
    },
    "skill_types": [
        {
            "name": "Back-End-Developer Junior",
            "cost_per_day": 171.15,
            "error_rate": 0.06,
            "throughput": 2,
            "development_quality": 25,
            "management_quality": 10,
            "signing_bonus": 0
        },
        {
            "name": "Back-End-Developer Senior",
            "cost_per_day": 250,
            "error_rate": 0.03,
            "throughput": 3,
            "development_quality": 70,
            "management_quality": 10,
            "signing_bonus": 0
        },
        {
            "name": "Front-End-Developer Junior",
            "cost_per_day": 184.6,
            "error_rate": 0.05,
            "throughput": 2,
            "development_quality": 20,
            "management_quality": 10,
            "signing_bonus": 0
        },
        {
            "name": "Front-End-Developer Senior",
            "cost_per_day": 216.09,
            "error_rate": 0.03,
            "throughput": 3,
            "development_quality": 50,
            "management_quality": 10,
            "signing_bonus": 0
        },
    ],
}


def user_data(**overrides):
    data = deepcopy(_BASE_DATA["user_data"])
    data.update(overrides)
    return data


def management_goal_data(**overrides):
    data = deepcopy(_BASE_DATA["management_goal"])
    data.update(overrides)
    return data


def template_scenario_data(**overrides):
    data = deepcopy(_BASE_DATA["template_scenario"])
    data.update(overrides)
    return data


def config_data(**overrides):
    data = deepcopy(_BASE_DATA["config_data"])
    data.update(overrides)
    return data


def skill_type_data(index: int = 0, **overrides):
    data = deepcopy(_BASE_DATA["skill_types"][index])
    data.update(overrides)
    return data
