"""
core/views/sync.py

Cloud sync endpoints for Ichebo Desktop (DOC C §7):

  GET  /api/sync/pull/  — delta pull (replaces legacy /sync/changes/)
  POST /api/sync/push/  — receive desktop change events, apply to cloud store

Both endpoints require Token authentication.
"""

import uuid

from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from records.models import Record, Relationship
from records.serializers import RecordSerializer, RelationshipSerializer
from activity.models import Activity
from activity.serializers import ActivitySerializer
from notifications.models import Notification
from notifications.serializers import NotificationSerializer

from core.models import SyncChangelog, OP_CREATE, OP_UPDATE, OP_DELETE

# Maximum entities returned per type per pull response (DOC C §7.2)
PULL_PAGE_SIZE = 500


# ── Steward role set (used by both views) ─────────────────────────────────────

_STEWARD_ROLES = {
    'branch-steward', 'district-steward', 'provincial-steward',
    'national-steward', 'regional-steward', 'continental-steward',
    'global-steward', 'admin',
}


# ── Pull ──────────────────────────────────────────────────────────────────────

class SyncPullView(APIView):
    """
    GET /api/sync/pull/

    Query params:
      since       ISO-8601 or HLC timestamp of last successful pull
      device_id   UUID of the requesting device (audit only, not used for filtering)
      tenant_id   UUID — scope the pull to this tenant

    Returns a PullResponse (DOC C §7.2):
      {
        "since": <echo>,
        "retrieved_at": <ISO-8601>,
        "has_more": bool,
        "records": [...],
        "activities": [...],
        "relationships": [...],
        "notifications": [...]
      }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        since_str = request.query_params.get('since')
        tenant_id_str = request.query_params.get('tenant_id')

        since = None
        if since_str:
            # HLC timestamps serialise as "{unix_nano}_{logical}" — strip logical part
            # for Django's ISO-8601 parser if present
            iso_part = since_str.split('_')[0] if '_' in since_str else since_str
            since = parse_datetime(iso_part)

        tenant_id = None
        if tenant_id_str:
            try:
                tenant_id = uuid.UUID(tenant_id_str)
            except ValueError:
                pass

        user = request.user
        user_perms = user.tenant_permissions.select_related('tenant').all()
        direct_tenant_ids = [p.tenant_id for p in user_perms]
        oversight_paths = [p.tenant.path for p in user_perms if p.role in _STEWARD_ROLES]

        # Narrow scope to requested tenant_id if provided
        if tenant_id:
            direct_tenant_ids = [t for t in direct_tenant_ids if t == tenant_id]

        # ── Records ───────────────────────────────────────────────────────────
        record_qs = Record.objects.filter(deleted_at__isnull=True)
        if since:
            record_qs = record_qs.filter(updated_at__gt=since)

        record_filter = Q(created_by=user) | Q(tenant_id__in=direct_tenant_ids)
        if user.competence_level >= 3:
            record_filter |= Q(record_class='governance')
        for path in oversight_paths:
            record_filter |= Q(tenant__path__startswith=path)
        record_qs = record_qs.filter(record_filter).distinct().order_by('updated_at')

        # ── Activities ────────────────────────────────────────────────────────
        activity_qs = Activity.objects.filter(deleted_at__isnull=True)
        if since:
            activity_qs = activity_qs.filter(updated_at__gt=since)

        activity_filter = Q(created_by=user) | Q(assigned_to=user) | Q(tenant_id__in=direct_tenant_ids)
        for path in oversight_paths:
            activity_filter |= Q(tenant__path__startswith=path)
        activity_qs = activity_qs.filter(activity_filter).distinct().order_by('updated_at')

        # ── Relationships ─────────────────────────────────────────────────────
        rel_qs = Relationship.objects.filter(deleted_at__isnull=True)
        if since:
            rel_qs = rel_qs.filter(created_at__gt=since)
        rel_qs = rel_qs.filter(
            Q(created_by=user) | Q(from_record__tenant_id__in=direct_tenant_ids)
        ).distinct().order_by('created_at')

        # ── Notifications ─────────────────────────────────────────────────────
        notification_qs = Notification.objects.filter(user=user, deleted_at__isnull=True)
        if since:
            notification_qs = notification_qs.filter(updated_at__gt=since)
        notification_qs = notification_qs.order_by('updated_at')

        # ── Pagination ────────────────────────────────────────────────────────
        records_page = list(record_qs[:PULL_PAGE_SIZE + 1])
        activities_page = list(activity_qs[:PULL_PAGE_SIZE + 1])
        rels_page = list(rel_qs[:PULL_PAGE_SIZE + 1])
        notifs_page = list(notification_qs[:PULL_PAGE_SIZE + 1])

        has_more = any(
            len(p) > PULL_PAGE_SIZE
            for p in (records_page, activities_page, rels_page, notifs_page)
        )

        retrieved_at = timezone.now()

        return Response({
            'since': since_str,
            'retrieved_at': retrieved_at.isoformat(),
            'has_more': has_more,
            'records': RecordSerializer(records_page[:PULL_PAGE_SIZE], many=True).data,
            'activities': ActivitySerializer(activities_page[:PULL_PAGE_SIZE], many=True).data,
            'relationships': RelationshipSerializer(rels_page[:PULL_PAGE_SIZE], many=True).data,
            'notifications': NotificationSerializer(notifs_page[:PULL_PAGE_SIZE], many=True).data,
        })


# ── Push ──────────────────────────────────────────────────────────────────────

class SyncPushView(APIView):
    """
    POST /api/sync/push/

    Receives a batch of ChangeLog entries from an Ichebo Desktop installation.
    For each entry, applies the change to the cloud store and returns a status.

    Request body (DOC C §7.1 PushPayload):
      {
        "device_id": "<uuid>",
        "entries": [
          {
            "entity_type": "record" | "activity" | "relationship" | ...,
            "entity_id": "<uuid>",
            "operation": "CREATE" | "UPDATE" | "DELETE",
            "changed_at": "<ISO-8601>",
            "payload_hash": "<sha256>",
            "payload": { ... full entity JSON ... }
          },
          ...
        ]
      }

    Response:
      {
        "results": [
          { "entity_id": "<uuid>", "status": "success" },
          { "entity_id": "<uuid>", "status": "conflict", "reason": "newer_version_exists" },
          { "entity_id": "<uuid>", "status": "rejected", "reason": "permission_denied" }
        ]
      }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        device_id_str = data.get('device_id')
        entries = data.get('entries', [])

        try:
            device_id = uuid.UUID(device_id_str) if device_id_str else None
        except ValueError:
            device_id = None

        results = []
        for entry in entries:
            result = self._apply_entry(request.user, device_id, entry)
            results.append(result)

        return Response({'results': results})

    def _apply_entry(self, user, device_id, entry):
        entity_type = entry.get('entity_type', '')
        entity_id_str = entry.get('entity_id', '')
        operation = entry.get('operation', '')
        changed_at_str = entry.get('changed_at', '')
        payload_hash = entry.get('payload_hash', '')
        payload = entry.get('payload', {})

        try:
            entity_id = uuid.UUID(entity_id_str)
        except (ValueError, AttributeError):
            return {'entity_id': entity_id_str, 'status': 'rejected', 'reason': 'invalid_entity_id'}

        changed_at = parse_datetime(changed_at_str) if changed_at_str else timezone.now()

        # Idempotency: duplicate (device_id, entity_id, operation, changed_at) silently succeeds
        if device_id and SyncChangelog.objects.filter(
            device_id=device_id,
            entity_id=entity_id,
            operation=operation,
            changed_at=changed_at,
        ).exists():
            return {'entity_id': entity_id_str, 'status': 'success'}

        handler = _PUSH_HANDLERS.get(entity_type)
        if not handler:
            return {'entity_id': entity_id_str, 'status': 'rejected', 'reason': 'unknown_entity_type'}

        try:
            status, reason = handler(user, entity_id, operation, payload, changed_at)
        except Exception as exc:
            return {'entity_id': entity_id_str, 'status': 'rejected', 'reason': str(exc)}

        if status == 'success':
            SyncChangelog.objects.create(
                entity_type=entity_type,
                entity_id=entity_id,
                operation=operation,
                changed_at=changed_at,
                device_id=device_id,
                actor=user,
                payload_hash=payload_hash,
            )

        result = {'entity_id': entity_id_str, 'status': status}
        if reason:
            result['reason'] = reason
        return result


