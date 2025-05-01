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
from .serializers import TrainerListSerializer,StadiumListSerializer,TrainerCourceSerializer
from core.permission import IsAdmin
from trainer.models import TrainerProfile,TrainerCource
from stadium_owner.models import StadiumOwnerProfile,Stadium
from stadium_owner.serializers import StadiumSerializer
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

class TrainerPendingCourceListView(APIView):
    permission_classes = [IsAuthenticated,IsAdmin]
    def get(self,request,*args,**kwargs):
        try:

            pending_cource = TrainerCource.objects.filter(status='pending',approval_status='pending',is_deleted=False,)
            serializer = TrainerCourceSerializer(pending_cource,many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ApproveTrainerCourceView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, cource_id):
        try:
            cource = TrainerCource.objects.get(id=cource_id, status="pending", is_deleted=False)
        except TrainerCource.DoesNotExist:
            return Response({"error": "Pending course not found."}, status=status.HTTP_404_NOT_FOUND)

        cource.status = "approved"
        cource.approval_status = "approved"
        cource.approval_note = request.data.get("approval_note", "")
        cource.save()

        return Response({"message": "Trainer course approved successfully."}, status=status.HTTP_200_OK)


class RejectTrainerCourceView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, cource_id):
        try:
            cource = TrainerCource.objects.get(id=cource_id, status="pending", is_deleted=False)
        except TrainerCource.DoesNotExist:
            return Response({"error": "Pending course not found."}, status=status.HTTP_404_NOT_FOUND)

        
        cource.is_approved = False
        
        cource.save()

        return Response({"message": "Trainer course rejected successfully."}, status=status.HTTP_200_OK)


class PendingStadiumOwnerApprovalView(APIView):
    permission_classes = [IsAuthenticated,IsAdmin]
    def get(self,request,*args,**kwargs):
        if not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        pending_stadium_owners = User.objects.filter(role='stadium_owner',is_approved='pending')
        serializer = StadiumListSerializer(pending_stadium_owners,many=True)
        return Response({"pending_stadium_owners":serializer.data},status=status.HTTP_200_OK)

class ApprovedStadiumOwnerListView(APIView):
    permission_classes = [IsAuthenticated,IsAdmin]

    def get(self,request,*args,**kwargs):
        if not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        approved_stadium_owners =  User.objects.filter(role='stadium_owner',is_approved='approved')
        serializer = StadiumListSerializer(approved_stadium_owners,many=True)
        return   Response({"approved_stadium_owners":serializer.data},status=status.HTTP_200_OK)




class ApprovedStadiumOwnerView(APIView):
    permission_classes = [IsAuthenticated,IsAdmin]
    def post(self,request,stadium_owner_id):
        if not request.user.is_staff:
            return Response({"error":"Unauthorized"},status=status.HTTP_403_FORBIDDEN)
        try:
            stadium_owner = User.objects.get(id=stadium_owner_id,role='stadium_owner',is_approved='pending')
        except User.DoesNotExist:
            return Response({"error":"User not Found"},status=status.HTTP_404_NOT_FOUND)
        stadium_owner.is_approved = "approved"
        stadium_owner.save()
        return Response({"message":"Approved Succesfully"},status=status.HTTP_200_OK)

class RejectStadiumOwnerView(APIView):
    permission_classes = [IsAuthenticated,IsAdmin]

    def post(self,request,stadium_owner_id):
        if not request.user.is_staff:
            return  Response({"error":"Unauthorized"},status=Status.HTTP_403_FORBIDDEN)
        try:
            stadium_owner = User.objects.get(id=stadium_owner_id,role='stadium_owner',is_approved='pending')
        except User.DoesNotExist:
            return   Response({"error":"User Not Found"},status=status.HTTP_404_NOT_FOUND)
        stadium_owner.is_approved ='rejected'
        stadium_owner.save()
        return  Response({"message":"Rejected"},status=status.HTTP_200_OK)

    
class ListUnlistStadiumOwnerView(APIView):
    permission_classes = [IsAuthenticated,IsAdmin]
    
    def post(self,request,stadium_owner_id,*args,**kwargs):
        try:
            stadium_owner = StadiumOwnerProfile.objects.get(user_id=stadium_owner_id)
        except StadiumOwnerProfile.DoesNotExist:
            return Response({"message":"User not found"},status=status.HTTP_404_NOT_FOUND)
        stadium_owner.listed = not stadium_owner.listed
        stadium_owner.save()
        status_text = "listed" if stadium_owner.listed else "unlisted"
        return Response({"message":status_text},status=status.HTTP_200_OK)

class PendingStadiumListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        pending_stadiums = Stadium.objects.filter(approval_status='pending', is_deleted=False)
        serializer = StadiumSerializer(pending_stadiums, many=True)
        return Response({"pending_stadiums": serializer.data}, status=status.HTTP_200_OK)

class ApprovedStadiumListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        approved_stadiums = Stadium.objects.filter(approval_status='approved', is_deleted=False)
        serializer = StadiumSerializer(approved_stadiums, many=True)
        return Response({"approved_stadiums": serializer.data}, status=status.HTTP_200_OK)

class ApproveStadiumView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def post(self, request, stadium_id):
        try:
            stadium = Stadium.objects.get(id=stadium_id, approval_status='pending')

        except Stadium.DoesNotExist:
            return Response(
                {"error": "Stadium not found or already processed"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        stadium.approval_status = 'approved'
        stadium.save()
        return Response(
            {"message": "Stadium approved successfully"},
            status=status.HTTP_200_OK
        )

class RejectStadiumView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def post(self, request, stadium_id):
        try:
            stadium = Stadium.objects.get(id=stadium_id, approval_status='pending')
        except Stadium.DoesNotExist:
            return Response(
                {"error": "Stadium not found or already processed"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        stadium.approval_status = 'rejected'
        stadium.save()
        
        
        return Response(
            {"message": "Stadium rejected successfully"},
            status=status.HTTP_200_OK
        )


class ListUnlistStadiumView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, stadium_id, *args, **kwargs):
        try:
            stadium = Stadium.objects.get(id=stadium_id)
        except Stadium.DoesNotExist:
            return Response({"message": "Stadium not found"}, status=status.HTTP_404_NOT_FOUND)

        stadium.listed = not stadium.listed 
        stadium.save()
        
        status_text = "listed" if stadium.listed else "unlisted"
        return Response({"message": f"Stadium successfully {status_text}."}, status=status.HTTP_200_OK)


class AdminLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response({"message": "Admin logged out successfully."}, status=status.HTTP_200_OK)

        
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return response