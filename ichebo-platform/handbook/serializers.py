from rest_framework import serializers
from .models import HandbookRecord, HandbookAccess


class HandbookRecordListSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.display_name', read_only=True, default='')

    class Meta:
        model = HandbookRecord
        fields = [
            'id', 'title', 'slug', 'summary', 'category', 'tags',
            'status', 'version_number', 'created_by_name',
            'published_at', 'updated_at',
        ]


class HandbookRecordDetailSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.display_name', read_only=True, default='')
    locked_by_name = serializers.CharField(source='locked_by.display_name', read_only=True, default='')
    previous_version_id = serializers.UUIDField(source='previous_version.id', read_only=True, default=None)
    superseded_by_id = serializers.UUIDField(source='superseded_by.id', read_only=True, default=None)

    class Meta:
        model = HandbookRecord
        fields = [
            'id', 'title', 'slug', 'content', 'summary', 'category', 'tags',
            'status', 'version_number',
            'previous_version_id', 'superseded_by_id',
            'created_by_name', 'locked_by_name',
            'locked_at', 'published_at', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'status', 'version_number', 'locked_at', 'published_at',
            'created_at', 'updated_at',
        ]


class HandbookRecordWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = HandbookRecord
        fields = ['title', 'slug', 'content', 'summary', 'category', 'tags']


class HandbookAccessSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.display_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = HandbookAccess
        fields = ['id', 'user', 'user_name', 'user_email', 'role', 'granted_at']
        read_only_fields = ['id', 'granted_at']
