from rest_framework import serializers
from .models import Record, Relationship


class RecordSerializer(serializers.ModelSerializer):
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True, allow_null=True)

    class Meta:
        model = Record
        fields = [
            'id', 'tenant', 'tenant_name', 'created_by', 'created_by_email',
            'created_at', 'updated_at', 'deleted_at',
            'record_class', 'record_family', 'record_type', 'origin',
            'title', 'content', 'summary',
            'status', 'locked_by', 'locked_at',
            'version', 'previous_version', 'superseded_by',
            'tags', 'categories', 'custom_fields', 'metadata', 'permissions_data'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class RelationshipSerializer(serializers.ModelSerializer):
    from_record_title = serializers.CharField(source='from_record.title', read_only=True)
    to_record_title = serializers.CharField(source='to_record.title', read_only=True)
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)

    class Meta:
        model = Relationship
        fields = [
            'id', 'tenant', 'created_by', 'created_by_email',
            'created_at', 'deleted_at',
            'from_record', 'from_record_title',
            'to_record', 'to_record_title',
            'direction', 'relationship_type', 'notes', 'strength'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']
