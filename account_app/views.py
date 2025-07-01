from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from services.email_service import send_otp_email
from services.otp_service import store_otp
from core.utils import generate_jwt_response
from .serializers import VerifyOtpSerializer,ResendOtpSerializer,BaseProfileSerializer
from django.core.cache import cache
from django.contrib.auth import get_user_model
from services.tasks import send_otp_email_task,send_password_reset_email_task
from django.contrib.auth.hashers import make_password
from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.exceptions import NotFound
from datetime import datetime, timedelta
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
import logging
import secrets
import requests 
# Create your views here.
User =  get_user_model()
logger = logging.getLogger(__name__)
COOLDOWN_TIME = 30

class  BaseSignupView(APIView):
    permission_classes = [AllowAny]
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
    
class GoogleLogin(APIView):
    permission_classes = [AllowAny] 
    def post(self, request):
        token = request.data.get('token')

        if not token:
            return Response(
                {'message': 'Google token not provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                token, 
                google_requests.Request(), 
                settings.GOOGLE_CLIENT_ID
            )

            # Validate token audience
            if idinfo['aud'] != settings.GOOGLE_CLIENT_ID:
                raise ValueError('Invalid audience')
                
            # Validate issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Invalid issuer')
                
            # Check email verification
            if not idinfo.get('email_verified', False):
                raise ValueError('Email not verified by Google')
            
            # Get or create user
            user, created = User.objects.get_or_create(
                email=idinfo['email'],
                defaults={
                    'username': idinfo['email'].split('@')[0],
                    'first_name': idinfo.get('given_name', ''),
                    'last_name': idinfo.get('family_name', ''),
                    'is_active': True,
                    'auth_provider': 'google',
                    'google_id': idinfo.get('sub'),
                    'role': 'user',  # Default role
                    'is_verified': True,  # Google verified email
                    'is_approved': 'approved'
                }
            )
            
            # Update user if not created (in case they logged in with email before)
            if not created:
                if not user.google_id:
                    user.google_id = idinfo.get('sub')
                if not user.is_verified:
                    user.is_verified = True
                user.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            
            # Add role to access token
            access['role'] = user.role
            
            # Prepare response
            response_data = {
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "is_verified": user.is_verified,
                    "is_approved": user.is_approved,
                }
            }
            
            # Set cookies
            response = Response(response_data, status=status.HTTP_200_OK)
            
            expires = datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRY_HOURS)
            
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
                expires=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRY_DAYS),
                samesite='Lax',
                secure=False 
            )
            
            return response
            
        except ValueError as e:
            return Response(
                {'message': 'Invalid Google token', 'detail': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'message': 'Authentication failed', 'detail': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class FacebookLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        code = request.data.get('code')
        
        if not code:
            return Response(
                {'message': 'Authorization code missing'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 1. Exchange code for token
            token_response = requests.post(
                'https://graph.facebook.com/v19.0/oauth/access_token',
                params={
                    'client_id': settings.FACEBOOK_APP_ID,
                    'redirect_uri': f"{settings.FRONTEND_URL}/user/auth/facebook/callback",
                    'client_secret': settings.FACEBOOK_APP_SECRET,
                    'code': code
                }
            )
            
            token_response.raise_for_status()
            token_data = token_response.json()
            
            if 'error' in token_data:
                raise ValueError(token_data['error']['message'])
            
            access_token = token_data['access_token']
            
            # 2. Get user profile with more fields
            profile_response = requests.get(
                'https://graph.facebook.com/v19.0/me',
                params={
                    'fields': 'id,name,email,first_name,last_name',
                    'access_token': access_token
                }
            )
            profile_response.raise_for_status()
            profile = profile_response.json()
            
            # 3. Validate required fields
            if not profile.get('email'):
                logger.error("Facebook login failed - no email provided")
                return Response(
                    {'message': 'Email permission not granted'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 4. Create or update user with transaction
            with transaction.atomic():
                # First try to find by facebook_id
                user = User.objects.filter(facebook_id=profile['id']).first()
                
                if not user:
                    # Then try by email
                    user = User.objects.filter(email=profile['email']).first()
                    
                    if user:
                        # Update existing user with facebook_id
                        user.facebook_id = profile['id']
                        user.auth_provider = 'facebook'
                        user.save()
                
                if not user:
                    # Create new user
                    username_base = profile['email'].split('@')[0]
                    username = username_base
                    counter = 1
                    
                    # Ensure unique username
                    while User.objects.filter(username=username).exists():
                        username = f"{username_base}_{counter}"
                        counter += 1
                    
                    user = User.objects.create(
                        email=profile['email'],
                        username=username,
                        first_name=profile.get('first_name', ''),
                        last_name=profile.get('last_name', ''),
                        is_active=True,
                        auth_provider='facebook',
                        role='user',
                        is_verified=True,
                    )
                    logger.info(f"Created new user: {user.email}")
                
                # Generate tokens
                refresh = RefreshToken.for_user(user)
                access = refresh.access_token
                
                response_data = {
                    "message": "Login successful",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": user.role,
                    }
                }
                
                response = Response(response_data, status=status.HTTP_200_OK)
                
                # Set cookies
                expires = datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRY_HOURS)
                response.set_cookie(
                    key="access_token",
                    value=str(access),
                    httponly=True,
                    expires=expires,
                    samesite='Lax',
                    secure=False
                )
                
                return response

        except Exception as e:
            logger.error(f"Facebook login failed: {str(e)}")
            return Response(
                {'message': 'Facebook authentication failed', 'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class BaseLoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class =None
    user_type = None

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,context={"expected_role":self.user_type})

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user"]
        
        refresh =  RefreshToken.for_user(user)
        access = refresh.access_token

        access['role'] = self.user_type

        
        response = Response({
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username":user.username,
                "email": user.email,
                "role": self.user_type,
            }
        }, status=status.HTTP_200_OK)

        expires = datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRY_HOURS)

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
            expires=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRY_DAYS),
            samesite='Lax',
            secure=False 
            
        )
        

        return response


class BaseLogoutView(APIView):
    permission_classes = [AllowAny]
    user_type =  None


    def post(self,request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            
            if refresh_token is None:
                return Response({"error": "No refresh token found"}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            user_id  =  token["user_id"]
            user = User.objects.get(id=user_id)

            if user.role != self.user_type:
                return Response({"error": "Invalid user role"}, status=403)

            token.blacklist()
            response  =  Response({"message":"Logged Out"})
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")
            return response
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BaseVerifyOtp(APIView):
    permission_classes = [AllowAny]
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
    permission_classes = [AllowAny]
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


class BaseForgotPassword(APIView):
    permission_classes = [AllowAny]
    serializer_class = None
    user_type = None

    def post(self,request,*args,**kwargs):
        serializer = self.serializer_class(data = request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email, role=self.user_type)
        except User.DoesNotExist:
            return Response({"error": "No active account found with this email."}, status=status.HTTP_404_NOT_FOUND)

        token = secrets.token_urlsafe(64)

        cache.set(f"password_reset_token:{token}", user.id, timeout=60 * 60) # one hour

        reset_link =  f"{settings.FRONTEND_URL}/{self.user_type}/reset-password?token={token}"

        send_password_reset_email_task.delay(email,reset_link)

        return Response({"message": "Password reset email sent successfully."}, status=status.HTTP_200_OK)

class BaseResetPassword(APIView):
    permission_classes = [AllowAny]
    serializer_class = None
    user_type = None
    def post(self,request,*args,**kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        user_id = cache.get(f"password_reset_token:{token}")

        if not user_id:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user  = User.objects.get(id=user_id,role=self.user_type)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        user.password = make_password(new_password)
        user.save()

        cache.delete(f"password_reset_token:{token}")

        return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)



class BaseProfileView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BaseProfileSerializer
    user_type = None
    def get(self,request,*args,**kwargs):
        user=request.user
        
        
        try:
            user_role = request.auth.get('role', None)
            

            if user_role != self.user_type:
                return Response({"error": "Unauthorized role"}, status=status.HTTP_403_FORBIDDEN)
            
            serializer = self.serializer_class(user)


            return Response({
                "message":"Profile Fetched Successfully",
                "profile": serializer.data
            }, status= status.HTTP_200_OK)
        except Exception as e:
            
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    

class BaseProfileEditView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BaseProfileSerializer
    user_type = None

    def patch(self, request, *args, **kwargs):
        user = request.user
        try:
            user_role = request.auth.get('role', None)
            if user_role != self.user_type:
                return Response({"error": "Unauthorized role"}, status=status.HTTP_403_FORBIDDEN)

            serializer = self.serializer_class(user, data=request.data, partial=True)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()
            return Response({
                "message": "Profile Updated Successfully",
                "profile": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        

class BaseTokenRefreshView(APIView):
    permission_classes = [AllowAny]
    user_type = None  

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response({"error": "Refresh token not found in cookies."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)
            payload = refresh.payload

            user_id = payload.get('user_id')
            if not user_id:
                return Response({"error": "Invalid token payload: user_id missing."}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise NotFound("User not found.")

           
            if getattr(user, 'role', None) != self.user_type:
                return Response({"error": "Role mismatch."}, status=status.HTTP_403_FORBIDDEN)

        
            access = refresh.access_token
            access['role'] = self.user_type  

            expires = datetime.utcnow() + timedelta(hours=2)

            response = Response({
                "message": "Token refreshed successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": self.user_type,
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

            return response

        except TokenError:
            return Response({"error": "Invalid refresh token."}, status=status.HTTP_401_UNAUTHORIZED)