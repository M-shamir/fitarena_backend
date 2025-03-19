from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()

class AdminLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self,data):
        username = data.get("username")
        password = data.get("password")

        user = authenticate(username=username,password=password)

        if not user:
            raise AuthenticationFailed("Invalid credentials")

        if not user.is_superuser:
            raise AuthenticationFailed("You are not authorized as an admin")
        
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "is_superuser": user.is_superuser,
            },
            "access_token": access,
            "refresh_token": str(refresh),
        }