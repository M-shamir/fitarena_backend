from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from core.permission import IsTrainer
from rest_framework.views import APIView
from .serializers import TrainerSerializer,TrainerTypeSerializer,LanguageSerializer
from services.email_service import send_otp_email
from services.otp_service import generate_otp,store_otp
from django.core.cache import  cache
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from core.utils import generate_jwt_response
from account_app.views import BaseSignupView,BaseLoginView,BaseVerifyOtp,BaseResendOtp,BaseLogoutView
from account_app.serializers import LoginSerializer
from .models import TrainerType,Language
from rest_framework.permissions import AllowAny
import logging


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