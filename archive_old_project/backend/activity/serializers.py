from rest_framework import serializers
from .models import Activity, ActivityLog


class ActivitySerializer(serializers.ModelSerializer):
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    assigned_to_email = serializers.CharField(source='assigned_to.email', read_only=True, allow_null=True)
    parent_activity_title = serializers.CharField(source='parent_activity.title', read_only=True, allow_null=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True, allow_null=True)

    class Meta:
        model = Activity
        fields = [
            'id', 'tenant', 'tenant_name', 'created_by', 'created_by_email',
            'created_at', 'updated_at', 'deleted_at',
            'activity_type', 'title', 'description',
            'scheduled_at', 'due_at', 'recurrence', 'recurrence_rule',
            'parent_activity', 'parent_activity_title',
            'status', 'progress', 'assigned_to', 'assigned_to_email',
            'kgs_pillar', 'kgs_pathway',
            'metadata',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class ActivityLogSerializer(serializers.ModelSerializer):
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    activity_title = serializers.CharField(source='activity.title', read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            'id', 'tenant', 'created_by', 'created_by_email',
            'created_at', 'activity', 'activity_title',
            'event_type', 'previous_value', 'new_value', 'note',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'activity_title']
