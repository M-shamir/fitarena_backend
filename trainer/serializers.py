from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import datetime, timedelta 
from account_app.serializers import BaseSignUpSerializer,LoginSerializer,BaseProfileSerializer
from .models import Language,TrainerType,TrainerProfile,TrainerCource,CourseSession,SessionParticipant
from orders.models import    CourseEnrollment

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
            training_photo=training_photo,
            
        )

        trainer_profile.trainer_type.set(TrainerType.objects.filter(id__in=trainer_type_ids))
        trainer_profile.languages_spoken.set(Language.objects.filter(id__in=language_ids))

        # Handle multiple file uploads for certifications
        trainer_profile.certifications = certifications[0] if certifications else None
        trainer_profile.save()
        return user



class TrainerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model =TrainerType
        fields = ["id", "name"]


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ["id", "name"]

    
class TrainerCourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainerCource
        fields = ['id', 'trainer', 'title', 'trainer_type', 'description', 'thumbnail', 
                  'start_date', 'end_date', 'start_time', 'end_time', 'days_of_week', 
                  'max_participants', 'price', 'status', 'created_at', 'updated_at']

        read_only_fields = ['cancellation_reason', 'is_approved', 'approval_note']
    def validate(self, data):
        
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("End time must be after the start time.")
        return data

class TrainerProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    profile_photo = serializers.ImageField(source='user.profile_photo', required=False)

    
    trainer_type = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=TrainerType.objects.all(),
        write_only=True
    )
    languages_spoken = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Language.objects.all(),
        write_only=True
    )

    # For GET: Return names
    trainer_type_names = serializers.SerializerMethodField(read_only=True)
    languages_spoken_names = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TrainerProfile
        fields = [
            'username', 'email', 'profile_photo',
            'phone_number', 'gender',
            'trainer_type',        # for input (IDs)
            'trainer_type_names',  # for output (Names)
            'certifications',
            'languages_spoken',    # for input (IDs)
            'languages_spoken_names',  # for output (Names)
            'training_photo'
        ]
        read_only_fields = ['gender']

    def get_trainer_type_names(self, obj):
        return [trainer.name for trainer in obj.trainer_type.all()]

    def get_languages_spoken_names(self, obj):
        return [language.name for language in obj.languages_spoken.all()]

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)

        if user_data:
            user = instance.user
            user.profile_photo = user_data.get('profile_photo', user.profile_photo)
            user.save()

        if 'trainer_type' in validated_data:
            trainer_types = validated_data.pop('trainer_type')
            instance.trainer_type.set(trainer_types)

        if 'languages_spoken' in validated_data:
            languages = validated_data.pop('languages_spoken')
            instance.languages_spoken.set(languages)

        return super().update(instance, validated_data)

class CourseEnrollmentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='course.id')
    title = serializers.CharField(source='course.title')
    enrolled_users_count = serializers.SerializerMethodField()
    upcoming_sessions_count = serializers.SerializerMethodField()

    class Meta:
        model = CourseEnrollment
        fields = ['id', 'title', 'enrolled_users_count', 'upcoming_sessions_count']

    def get_enrolled_users_count(self, obj):
        return CourseEnrollment.objects.filter(course=obj.course, is_cancelled=False).count()

    def get_upcoming_sessions_count(self, obj):
        # Use session_date and current date for filtering upcoming sessions
        return CourseSession.objects.filter(
            course=obj.course,
            session_date__gte=timezone.now().date(),
            is_completed=False
        ).count()

class EnrolledUserSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='order.user.id')
    name = serializers.CharField(source='order.user.get_full_name')
    email = serializers.CharField(source='order.user.email')
    enrolled_at = serializers.DateTimeField()

    class Meta:
        model = CourseEnrollment
        fields = ['id', 'name', 'email', 'enrolled_at']

class TrainerStatsSerializer(serializers.Serializer):
    total_sessions = serializers.IntegerField()
    active_clients = serializers.IntegerField()
    upcoming_sessions_today = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)

class UpcomingSessionSerializer(serializers.ModelSerializer):
    client = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    type = serializers.CharField(source='course.title')
    
    class Meta:
        model = CourseSession
        fields = ['id', 'client', 'time', 'type']
    
    def get_client(self, obj):
        enrollments = obj.course.enrollments.filter(is_cancelled=False)
        if enrollments.exists():
            return enrollments.first().order.user.get_full_name()
        return "No clients enrolled"
    
    def get_time(self, obj):
        return f"{obj.course.start_time.strftime('%I:%M %p')} - {obj.course.end_time.strftime('%I:%M %p')}"

class RecentClientSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    last_session = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseEnrollment
        fields = ['id', 'name', 'last_session', 'progress']
    
    def get_name(self, obj):
        return obj.order.user.get_full_name()
    
    def get_last_session(self, obj):
        last_session = CourseSession.objects.filter(
            course=obj.course,
            is_completed=True
        ).order_by('-session_date').first()
        
        if last_session:
            delta = timezone.now().date() - last_session.session_date
            return f"{delta.days} days ago"
        return "No sessions yet"
    
    def get_progress(self, obj):
        # This would need actual progress tracking logic
        return "+5%"

class QuickActionSerializer(serializers.Serializer):
    actions = serializers.SerializerMethodField()
    
    def get_actions(self, obj):
        return [
            {'id': 1, 'name': 'Add Session', 'icon': 'add'},
            {'id': 2, 'name': 'Add Client', 'icon': 'user'},
            {'id': 3, 'name': 'Create Plan', 'icon': 'document'},
            {'id': 4, 'name': 'Nutrition Plan', 'icon': 'nutrition'}
        ]