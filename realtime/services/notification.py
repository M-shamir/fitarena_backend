from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from realtime.models import Notification

class NotificationService:
    @staticmethod
    def send_notification_to_user(user_id, message,related_url=None):
        notification = Notification.objects.create(
            user_id=user_id,
            message=message,
            related_url=related_url
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{user_id}',
            {
                'type': 'send_notification',
                'data': {
                    'id': notification.id,
                    'message': notification.message,
                    'related_url': notification.related_url,
                    'read': notification.read,
                    'created_at': notification.created_at.isoformat()
                }
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