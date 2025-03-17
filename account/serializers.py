from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.contrib.auth import authenticate

User =  get_user_model()
MAX_ATTEMPTS = 5
BLOCK_TIME = 300
RESEND_COOLDOWN = 30


class BaseSignUpSerializer(serializers.ModelSerializer):
    role = None
    class Meta:
        model = User
        fields = ['username','email','password']
        extra_kwargs={
            'password':{'write_only':True}
        }

    def validate_email(self,value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already Registered")
        return value

    def validate_password(self,value):
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long.")
        return value

    def create(self, validated_data):
        validated_data['role'] =  self.role
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role =  validated_data['role']
        )
        return user   


class LoginSerializer(serializers.Serializer):
    username  = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        user = authenticate(username=username,password=password)
    
        if not user:
            raise serializers.ValidationError("Invalid Email or Password")
    
        data["user"] =  user

        return data

class VerifyOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()  # Accepting email as part of the request data
    otp = serializers.CharField(min_length=6, max_length=6)

    def validate(self, data):
        email = data.get('email')  # Get email from the data
        otp_entered = data.get('otp')

        stored_otp = cache.get(f'otp:{email}')
        
        if cache.get(f'otp_blocked:{email}'):
            raise serializers.ValidationError({"otp": "Your OTP attempts have been blocked. Please try again later."})
        
        if stored_otp is None:
            raise serializers.ValidationError({"otp":"Expire OTP or Invalid"})
        
        if stored_otp != otp_entered:
            attempts =  cache.get(f'otp_attempts:{email}',0)+1
            cache.set(f'otp_attempts:{email}', attempts, timeout=BLOCK_TIME)

            if attempts >= MAX_ATTEMPTS:
                cache.set(f'otp_blocked:{email}',True,timeout=BLOCK_TIME)
                raise serializers.ValidationError({"otp": "Too many incorrect attempts. You have been temporarily blocked."})

            raise serializers.ValidationError({"otp": "Invalid OTP"})
        cache.delete(f'otp_attempts:{email}')
        cache.delete(f'otp_blocked:{email}')
        cache.delete(f'otp:{email}') 
        return data
    
class ResendOtpSerializer(serializers.Serializer):
    email =  serializers.EmailField()

    def validate_email(self, value):
        email = value  # Directly get the value of the email field

        # Check if OTP attempts are blocked for this email
        if cache.get(f'otp_blocked:{email}'):
            raise serializers.ValidationError({"otp": "Your OTP attempts have been blocked. Please try again later."})
        
        # Check if the resend cooldown period is active for this email
        if cache.get(f'otp_resend_cooldown:{email}'):
            raise serializers.ValidationError({"otp": "You must wait before requesting another OTP."})
        
        return value

class ForgotPasswordSerializer(serializers.Serializer):
    email =  serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8, write_only=True)
