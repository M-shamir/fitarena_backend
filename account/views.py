from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from services.email_service import send_otp_email
from services.otp_service import store_otp
from core.utils import generate_jwt_response
from .serializers import VerifyOtpSerializer,ResendOtpSerializer
from django.core.cache import cache
from django.contrib.auth import get_user_model
from services.tasks import send_otp_email_task
import logging

# Create your views here.
User =  get_user_model()
logger = logging.getLogger(__name__)
COOLDOWN_TIME = 30

class  BaseSignupView(APIView):
    serializer_class = None
    user_type =  None

    def post(self,request,*args,**kwargs):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            otp =  store_otp(user.email)
            logger.info(f"Generated OTP: {otp} for {self.user_type} user: {user.email}")

            try:
                send_otp_email_task.delay(user.email, otp)
                logger.info(f"OTP sent to {user.email}")
            except Exception as e:
                logger.error(f"Error sending OTP: {str(e)}")
            response = Response({'message': "Account created successfully. OTP sent to your email."}, status=status.HTTP_201_CREATED)
            response.set_cookie('otp_email', user.email, max_age=600, httponly=True, samesite='Lax') 


            return response
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class BaseLoginView(APIView):
    serializer_class =None
    user_type = None

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user"]
        return generate_jwt_response(user)

class BaseVerifyOtp(APIView):
    user_role = None

    def post(self,request,*args,**kwargs):
        email = request.COOKIES.get('otp_email')  

        logger.info(f"Email from cookie: {email}")
        
        if not email:
            return Response({"error": "OTP session expired. Please sign up again."}, status=status.HTTP_400_BAD_REQUEST)
        

        data = request.data.copy()
        data['email'] = email  

      
        serializer = VerifyOtpSerializer(data=data, context={'request': request})  
        if  not serializer.is_valid():
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email,role=self.user_role)
            if user.is_verified:
                return Response({"message": "User is already verified."}, status=status.HTTP_400_BAD_REQUEST)
            user.is_verified = True
            user.save()
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        cache.delete(f'otp:{email}')
        cache.delete(f'otp_attempts:{email}')
        cache.delete(f'otp_blocked:{email}')
        logger.info(f"OTP for {email} has been successfully verified and deleted from cache.")
        
        response = Response({"message": "OTP verified successfully."}, status=status.HTTP_200_OK)
        response.delete_cookie('otp_email')
        return response
        

class BaseResendOtp(APIView):
    def post(self, request, *args, **kwargs):
        email =  request.COOKIES.get('otp_email')
        if not email:
            return Response({"error": "OTP session expired. Please sign up again."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ResendOtpSerializer(data={"email":email})

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        if cache.get(f'otp_blocked:{email}'):
            return Response({"error": "Your OTP attempts have been blocked. Please try again later."}, status=status.HTTP_400_BAD_REQUEST)
        otp = store_otp(email)

        try:
            send_otp_email_task.delay(email, otp)
        except Exception as e:
            return Response({"error": "Error sending OTP. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cache.set(f'otp_resend_cooldown:{email}', 1, timeout=COOLDOWN_TIME)

        return Response({"message": "OTP has been resent to your email."}, status=status.HTTP_200_OK)
