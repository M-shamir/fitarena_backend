from rest_framework import serializers
from django.contrib.auth import get_user_model
import re

User = get_user_model()

def validate_unique_email(value):
    if User.objects.filter(email=value).exists():
        raise serializers.ValidationError("Email already registered")
    return value

def validate_password_strength(value):
    if len(value) < 8:
        raise serializers.ValidationError("Password must be at least 8 characters long.")
    return value

def validate_username_format(value):
    if not re.match(r'^[a-zA-Z0-9_]+$', value):
        raise serializers.ValidationError("Username must not contain special characters.")
    if value.isdigit():
        raise serializers.ValidationError("Username must not be fully numeric.")
    return value
