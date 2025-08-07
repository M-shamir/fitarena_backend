from rest_framework import serializers
import re

def validate_phone_number(value):
    if not re.match(r'^\+?\d{7,15}$', value):
        raise serializers.ValidationError("Enter a valid phone number.")
    return value

def validate_document_file(value):
    if value:
        if value.size > 2 * 1024 * 1024:  # 2MB
            raise serializers.ValidationError("File size must be under 2MB.")
        if not value.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
            raise serializers.ValidationError("Only PDF, JPG, JPEG, PNG formats are allowed.")
    return value
