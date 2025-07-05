# notifications/urls.py
from django.urls import path
from .views import NotificationListView, MarkNotificationAsReadView, MarkAllNotificationsAsReadView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<int:notification_id>/read/', MarkNotificationAsReadView.as_view(), name='mark-notification-read'),
    path('read-all/', MarkAllNotificationsAsReadView.as_view(), name='mark-all-notifications-read'),
]