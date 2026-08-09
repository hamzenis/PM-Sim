from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from app.models import ScenarioConfig

User = get_user_model()


class ScenarioConfigViewTest(TestCase):

    def create_and_login_test_account(self):
        self.user_data = {
            "username": "testuser",
            "password": "secretpass123",
            "staff": True
        }
        User.objects.create_user(**self.user_data)
        self.client.post("/api/login", self.user_data, format="json")

    def setUp(self) -> None:
        self.client = APIClient()
        self.url_scenario_config = "/api/scenario-config"
        self.create_and_login_test_account()
        self.config_data = {
            "name": "test_conf_low_stress",
            "stress_weekend_reduction": -0.2,
            "stress_overtime_increase": 0.05,
            "stress_error_increase": 0.02,
            "done_tasks_per_meeting": 50,
            "train_skill_increase_rate": 0.01,
            "cost_member_team_event": 500,
            "randomness": "full"  # 'full', 'semi', 'none'
        }

    def create_test_scenario_config(self):
        return self.client.post(self.url_scenario_config, self.config_data, format="json")

    def test_create_scenario_config(self):
        response = self.create_test_scenario_config()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_scenario_config(self):
        self.create_test_scenario_config()
        scenario_config = ScenarioConfig.objects.get(name="test_conf_low_stress")
        response = self.client.get(self.url_scenario_config + "/" + str(scenario_config.id), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("data", {}).get("id"), scenario_config.id)

    def test_change_config_attributes(self):
        self.create_test_scenario_config()
        scenario_config = ScenarioConfig.objects.get(name="test_conf_low_stress")
        response = self.client.patch("/api/scenario-config/" + str(scenario_config.id), {
            "name": "test_conf_low_stress_2",
            "stress_error_increase": 0.5
        }, format="json")
        changed_scenario_config = ScenarioConfig.objects.get(id=scenario_config.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(changed_scenario_config.name, "test_conf_low_stress_2")
        self.assertEqual(changed_scenario_config.stress_error_increase, 0.5)

    def test_delete_scenario_config(self):
        self.create_test_scenario_config()
        scenario_config = ScenarioConfig.objects.get(name="test_conf_low_stress")
        response = self.client.delete("/api/scenario-config/" + str(scenario_config.id), format="json")
        deleted_config = ScenarioConfig.objects.filter(name="test_conf_low_stress").exists()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(deleted_config)

