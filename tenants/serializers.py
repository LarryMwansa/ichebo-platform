from rest_framework import serializers
from .models import Tenant, UserPermission

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'path']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        # Materialized path generation logic placeholder
        # For a true implementation, path must be built from parent
        parent = validated_data.get('parent')
        if parent:
            validated_data['path'] = f"{parent.path}{validated_data['slug']}/"
        else:
            validated_data['path'] = f"/{validated_data['slug']}/"
            
        return super().create(validated_data)

class UserPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPermission
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'granted_at', 'granted_by', 'tenant_path']

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        validated_data['granted_by'] = request.user
        validated_data['tenant_path'] = validated_data['tenant'].path
        return super().create(validated_data)
