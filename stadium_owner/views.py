from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import StadiumOwnerSerializer
from services.email_service import send_otp_email
from services.otp_service import generate_otp,store_otp
from django.core.cache import  cache
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from core.utils import generate_jwt_response
from account.views import BaseSignupView,BaseLoginView,BaseVerifyOtp,BaseResendOtp
from account.serializers import LoginSerializer
import logging


# Create your views here.
logger = logging.getLogger(__name__)
User = get_user_model()


class StadiumOwnerSignUpView(BaseSignupView):
    serializer_class =StadiumOwnerSerializer
    user_type = 'stadium_owner'

class StadiumOwnerVerifyOtpView(BaseVerifyOtp):
    user_role = 'stadium_owner'

class StadiumOwnerResendOtpView(BaseResendOtp):
    pass

class StadiumOwnerLoginView(BaseLoginView):
    serializer_class = LoginSerializer
    user_type = 'stadium_owner'