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
        return [HandbookRecord.STATUS_DRAFT, HandbookRecord.STATUS_ACTIVE,
                HandbookRecord.STATUS_LOCKED, HandbookRecord.STATUS_SUPERSEDED]
    return [HandbookRecord.STATUS_ACTIVE, HandbookRecord.STATUS_LOCKED]


def _is_key_record(record_or_branch):
    """True if this record/branch is the Keys Library — owner-only."""
    if isinstance(record_or_branch, HandbookRecord):
        return record_or_branch.branch == BRANCH_KEYS
    return record_or_branch == BRANCH_KEYS


class HandbookRecordListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        access = _get_access(request.user)
        branch = request.query_params.get('branch')

        if branch == BRANCH_KEYS or not branch:
            # Keys branch: always scoped to the requesting user only
            keys_qs = HandbookRecord.objects.filter(branch=BRANCH_KEYS, created_by=request.user)
            if branch == BRANCH_KEYS:
                # Only keys requested — return just the user's own keys
                return Response(HandbookRecordListSerializer(keys_qs.order_by('-updated_at'), many=True).data)
            # No branch filter — return shared records + user's own keys
            shared_qs = HandbookRecord.objects.filter(
                status__in=_readable_statuses(access),
            ).exclude(branch=BRANCH_KEYS)
            rtype = request.query_params.get('record_type')
            if rtype:
                shared_qs = shared_qs.filter(record_type=rtype)
                keys_qs = keys_qs.filter(record_type=rtype)
            stat = request.query_params.get('status')
            if stat:
                shared_qs = shared_qs.filter(status=stat)
                keys_qs = keys_qs.filter(status=stat)
            combined = list(shared_qs) + list(keys_qs)
            return Response(HandbookRecordListSerializer(combined, many=True).data)

        # Non-keys branch — require Handbook access to read
        qs = HandbookRecord.objects.filter(
            branch=branch,
            status__in=_readable_statuses(access),
        )
        rtype = request.query_params.get('record_type')
        if rtype:
            qs = qs.filter(record_type=rtype)
        stat = request.query_params.get('status')
        if stat:
            qs = qs.filter(status=stat)
        return Response(HandbookRecordListSerializer(qs, many=True).data)

    def post(self, request):
        branch = request.data.get('branch', '')
        if _is_key_record(branch):
            # Any authenticated user can create their own key records — no HandbookAccess needed
            serializer = HandbookRecordWriteSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            record = serializer.save(created_by=request.user)
            return Response(HandbookRecordDetailSerializer(record).data, status=status.HTTP_201_CREATED)

        # All other branches require author/editor access
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
        record = get_object_or_404(HandbookRecord, pk=pk)
        if _is_key_record(record):
            # Key records: owner-only at all times
            if record.created_by_id != request.user.pk:
                return None, None
            return record, None  # access object not needed for keys
        access = _get_access(request.user)
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
        if _is_key_record(record):
            # Owner can always edit their own key records (unless locked)
            if record.status == HandbookRecord.STATUS_LOCKED:
                return Response({'detail': 'Record is locked.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
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
        record = get_object_or_404(HandbookRecord, pk=pk)
        if _is_key_record(record):
            return Response({'detail': 'Key records are personal and cannot be published.'}, status=status.HTTP_400_BAD_REQUEST)
        access = _get_access(request.user)
        if not _can_write(access):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        if record.status != HandbookRecord.STATUS_DRAFT:
            return Response({'detail': 'Only draft records can be published.'}, status=status.HTTP_400_BAD_REQUEST)
        record.publish(request.user)
        return Response(HandbookRecordDetailSerializer(record).data)


class HandbookLockView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        record = get_object_or_404(HandbookRecord, pk=pk)
        if _is_key_record(record):
            return Response({'detail': 'Key records cannot be locked via this endpoint.'}, status=status.HTTP_400_BAD_REQUEST)
        access = _get_access(request.user)
        if not access or access.role != HandbookAccess.ROLE_EDITOR:
            return Response({'detail': 'Only editors can lock records.'}, status=status.HTTP_403_FORBIDDEN)
        if record.status != HandbookRecord.STATUS_ACTIVE:
            return Response({'detail': 'Only active records can be locked.'}, status=status.HTTP_400_BAD_REQUEST)
        record.lock(request.user)
        return Response(HandbookRecordDetailSerializer(record).data)


class HandbookNewVersionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        record = get_object_or_404(HandbookRecord, pk=pk)
        if _is_key_record(record):
            # Owner can version their own key records
            if record.created_by_id != request.user.pk:
                return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            access = _get_access(request.user)
            if not _can_write(access):
                return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        if record.status not in (HandbookRecord.STATUS_ACTIVE, HandbookRecord.STATUS_LOCKED):
            return Response({'detail': 'Only active or locked records can be versioned.'}, status=status.HTTP_400_BAD_REQUEST)
        new = record.new_version(request.user)
        return Response(HandbookRecordDetailSerializer(new).data, status=status.HTTP_201_CREATED)


class HandbookHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        record = get_object_or_404(HandbookRecord, pk=pk)
        if _is_key_record(record):
            if record.created_by_id != request.user.pk:
                return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            access = _get_access(request.user)
            if record.status not in _readable_statuses(access):
                return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        history = []
        cursor = record
        while cursor is not None:
            history.append(cursor)
            cursor = cursor.previous_version
        return Response(HandbookRecordListSerializer(history, many=True).data)


# ── K.3 HRS Relationships ─────────────────────────────────────────────────────

def _assert_can_access_record(request, record):
    """Return True if the user may read this record. Raises nothing — caller checks."""
    if _is_key_record(record):
        return record.created_by_id == request.user.pk
    access = _get_access(request.user)
    return record.status in _readable_statuses(access)


def _assert_can_write_record(request, record):
    """Return True if the user may write to this record."""
    if _is_key_record(record):
        return record.created_by_id == request.user.pk
    access = _get_access(request.user)
    return _can_write(access)


class HandbookRelationshipListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        record = get_object_or_404(HandbookRecord, pk=pk)
        if not _assert_can_access_record(request, record):
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        rels = record.outgoing_relationships.select_related('to_record', 'bible_verse', 'bible_verse__book')
        return Response(HandbookRelationshipSerializer(rels, many=True).data)

    def post(self, request, pk):
        record = get_object_or_404(HandbookRecord, pk=pk)
        if not _assert_can_write_record(request, record):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
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
        record = get_object_or_404(HandbookRecord, pk=pk)
        if not _assert_can_write_record(request, record):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
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

        # Keys are personal — they are never part of the network publish feed
        qs = HandbookRecord.objects.filter(
            status__in=[HandbookRecord.STATUS_ACTIVE, HandbookRecord.STATUS_LOCKED],
        ).exclude(branch=BRANCH_KEYS)

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
