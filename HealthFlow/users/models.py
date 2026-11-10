from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    SUBSCRIPTION_CHOICES = [
        ("FREE", "Free"),
        ("STANDART", "Standart"),
        ("PLUS", "Plus"),
        ("PRO", "Pro"),
    ]

    photo = models.ImageField(upload_to="users/%Y/%m/%d/", blank=True, null=True)
    phone = models.CharField(max_length=16, blank=True, null=True)
    phone_notifications = models.BooleanField(default=True)
    subscription = models.CharField(max_length=8, choices=SUBSCRIPTION_CHOICES, default="FREE")
    subscription_until = models.DateTimeField(blank=True, null=True)

    def subscription_is_active(self):
        if self.subscription == "FREE":
            return False
        return self.subscription_until is None or self.subscription_until > timezone.now()
