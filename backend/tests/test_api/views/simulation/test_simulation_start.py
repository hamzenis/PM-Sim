from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from app.models.action import Action
from app.models.score_card import ScoreCard
from app.models.simulation_end import SimulationEnd
from app.models.simulation_fragment import SimulationFragment

from factories import (
    user_data,
    template_scenario_data,
    config_data,
    management_goal_data,
)

User = get_user_model()


class StartUserScenarioViewTest(TestCase):
    def create_and_login_test_account(self):
        User.objects.create_user(**user_data())
        self.client.post("/api/login", user_data(), format="json")

    def setUp(self) -> None:
        self.client = APIClient()
        self.url_start_simulation = "/api/sim/start"
        self.create_and_login_test_account()
        template_response = self.client.post(
            "/api/template-scenario", template_scenario_data(), format="json"
        )
        config_response = self.client.post(
            "/api/scenario-config", config_data(), format="json"
        )
        factory_management_goal_data = management_goal_data(
            template_scenario=template_response.data.get("data").get("id")
        )
        self.client.post(
            "/api/management-goal/", factory_management_goal_data, format="json"
        )
        self.response_ids = {
            "template-id": template_response.data.get("data").get("id"),
            "config-id": config_response.data.get("data").get("id"),
        }

    def test_start_simulation(self):
        response = self.client.post(
            self.url_start_simulation, self.response_ids, format="json"
        )
        ScoreCard.objects.create(
            budget_limit=100, time_limit=100, quality_limit=100, template_scenario_id=1
        )
        SimulationFragment.objects.create(
            template_scenario_id=1, index=0, text="Beispieltext"
        )
        SimulationEnd.objects.create(
            limit=2, limit_type="ge", type="duration", simulation_fragment_id=1
        )
        Action.objects.create(title="bugfix", simulation_fragment_id=1)
        Action.objects.create(
            title="meetings", lower_limit=0, upper_limit=5, simulation_fragment_id=1
        )
        response_2 = self.client.post(
            "/api/sim/next",
            {
                "type": "START",
                "scenario_id": 1,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
