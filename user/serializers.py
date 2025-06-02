from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.contrib.auth import authenticate 
from account_app.serializers import BaseSignUpSerializer,LoginSerializer
from trainer.models import *
from stadium_owner.models import *
from orders.models import *
from django.utils import timezone

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

class StadiumOwnerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = StadiumOwnerProfile
        fields = ['user', 'phone_number']

class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ['id', 'date', 'start_time', 'end_time', 'price', 'status']

class StadiumSerializer(serializers.ModelSerializer):
    owner = StadiumOwnerProfileSerializer()
    slots = SlotSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta:
        model = Stadium
        fields = [
            'id', 'name', 'description', 'address', 'city', 'state', 'pincode',
            'image_url', 'location', 'owner', 'approval_status', 'listed',
            'created_at', 'slots'
        ]
        read_only_fields = ['approval_status', 'created_at']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_location(self, obj):
        if obj.location:
            return {
                'type': 'Point',
                'coordinates': [obj.location.x, obj.location.y]
            }
        return None


class UserEnrolledCourseSerializer(serializers.ModelSerializer):
    course_id = serializers.IntegerField(source='course.id')
    title = serializers.CharField(source='course.title')
    trainer_name = serializers.CharField(source='course.trainer.user.username')
    start_date = serializers.DateField(source='course.start_date')
    end_date = serializers.DateField(source='course.end_date')
    start_time = serializers.TimeField(source='course.start_time')
    end_time = serializers.TimeField(source='course.end_time')
    price = serializers.DecimalField(source='course.price', max_digits=8, decimal_places=2)
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = CourseEnrollment
        fields = ['id', 'course_id', 'title', 'trainer_name', 'start_date', 
                 'end_date', 'start_time', 'end_time', 'price', 'can_cancel']

    def get_can_cancel(self, obj):
        # Course can be canceled if it hasn't started yet
        
        today = timezone.now().date()
        return obj.course.start_date > today
    
class PastCourseSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    course_id = serializers.IntegerField(source='course.id')
    title = serializers.CharField(source='course.title')
    trainer_name = serializers.CharField(source='course.trainer.user.username')
    start_date = serializers.DateField(source='course.start_date')
    end_date = serializers.DateField(source='course.end_date')
    sessions_completed = serializers.SerializerMethodField()
    cancelled_at = serializers.DateTimeField()

    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'course_id', 'title', 'trainer_name', 'status',
            'start_date', 'end_date', 'sessions_completed', 'cancelled_at'
        ]

    def get_status(self, obj):
        return "cancelled" if obj.is_cancelled else "completed"

    def get_sessions_completed(self, obj):
        if obj.is_cancelled:
            return 0
        return obj.course.sessions.filter(is_completed=True).count()
    

class SlotBookingSerializer(serializers.ModelSerializer):
    slot = SlotSerializer()
    
    class Meta:
        model = SlotBooking
        fields = ['id', 'slot', 'booking_date', 'booked_at']
