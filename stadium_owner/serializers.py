from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.contrib.auth import authenticate 
from account_app.serializers import BaseSignUpSerializer,LoginSerializer
from .models import FacilityType,Amenity,StadiumDetails


User = get_user_model()
class StadiumOwnerSerializer(BaseSignUpSerializer):
    role = 'stadium_owner'

    stadium_name = serializers.CharField(max_length=255)
    facility_types = serializers.PrimaryKeyRelatedField(queryset=FacilityType.objects.all(), many=True)
    contact_number = serializers.CharField(max_length=15)
    location = serializers.JSONField(required=False)
    amenities = serializers.PrimaryKeyRelatedField(queryset=Amenity.objects.all(), many=True)
    business_license = serializers.FileField()
    ownership_proof = serializers.FileField()
    terms_accepted = serializers.BooleanField()

    class Meta(BaseSignUpSerializer.Meta):
        fields = BaseSignUpSerializer.Meta.fields + [
            'stadium_name', 'facility_types', 'contact_number', 'location',
            'amenities', 'business_license', 'ownership_proof', 'terms_accepted'
        ]
    def create(self,validated_data):
        stadium_data = {
            'stadium_name': validated_data.pop('stadium_name'),
            'facility_types': validated_data.pop('facility_types'),
            'contact_number': validated_data.pop('contact_number'),
            'location': validated_data.pop('location', None),
            'amenities': validated_data.pop('amenities'),
            'business_license': validated_data.pop('business_license'),
            'ownership_proof': validated_data.pop('ownership_proof'),
            'terms_accepted': validated_data.pop('terms_accepted'),
        }

        user = super.create(validated_data)

        stadium = StadiumDetails.objects.create(user=user, **stadium_data)
        stadium.facility_types.set(stadium_data['facility_types'])
        stadium.amenities.set(stadium_data['amenities'])
