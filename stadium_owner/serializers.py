from rest_framework import serializers
from account_app.serializers import BaseSignUpSerializer
from django.contrib.gis.geos import Point
from .models import *
from orders.models import *
from datetime import datetime, time
from django.contrib.auth import get_user_model

User = get_user_model()
class StadiumOwnerSignUpSerializer(BaseSignUpSerializer):
    phone_number = serializers.CharField(max_length=15)
    document = serializers.FileField(required=False)

    class Meta(BaseSignUpSerializer.Meta):
        fields = BaseSignUpSerializer.Meta.fields +['phone_number','document']

    def create(self,validated_data):
        phone_number =  validated_data.pop('phone_number')
        document = validated_data.pop('document', None)
        self.role = 'stadium_owner'  


        user = super().create(validated_data)

        StadiumOwnerProfile.objects.create(
            user = user,
            phone_number = phone_number,
            document= document
        )
        return user

class StadiumSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)

    class Meta:
        model = Stadium
        fields = [
            'id', 'name', 'description', 'address', 'image',
            'city', 'state', 'pincode',
            'latitude', 'longitude'
        ]

    def create(self,validated_data):
        lat = validated_data.pop('latitude')
        lng = validated_data.pop('longitude')
        validated_data['location'] = Point(lng, lat)
        validated_data['owner'] = self.context['request'].user.stadiumowner_profile
        return super().create(validated_data)


class SlotCreateSerializer(serializers.Serializer):
    stadium_id = serializers.IntegerField()
    start_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    price = serializers.DecimalField(max_digits=8, decimal_places=2)

    def validate(self, data):
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("End time must be after start time.")
        return data



class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ['date','stadium', 'start_time', 'end_time', 'price', 'status']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        
class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = Order
        fields = ['id', 'user', 'amount', 'status', 'created_at']

class SlotBookingSerializer(serializers.ModelSerializer):
    slot = SlotSerializer()
    order = OrderSerializer()
    
    class Meta:
        model = SlotBooking
        fields = [
            'id', 
            'slot', 
            'order', 
            'booking_date', 
            'booked_at', 
            'is_cancelled', 
            'cancelled_at'
        ]