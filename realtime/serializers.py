# notifications/serializers.py
from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    time = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = ['id', 'message', 'read', 'created_at', 'time', 'related_url']
    
    def get_time(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.created_at) + ' ago'