from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer
from django.utils import timezone
from services.email_service import send_otp_email
from services.otp_service import generate_otp,store_otp
from django.core.cache import  cache
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from core.utils import generate_jwt_response
from account.views import BaseSignupView,BaseLoginView,BaseVerifyOtp,BaseResendOtp
from account.serializers import LoginSerializer
import logging
# Create your views here.

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
    
        


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]
    def post(self,request,*args,**kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response({"error": "Refresh token is missing"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            refresh=RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            return Response({"access": access_token}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": "Invalid or expired refresh token"}, status=status.HTTP_401_UNAUTHORIZED)
