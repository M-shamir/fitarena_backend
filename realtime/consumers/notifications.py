from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed

class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Get JWT token from cookies
        cookies = self.scope.get('cookies', {})
        jwt_token = cookies.get('access_token')  # or whatever your JWT cookie is named
        
        if not jwt_token:
            await self.close(code=4001)
            return

        # Authenticate using JWT
        try:
            jwt_auth = JWTAuthentication()
            validated_token = await database_sync_to_async(jwt_auth.get_validated_token)(jwt_token)
            self.user = await database_sync_to_async(jwt_auth.get_user)(validated_token)
            self.scope['user'] = self.user
        except (InvalidToken, AuthenticationFailed):
            await self.close(code=4001)
            return

        if not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.group_name = f'notifications_{self.user.id}'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()