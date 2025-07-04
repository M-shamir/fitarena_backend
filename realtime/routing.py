# realtime/routing.py

from django.urls import re_path

def get_websocket_urlpatterns():
    from .consumers.notifications import NotificationConsumer  # Move import inside
    return [
        re_path(r"ws/notifications/$", NotificationConsumer.as_asgi()),
    ]
