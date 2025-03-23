from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.contrib.auth import authenticate 
from account_app.serializers import BaseSignUpSerializer,LoginSerializer

User =  get_user_model()

class TrainerSerializer(BaseSignUpSerializer):
    role = 'trainer'