from rest_framework import serializers
from account_app.serializers import BaseSignUpSerializer
from .models import StadiumOwnerProfile

class   StadiumOnwerSignUpSerializer(BaseSignUpSerializer):
    phone_number = serializers.CharField(max_length=15)
    document = serializers.FileField(required=False)

    class Meta(BaseSignUpSerializer.Meta):
        fields = BaseSignUpSerializer.Meta.fields +['phone_number','document']

    def create(self,validated_data):
        phone_number =  validated_data.pop('phone_number')
        document = validated_data.pop('document', None)
        self.role = 'stadium_onwer'

        user = super().create(validated_data)

        StadiumOwnerProfile.objects.create(
            user = user,
            phone_number = phone_number,
            document= document
        )
        return user