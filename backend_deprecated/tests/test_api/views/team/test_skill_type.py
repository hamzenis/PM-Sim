from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from app.models.team import SkillType
from test_api.factories import user_data, skill_type_data

User = get_user_model()


class SkillTypeViewTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url_skill_type = "/api/skill-type"
        User.objects.create_user(**user_data())
        self.client.post("/api/login", user_data(), format="json")

    def create_test_skill_type(self):
        return self.client.post(self.url_skill_type, skill_type_data(), format="json")

    def test_create_skill_type(self):
        response = self.create_test_skill_type()
        sti = SkillType.objects.filter()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_skill_type_by_id(self):
        self.create_test_skill_type()
        skill_type = SkillType.objects.get(name="Back-End-Developer Junior")
        response = self.client.get("/api/skill-type/" + str(skill_type.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("data").get("id"), skill_type.id)

    def test_change_course_name(self):
        self.create_test_skill_type()
        skill_type = SkillType.objects.get(name="Back-End-Developer Junior")
        response = self.client.patch("/api/skill-type/" + str(skill_type.id), {"name": "Back-End-Developer Senior"}, format="json")
        renamed_skill_type = SkillType.objects.get(id=skill_type.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(renamed_skill_type.name, "Back-End-Developer Senior")

    def test_delete_skill_type(self):
        self.create_test_skill_type()
        skill_type = SkillType.objects.get(name="Back-End-Developer Junior")
        response = self.client.delete("/api/skill-type/" + str(skill_type.id), format="json")
        deleted_skill_type = SkillType.objects.filter(name="Back-End-Developer Junior").exists()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(deleted_skill_type)

