from django.db import models
from django.conf import settings
# Create your models here.
class TrainerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trainer_profile")
    phone_number = models.CharField(max_length=15, unique=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    trainer_type = models.ManyToManyField("TrainerType", related_name="trainers")  # Multi-select
    certifications = models.FileField(upload_to="certifications/", blank=True, null=True)  # Multi-file uploads can be handled in forms
    languages_spoken = models.ManyToManyField("Language", related_name="trainers")  # Multi-select
    training_photo = models.ImageField(upload_to="training_photos/", blank=True, null=True)

    def __str__(self):
        return f"Trainer: {self.user.username}"

class TrainerType(models.Model):
    name = models.CharField(max_length=50, unique=True)  # Example: Yoga, Gym, etc.

    def __str__(self):
        return self.name

class Language(models.Model):
    name = models.CharField(max_length=50, unique=True)  # Example: English, Hindi, etc.

    def __str__(self):
        return self.name