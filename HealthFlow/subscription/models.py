from django.conf import settings
from django.db import models


class Plan(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=40)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    duration_days = models.PositiveSmallIntegerField(default=30)
    features = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'price']

    def __str__(self):
        return f'{self.name} ({self.price} Br)'


class Payment(models.Model):
    STATUS_CHOICES = [
        ('succeeded', 'Успешно'),
        ('canceled', 'Отменён'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    duration_days = models.PositiveSmallIntegerField()
    card_mask = models.CharField(max_length=19, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='succeeded')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.plan.name} — {self.amount} Br'
