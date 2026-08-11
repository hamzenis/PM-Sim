from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from app.models import TemplateScenario

User = get_user_model()


class ManagementGoalViewTest(TestCase):
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
        self.url_management_goal = "/api/management-goal/"
        self.create_and_login_test_account()
        template_scenario = TemplateScenario.objects.create()
        self.management_goal_data = {
            "budget": 250000,
            "duration": 60,
            "easy_tasks": 120,
            "medium_tasks": 250,
            "hard_tasks": 150,
            "tasks_predecessor_p": 0.2,
            "template_scenario": template_scenario.id,
        }

    def create_test_management_goal(self):
        return self.client.post(self.url_management_goal, self.management_goal_data, format="json")

    def test_create_management_goal(self):
        response = self.create_test_management_goal()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
