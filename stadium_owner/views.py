from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import StadiumOwnerSignUpSerializer,StadiumSerializer,SlotCreateSerializer,SlotSerializer
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
from .models import StadiumOwnerProfile,Stadium,Slot
from django.shortcuts import get_object_or_404
from django.db.models import OuterRef, Exists

from datetime import timedelta, datetime
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


class ApprovedStadiumsListView(APIView):
    permission_classes = [IsAuthenticated, IsStadiumOwner]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            owner_profile = user.stadiumowner_profile  
            
            stadiums = Stadium.objects.filter(
                owner=owner_profile,
                approval_status='approved',
                is_deleted=False
            )
            
            serializer = StadiumSerializer(stadiums, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except StadiumOwnerProfile.DoesNotExist:
            return Response(
                {'error': 'Stadium owner profile not found for this user.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': 'Failed to retrieve stadiums', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UnassignedStadiumsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsStadiumOwner]

    def get(self, request, *args, **kwargs):
        stadiums = Stadium.objects.filter(
            approval_status='approved',
            is_deleted=False,
            owner__user=request.user  
        ).annotate(
            has_slots=Exists(Slot.objects.filter(stadium=OuterRef('pk')))
        ).filter(
            has_slots=False
        )

        serializer = StadiumSerializer(stadiums, many=True)
        return Response(serializer.data, status=200)


class SlotCreateAPIView(APIView):
    permission_classes = [IsAuthenticated,IsStadiumOwner]
    def post(self, request):
        serializer = SlotCreateSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            stadium = get_object_or_404(Stadium, id=data['stadium_id'])

            
            if stadium.owner.user != request.user:
                return Response({"error": "You do not own this stadium."}, status=status.HTTP_403_FORBIDDEN)

            slot_duration = timedelta(hours=1)
            created_slots = []

            for day_offset in range(7):  
                slot_date = data['start_date'] + timedelta(days=day_offset)
                current_time = datetime.combine(slot_date, data['start_time'])
                day_end_time = datetime.combine(slot_date, data['end_time'])

                while current_time + slot_duration <= day_end_time:
                    slot_start = current_time.time()
                    slot_end = (current_time + slot_duration).time()

                    
                    if not Slot.objects.filter(stadium=stadium, date=slot_date, start_time=slot_start).exists():
                        slot = Slot.objects.create(
                            stadium=stadium,
                            date=slot_date,
                            start_time=slot_start,
                            end_time=slot_end,
                            price=data['price'],
                            status='available'
                        )
                        created_slots.append({
                            "date": slot_date,
                            "start_time": slot_start,
                            "end_time": slot_end
                        })

                    current_time += slot_duration

            return Response({"message": "Slots created", "slots": created_slots}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SlotListAPIView(APIView):
    permission_classes = [IsAuthenticated,IsStadiumOwner] 
    def get(self, request, stadium_id, *args, **kwargs):
        
        try:
            stadium = Stadium.objects.get(id=stadium_id)  
        except Stadium.DoesNotExist:
            return Response({"message": "Stadium not found."}, status=status.HTTP_404_NOT_FOUND)

        
        slots = Slot.objects.filter(stadium=stadium).order_by('date', 'start_time')

        if slots.exists():
            
            serializer = SlotSerializer(slots, many=True)
            return Response({
                "message": "Slots retrieved successfully.",
                "slots": serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "message": "No slots found for this stadium."
            }, status=status.HTTP_404_NOT_FOUND)