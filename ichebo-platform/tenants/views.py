from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Tenant, UserPermission
from .serializers import TenantSerializer, UserPermissionSerializer
from .service import get_oversight_tenant_ids

class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # See get_oversight_tenant_ids's docstring — this used to be the
        # only place this hierarchy-walk existed; now shared with every
        # template-rendered tenancy page too.
        return Tenant.objects.filter(id__in=get_oversight_tenant_ids(self.request.user))

class UserPermissionViewSet(viewsets.ModelViewSet):
    queryset = UserPermission.objects.all()
    serializer_class = UserPermissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Allow users to only see permissions related to them or their tenants
        return UserPermission.objects.filter(user=self.request.user)
