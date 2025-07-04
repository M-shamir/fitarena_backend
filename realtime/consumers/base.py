from channels.generic.websocket import AsyncJsonWebsocketConsumer

class BaseWebSocketConsumer(AsyncJsonWebsocketConsumer):
    """Handles core connection logic"""
    group_prefix = None
    
    async def connect(self):
        if self.group_prefix is None:
            raise NotImplementedError("Child classes must define group_prefix")
            
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
        else:
            self.group_name = f"{self.group_prefix}_{user.id}"
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )