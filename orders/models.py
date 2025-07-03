from django.db import models
from django.conf import settings
from trainer.models import TrainerCource
from stadium_owner.models import Slot

class Order(models.Model):
    ORDER_TYPES = [
        ('course', 'Training Course'),
        ('slot', 'Stadium Slot'),
    ]
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPES)
    stripe_session_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20,choices=ORDER_STATUS, default='pending')
    refund_id = models.CharField(max_length=255, blank=True, null=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    refunded_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

class CourseEnrollment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='course_enrollment')
    course = models.ForeignKey(TrainerCource, on_delete=models.PROTECT, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_cancelled = models.BooleanField(default=False)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-enrolled_at']
        indexes = [
            models.Index(fields=['course', 'is_cancelled']),
        ]

    def __str__(self):
        return f"{self.order.user.email} - {self.course.title}"

class SlotBooking(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='slot_bookings')
    slot = models.ForeignKey(Slot, on_delete=models.PROTECT)
    booking_date = models.DateField()
    booked_at = models.DateTimeField(auto_now_add=True)
    is_cancelled = models.BooleanField(default=False)
    cancelled_at = models.DateTimeField(blank=True, null=True)
