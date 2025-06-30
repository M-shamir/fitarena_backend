from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import *
from datetime import date, timedelta
from django.utils import timezone
from datetime import datetime
from django.db.models import DateTimeField, ExpressionWrapper, F, Func
from rest_framework import generics
from services.email_service import send_otp_email
from services.otp_service import generate_otp,store_otp
from django.core.cache import  cache
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from core.utils import generate_jwt_response
from account_app.views import BaseSignupView,BaseLoginView,BaseVerifyOtp,BaseResendOtp,BaseForgotPassword,BaseResetPassword,BaseLogoutView,BaseProfileView,BaseProfileEditView,BaseTokenRefreshView
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
from orders.models import *
from trainer.services.zego_service import ZegoCloudService
import logging
from django.db.models import Q
from datetime import datetime



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

class UserTokenRefreshView(BaseTokenRefreshView):
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


class UserProfileEditView(BaseProfileEditView):
    user_type = 'user'
    

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
                    location__distance_lte=(user_location, D(km=settings.SEARCH_RADIUS_KM))
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

        # Get today's date and add 1 day (tomorrow)
        tomorrow = date.today() + timedelta(days=1)

        courses = TrainerCource.objects.filter(
            trainer=trainer,
            approval_status='approved',
            is_deleted=False,
            start_date__gte=tomorrow  
        ).select_related('trainer', 'trainer_type')\
         .prefetch_related(
            'trainer__trainer_type', 
            'trainer__languages_spoken',
            'enrollments'
         )

        serializer = TrainerCourceSerializer(courses, many=True, context={'request': request})
        
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


        today_slots = Slot.objects.filter(
            stadium_id=stadium_id,
            date=today,
            start_time__gt=current_time,
            status='available'
        )

        
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
            
            
            if not session.course.enrollments.filter(order__user=user).exists():
                return Response(
                    {"detail": "You are not enrolled in this course."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
           
            token = ZegoCloudService.generate_token(
                user_id=user.id,
                room_id=session.zego_room_id,
                role='user',  
                expired_in=3600
            )
            
            
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



class UserEnrolledCoursesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserEnrolledCourseSerializer

    def get_queryset(self):
        
        today = timezone.now().date()
        return CourseEnrollment.objects.filter(
            order__user=self.request.user,
            is_cancelled=False,
            course__start_date__gt=today
        ).select_related('course', 'course__trainer', 'course__trainer__user')
    

class CancelCourseEnrollmentView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = CourseEnrollment.objects.all()
    lookup_field = 'id'

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        
        if instance.order.user != request.user:
            return Response(
                {"detail": "You don't have permission to cancel this enrollment."},
                status=status.HTTP_403_FORBIDDEN
            )
        
       
        today = timezone.now().date()
        if instance.course.start_date <= today:
            return Response(
                {"detail": "Cannot cancel enrollment after the course has started."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
       
        instance.is_cancelled = True
        instance.cancelled_at = timezone.now()
        instance.save()
        
        return Response(
            {"detail": "Course enrollment cancelled successfully."},
            status=status.HTTP_200_OK
        )
    


class PastCoursesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PastCourseSerializer

    def get_queryset(self):
        today = timezone.now().date()
        return CourseEnrollment.objects.filter(
            Q(order__user=self.request.user),
            Q(is_cancelled=True) | 
            Q(  
                is_cancelled=False,
                course__end_date__lt=today
            )
        ).select_related(
            'course',
            'course__trainer',
            'course__trainer__user'
        ).order_by('-cancelled_at', '-course__end_date')
    




class UserUpcomingSlotBookingsAPI(generics.ListAPIView):
    serializer_class = UserSlotSerializer

    def get_queryset(self):
        user = self.request.user
        now = timezone.now()
        cutoff = now + timedelta(hours=1)

        return Slot.objects.filter(
            booked_by=user,
            status='booked'
        ).filter(
            Q(date__gt=cutoff.date()) |
            Q(date=cutoff.date(), start_time__gte=cutoff.time())
        ).select_related('stadium')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    

class UserCurrentAndNextSlotBookingsAPI(generics.ListAPIView):
    serializer_class = UserSlotSerializer

    def get_queryset(self):
        user = self.request.user
        now = timezone.now()
        current_time = now.time()
        today = now.date()

        queryset = Slot.objects.filter(
            booked_by=user,
            status='booked'
        ).filter(
            Q(date__gt=today) |
            Q(date=today, end_time__gte=current_time)
        ).select_related('stadium').order_by('date', 'start_time')

        
        print(queryset.query)
        print(list(queryset.values('id', 'date', 'start_time', 'end_time')))
        
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        now = timezone.now()
        current_time = now.time()
        today = now.date()

        ongoing_slot = None
        upcoming_slot = None

        for slot in queryset:
            print(f"Checking slot {slot.id}: {slot.date} {slot.start_time}-{slot.end_time}")
            
           
            if (slot.date == today and 
                slot.start_time <= current_time <= slot.end_time):
                print("Found ongoing slot")
                ongoing_slot = slot
                continue
            
           
            if ongoing_slot:
                if (slot.date > ongoing_slot.date or 
                    (slot.date == ongoing_slot.date and slot.start_time > ongoing_slot.end_time)):
                    print("Found upcoming slot after ongoing")
                    upcoming_slot = slot
                    break
            else:
                
                if (slot.date > today or 
                    (slot.date == today and slot.start_time > current_time)):
                    print("Found upcoming slot (no ongoing)")
                    upcoming_slot = slot
                    break

        result = {
            'ongoing': ongoing_slot,
            'upcoming': upcoming_slot
        }

        print(f"Final result: {result}")
        serializer = UserCurrentNextSlotSerializer(result, context={'request': request})
        return Response(serializer.data)
    
class UserPastSlotBookingsAPI(generics.ListAPIView):
    serializer_class = UserSlotSerializer
    queryset = Slot.objects.none()  

    def get_queryset(self):
        user = self.request.user
        now = timezone.now()
        current_time = now.time()
        today = now.date()

        # Get all truly past bookings (completely finished)
        return Slot.objects.filter(
            booked_by=user,
            status='booked'
        ).filter(
            Q(date__lt=today) |  # All slots from previous days
            Q(date=today, end_time__lt=current_time)  # Today's slots that have completely ended
        ).exclude(
            Q(date=today, start_time__lte=current_time, end_time__gte=current_time)  # Exclude ongoing slot
        ).select_related('stadium').order_by('-date', '-end_time')  # Most recent first

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    

class CancelSlotBookingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        try:
            # Get the booking
            booking = get_object_or_404(
                SlotBooking, 
                id=booking_id,          # This should be the SlotBooking ID (14 in your case)
                order__user=request.user,
                is_cancelled=False
            )
            
            # Get the associated slot
            slot = booking.slot
            
            # Update booking status
            booking.is_cancelled = True
            booking.cancelled_at = timezone.now()
            booking.save()
            
            # Update slot status
            slot.status = 'available'
            slot.booked_by = None
            slot.save()
            
            # Update order status
            booking.order.status = 'cancelled'
            booking.order.save()
            
            return Response(
                {"detail": "Booking cancelled successfully."},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )