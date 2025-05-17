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


class Slot(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('blocked', 'Blocked'),
    ]

    stadium = models.ForeignKey(Stadium, on_delete=models.CASCADE, related_name='slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    price = models.DecimalField(max_digits=8, decimal_places=2)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    block_reason = models.CharField(max_length=100, blank=True, null=True)

    booked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='booked_slots'
    )

    blocked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blocked_slots'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('stadium', 'date', 'start_time')

    def __str__(self):
        return f"{self.stadium.name} | {self.date} | {self.start_time}-{self.end_time}"