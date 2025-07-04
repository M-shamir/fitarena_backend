from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class NotificationService:
    @staticmethod
    def send_notification_to_user(user_id, message):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{user_id}',
            {
                'type': 'send_notification',
                'data': message
            }
        )
    
    @staticmethod
    async def async_send_notification_to_user(user_id, message):
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f'notifications_{user_id}',
            {
                'type': 'send_notification',
                'data': message
            }
        )