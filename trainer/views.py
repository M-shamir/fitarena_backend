from rest_framework import status
from rest_framework import generics
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.permission import IsTrainer
from rest_framework.views import APIView
from .serializers import TrainerSerializer,TrainerTypeSerializer,LanguageSerializer,TrainerCourceSerializer,TrainerProfileSerializer
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
from rest_framework.generics import DestroyAPIView

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
    serializer_class = TrainerProfileSerializer
    user_type = 'trainer'

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            user_role = request.auth.get('role', None)

            if user_role != self.user_type:
                return Response({"error": "Unauthorized role"}, status=status.HTTP_403_FORBIDDEN)

            trainer_profile = user.trainer_profile  # This will fetch the TrainerProfile
            serializer = self.serializer_class(trainer_profile)

            return Response({
                "message": "Trainer Profile Fetched Successfully",
                "profile": serializer.data
            }, status=status.HTTP_200_OK)

        except TrainerProfile.DoesNotExist:
            return Response({"error": "Trainer profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    def patch(self, request, *args, **kwargs):
        user = request.user

        try:
            user_role = request.auth.get('role', None)
            if user_role != self.user_type:
                return Response({"error": "Unauthorized role"}, status=status.HTTP_403_FORBIDDEN)
            
            trainer_profile = user.trainer_profile
            serializer = self.serializer_class(trainer_profile, data=request.data, partial=True)

            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return Response({"message": "Profile Updated Successfully", "profile": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class TrainerForgotPassword(BaseForgotPassword):
    serializer_class = ForgotPasswordSerializer
    user_type = 'trainer'

class TrainerResetPasswordView(BaseResetPassword):
    serializer_class = ResetPasswordSerializer
    user_type = 'trainer'


class TrainerCreateCourceView(APIView):
    permission_classes = [IsAuthenticated, IsTrainer]
    def post(self,request,*args,**kwargs):
            user = request.user

            trainer = user.trainer_profile
            
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
    

class PendingApprovalSessionsView(ListAPIView):
    permission_classes = [IsAuthenticated, IsTrainer] 
    serializer_class = TrainerCourceSerializer

    def get_queryset(self):
        
        user = self.request.user 

        try:
         
            trainer_profile = TrainerProfile.objects.get(user=user)

        except TrainerProfile.DoesNotExist:
            raise AuthenticationFailed('Trainer profile not found.')
        
        

        
        return TrainerCource.objects.filter(
            trainer=trainer_profile,
            status='pending',
            is_approved=False,
            is_deleted=False
        )


class TrainerTypesView(APIView):
    permission_classes = [IsAuthenticated, IsTrainer] 
    def get(self, request):
        try:
            
            user = request.user
            
            trainer_profile = user.trainer_profile

            
            trainer_types = trainer_profile.trainer_type.all()

            
            serializer = TrainerTypeSerializer(trainer_types, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except TrainerProfile.DoesNotExist:
            return Response({"error": "Trainer profile not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ApprovedSessionsView(ListAPIView):
    permission_classes = [IsAuthenticated, IsTrainer] 
    serializer_class = TrainerCourceSerializer

    def get_queryset(self):
        

        user = self.request.user

        try:
            
            trainer_profile = TrainerProfile.objects.get(user=user)
        except TrainerProfile.DoesNotExist:
            raise AuthenticationFailed('Trainer profile not found.')
        
        return TrainerCource.objects.filter(
            trainer=trainer_profile,
            status='approved',
            is_approved=True
        )


class ApprovedSessionsView(ListAPIView):
    permission_classes = [IsAuthenticated, IsTrainer] 
    serializer_class = TrainerCourceSerializer

    def get_queryset(self):
        user = self.request.user

        

        try:
            trainer_profile = TrainerProfile.objects.get(user=user)
        except TrainerProfile.DoesNotExist:
            raise AuthenticationFailed('Trainer profile not found.')

      
        return TrainerCource.objects.filter(
            trainer=trainer_profile,
            is_approved=True
        )

class DeleteTrainerCourceView(DestroyAPIView):
    permission_classes = [IsAuthenticated, IsTrainer] 
    queryset = TrainerCource.objects.all()
    lookup_field = 'pk'

    def delete(self,request,*args,**kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()
        return Response({"detail": "Course deleted."}, status=204)


class TrainerPendingEditView(APIView):
    permission_classes = [IsAuthenticated, IsTrainer]

    def patch(self, request, *args, **kwargs):
        user = request.user
        pk = kwargs.get('pk')

        try:
            trainer_profile = TrainerProfile.objects.get(user=user)
        except TrainerProfile.DoesNotExist:
            raise PermissionDenied("Trainer profile not found.")

        try:
            cource = TrainerCource.objects.get(pk=pk, trainer=trainer_profile)
        except TrainerCource.DoesNotExist:
            raise NotFound("Course not found.")

        if cource.status != 'pending' or cource.is_approved:
            return Response({'detail': 'Course is not in pending approval state.'}, status=400)

        serializer = TrainerCourceSerializer(cource, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
