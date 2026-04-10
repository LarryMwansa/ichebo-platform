from rest_framework import serializers
from .models import Tenant, UserPermission

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            'id', 'parent', 'created_by', 'created_at', 'updated_at',
            'name', 'slug', 'path', 'tier', 'affiliation', 'status',
            'is_collective', 'description', 'logo_url', 'location', 'settings_data'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

class UserPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPermission
        fields = [
            'id', 'tenant', 'user', 'created_by', 'created_at',
            'tenant_path', 'role', 'level', 'is_active', 'granted_at', 'granted_by'
        ]
        read_only_fields = ['id', 'created_at', 'created_by', 'granted_at', 'granted_by']