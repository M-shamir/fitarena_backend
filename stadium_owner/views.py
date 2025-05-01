from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import StadiumOwnerSignUpSerializer,StadiumSerializer
from services.email_service import send_otp_email
from services.otp_service import generate_otp,store_otp
from django.core.cache import  cache
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from core.utils import generate_jwt_response
from account_app.views import BaseSignupView,BaseLoginView,BaseVerifyOtp,BaseResendOtp,BaseProfileView,BaseLogoutView
from account_app.serializers import LoginSerializer
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from core.permission import IsStadiumOwner
from .models import StadiumOwnerProfile,Stadium
import logging


# Create your views here.
logger = logging.getLogger(__name__)
User = get_user_model()


class StadiumOwnerSignUpView(BaseSignupView):
    serializer_class = StadiumOwnerSignUpSerializer
    user_type = 'stadium_owner'

class StadiumOwnerVerifyOtpView(BaseVerifyOtp):
    user_role = 'stadium_owner'

class StadiumOwnerResendOtpView(BaseResendOtp):
    pass

class StadiumOwnerLoginView(BaseLoginView):
    serializer_class = LoginSerializer
    user_type = 'stadium_owner'

class StadiumOwnerLogoutView(BaseLogoutView):
    user_type = 'stadium_owner'

class StadiumOwnerProfile(BaseProfileView):
    permission_classes= [IsAuthenticated,IsStadiumOwner]
    user_type = 'stadium_owner'
    

class StadiumCreateView(generics.CreateAPIView):
    queryset = Stadium.objects.all()
    serializer_class = StadiumSerializer
    permission_classes= [IsAuthenticated,IsStadiumOwner]

    def perform_create(self,serializer):
        stadium_owner=  self.request.user.stadiumowner_profile
        serializer.save(owner=stadium_owner)

class PendingStadiumListView(generics.ListAPIView):
    serializer_class = StadiumSerializer
    permission_classes = [IsAuthenticated,IsStadiumOwner]

    def get_queryset(self):
        return Stadium.objects.filter(approval_status='pending', is_deleted=False)

class StadiumOwnerEditPendingView(generics.RetrieveUpdateAPIView):
    queryset = Stadium.objects.filter(is_deleted=False)
    serializer_class = StadiumSerializer
    permission_classes = [IsAuthenticated,IsStadiumOwner]

class StadiumSoftDeleteView(generics.DestroyAPIView):
    queryset = Stadium.objects.all()
    permission_classes = [IsAuthenticated, IsStadiumOwner]

    def delete(self, request, *args, **kwargs):
        stadium = self.get_object()
        stadium.is_deleted = True
        stadium.save()
        return Response({'detail': 'Stadium soft deleted successfully.'}, status=status.HTTP_200_OK)

