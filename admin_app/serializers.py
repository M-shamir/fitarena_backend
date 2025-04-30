from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.exceptions import AuthenticationFailed
from trainer.serializers import TrainerProfile
from stadium_owner.models import StadiumOwnerProfile
from trainer.models import TrainerCource,TrainerProfile,TrainerType

User = get_user_model()


class AdminLoginSerializer(serializers.Serializer):
    username = serializers.CharField() 
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        # Authenticate using email as username
        user = authenticate(username=username,password=password)
        
        if user is None:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_staff:
            raise serializers.ValidationError("You are not authorized as admin.")

        refresh = RefreshToken.for_user(user)

        return {
            "user": user,  # important: return the actual user instance
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }

class TrainerListSerializer(serializers.ModelSerializer):
    trainer_profile = TrainerProfile()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_approved', 'trainer_profile']


class StadiumListSerializer(serializers.ModelSerializer):
    stadiumowner_profile = StadiumOwnerProfile()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_approved', 'stadiumowner_profile']


    
class TrainerCourceSerializer(serializers.ModelSerializer):
    trainer_name = serializers.CharField(source='trainer.user.username', read_only=True)
    duration_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = TrainerCource
        fields = [
            'id', 'title', 'trainer_name', 'trainer_type', 'description', 'thumbnail',
            'start_date', 'end_date', 'start_time', 'end_time', 'days_of_week',
            'max_participants', 'price', 'status', 'cancellation_reason',
            'is_approved', 'approval_note', 'is_deleted', 'created_at', 'updated_at',
            'duration_minutes'
        ]