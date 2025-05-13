from rest_framework import serializers
from .models import Order, CourseEnrollment, SlotBooking

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

class CourseEnrollmentSerializer(serializers.ModelSerializer):
    course_details = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseEnrollment
        fields = '__all__'
    
    def get_course_details(self, obj):
        from trainer.serializers import TrainerCourceSerializer
        return TrainerCourceSerializer(obj.course).data

class SlotBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlotBooking
        fields = '__all__'