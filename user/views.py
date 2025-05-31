from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer,TrainerCourceSerializer,TrainerProfileSerializer,TrainerTypeSerializer,StadiumSerializer,SlotSerializer
from django.utils import timezone
from rest_framework import generics
from services.email_service import send_otp_email
from services.otp_service import generate_otp,store_otp
from django.core.cache import  cache
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from core.utils import generate_jwt_response
from account_app.views import BaseSignupView,BaseLoginView,BaseVerifyOtp,BaseResendOtp,BaseForgotPassword,BaseResetPassword,BaseLogoutView,BaseProfileView
from account_app.serializers import LoginSerializer,ForgotPasswordSerializer,ResetPasswordSerializer
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from trainer.models import TrainerCource
from stadium_owner.models import Stadium,Slot
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from trainer.models import TrainerProfile
from django.utils.timezone import now
from django.db.models import Sum
from django.conf import settings
from trainer.models import *
from trainer.services.zego_service import ZegoCloudService
import logging



logger = logging.getLogger(__name__)
User = get_user_model()

class SignUpView(BaseSignupView):
    serializer_class = UserSerializer
    user_type = 'user'
    

class UserVerifyOtpView(BaseVerifyOtp):
    user_role = 'user'
    
    
class UserResendOtpView(BaseResendOtp):
    pass



class LoginView(BaseLoginView):
    serializer_class = LoginSerializer
    user_type = 'user'
    
class UserLogoutView(BaseLogoutView):
    user_type = 'user'
    


class UserForgotPasswordView(BaseForgotPassword):
    serializer_class = ForgotPasswordSerializer
    user_type = 'user'

class UserResetPasswordView(BaseResetPassword):
    serializer_class = ResetPasswordSerializer
    user_type='user'

class UserProfileView(BaseProfileView):
    user_type ='user'
    

class NearbyStadiumsAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        
        try:
            
            if lat and lng:
                user_location = Point(float(lng), float(lat), srid=4326)
                
                stadiums = Stadium.objects.filter(
                    approval_status='approved',
                    listed=True,
                    is_deleted=False,
                    location__distance_lte=(user_location, D(km=50))
                ).annotate(
                    distance=Distance('location', user_location)
                ).order_by('distance')[:6]
                
                stadiums_data = [{
                    'id': stadium.id,
                    'name': stadium.name,
                    'description': stadium.description,
                    'address': stadium.address,
                    'city': stadium.city,
                    'state': stadium.state,
                    'distance': round(stadium.distance.km, 2),
                    'image_url': request.build_absolute_uri(stadium.image.url) if stadium.image else None
                } for stadium in stadiums]
                
                return Response({
                    'stadiums': stadiums_data,
                    'message': f'Showing {len(stadiums_data)} stadiums near your location'
                })
            
            
            else:
                stadiums = Stadium.objects.filter(
                    approval_status='approved',
                    listed=True,
                    is_deleted=False
                ).order_by('?')[:20]  
                
                stadiums_data = [{
                    'id': stadium.id,
                    'name': stadium.name,
                    'description': stadium.description,
                    'address': stadium.address,
                    'city': stadium.city,
                    'state': stadium.state,
                    'distance': None,  
                    'image_url': request.build_absolute_uri(stadium.image.url) if stadium.image else None
                } for stadium in stadiums]
                
                return Response({
                    'stadiums': stadiums_data,
                    'message': 'Showing popular stadiums (enable location to see nearby ones)'
                })
                
        except ValueError:
            return Response(
                {'error': 'Invalid latitude/longitude values'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class StadiumDetailAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        stadium = get_object_or_404(Stadium, pk=pk, listed=True, is_deleted=False)
        
        
        stadium = Stadium.objects.select_related(
            'owner', 
            'owner__user'
        ).prefetch_related(
            'slots'
        ).get(pk=pk)
        
        serializer = StadiumSerializer(stadium)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class AvailableTrainerAPIView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = TrainerProfileSerializer

    def get_queryset(self):
        return TrainerProfile.objects.filter(
            listed=True,
            courses__is_deleted=False,
            courses__approval_status='approved'
        ).distinct().prefetch_related('trainer_type', 'languages_spoken', 'user')
    

    
class TrainerCoursesAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, trainer_id):
        try:
            trainer = TrainerProfile.objects.get(id=trainer_id, listed=True)
        except TrainerProfile.DoesNotExist:
            return Response(
                {'error': 'Trainer not found or not listed.'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        courses = TrainerCource.objects.filter(
            trainer=trainer,
            approval_status='approved',
            is_deleted=False
        ).select_related('trainer', 'trainer_type')\
         .prefetch_related(
            'trainer__trainer_type', 
            'trainer__languages_spoken',
            'enrollments'  # Prefetch enrollments for counting
         )

        serializer = TrainerCourceSerializer(courses, many=True, context={'request': request})
        
        # Add enrollment info to each course in response
        response_data = serializer.data
        for course_data, course_obj in zip(response_data, courses):
            course_data['available_slots'] = course_obj.available_slots
            course_data['current_enrollments'] = course_obj.current_enrollments
        
        return Response(response_data, status=status.HTTP_200_OK)


class CourseDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, course_id):
        try:
            course = TrainerCource.objects.select_related('trainer', 'trainer_type')\
                .prefetch_related('trainer__trainer_type', 'trainer__languages_spoken')\
                .get(id=course_id, approval_status='approved', is_deleted=False)
        except TrainerCource.DoesNotExist:
            return Response(
                {'error': 'Course not found or not available.'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TrainerCourceSerializer(course)
        response_data = serializer.data
        response_data['available_slots'] = course.available_slots
        response_data['current_enrollments'] = course.current_enrollments
        
        return Response(response_data, status=status.HTTP_200_OK)


class AvailableUpcomingSlotsAPIView(APIView):
    permission_classes = [AllowAny]  

    def get(self, request, stadium_id):
        current_datetime = now()
        today = current_datetime.date()
        current_time = current_datetime.time()

        # Get today's future slots
        today_slots = Slot.objects.filter(
            stadium_id=stadium_id,
            date=today,
            start_time__gt=current_time,
            status='available'
        )

        # Get future days' slots
        future_slots = Slot.objects.filter(
            stadium_id=stadium_id,
            date__gt=today,
            status='available'
        )

        slots = today_slots.union(future_slots).order_by('date', 'start_time')

        serializer = SlotSerializer(slots, many=True)
        return Response(serializer.data)




class BookSlotsAPIView(APIView):
    def get(self, request, stadium_id):
        slot_ids_param = request.query_params.get('ids')

        if not slot_ids_param:
            return Response({'error': 'No slot IDs provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            slot_ids = [int(sid) for sid in slot_ids_param.split(',') if sid.strip().isdigit()]
        except ValueError:
            return Response({'error': 'Invalid slot ID format'}, status=status.HTTP_400_BAD_REQUEST)

       
        slots = Slot.objects.filter(id__in=slot_ids, stadium_id=stadium_id, status='available')

        if slots.count() != len(slot_ids):
            return Response({'error': 'Some slots are not available or do not exist'}, status=status.HTTP_400_BAD_REQUEST)

        
        if slots.values('stadium_id').distinct().count() > 1:
            return Response({'error': 'Slots do not belong to the same stadium'}, status=status.HTTP_400_BAD_REQUEST)

        total_price = sum([slot.price for slot in slots])

        slot_data = [{
            'id': slot.id,
            'start_time': slot.start_time,
            'end_time': slot.end_time,
            'price': str(slot.price),
            'status': slot.status,
            'stadium_id': slot.stadium_id,
        } for slot in slots]

        return Response({
            'slots': slot_data,
            'total_price': str(total_price)
        }, status=status.HTTP_200_OK)




class UserLiveSessionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            today = timezone.now().date()
            
            # Get sessions where user is enrolled and session is today
            sessions = CourseSession.objects.filter(
                course__enrollments__order__user=user,
                session_date=today,
                is_completed=False
            ).select_related('course', 'course__trainer__user').order_by('course__start_time')
            
            data = [{
                "id": session.id,
                "course_id": session.course.id,
                "course_title": session.course.title,
                "session_date": session.session_date,
                "start_time": session.course.start_time.strftime("%H:%M"),
                "end_time": session.course.end_time.strftime("%H:%M"),
                "zego_room_id": session.zego_room_id,
                "trainer_name": session.course.trainer.user.get_full_name(),
                "is_live": session.started_at is not None and session.ended_at is None,
                "thumbnail": request.build_absolute_uri(session.course.thumbnail.url) if session.course.thumbnail else None
            } for session in sessions]
            
            return Response(data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class UserJoinSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        try:
            session = CourseSession.objects.get(id=session_id)
            user = request.user
            
            # Verify user is enrolled in the course
            if not session.course.enrollments.filter(order__user=user).exists():
                return Response(
                    {"detail": "You are not enrolled in this course."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Generate token (3600 seconds = 1 hour expiration)
            token = ZegoCloudService.generate_token(
                user_id=user.id,
                room_id=session.zego_room_id,
                role='user',  # Always participant role for users
                expired_in=3600
            )
            
            # Record participant
            SessionParticipant.objects.get_or_create(
                session=session,
                user=user,
                defaults={'joined_at': timezone.now()}
            )
            
            return Response({
                "room_id": session.zego_room_id,
                "token": token,
                "role": 'user',
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