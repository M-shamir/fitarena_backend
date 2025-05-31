# zego_service.py
import jwt
import time
from django.conf import settings

class ZegoCloudService:
    @staticmethod
    def generate_token(user_id, room_id, role='host', expired_in=3600):
        """Generate ZegoCloud token with specified role and expiration"""
        app_id = settings.ZEGO_APP_ID
        server_secret = settings.ZEGO_APP_SECRET
        
        payload = {
            "app_id": app_id,
            "user_id": str(user_id),
            "room_id": room_id,
            "privilege": {
                1: 1,  # login privilege
                2: 1 if role == 'host' else 0  # publish privilege
            },
            "expire_time": int(time.time()) + expired_in
        }
        
        # Generate token
        token = jwt.encode(
            payload,
            server_secret,
            algorithm='HS256',
            headers={'alg': 'HS256', 'typ': 'JWT'}
        )
        
        return token

    @staticmethod
    def create_room(room_id, room_name):
        """Create a room in ZegoCloud (if needed)"""
        # Note: With ZegoCloud, rooms are created automatically when first user joins
        return {"room_id": room_id, "room_name": room_name}