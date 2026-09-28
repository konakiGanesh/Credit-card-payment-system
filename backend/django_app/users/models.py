from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def role(self) -> str:
        return "admin" if self.is_staff else "user"