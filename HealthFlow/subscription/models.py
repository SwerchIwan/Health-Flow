from django.db import models


class Subscriptions(models.Model):
    name = models.CharField(max_length=25)
    price = models.FloatField()
    description = models.JSONField()