# ── Push handlers per entity type ─────────────────────────────────────────────

def _push_record(user, entity_id, operation, payload, changed_at):
    from records.models import Record
    from records.serializers import RecordSerializer

    if operation == OP_DELETE:
        try:
            record = Record.objects.get(pk=entity_id)
        except Record.DoesNotExist:
            return 'success', None  # already gone — idempotent
        if record.created_by_id != user.pk and not user.tenant_permissions.filter(
            role__in=_STEWARD_ROLES, tenant_id=record.tenant_id
        ).exists():
            return 'rejected', 'permission_denied'
        record.deleted_at = changed_at
        record.save(update_fields=['deleted_at'])
        return 'success', None

    if operation == OP_CREATE:
        if Record.objects.filter(pk=entity_id).exists():
            return 'success', None  # idempotent
        payload['id'] = str(entity_id)
        payload['created_by'] = str(user.pk)
        serializer = RecordSerializer(data=payload)
        if not serializer.is_valid():
            return 'rejected', str(serializer.errors)
        serializer.save()
        return 'success', None

    if operation == OP_UPDATE:
        try:
            record = Record.objects.get(pk=entity_id)
        except Record.DoesNotExist:
            return 'rejected', 'not_found'
        # Conflict detection: cloud version newer than incoming change
        if record.updated_at and changed_at and record.updated_at > changed_at:
            incoming_hash = SyncChangelog.compute_hash(payload)
            if incoming_hash != SyncChangelog.compute_hash({}):
                return 'conflict', 'newer_version_exists'
        serializer = RecordSerializer(record, data=payload, partial=True)
        if not serializer.is_valid():
            return 'rejected', str(serializer.errors)
        serializer.save()
        return 'success', None

    return 'rejected', 'unknown_operation'


