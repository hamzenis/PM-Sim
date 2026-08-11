from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from ..factories import user_data, template_scenario_data

from app.models import TemplateScenario

User = get_user_model()


class TemplateScenarioViewTest(TestCase):

    def create_and_login_test_account(self):
        User.objects.create_user(**user_data())
        self.client.post("/api/login", user_data(), format="json")

    def setUp(self) -> None:
        self.client = APIClient()
        self.url_template_scenario = "/api/template-scenario"
        self.create_and_login_test_account()

    def create_test_template_scenario(self):
        return self.client.post(self.url_template_scenario, template_scenario_data(), format="json")

    def test_create_template_scenario(self):
        response = self.create_test_template_scenario()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_template_scenario(self):
        self.create_test_template_scenario()
        template_scenario = TemplateScenario.objects.get(name="Test Scenario")
        response = self.client.get(self.url_template_scenario + "/" + str(template_scenario.id), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), template_scenario.id)

    def test_change_template_scenario_attributes(self):
        self.create_test_template_scenario()
        template_scenario = TemplateScenario.objects.get(name="Test Scenario")
        response = self.client.patch(self.url_template_scenario + "/" + str(template_scenario.id), {
            "name": "Test Scenario 2",
            "story": "Changed test story"
        }, format="json")
        changed_template_scenario = TemplateScenario.objects.get(id=template_scenario.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(changed_template_scenario.name, "Test Scenario 2")
        self.assertEqual(changed_template_scenario.story, "Changed test story")
