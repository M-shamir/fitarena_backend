# fitarena/asgi.py

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitarena.settings')
django.setup()

from channels.auth import AuthMiddlewareStack
from realtime.routing import get_websocket_urlpatterns  # Import function

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            get_websocket_urlpatterns()  
        )
    ),
})
