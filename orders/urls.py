# urls.py
from django.urls import path
from .views import UserBookingsView

urlpatterns = [
    path('bookings/', UserBookingsView.as_view(), name='user-bookings'),
]