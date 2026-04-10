from rest_framework import serializers
from .models import Activity, ActivityLog

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
