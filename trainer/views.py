from rest_framework import status
from rest_framework import generics
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from core.permission import IsTrainer
from rest_framework.views import APIView
from .serializers import TrainerSerializer,TrainerTypeSerializer,LanguageSerializer,TrainerCourceSerializer
from services.email_service import send_otp_email
from services.otp_service import generate_otp,store_otp
from django.core.cache import  cache
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from core.utils import generate_jwt_response
from account_app.views import BaseSignupView,BaseLoginView,BaseVerifyOtp,BaseResendOtp,BaseLogoutView,BaseProfileView,BaseForgotPassword,BaseResetPassword
from account_app.serializers import LoginSerializer,ResetPasswordSerializer,ForgotPasswordSerializer
from .models import TrainerType,Language,TrainerProfile,TrainerCource
from rest_framework.permissions import AllowAny
from .services.course_service import TrainerCourseService
from rest_framework_simplejwt.tokens import AccessToken

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

class TrainerProfileView(BaseProfileView):
    permission_classes  = [IsTrainer]
    user_type = 'trainer'

class TrainerForgotPassword(BaseForgotPassword):
    serializer_class = ForgotPasswordSerializer
    user_type = 'trainer'

class TrainerResetPasswordView(BaseResetPassword):
    serializer_class = ResetPasswordSerializer
    user_type = 'trainer'


class TrainerCreateCourceView(APIView):
    permission_classes = [AllowAny]
    def post(self,request,*args,**kwargs):
        token = request.COOKIES.get('access_token')

        if not token:
            return Response({"error": "Token not found"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user_role = access_token.get('role', None)

            # Check if the user has the "trainer" role
            if user_role != "trainer":
                return Response({"error": "You are not authorized to create courses."}, status=status.HTTP_403_FORBIDDEN)

            user = User.objects.get(id=user_id)  
            if not hasattr(user, 'trainer_profile'):
                return Response({"error": "Trainer profile not found."}, status=status.HTTP_400_BAD_REQUEST)

            trainer = user.trainer_profile
            # Extract data from request
            base_info = request.data.get('base_info')
            course_variant = request.data.get('course_variant')

            if not base_info or not course_variant:
                return Response(
                    {"error": "Both 'base_info' and 'course_variant' are required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
             # Create the course using the service
            course = TrainerCourseService.create_course(trainer, base_info, course_variant)
            course_serializer = TrainerCourceSerializer(course)
            return Response(
                {"message": "Course created successfully!", "course": course_serializer.data},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class PendingApprovalSessionsView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = TrainerCourceSerializer

    def get_queryset(self):
        # Get the token from cookies
        token = self.request.COOKIES.get('access_token')

        if not token:
            raise AuthenticationFailed('No token found in cookies.')

        try:
            # Decode the token
            access_token = AccessToken(token)
            user_id = access_token['user_id']  # Extract user ID from the token

            # Fetch the user object
            user = User.objects.get(id=user_id)
            
            # Assuming the user has a TrainerProfile
            trainer_profile = TrainerProfile.objects.get(user=user)

        except User.DoesNotExist:
            raise AuthenticationFailed('User not found.')
        
        

        # Return the queryset based on the trainer's profile
        return TrainerCource.objects.filter(
            trainer=trainer_profile,
            status='pending',
            is_approved=False
        )


class TrainerTypesView(APIView):
    permission_classes = [AllowAny]
    

    def get(self, request):
        
        token = request.COOKIES.get('access_token')

        if not token:
            return Response({"error": "Token not found"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user_role = access_token.get('role', None)

           
            if user_role != "trainer":
                return Response({"error": "You are not authorized to view trainer types."}, status=status.HTTP_403_FORBIDDEN)

  
            user = User.objects.get(id=user_id)
            trainer_profile = user.trainer_profile  

          
            trainer_types = trainer_profile.trainer_type.all()
            serializer = TrainerTypeSerializer(trainer_types, many=True)

           
            return Response(serializer.data, status=status.HTTP_200_OK)

        except AccessToken.Expired:
            return Response({"error": "Token has expired."}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except TrainerProfile.DoesNotExist:
            return Response({"error": "Trainer profile not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ApprovedSessionsView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = TrainerCourceSerializer

    def get_queryset(self):
        token = self.request.COOKIES.get('access_token')

        if not token:
            raise AuthenticationFailed('No token found in cookies.')

        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.get(id=user_id)
            trainer_profile = TrainerProfile.objects.get(user=user)

        except User.DoesNotExist:
            raise AuthenticationFailed('User not found.')

        return TrainerCource.objects.filter(
            trainer=trainer_profile,
            status='approved',
            is_approved=True
        )


class ApprovedSessionsView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = TrainerCourceSerializer

    def get_queryset(self):
        token = self.request.COOKIES.get('access_token')

        if not token:
            raise AuthenticationFailed('No token found in cookies.')

        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.get(id=user_id)
            trainer_profile = TrainerProfile.objects.get(user=user)

        except User.DoesNotExist:
            raise AuthenticationFailed('User not found.')

      
        return TrainerCource.objects.filter(
            trainer=trainer_profile,
            is_approved=True
        )
