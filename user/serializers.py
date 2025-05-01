from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.contrib.auth import authenticate 
from account_app.serializers import BaseSignUpSerializer,LoginSerializer
from trainer.models import TrainerProfile,TrainerCource,TrainerType,Language

User =  get_user_model()



class UserSerializer(BaseSignUpSerializer):
    role = 'user'
    

class TrainerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerType
        fields = ['id', 'name']

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'name']

class TrainerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    trainer_type = TrainerTypeSerializer(many=True)
    languages_spoken = LanguageSerializer(many=True)

    class Meta:
        model = TrainerProfile
        fields = [
            'id', 'user', 'phone_number', 'gender', 'trainer_type',
            'certifications', 'languages_spoken', 'training_photo', 'listed'
        ]

class TrainerCourceSerializer(serializers.ModelSerializer):
    trainer = TrainerProfileSerializer()
    trainer_type = TrainerTypeSerializer()
    duration_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = TrainerCource
        fields = [
            'id', 'title', 'description', 'trainer', 'trainer_type',
            'thumbnail', 'start_date', 'end_date', 'start_time', 'end_time',
            'days_of_week', 'max_participants', 'price', 'status',
            'approval_status', 'approval_note', 'duration_minutes', 'created_at'
        ]