from django.db import models
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
# Create your models here.
class TrainerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trainer_profile")
    phone_number = models.CharField(max_length=15, unique=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    trainer_type = models.ManyToManyField("TrainerType", related_name="trainers")  
    certifications = models.FileField(upload_to="certifications/", blank=True, null=True)  
    languages_spoken = models.ManyToManyField("Language", related_name="trainers") 
    training_photo = models.ImageField(upload_to="training_photos/", blank=True, null=True)
    listed = models.BooleanField(default=True)

    def __str__(self):
        return f"Trainer: {self.user.username}"

class TrainerType(models.Model):
    name = models.CharField(max_length=50, unique=True)  

    def __str__(self):
        return self.name

class Language(models.Model):
    name = models.CharField(max_length=50, unique=True)  

    def __str__(self):
        return self.name


class TrainerCource(models.Model):
    APPROVAL_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ]

    trainer = models.ForeignKey("TrainerProfile", on_delete=models.CASCADE, related_name="courses")
    title =  models.CharField(max_length=100)
    trainer_type = models.ForeignKey("TrainerType", on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)

    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)

    start_date = models.DateField()
    end_date = models.DateField()

    start_time = models.TimeField()
    end_time = models.TimeField() 

    days_of_week = models.JSONField(help_text="List of days like ['Mon', 'Wed', 'Fri']")
    max_participants = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)

    status = models.CharField(max_length=20, choices=APPROVAL_CHOICES, default='pending')
    cancellation_reason = models.TextField(blank=True, null=True)

    approval_status = models.CharField(max_length=10, choices=APPROVAL_CHOICES, default='pending')
    approval_note = models.TextField(blank=True, null=True)
    is_deleted =  models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.trainer.user.username}"


    @property
    def duration_minutes(self):
        dt_start = datetime.combine(timezone.now().date(), self.start_time)
        dt_end = datetime.combine(timezone.now().date(), self.end_time)

 
        if dt_end < dt_start:
            dt_end += timedelta(days=1)

        return int((dt_end - dt_start).total_seconds() / 60)
    
    @property
    def available_slots(self):
        return self.max_participants - self.current_enrollments
    
    @property
    def current_enrollments(self):
        return self.enrollments.filter(is_cancelled=False).count()
    
    def is_user_enrolled(self, user):
        return self.enrollments.filter(
            order__user=user,
            is_cancelled=False
        ).exists()
    

class CourseSession(models.Model):
    course = models.ForeignKey(TrainerCource, on_delete=models.CASCADE, related_name='sessions')
    session_date = models.DateField()
    zego_room_id = models.CharField(max_length=255)
    zego_token = models.TextField()
    is_completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

class SessionParticipant(models.Model):
    session = models.ForeignKey(CourseSession, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)