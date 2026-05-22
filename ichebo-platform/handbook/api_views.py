from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    HandbookAccess, HandbookRecord, HandbookRelationship,
    BRANCH_CHOICES, BRANCH_KEYS,
)
from .serializers import (
    HandbookAccessSerializer,
    HandbookRecordDetailSerializer,
    HandbookRecordListSerializer,
    HandbookRecordWriteSerializer,
    HandbookRelationshipSerializer,
)


def _get_access(user):
    return HandbookAccess.objects.filter(user=user).select_related('user').first()


def _can_write(access):
    return access and access.role in (HandbookAccess.ROLE_AUTHOR, HandbookAccess.ROLE_EDITOR)


def _readable_statuses(access):
    """Return the status values visible to this access level."""
    if not access:
        return []
    if _can_write(access):
        # Authors/Editors see everything including drafts
        return [HandbookRecord.STATUS_DRAFT, HandbookRecord.STATUS_ACTIVE,
                HandbookRecord.STATUS_LOCKED, HandbookRecord.STATUS_SUPERSEDED]
    # Readers see active and locked only
    return [HandbookRecord.STATUS_ACTIVE, HandbookRecord.STATUS_LOCKED]


class HandbookRecordListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        access = _get_access(request.user)
        qs = HandbookRecord.objects.filter(status__in=_readable_statuses(access))

        branch = request.query_params.get('branch')
        if branch:
            qs = qs.filter(branch=branch)
        rtype = request.query_params.get('record_type')
        if rtype:
            qs = qs.filter(record_type=rtype)
        stat = request.query_params.get('status')
        if stat:
            qs = qs.filter(status=stat)

        return Response(HandbookRecordListSerializer(qs, many=True).data)

    def post(self, request):
        access = _get_access(request.user)
        if not _can_write(access):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = HandbookRecordWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        record = serializer.save(created_by=request.user)
        return Response(HandbookRecordDetailSerializer(record).data, status=status.HTTP_201_CREATED)


class HandbookRecordDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _fetch(self, request, pk):
        access = _get_access(request.user)
        record = get_object_or_404(HandbookRecord, pk=pk)
        if record.status not in _readable_statuses(access):
            return None, None
        return record, access

    def get(self, request, pk):
        record, access = self._fetch(request, pk)
        if not record:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(HandbookRecordDetailSerializer(record).data)

    def patch(self, request, pk):
        record, access = self._fetch(request, pk)
        if not record:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        if not _can_write(access):
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
        access = _get_access(request.user)
        if not _can_write(access):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        record = get_object_or_404(HandbookRecord, pk=pk)
        if record.status != HandbookRecord.STATUS_DRAFT:
            return Response({'detail': 'Only draft records can be published.'}, status=status.HTTP_400_BAD_REQUEST)
        record.publish(request.user)
        return Response(HandbookRecordDetailSerializer(record).data)


class HandbookLockView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        access = _get_access(request.user)
        if not access or access.role != HandbookAccess.ROLE_EDITOR:
            return Response({'detail': 'Only editors can lock records.'}, status=status.HTTP_403_FORBIDDEN)
        record = get_object_or_404(HandbookRecord, pk=pk)
        if record.status != HandbookRecord.STATUS_ACTIVE:
            return Response({'detail': 'Only active records can be locked.'}, status=status.HTTP_400_BAD_REQUEST)
        record.lock(request.user)
        return Response(HandbookRecordDetailSerializer(record).data)


class HandbookNewVersionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        access = _get_access(request.user)
        if not _can_write(access):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        record = get_object_or_404(HandbookRecord, pk=pk)
        if record.status not in (HandbookRecord.STATUS_ACTIVE, HandbookRecord.STATUS_LOCKED):
            return Response({'detail': 'Only active or locked records can be versioned.'}, status=status.HTTP_400_BAD_REQUEST)
        new = record.new_version(request.user)
        return Response(HandbookRecordDetailSerializer(new).data, status=status.HTTP_201_CREATED)


class HandbookHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        access = _get_access(request.user)
        record = get_object_or_404(HandbookRecord, pk=pk)
        if record.status not in _readable_statuses(access):
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        history = []
        cursor = record
        while cursor is not None:
            history.append(cursor)
            cursor = cursor.previous_version
        return Response(HandbookRecordListSerializer(history, many=True).data)


# ── K.3 HRS Relationships ─────────────────────────────────────────────────────

class HandbookRelationshipListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        access = _get_access(request.user)
        record = get_object_or_404(HandbookRecord, pk=pk)
        if record.status not in _readable_statuses(access):
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        rels = record.outgoing_relationships.select_related('to_record', 'bible_verse', 'bible_verse__book')
        return Response(HandbookRelationshipSerializer(rels, many=True).data)

    def post(self, request, pk):
        access = _get_access(request.user)
        if not _can_write(access):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        record = get_object_or_404(HandbookRecord, pk=pk)
        if record.status == HandbookRecord.STATUS_LOCKED:
            return Response({'detail': 'Cannot add relationships to a locked record.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = HandbookRelationshipSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        rel = serializer.save(from_record=record, created_by=request.user)
        return Response(HandbookRelationshipSerializer(rel).data, status=status.HTTP_201_CREATED)


class HandbookRelationshipDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, rel_id):
        access = _get_access(request.user)
        if not _can_write(access):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        record = get_object_or_404(HandbookRecord, pk=pk)
        rel = get_object_or_404(HandbookRelationship, pk=rel_id, from_record=record)
        rel.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── K.5 Publish Feed ──────────────────────────────────────────────────────────

class HandbookPublishFeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        access = _get_access(request.user)
        if not access:
            return Response([], status=status.HTTP_200_OK)

        qs = HandbookRecord.objects.filter(
            status__in=[HandbookRecord.STATUS_ACTIVE, HandbookRecord.STATUS_LOCKED],
        )

        since = request.query_params.get('since')
        if since:
            try:
                from django.utils.dateparse import parse_datetime
                since_dt = parse_datetime(since)
                if since_dt:
                    qs = qs.filter(updated_at__gte=since_dt)
            except (ValueError, TypeError):
                pass

        qs = qs.order_by('-updated_at')[:100]
        return Response(HandbookRecordListSerializer(qs, many=True).data)


# ── Access management ─────────────────────────────────────────────────────────

class HandbookAccessListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        access = _get_access(request.user)
        if not access or access.role != HandbookAccess.ROLE_EDITOR:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        all_access = HandbookAccess.objects.select_related('user', 'granted_by').all()
        return Response(HandbookAccessSerializer(all_access, many=True).data)

    def post(self, request):
        access = _get_access(request.user)
        if not access or access.role != HandbookAccess.ROLE_EDITOR:
            return Response({'detail': 'Only editors can grant access.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = HandbookAccessSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        grant = serializer.save(granted_by=request.user)
        return Response(HandbookAccessSerializer(grant).data, status=status.HTTP_201_CREATED)


class HandbookMyAccessView(APIView):
    """Returns the requesting user's own access record."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        access = _get_access(request.user)
        if not access:
            return Response({'role': None, 'has_access': False})
        return Response({
            'role': access.role,
            'has_access': True,
            'can_write': _can_write(access),
            'is_editor': access.role == HandbookAccess.ROLE_EDITOR,
        })
