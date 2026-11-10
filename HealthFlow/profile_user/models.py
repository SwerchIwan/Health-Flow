# models.py в приложении profile_user
from django.db import models
from django.conf import settings
from datetime import date  # Добавим импорт для работы с датой

class Specialist(models.Model):
    SPECIALTY_CHOICES = [
        ("therapist", "Терапевт"),
        ("cardiology", "Кардиолог"),
        ("neurology", "Невролог"),
        ("endocrinology", "Эндокринолог"),
        ("gastroenterology", "Гастроэнтеролог"),
        ("dermatology", "Дерматолог"),
        ("psychiatry", "Психиатр / психотерапевт"),
        ("psychology", "Психолог"),
        ("pediatrics", "Педиатр"),
        ("gynecology", "Гинеколог"),
        ("urology", "Уролог"),
        ("ophthalmology", "Офтальмолог"),
        ("otorhinolaryngology", "ЛОР"),
        ("orthopedics", "Ортопед-травматолог"),
        ("dentistry", "Стоматолог"),
        ("dietology", "Диетолог / нутрициолог"),
        ("rehabilitation", "Реабилитолог"),
        ("other", "Другое"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    specialty = models.CharField(max_length=32, choices=SPECIALTY_CHOICES, default="other")
    about = models.TextField(blank=True)
    experience_years = models.PositiveSmallIntegerField(default=0)
    price = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True, help_text="Стоимость консультации, Br")
    city = models.CharField(max_length=80, blank=True)
    languages = models.CharField(max_length=120, blank=True, default="Русский")
    is_published = models.BooleanField(default=False, help_text="Показывать в публичном каталоге")
    is_catalog_demo = models.BooleanField(default=False, help_text="Демонстрационная карточка из демо-данных")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def average_rating(self):
        ratings = self.ratings.all()
        if ratings.exists():
            return sum(rating.rating for rating in ratings) / ratings.count()
        return 0

class Chat(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_chats')
    specialist = models.ForeignKey(Specialist, on_delete=models.CASCADE, related_name='specialist_chats')
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

class Rating(models.Model):
    specialist = models.ForeignKey(Specialist, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"Rating {self.rating} for {self.specialist.name} by {self.user.username}"


class Review(models.Model):
    specialist = models.ForeignKey(Specialist, on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='specialist_reviews')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review for {self.specialist.name} by {self.author.username}"



class SpecialistApplication(models.Model):
    STATUS_CHOICES = [
        ("pending", "На рассмотрении"),
        ("approved", "Одобрена"),
        ("rejected", "Отклонена"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    contact = models.CharField(max_length=120)
    specialization = models.CharField(max_length=32, choices=Specialist.SPECIALTY_CHOICES, default="other")
    additional_info = models.TextField(blank=True)
    attached_file = models.FileField(upload_to='specialist_applications/%Y/%m/%d/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Application by {self.first_name} {self.last_name} at {self.created_at}"