from django.urls import path
from .views import CreateCoursePaymentAPIView,VerifyPaymentAPIView

urlpatterns = [
    path('course/<int:course_id>/', CreateCoursePaymentAPIView.as_view(), name='create_course_payment'),
    path('verify/', VerifyPaymentAPIView.as_view(), name='verify_payment'),
]
