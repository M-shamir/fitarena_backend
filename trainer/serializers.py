from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.contrib.auth import authenticate 
from account_app.serializers import BaseSignUpSerializer,LoginSerializer
from .models import Language,TrainerType,TrainerProfile

User =  get_user_model()

class TrainerSerializer(BaseSignUpSerializer):
    role = 'trainer'
    phone_number = serializers.CharField(max_length=15, required=True)
    gender = serializers.ChoiceField(choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    trainer_type = serializers.ListField(child=serializers.IntegerField(), required=True)  # List of IDs
    languages_spoken = serializers.ListField(child=serializers.IntegerField(), required=True)  # List of IDs
    certifications = serializers.ListField(child=serializers.FileField(), required=False)
    training_photo = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'phone_number', 'gender', 'trainer_type', 'languages_spoken', 'certifications', 'training_photo']

    def validate_phone_number(self, value):
        """Ensure phone number is unique"""
        if TrainerProfile.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("This phone number is already registered.")
        return value

    def validate_trainer_type(self, value):
        """Ensure trainer types exist"""
        if not TrainerType.objects.filter(id__in=value).exists():
            raise serializers.ValidationError("Invalid Trainer Type IDs provided.")
        return value

    def create(self, validated_data):
        """Create User and TrainerProfile"""
        trainer_type_ids = validated_data.pop('trainer_type', [])
        language_ids = validated_data.pop('languages_spoken', [])
        certifications = validated_data.pop('certifications', [])
        training_photo = validated_data.pop('training_photo', None)
        phone_number = validated_data.pop('phone_number')
        gender = validated_data.pop('gender')

        user = super().create(validated_data)

        trainer_profile = TrainerProfile.objects.create(
            user=user,
            phone_number=phone_number,
            gender=gender,
            training_photo=training_photo
        )

        trainer_profile.trainer_type.set(TrainerType.objects.filter(id__in=trainer_type_ids))
        trainer_profile.languages_spoken.set(Language.objects.filter(id__in=language_ids))

        # Handle multiple file uploads for certifications
        for cert in certifications:
            trainer_profile.certifications.create(file=cert)

        return user


class TrainerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model =TrainerType
        fields = ["id", "name"]


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ["id", "name"]