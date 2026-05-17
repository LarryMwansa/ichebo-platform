from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Tenant, UserPermission
from .serializers import TenantSerializer, UserPermissionSerializer

class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Tenant.objects.all()
        
        # Get all tenants where user has direct permissions
        direct_tenant_ids = user.tenant_permissions.values_list('tenant_id', flat=True)
        
        # Identify "steward" roles that imply oversight of descendants
        steward_roles = [
            'branch-steward', 'district-steward', 'provincial-steward',
            'national-steward', 'regional-steward', 'continental-steward',
            'global-steward', 'admin'
        ]
        
        oversight_permissions = user.tenant_permissions.filter(role__in=steward_roles).select_related('tenant')
        
        if not oversight_permissions.exists():
            return Tenant.objects.filter(id__in=direct_tenant_ids)
            
        # User sees their direct tenants + all descendants of tenants they oversee
        from django.db.models import Q
        q_objects = Q(id__in=direct_tenant_ids)
        for perm in oversight_permissions:
            q_objects |= Q(path__startswith=perm.tenant.path)
            
        return Tenant.objects.filter(q_objects).distinct()

class UserPermissionViewSet(viewsets.ModelViewSet):
    queryset = UserPermission.objects.all()
    serializer_class = UserPermissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Allow users to only see permissions related to them or their tenants
        return UserPermission.objects.filter(user=self.request.user)
