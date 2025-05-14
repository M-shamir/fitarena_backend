from django.urls import path
from .views import (
    CreateCoursePaymentAPIView,
    VerifyPaymentAPIView,
    CreateSlotPaymentAPIView,
    VerifySlotPaymentAPIView
)

urlpatterns = [
    path('course/<int:course_id>/', CreateCoursePaymentAPIView.as_view(), name='create_course_payment'),
    path('verify/', VerifyPaymentAPIView.as_view(), name='verify_payment'),
    path('slot/', CreateSlotPaymentAPIView.as_view(), name='create_slot_payment'),
    path('verify-slot/', VerifySlotPaymentAPIView.as_view(), name='verify_slot_payment'),
]
