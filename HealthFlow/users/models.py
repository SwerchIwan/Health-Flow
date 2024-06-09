from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    SUBSCRIPTION_CHOICES = [
        ("FREE", "Free"),
        ("STANDART", "Standart"),
        ("PLUS", "Plus"),
        ("PRO", "Pro"),
    ]

    photo = models.ImageField(upload_to="users/%Y/%m/%d/", blank=True, null=True)
    phone = models.CharField(max_length=16, blank=True, null=True)
    subscription = models.CharField(max_length=8, choices=SUBSCRIPTION_CHOICES, default="FREE")
