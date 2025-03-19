from django.shortcuts import render
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import AdminLoginSerializer
from django.contrib.auth import get_user_model
# Create your views here.

User = get_user_model()
class AdminLoginView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AdminLoginSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            response = Response({
                "user": data["user"],
                "access_token": data["access_token"],
            }, status=status.HTTP_200_OK)
            response.set_cookie(
                key="refresh_token",
                value=data["refresh_token"],
                httponly=True,
                secure=True,  # Ensure this is enabled in production (HTTPS required)
                samesite="Lax",
            )
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated] 

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        

        users = User.objects.exclude(
            is_superuser=True
        ).exclude(
            role__in=["trainer", "stadium_owner"]
        ).values(
            "id", "username", "email", "role", "profile_photo", "is_staff", "is_verified"
        )

        return Response({"users": list(users)}, status=status.HTTP_200_OK)  

class   BlockUnblockUserView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    def patch(self, request, user_id, *args, **kwargs):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise NotFound({"error": "User not found"})

        if user.is_superuser:
            raise PermissionDenied({"error": "Cannot modify a superuser"})

        user.is_active = not user.is_active
        user.save()
        status_text = "unblocked" if user.is_active else "blocked"
        return Response({"message": f"User {user.username} has been {status_text}."}, status=status.HTTP_200_OK)
