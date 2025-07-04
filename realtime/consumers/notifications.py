# realtime/consumers/notifications.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Lazy import of auth models
        from django.contrib.auth.models import AnonymousUser
        
        self.user = self.scope["user"]
        if isinstance(self.user, AnonymousUser):
            await self.close(code=4001)
            return
            
        await self.accept()
        await self.channel_layer.group_add(
            f"notifications_{self.user.id}",
            self.channel_name
        )