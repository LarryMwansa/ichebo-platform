from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import HandbookAccess, HandbookRecord
from .serializers import (
    HandbookAccessSerializer,
    HandbookRecordDetailSerializer,
    HandbookRecordListSerializer,
    HandbookRecordWriteSerializer,
)


def _get_tenant_access(user, tenant_id=None):
    """Return (tenant, role) for the user, or (None, None) if no access."""
    qs = HandbookAccess.objects.filter(user=user).select_related('tenant')
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)
    access = qs.first()
    if access:
        return access.tenant, access.role
    return None, None


def _can_write(role):
    return role in (HandbookAccess.ROLE_AUTHOR, HandbookAccess.ROLE_EDITOR)


class HandbookRecordListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant, role = _get_tenant_access(request.user)
        if not tenant:
            return Response([], status=status.HTTP_200_OK)
        records = HandbookRecord.objects.filter(tenant=tenant).order_by('-updated_at')
        # Readers only see published/locked; authors/editors see all
        if role == HandbookAccess.ROLE_READER:
            records = records.filter(status__in=[HandbookRecord.STATUS_PUBLISHED, HandbookRecord.STATUS_LOCKED])
        serializer = HandbookRecordListSerializer(records, many=True)
        return Response(serializer.data)

    def post(self, request):
        tenant, role = _get_tenant_access(request.user)
        if not tenant or not _can_write(role):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = HandbookRecordWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        record = serializer.save(tenant=tenant, created_by=request.user)
        return Response(HandbookRecordDetailSerializer(record).data, status=status.HTTP_201_CREATED)


class HandbookRecordDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_record(self, request, pk):
        tenant, role = _get_tenant_access(request.user)
        if not tenant:
            return None, None, None
        record = get_object_or_404(HandbookRecord, pk=pk, tenant=tenant)
        return record, tenant, role

    def get(self, request, pk):
        record, tenant, role = self._get_record(request, pk)
        if not record:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(HandbookRecordDetailSerializer(record).data)

    def patch(self, request, pk):
        record, tenant, role = self._get_record(request, pk)
        if not record:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        if not _can_write(role):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        if record.status == HandbookRecord.STATUS_LOCKED:
            return Response({'detail': 'Record is locked.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = HandbookRecordWriteSerializer(record, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(HandbookRecordDetailSerializer(record).data)


class HandbookPublishView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        tenant, role = _get_tenant_access(request.user)
        if not tenant or not _can_write(role):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        record = get_object_or_404(HandbookRecord, pk=pk, tenant=tenant)
        if record.status not in (HandbookRecord.STATUS_DRAFT,):
            return Response({'detail': 'Only drafts can be published.'}, status=status.HTTP_400_BAD_REQUEST)
        record.publish(request.user)
        return Response(HandbookRecordDetailSerializer(record).data)


class HandbookLockView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        tenant, role = _get_tenant_access(request.user)
        if not tenant or role != HandbookAccess.ROLE_EDITOR:
            return Response({'detail': 'Only editors can lock records.'}, status=status.HTTP_403_FORBIDDEN)
        record = get_object_or_404(HandbookRecord, pk=pk, tenant=tenant)
        if record.status != HandbookRecord.STATUS_PUBLISHED:
            return Response({'detail': 'Only published records can be locked.'}, status=status.HTTP_400_BAD_REQUEST)
        record.lock(request.user)
        return Response(HandbookRecordDetailSerializer(record).data)


class HandbookNewVersionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        tenant, role = _get_tenant_access(request.user)
        if not tenant or not _can_write(role):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        record = get_object_or_404(HandbookRecord, pk=pk, tenant=tenant)
        new = record.new_version(request.user)
        return Response(HandbookRecordDetailSerializer(new).data, status=status.HTTP_201_CREATED)


class HandbookHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        tenant, role = _get_tenant_access(request.user)
        if not tenant:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        record = get_object_or_404(HandbookRecord, pk=pk, tenant=tenant)
        # Walk previous_version chain
        history = []
        cursor = record
        while cursor is not None:
            history.append(cursor)
            cursor = cursor.previous_version
        serializer = HandbookRecordListSerializer(history, many=True)
        return Response(serializer.data)


class HandbookAccessListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant, role = _get_tenant_access(request.user)
        if not tenant or role != HandbookAccess.ROLE_EDITOR:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        access = HandbookAccess.objects.filter(tenant=tenant).select_related('user', 'granted_by')
        return Response(HandbookAccessSerializer(access, many=True).data)

    def post(self, request):
        tenant, role = _get_tenant_access(request.user)
        if not tenant or role != HandbookAccess.ROLE_EDITOR:
            return Response({'detail': 'Only editors can grant access.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = HandbookAccessSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        access = serializer.save(tenant=tenant, granted_by=request.user)
        return Response(HandbookAccessSerializer(access).data, status=status.HTTP_201_CREATED)


class HandbookPublishFeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant, role = _get_tenant_access(request.user)
        if not tenant:
            return Response([], status=status.HTTP_200_OK)
        records = HandbookRecord.objects.filter(
            tenant=tenant,
            status__in=[HandbookRecord.STATUS_PUBLISHED, HandbookRecord.STATUS_LOCKED],
        ).order_by('-published_at')[:20]
        return Response(HandbookRecordListSerializer(records, many=True).data)
