from rest_framework import status
from rest_framework import generics
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.permission import IsTrainer
from rest_framework.views import APIView
from .serializers import *
from services.email_service import send_otp_email
from services.otp_service import generate_otp,store_otp
from django.core.cache import  cache
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from core.utils import generate_jwt_response
from account_app.views import BaseSignupView,BaseLoginView,BaseVerifyOtp,BaseResendOtp,BaseLogoutView,BaseProfileView,BaseForgotPassword,BaseResetPassword,BaseTokenRefreshView
from account_app.serializers import LoginSerializer,ResetPasswordSerializer,ForgotPasswordSerializer
from .models import TrainerType,Language,TrainerProfile,TrainerCource
from rest_framework.permissions import AllowAny
from .services.course_service import TrainerCourseService
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.generics import DestroyAPIView
from .models import TrainerCource, CourseSession, SessionParticipant
from django.db.models import Count, Q
from .services.zego_service import ZegoCloudService
from orders.models import CourseEnrollment
from django.utils import timezone
from datetime import datetime, timedelta
import logging
from orders.models import *
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum, Q
import datetime
from rest_framework.response import Response
from rest_framework import status
import time
import hashlib
import hmac




# Create your views here.
logger = logging.getLogger(__name__)
User = get_user_model()


class TrainerSignUpView(BaseSignupView):
    
    serializer_class = TrainerSerializer
    user_type = 'trainer'
    permission_classes = [AllowAny]

class TrainerVerifyOtpView(BaseVerifyOtp):
    user_role = 'trainer'

class TrainerResendOtpView(BaseResendOtp):
    pass


class TrainerLoginView(BaseLoginView):
    serializer_class = LoginSerializer
    user_type = 'trainer'

class TrainerTokenRefreshView(BaseTokenRefreshView):
    user_type = 'trainer'
    
class TrainerLogoutView(BaseLogoutView):
    user_type =  'trainer'

class TrainerTypeListView(generics.ListAPIView):
    queryset = TrainerType.objects.all()
    serializer_class=TrainerTypeSerializer
    permission_classes = [AllowAny]



class LanguageListView(generics.ListAPIView):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    permission_classes = [AllowAny]

