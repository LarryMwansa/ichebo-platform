"""
core/views/sync.py

Cloud sync endpoints for Ichebo Desktop (DOC C §7):

  POST /api/sync/validate-licence/  — pre-auth licence key validation (no auth required)
  GET  /api/sync/pull/              — delta pull (replaces legacy /sync/changes/)
  POST /api/sync/push/              — receive desktop change events, apply to cloud store

validate-licence requires no authentication — it is the pre-auth handshake.
pull and push require Token authentication.
"""

import uuid

from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
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


# ── Licence validation ────────────────────────────────────────────────────────

class ValidateLicenceView(APIView):
    """
    POST /api/sync/validate-licence/

    Pre-auth handshake. No authentication required — the licence key is the credential.

    Request body:
      { "licence_key": "XXXX-XXXX-XXXX-XXXX" }

    Response 200:
      { "tenant_id": "<uuid>", "tenant_name": "<name>" }

    Error responses (handled by Flutter wizard):
      404 — key not found
      403 — key revoked
      410 — key expired
    """
    permission_classes = [AllowAny]

    def post(self, request):
        from tenants.models import DesktopLicence

        key = request.data.get('licence_key', '').strip().upper()
        if not key:
            return Response({'detail': 'licence_key is required.'}, status=400)

        try:
            licence = DesktopLicence.objects.select_related('tenant').get(licence_key=key)
        except DesktopLicence.DoesNotExist:
            return Response({'detail': 'Licence key not found.'}, status=404)

        if licence.revoked_at:
            return Response({'detail': 'Licence key has been revoked.'}, status=403)

        if licence.expires_at and timezone.now() > licence.expires_at:
            return Response({'detail': 'Licence key has expired.'}, status=410)

        return Response({
            'tenant_id': str(licence.tenant_id),
            'tenant_name': licence.tenant.name,
        })


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

        # ── Members ───────────────────────────────────────────────────────────
        member_qs = User.objects.filter(is_active=True)
        if tenant_id:
            member_qs = member_qs.filter(
                tenant_permissions__tenant_id=tenant_id
            ).distinct()
        if since:
            member_qs = member_qs.filter(updated_at__gt=since)
        member_qs = member_qs.order_by('updated_at')

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
        members_page = list(member_qs[:PULL_PAGE_SIZE + 1])

        has_more = any(
            len(p) > PULL_PAGE_SIZE
            for p in (records_page, activities_page, rels_page, notifs_page, members_page)
        )

        retrieved_at = timezone.now()

        def _serialise_member(u):
            return {
                'id': str(u.id),
                'email': u.email,
                'display_name': u.display_name or '',
                'first_name': u.first_name or '',
                'last_name': u.last_name or '',
                'competence_level': u.competence_level or 0,
                'is_active': u.is_active,
                'status': u.status or 'active',
                'created_at': u.created_at.isoformat() if u.created_at else '',
                'updated_at': u.updated_at.isoformat() if u.updated_at else '',
                'deleted_at': None,
            }

        return Response({
            'since': since_str,
            'retrieved_at': retrieved_at.isoformat(),
            'has_more': has_more,
            'members': [_serialise_member(u) for u in members_page[:PULL_PAGE_SIZE]],
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
        allowed = {'title', 'record_type', 'record_family', 'record_class', 'status',
                   'tenant_id', 'tenant', 'body', 'metadata', 'permissions_data'}
        kwargs = {k: v for k, v in payload.items() if k in allowed}
        # Resolve tenant FK if provided as UUID string
        if 'tenant' in kwargs and 'tenant_id' not in kwargs:
            kwargs['tenant_id'] = kwargs.pop('tenant')
        Record.objects.create(pk=entity_id, created_by=user, **kwargs)
        return 'success', None

    if operation == OP_UPDATE:
        try:
            record = Record.objects.get(pk=entity_id)
        except Record.DoesNotExist:
            return 'rejected', 'not_found'
        if record.updated_at and changed_at and record.updated_at > changed_at:
            return 'conflict', 'newer_version_exists'
        allowed_update = {'title', 'body', 'status', 'metadata', 'permissions_data'}
        for field, value in payload.items():
            if field in allowed_update:
                setattr(record, field, value)
        record.save()
        return 'success', None

    return 'rejected', 'unknown_operation'


def _push_activity(user, entity_id, operation, payload, changed_at):
    from activity.models import Activity

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
        allowed = {'title', 'activity_type', 'status', 'tenant_id', 'tenant',
                   'assigned_to_id', 'assigned_to', 'due_at', 'scheduled_at', 'body'}
        kwargs = {k: v for k, v in payload.items() if k in allowed}
        if 'tenant' in kwargs and 'tenant_id' not in kwargs:
            kwargs['tenant_id'] = kwargs.pop('tenant')
        if 'assigned_to' in kwargs and 'assigned_to_id' not in kwargs:
            kwargs['assigned_to_id'] = kwargs.pop('assigned_to')
        Activity.objects.create(pk=entity_id, created_by=user, **kwargs)
        return 'success', None

    if operation == OP_UPDATE:
        try:
            act = Activity.objects.get(pk=entity_id)
        except Activity.DoesNotExist:
            return 'rejected', 'not_found'
        if act.updated_at and changed_at and act.updated_at > changed_at:
            return 'conflict', 'newer_version_exists'
        allowed_update = {'title', 'status', 'body', 'due_at', 'scheduled_at'}
        for field, value in payload.items():
            if field in allowed_update:
                setattr(act, field, value)
        act.save()
        return 'success', None

    return 'rejected', 'unknown_operation'


def _push_relationship(user, entity_id, operation, payload, changed_at):
    from records.models import Relationship

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
        allowed = {'from_record_id', 'from_record', 'to_record_id', 'to_record',
                   'relationship_type', 'strength', 'bible_verse_id', 'bible_verse'}
        kwargs = {k: v for k, v in payload.items() if k in allowed}
        if 'from_record' in kwargs and 'from_record_id' not in kwargs:
            kwargs['from_record_id'] = kwargs.pop('from_record')
        if 'to_record' in kwargs and 'to_record_id' not in kwargs:
            kwargs['to_record_id'] = kwargs.pop('to_record')
        Relationship.objects.create(pk=entity_id, created_by=user, **kwargs)
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