def _push_activity(user, entity_id, operation, payload, changed_at):
    from activity.models import Activity
    from activity.serializers import ActivitySerializer

    if operation == OP_DELETE:
        try:
            act = Activity.objects.get(pk=entity_id)
        except Activity.DoesNotExist:
            return 'success', None
        act.deleted_at = changed_at
        act.save(update_fields=['deleted_at'])
        return 'success', None

    if operation == OP_CREATE:
        if Activity.objects.filter(pk=entity_id).exists():
            return 'success', None
        payload['id'] = str(entity_id)
        payload['created_by'] = str(user.pk)
        serializer = ActivitySerializer(data=payload)
        if not serializer.is_valid():
            return 'rejected', str(serializer.errors)
        serializer.save()
        return 'success', None

    if operation == OP_UPDATE:
        try:
            act = Activity.objects.get(pk=entity_id)
        except Activity.DoesNotExist:
            return 'rejected', 'not_found'
        if act.updated_at and changed_at and act.updated_at > changed_at:
            return 'conflict', 'newer_version_exists'
        serializer = ActivitySerializer(act, data=payload, partial=True)
        if not serializer.is_valid():
            return 'rejected', str(serializer.errors)
        serializer.save()
        return 'success', None

    return 'rejected', 'unknown_operation'


def _push_relationship(user, entity_id, operation, payload, changed_at):
    from records.models import Relationship
    from records.serializers import RelationshipSerializer

    if operation == OP_DELETE:
        try:
            rel = Relationship.objects.get(pk=entity_id)
        except Relationship.DoesNotExist:
            return 'success', None
        rel.deleted_at = changed_at
        rel.save(update_fields=['deleted_at'])
        return 'success', None

    if operation == OP_CREATE:
        if Relationship.objects.filter(pk=entity_id).exists():
            return 'success', None
        payload['id'] = str(entity_id)
        payload['created_by'] = str(user.pk)
        serializer = RelationshipSerializer(data=payload)
        if not serializer.is_valid():
            return 'rejected', str(serializer.errors)
        serializer.save()
        return 'success', None

    return 'rejected', 'unknown_operation'


_PUSH_HANDLERS = {
    'record': _push_record,
    'activity': _push_activity,
    'relationship': _push_relationship,
}


# ── Legacy alias — keep /sync/changes/ working during transition ───────────────

class SyncChangesView(SyncPullView):
    """
    GET /api/sync/changes/

    Legacy endpoint kept for backward-compatibility with the Flutter mobile
    client while it migrates to /api/sync/pull/. Delegates to SyncPullView.
    """
    pass
