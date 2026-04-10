from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import TenantSerializer, UserPermissionSerializer
from .models import Tenant, UserPermission

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def tenant_list_create(request):
    if request.method == 'GET':
        tenants = Tenant.objects.all()
        serializer = TenantSerializer(tenants, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = TenantSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def tenant_detail(request, pk):
    try:
        tenant = Tenant.objects.get(pk=pk)
    except Tenant.DoesNotExist:
        return Response({'error': 'Tenant not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = TenantSerializer(tenant)
        return Response(serializer.data)
    elif request.method in ['PUT', 'PATCH']:
        serializer = TenantSerializer(tenant, data=request.data, partial=request.method == 'PATCH')
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        tenant.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def user_permission_list_create(request):
    if request.method == 'GET':
        permissions = UserPermission.objects.filter(user=request.user)
        serializer = UserPermissionSerializer(permissions, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = UserPermissionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user, granted_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def user_permission_detail(request, pk):
    try:
        permission = UserPermission.objects.get(pk=pk)
    except UserPermission.DoesNotExist:
        return Response({'error': 'Permission not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = UserPermissionSerializer(permission)
        return Response(serializer.data)
    elif request.method in ['PUT', 'PATCH']:
        serializer = UserPermissionSerializer(permission, data=request.data, partial=request.method == 'PATCH')
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        permission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
