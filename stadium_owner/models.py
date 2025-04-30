from django.contrib.gis.db import models
from django.conf import settings
from django.contrib.gis.geos import Point



class StadiumOwnerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="stadiumowner_profile")
    phone_number = models.CharField(max_length=15)
    document = models.FileField(upload_to='stadiumonwer_document/',blank=True,null=True)
    listed = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - Stadium Owner Profile"


