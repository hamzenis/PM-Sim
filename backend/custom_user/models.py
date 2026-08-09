from django.contrib.auth.models import AbstractUser
from django.db import models
from app.api.security.custom_user_manager import CustomUserManager


class User(AbstractUser):

    student = models.BooleanField(default=True)
    creator = models.BooleanField(default=False)
    staff = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)
    objects = CustomUserManager()
