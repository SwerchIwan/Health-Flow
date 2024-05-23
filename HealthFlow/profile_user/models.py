# models.py в приложении profile_user
from django.db import models
from django.conf import settings
from datetime import date  # Добавим импорт для работы с датой

class Specialist(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    # добавьте любые другие поля, необходимые для специалиста

    def __str__(self):
        return self.name

class Chat(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    specialist = models.ForeignKey(Specialist, on_delete=models.CASCADE)
    last_message = models.TextField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Chat between {self.user.username} and {self.specialist.name}"

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} at {self.timestamp}"

class Note(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(default=date.today)  # Дата заметки
    additional_notes = models.TextField(blank=True)
    file = models.FileField(upload_to='notes/%Y/%m/%d/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note by {self.user.username} at {self.created_at}"

class Blood(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='blood_data')
    hemoglobin = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    leukocytes = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    lymphocytes = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

class Pressure(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='pressure_data')
    systolic = models.PositiveIntegerField(blank=True, null=True)
    diastolic = models.PositiveIntegerField(blank=True, null=True)
    pulse_rate = models.PositiveIntegerField(blank=True, null=True)

class BMI(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='bmi_data')
    height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  # Рост в метрах
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  # Вес в килограммах

