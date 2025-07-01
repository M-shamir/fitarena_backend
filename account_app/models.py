from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
        ('trainer', 'Trainer'),
        ('stadium_owner', 'Stadium Owner'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    email =  models.EmailField(unique=True)
    role = models.CharField(max_length=20,choices=ROLE_CHOICES)
    profile_photo  = models.ImageField(upload_to='profile/',default='test_uploads/profile-default.png')
    is_verified = models.BooleanField(default=False)
    is_approved = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending') 
    google_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    auth_provider = models.CharField(max_length=50, default='email')  
    def __str__(self):
        return self.username
    

