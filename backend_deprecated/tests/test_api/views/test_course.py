from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from app.models import Course

User = get_user_model()


class CourseViewTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url_course = "/api/courses"
        self.user_data = {
            "username": "testuser",
            "password": "secretpass123",
            "staff": True
        }
        self.course_data = {"name": "test_course"}
        User.objects.create_user(**self.user_data)
        self.client.post("/api/login", self.user_data, format="json")

    def create_test_course(self):
        return self.client.post(self.url_course, self.course_data, format="json")

    def test_create_course(self):
        response = self.create_test_course()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_course_by_id(self):
        self.create_test_course()
        course = Course.objects.get(name="test_course")
        response = self.client.get("/api/courses/" + str(course.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("id"), course.id)

    def test_change_course_name(self):
        self.create_test_course()
        course = Course.objects.get(name="test_course")
        response = self.client.put("/api/courses/" + str(course.id), {"name": "test_course_2"}, format="json")
        renamed_course = Course.objects.get(id=course.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(renamed_course.name, "test_course_2")

    def test_delete_course(self):
        self.create_test_course()
        course = Course.objects.get(name="test_course")
        response = self.client.delete("/api/courses/" + str(course.id), format="json")
        deleted_course = Course.objects.filter(name="test_course").exists()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(deleted_course)

