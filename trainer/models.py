from django.db import models
from django.conf import settings
# Create your models here.
class TrainerDetails(models.Model):

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trainer_profile")
    stadium_name = models.CharField(max_length=255, db_index=True)  
    