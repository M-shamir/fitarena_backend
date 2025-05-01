from django.contrib.gis.db import models
from django.conf import settings
from django.contrib.gis.db import models as gis_models



class StadiumOwnerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="stadiumowner_profile")
    phone_number = models.CharField(max_length=15)
    document = models.FileField(upload_to='stadiumonwer_document/',blank=True,null=True)
    listed = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - Stadium Owner Profile"


class Stadium(models.Model):
    owner = models.ForeignKey(
        'StadiumOwnerProfile',
        on_delete=models.CASCADE,
        related_name='stadiums'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
   
    location = gis_models.PointField(geography=True)
    
    
    address = models.TextField()
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)

    image = models.ImageField(upload_to='stadium_images/', blank=True, null=True)

    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    approval_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    
    listed = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.owner.user.username})"