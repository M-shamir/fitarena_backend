from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer,TrainerCourceSerializer,TrainerProfileSerializer,TrainerTypeSerializer
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