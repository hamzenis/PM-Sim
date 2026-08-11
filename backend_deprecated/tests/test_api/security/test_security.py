from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from app.models import Course

User = get_user_model()


class RegisterViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            "username": "testuser",
            "password": "secretpass123"
        }

    def test_register_user_success(self):
        response = self.client.post("/api/register", self.user_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="testuser").exists())

    def test_register_user_missing_username(self):
        response = self.client.post("/api/register", {
            "password": self.user_data["password"]
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_register_user_with_course(self):
        course = Course.objects.create(name="Test Course")
        response = self.client.post("/api/register", {
            "username": "user_with_course",
            "password": "pw123",
            "course_id": course.id
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="user_with_course")
        self.assertIn(user, course.users.all())


class LoginViewTest(TestCase):

    def setUp(self) -> None:
        self.user_data = {
            "username": "testuser",
            "password": "secretpass123"
        }
        self.client.post("/api/register", self.user_data, format="json")

    def test_login_user_success(self):
        response = self.client.post("/api/login", self.user_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LogoutViewTest(TestCase):
    def setUp(self) -> None:
        self.user_data = {
            "username": "testuser",
            "password": "secretpass123"
        }
        self.client.post("/api/register", self.user_data, format="json")

    def test_user_logout_success(self):
        self.client.post("/api/login", self.user_data, format="json")
        request = self.client.post("/api/logout", format="json")

        self.assertEqual(request.status_code, status.HTTP_200_OK)

    def test_user_logout_fail(self):
        request = self.client.post("/api/logout", format="json")

        self.assertEqual(request.status_code, status.HTTP_403_FORBIDDEN)


class AuthenticatedViewTest(TestCase):

    def setUp(self) -> None:
        self.user_data = {
            "username": "testuser",
            "password": "secretpass123"
        }
        self.client.post("/api/register", self.user_data, format="json")

    def test_user_authenticated_success(self):
        self.client.post("/api/login", self.user_data, format="json")
        request = self.client.get("/api/authenticated", format="json")
        self.assertEqual(request.status_code, status.HTTP_200_OK)

    def test_without_user_authenticated_fail(self):
        request = self.client.get("/api/authenticated", format="json")
        self.assertEqual(request.status_code, status.HTTP_403_FORBIDDEN)
