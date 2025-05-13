from django.db import models
from django.conf import settings
from trainer.models import TrainerCource
from stadium_owner.models import Slot

class Order(models.Model):
    ORDER_TYPES = [
        ('course', 'Training Course'),
        ('slot', 'Stadium Slot'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPES)
    stripe_session_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

class CourseEnrollment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='course_enrollment')
    course = models.ForeignKey(TrainerCource, on_delete=models.PROTECT)
    enrolled_at = models.DateTimeField(auto_now_add=True)

class SlotBooking(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='slot_booking')
    slot = models.ForeignKey(Slot, on_delete=models.PROTECT)
    booking_date = models.DateField()
    booked_at = models.DateTimeField(auto_now_add=True)