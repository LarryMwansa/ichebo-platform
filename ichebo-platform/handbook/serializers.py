from rest_framework import serializers
from .models import HandbookAccess


class HandbookAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = HandbookAccess
        fields = ['id', 'user', 'role', 'granted_by', 'granted_at']
