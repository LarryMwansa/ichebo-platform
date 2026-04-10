from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Tenant, UserPermission
from .serializers import TenantSerializer, UserPermissionSerializer

class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filtering based on query params could go here
        return super().get_queryset()

class UserPermissionViewSet(viewsets.ModelViewSet):
    queryset = UserPermission.objects.all()
    serializer_class = UserPermissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Allow users to only see permissions related to them or their tenants
        return UserPermission.objects.filter(user=self.request.user)
