from django.shortcuts import render
from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import AdminLoginSerializer
from trainer.serializers import TrainerSerializer
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from .serializers import TrainerListSerializer
from core.permission import IsAdmin
from trainer.models import TrainerProfile
# Create your views here.

User = get_user_model()
class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = AdminLoginSerializer(data=request.data, context={"expected_role": "admin"})
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user"]

        if not user.is_staff:
            return Response({"error": "Unauthorized: not an admin user"}, status=status.HTTP_403_FORBIDDEN)

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        access['role'] = "admin"  # Custom claim for client side

        expires = datetime.utcnow() + timedelta(hours=2)

        # Prepare response
        response = Response({
            "message": "Admin login successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": "admin",
            }
        }, status=status.HTTP_200_OK)

        
        response.set_cookie(
            key="access_token",
            value=str(access),
            httponly=True,
            expires=expires,
            samesite='Lax',
            secure=False 
         
        )
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            expires=datetime.utcnow() + timedelta(days=7),
            samesite='Lax',
            secure=False 
            
        )

        return response


class UserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, *args, **kwargs):
        
        
        users = User.objects.exclude(
            is_superuser=True
        ).exclude(
            role__in=["trainer", "stadium_owner"]
        ).values(
            "id", "username", "email", "role", "profile_photo", "is_staff", "is_verified"
        )

        return Response({"users": list(users)}, status=status.HTTP_200_OK)  

class   BlockUnblockUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

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

class TrainerPendingAprrovalView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        pending_trainers = User.objects.filter(role="trainer", is_approved="pending")
        serializer = TrainerListSerializer(pending_trainers, many=True)
        
        return Response({"pending_trainers": serializer.data}, status=status.HTTP_200_OK)




class ApproveTrainerView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, trainer_id):
        if not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        try:
            trainer = User.objects.get(id=trainer_id, role="trainer", is_approved="pending")
        except User.DoesNotExist:
            return Response({"error": "Pending trainer not found."}, status=status.HTTP_404_NOT_FOUND)

        trainer.is_approved = "approved"
        trainer.save()

        return Response({"message": "Trainer approved successfully."}, status=status.HTTP_200_OK)

class RejectTrainerView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, trainer_id):
        if not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        try:
            trainer = User.objects.get(id=trainer_id, role="trainer", is_approved="pending")
        except User.DoesNotExist:
            return Response({"error": "Pending trainer not found."}, status=status.HTTP_404_NOT_FOUND)

        trainer.is_approved = "rejected"
        trainer.save()

        return Response({"message": "Trainer rejected successfully."}, status=status.HTTP_200_OK)
    
class ApprovedTrainerListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        # Only staff/admin can access this list
        if not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        approved_trainers = User.objects.filter(role="trainer", is_approved="approved")
        serializer = TrainerListSerializer(approved_trainers, many=True)

        return Response({"approved_trainers": serializer.data}, status=status.HTTP_200_OK)


class ListUnlistTrainerView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, trainer_id, *args, **kwargs):
        try:
            trainer = TrainerProfile.objects.get(id=trainer_id)
        except TrainerProfile.DoesNotExist:
            raise NotFound({"error": "Trainer not found"})
        trainer.listed = not trainer.listed
        trainer.save()
        status_text = "listed" if trainer.listed else "unlisted"
        return Response({"message": f"Trainer {trainer.user.username} has been {status_text}."},
                        status=status.HTTP_200_OK)