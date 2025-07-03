from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class Pilot(models.Model):
    name = models.CharField(max_length=100)

class Flight(models.Model):
    title = models.CharField(max_length=200)
    scheduled_time = models.DateTimeField()
    end_time = models.DateTimeField()
    flown = models.BooleanField(default=False)
    pilot = models.ForeignKey(Pilot, on_delete=models.SET_NULL, null=True, blank=True)
    frequency_days = models.IntegerField(default=7)  # e.g. should be flown every X days

class User(AbstractUser):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("user",  "User"),
    )
    role = models.CharField(
        max_length=5,
        choices=ROLE_CHOICES,
        default="user",
        help_text="Determines if a user can add other users",
    )

    @property
    def is_admin(self):
        return self.role == "admin"