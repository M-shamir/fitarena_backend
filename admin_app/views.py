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
from .serializers import TrainerListSerializer,StadiumListSerializer,TrainerCourceSerializer,UserListSerializer,EarningsSummarySerializer
from core.permission import IsAdmin
from trainer.models import TrainerProfile,TrainerCource
from stadium_owner.models import StadiumOwnerProfile,Stadium
from stadium_owner.serializers import StadiumSerializer
from trainer.services.course_service import TrainerCourseService
from rest_framework.pagination import PageNumberPagination
from realtime.services.notification import NotificationService
from trainer.models import TrainerProfile, TrainerCource
from stadium_owner.models import StadiumOwnerProfile, Slot
from orders.models import Order, CourseEnrollment, SlotBooking
from .serializers import EarningsSummarySerializer
from django.db.models import Sum, Count
from django.db.models import Q
from account_app.models import User  # Your custom User model
from .serializers import RecentUserSerializer

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
        ).order_by('id')  # Add ordering for consistent pagination
        
        # Create paginator instance
        paginator = PageNumberPagination()
        paginator.page_size = request.GET.get('page_size', 5) 
        
        # Paginate the queryset
        result_page = paginator.paginate_queryset(users, request)
        
        serializer = UserListSerializer(result_page, many=True)
        
        # Return paginated response
        return paginator.get_paginated_response(serializer.data)

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

        # Update course status
        cource.status = "approved"
        cource.approval_status = "approved"
        cource.approval_note = request.data.get("approval_note", "")
        cource.save()

        
        try:
            TrainerCourseService.approve_course(cource.id)
        except Exception as e:
            # Log the error but don't fail the approval
            # You might want to add proper logging here
            print(f"Error creating sessions: {str(e)}")

        trainer_user_id = cource.trainer.user.id
        NotificationService.send_notification_to_user(
            trainer_user_id,
            f"🎓 Congratulations! Your course '{cource.title}' has been approved and is now live on FitArena."
        )

        return Response(
            {"message": "Trainer course approved and sessions created successfully."},
            status=status.HTTP_200_OK
        )


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

class ApprovedTrainerCourceListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, *args, **kwargs):
        approved_cources = TrainerCource.objects.filter(
            status='approved',
            approval_status='approved',
            is_deleted=False
        )
        paginator = PageNumberPagination()
        paginator.page_size = request.GET.get('page_size', 5) 
        
        # Paginate the queryset
        result_page = paginator.paginate_queryset(approved_cources, request)

        serializer = TrainerCourceSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)



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
        owner_user_id = stadium.owner.user.id
        NotificationService.send_notification_to_user(
            owner_user_id,
            f"🏟️ Great news! Your stadium '{stadium.name}' has been approved and is now live on FitArena. You can now start receiving bookings."
        )

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
    

class EarningsSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    def get(self, request):
        role = request.query_params.get('role')

        if role not in ['trainer', 'stadium_owner']:
            return Response({'error': 'Invalid role. Use ?role=trainer or ?role=stadium_owner'}, status=400)

        response_data = []

        if role == 'trainer':
            trainers = TrainerProfile.objects.select_related('user').all()

            for trainer in trainers:
                courses = TrainerCource.objects.filter(trainer=trainer)
                enrollments = CourseEnrollment.objects.filter(
                    course__in=courses,
                    order__status='completed'
                )

                total_earned = enrollments.aggregate(
                    total=Sum('order__amount'),
                    count=Count('order')
                )

                response_data.append({
                    'user_id': trainer.user.id,
                    'username': trainer.user.username,
                    'email': trainer.user.email,
                    'role': trainer.user.role,
                    'profile_id': trainer.id,
                    'total_earnings': total_earned['total'] or 0.00,
                    'number_of_orders': total_earned['count']
                })

        elif role == 'stadium_owner':
            owners = StadiumOwnerProfile.objects.select_related('user').all()

            for owner in owners:
                # ✅ FIXED: Traverse through the stadium relation
                slots = Slot.objects.filter(stadium__owner=owner)

                bookings = SlotBooking.objects.filter(
                    slot__in=slots,
                    order__status='completed'
                )

                total_earned = bookings.aggregate(
                    total=Sum('order__amount'),
                    count=Count('order')
                )

                response_data.append({
                    'user_id': owner.user.id,
                    'username': owner.user.username,
                    'email': owner.user.email,
                    'role': owner.user.role,
                    'profile_id': owner.id,
                    'total_earnings': total_earned['total'] or 0.00,
                    'number_of_orders': total_earned['count']
                })

        serializer = EarningsSummarySerializer(response_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class UserStatsSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    def get(self, request):
        # Filter approved & verified users only
        approved_verified_filter = Q(is_verified=True) & Q(is_approved='approved')

        total_users = User.objects.filter(approved_verified_filter, role='user').count()
        total_trainers = User.objects.filter(approved_verified_filter, role='trainer').count()
        total_owners = User.objects.filter(approved_verified_filter, role='stadium_owner').count()

        recent_users = User.objects.exclude(role='admin').order_by('-date_joined')[:5]

        response_data = {
            "total_users": total_users,
            "total_trainers": total_trainers,
            "total_stadium_owners": total_owners,
            "recent_signups": RecentUserSerializer(recent_users, many=True).data
        }

        return Response(response_data, status=status.HTTP_200_OK)