class TrainerProfileView(BaseProfileView):
    permission_classes  = [IsTrainer]
    serializer_class = TrainerProfileSerializer
    user_type = 'trainer'

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            user_role = request.auth.get('role', None)

            if user_role != self.user_type:
                return Response({"error": "Unauthorized role"}, status=status.HTTP_403_FORBIDDEN)

            trainer_profile = user.trainer_profile  # This will fetch the TrainerProfile
            serializer = self.serializer_class(trainer_profile)

            return Response({
                "message": "Trainer Profile Fetched Successfully",
                "profile": serializer.data
            }, status=status.HTTP_200_OK)

        except TrainerProfile.DoesNotExist:
            return Response({"error": "Trainer profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    def patch(self, request, *args, **kwargs):
        user = request.user

        try:
            user_role = request.auth.get('role', None)
            if user_role != self.user_type:
                return Response({"error": "Unauthorized role"}, status=status.HTTP_403_FORBIDDEN)
            
            trainer_profile = user.trainer_profile
            serializer = self.serializer_class(trainer_profile, data=request.data, partial=True)

            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return Response({"message": "Profile Updated Successfully", "profile": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class TrainerForgotPassword(BaseForgotPassword):
    serializer_class = ForgotPasswordSerializer
    user_type = 'trainer'

class TrainerResetPasswordView(BaseResetPassword):
    serializer_class = ResetPasswordSerializer
    user_type = 'trainer'


class TrainerCreateCourceView(APIView):
    permission_classes = [IsAuthenticated, IsTrainer]
    def post(self,request,*args,**kwargs):
            user = request.user

            trainer = user.trainer_profile
            
            base_info = request.data.get('base_info')
            course_variant = request.data.get('course_variant')
            thumbnail = request.FILES.get('thumbnail')

            if not base_info or not course_variant:
                return Response(
                    {"error": "Both 'base_info' and 'course_variant' are required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
             # Create the course using the service
            course = TrainerCourseService.create_course(trainer, base_info, course_variant,thumbnail=thumbnail )
            course_serializer = TrainerCourceSerializer(course)
            return Response(
                {"message": "Course created successfully!", "course": course_serializer.data},
                status=status.HTTP_201_CREATED
            )
    

class PendingApprovalSessionsView(ListAPIView):
    permission_classes = [IsAuthenticated, IsTrainer] 
    serializer_class = TrainerCourceSerializer

    def get_queryset(self):
        
        user = self.request.user 

        try:
         
            trainer_profile = TrainerProfile.objects.get(user=user)

        except TrainerProfile.DoesNotExist:
            raise AuthenticationFailed('Trainer profile not found.')
        
        

        
        return TrainerCource.objects.filter(
            trainer=trainer_profile,
            status='pending',
            approval_status='pending',
            is_deleted=False
        )


class TrainerTypesView(APIView):
    permission_classes = [IsAuthenticated, IsTrainer] 
    def get(self, request):
        try:
            
            user = request.user
            
            trainer_profile = user.trainer_profile

            
            trainer_types = trainer_profile.trainer_type.all()

            
            serializer = TrainerTypeSerializer(trainer_types, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except TrainerProfile.DoesNotExist:
            return Response({"error": "Trainer profile not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ApprovedSessionsView(ListAPIView):
    permission_classes = [IsAuthenticated, IsTrainer] 
    serializer_class = TrainerCourceSerializer

    def get_queryset(self):
        

        user = self.request.user

        try:
            
            trainer_profile = TrainerProfile.objects.get(user=user)
        except TrainerProfile.DoesNotExist:
            raise AuthenticationFailed('Trainer profile not found.')
        
        return TrainerCource.objects.filter(
            trainer=trainer_profile,
            status="approved",
            approval_status = "approved"
        )


# class ApprovedSessionsView(ListAPIView):
#     permission_classes = [IsAuthenticated, IsTrainer] 
#     serializer_class = TrainerCourceSerializer

#     def get_queryset(self):
#         user = self.request.user

        

#         try:
#             trainer_profile = TrainerProfile.objects.get(user=user)
#         except TrainerProfile.DoesNotExist:
#             raise AuthenticationFailed('Trainer profile not found.')

      
#         return TrainerCource.objects.filter(
#             trainer=trainer_profile,
#             is_approved=True
#         )

class DeleteTrainerCourceView(DestroyAPIView):
    permission_classes = [IsAuthenticated, IsTrainer] 
    queryset = TrainerCource.objects.all()
    lookup_field = 'pk'

    def delete(self,request,*args,**kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()
        return Response({"detail": "Course deleted."}, status=204)


class TrainerPendingEditView(APIView):
    permission_classes = [IsAuthenticated, IsTrainer]

    def patch(self, request, *args, **kwargs):
        user = request.user
        pk = kwargs.get('pk')

        try:
            trainer_profile = TrainerProfile.objects.get(user=user)
        except TrainerProfile.DoesNotExist:
            raise PermissionDenied("Trainer profile not found.")

        try:
            cource = TrainerCource.objects.get(pk=pk, trainer=trainer_profile)
        except TrainerCource.DoesNotExist:
            raise NotFound("Course not found.")

        if cource.status != 'pending':
            return Response({'detail': 'Course is not in pending approval state.'}, status=400)

        serializer = TrainerCourceSerializer(cource, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class TrainerCourseEnrollmentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            trainer_profile = request.user.trainer_profile
        except TrainerProfile.DoesNotExist:
            return Response(
                {"detail": "Trainer profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        courses = TrainerCource.objects.filter(
            trainer=trainer_profile
        ).annotate(
            enrolled_users_count=Count(
                'enrollments',
                filter=Q(enrollments__is_cancelled=False)
            ),
            upcoming_sessions_count=Count(
                'sessions',
                filter=Q(sessions__session_date__gte=timezone.now().date(),
                        sessions__is_completed=False)
            )
        )
        
        data = [{
            'id': course.id,
            'title': course.title,
            'enrolled_users_count': course.enrolled_users_count,
            'upcoming_sessions_count': course.upcoming_sessions_count
        } for course in courses]
        
        return Response(data, status=status.HTTP_200_OK)
    
class CourseEnrolledUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        # Get the trainer profile for the current user
        try:
            trainer_profile = request.user.trainer_profile
        except TrainerProfile.DoesNotExist:
            return Response(
                {"detail": "Trainer profile not found."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Verify the course belongs to this trainer
        course = get_object_or_404(
            TrainerCource,
            id=course_id,
            trainer=trainer_profile
        )

        # Get all active enrollments for this course
        enrollments = CourseEnrollment.objects.filter(
            course=course,
            is_cancelled=False
        ).select_related('order__user').order_by('-enrolled_at')

        serializer = EnrolledUserSerializer(enrollments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class TrainerLiveSessionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            trainer_profile = request.user.trainer_profile
        except TrainerProfile.DoesNotExist:
            return Response(
                {"detail": "Trainer profile not found."},
                status=status.HTTP_403_FORBIDDEN
            )

        today = timezone.now().date()
        sessions = CourseSession.objects.filter(
            course__trainer=trainer_profile,
            session_date=today,
            is_completed=False
        ).annotate(
            participants_count=Count('participants')
        ).select_related('course').order_by('started_at')

        data = [{
            "id": session.id,
            "course_id": session.course.id,
            "course_title": session.course.title,
            "session_date": session.session_date,
            "start_time": session.started_at.time() if session.started_at else session.course.start_time,
            "zego_room_id": session.zego_room_id,
            "zego_token": session.zego_token,
            "participants_count": session.participants_count
        } for session in sessions]

        return Response(data, status=status.HTTP_200_OK)

class JoinSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        try:
            session = CourseSession.objects.get(id=session_id)
            user = request.user
            
            # Check if user is trainer or participant
            is_trainer = hasattr(user, 'trainer_profile') and user.trainer_profile == session.course.trainer
            role = 'host' if is_trainer else 'user'
            
            # Generate token (3600 seconds = 1 hour expiration)
            token = ZegoCloudService.generate_token(
                user_id=user.id,
                room_id=session.zego_room_id,
                role=role,
                expired_in=3600  # 1 hour expiration
            )
            
            # Update session if trainer is joining for the first time
            if is_trainer and not session.started_at:
                session.started_at = timezone.now()
                session.zego_token = token
                session.save()
            
            # Record participant if not trainer
            if not is_trainer:
                SessionParticipant.objects.get_or_create(
                    session=session,
                    user=user,
                    defaults={'joined_at': timezone.now()}
                )
            
            return Response({
                "room_id": session.zego_room_id,
                "token": token,
                "role": role,
                "user_id": str(user.id),
                "user_name": user.get_full_name() or user.username
            })
            
        except CourseSession.DoesNotExist:
            return Response(
                {"detail": "Session not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )




class DashboardStatsAPIView(APIView):
    def get(self, request, format=None):
        # Get current date and time
        now = timezone.now()
        today = now.date()
        last_month = today - timedelta(days=30)
        
        stats = {
            'total_clients': self.get_total_clients(),
            'upcoming_sessions': self.get_upcoming_sessions(),
            'active_plans': self.get_active_plans(),
            'revenue': self.get_revenue(),
            'clients_change': self.get_clients_change(last_month, today),
            'sessions_today': self.get_sessions_today(today),
            'plans_change': self.get_plans_change(last_month, today),
            'revenue_change': self.get_revenue_change(last_month, today)
        }
        return Response(stats, status=status.HTTP_200_OK)
    
    def get_total_clients(self):
        """Count unique users with active enrollments"""
        return CourseEnrollment.objects.filter(is_cancelled=False)\
                                      .values('order__user')\
                                      .distinct()\
                                      .count()
    
    def get_upcoming_sessions(self):
        """Count upcoming sessions (not completed, date >= today)"""
        return CourseSession.objects.filter(
            session_date__gte=timezone.now().date(),
            is_completed=False
        ).count()
    
    def get_active_plans(self):
        """Count active enrollments (not cancelled)"""
        return CourseEnrollment.objects.filter(is_cancelled=False).count()
    
    def get_revenue(self):
        """Sum of all successful orders"""
        result = Order.objects.filter(status='completed')\
                             .aggregate(total=Sum('amount'))
        return result['total'] or 0
    
    def get_clients_change(self, last_month, today):
        """Calculate client count change compared to last month"""
        # Count clients who enrolled before last month
        old_count = CourseEnrollment.objects.filter(
            enrolled_at__lt=last_month,
            is_cancelled=False
        ).values('order__user').distinct().count()
        
        # Count current clients
        current_count = self.get_total_clients()
        
        # Calculate percentage change (avoid division by zero)
        if old_count == 0:
            return 100 if current_count > 0 else 0
        return ((current_count - old_count) / old_count) * 100
    
    def get_sessions_today(self, today):
        """Count sessions scheduled for today"""
        return CourseSession.objects.filter(
            session_date=today,
            is_completed=False
        ).count()
    
    def get_plans_change(self, last_month, today):
        """Calculate active plans change compared to last month"""
        # Count active plans from last month
        old_count = CourseEnrollment.objects.filter(
            enrolled_at__lt=last_month,
            is_cancelled=False
        ).count()
        
        # Count current active plans
        current_count = self.get_active_plans()
        
        # Calculate absolute change
        return current_count - old_count
    
    def get_revenue_change(self, last_month, today):
        """Calculate revenue change compared to last month"""
        # Revenue from last month
        old_revenue = Order.objects.filter(
            status='completed',
            created_at__range=(last_month, today - timedelta(days=30))
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Current month revenue
        current_revenue = Order.objects.filter(
            status='completed',
            created_at__gte=today - timedelta(days=30)
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Calculate percentage change (avoid division by zero)
        if old_revenue == 0:
            return 100 if current_revenue > 0 else 0
        return ((current_revenue - old_revenue) / old_revenue) * 100

class TrainerPaymentHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        trainer_profile = request.user.trainer_profile
        
        
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)
        
       
        successful_orders = Order.objects.filter(
            course_enrollment__course__trainer=trainer_profile,
            status='completed'
        ).select_related('course_enrollment__course')
        
        
        weekly_earnings = successful_orders.filter(
            created_at__date__gte=start_of_week
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_earnings = successful_orders.filter(
            created_at__date__gte=start_of_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
      
        payment_history = []
        for order in successful_orders.order_by('-created_at'):
            payment_history.append({
                'id': order.id,
                'course_title': order.course_enrollment.course.title,
                'student_email': order.user.email,
                'amount': float(order.amount),
                'currency': order.currency,
                'payment_date': order.created_at,
                'course_id': order.course_enrollment.course.id
            })
        
        response_data = {
            'payment_history': payment_history,
            'earnings_summary': {
                'this_week': float(weekly_earnings),
                'this_month': float(monthly_earnings),
                'all_time': float(successful_orders.aggregate(total=Sum('amount'))['total'] or 0)
            }
        }
        
        return Response(response_data)