from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer,TrainerCourceSerializer,TrainerProfileSerializer,TrainerTypeSerializer,StadiumSerializer
from django.utils import timezone
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
from stadium_owner.models import Stadium
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D

from django.conf import settings
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
    
class UserTrainerCoursesView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        courses = TrainerCource.objects.filter(
            approval_status='approval',
            is_deleted=False,
            trainer__listed=True
        ).select_related('trainer__user', 'trainer_type').prefetch_related('trainer__trainer_type', 'trainer__languages_spoken')

        serializer = TrainerCourceSerializer(courses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserTrainerCourseDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, course_id):
        course = get_object_or_404(
            TrainerCource.objects.select_related('trainer__user', 'trainer_type')
            .prefetch_related('trainer__trainer_type', 'trainer__languages_spoken'),
            id=course_id,
            approval_status='approval',
            is_deleted=False,
            trainer__listed=True
        )

        serializer = TrainerCourceSerializer(course)
        return Response(serializer.data, status=status.HTTP_200_OK)
    



class NearbyStadiumsAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        
        try:
            # If location provided, filter by distance
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
        
        # Prefetch related data to optimize queries
        stadium = Stadium.objects.select_related(
            'owner', 
            'owner__user'
        ).prefetch_related(
            'slots'
        ).get(pk=pk)
        
        serializer = StadiumSerializer(stadium)
        return Response(serializer.data, status=status.HTTP_200_OK)