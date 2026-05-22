from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from activity.models import Activity
from .models import BroadcastSchedule
from .utils import get_embed_type, get_embed_url


def _event_qs():
    return (
        Activity.objects
        .filter(activity_type='event', deleted_at__isnull=True)
        .exclude(metadata__stream_url=None)
        .exclude(metadata__stream_url='')
        .order_by('scheduled_at')
    )


def _serialize_event(event):
    meta = event.metadata or {}
    stream_url = meta.get('stream_url', '')
    duration = int(meta.get('duration_minutes', 60))
    start = event.scheduled_at
    now = timezone.now()

    is_live = is_past = False
    if start:
        end = start + timezone.timedelta(minutes=duration)
        is_live = start <= now <= end
        is_past = now > end

    return {
        'id':           str(event.id),
        'title':        event.title,
        'description':  event.description or '',
        'scheduled_at': start.isoformat() if start else None,
        'stream_url':   stream_url,
        'embed_url':    get_embed_url(stream_url),
        'embed_type':   get_embed_type(stream_url),
        'duration_minutes': duration,
        'is_live':      is_live,
        'is_past':      is_past,
    }


class VideoFeedView(APIView):
    """
    GET /api/video/feed/
    Returns live, upcoming (next 7 days), and recent VOD events in one call.
    Also includes native BroadcastSchedule entries from the Media Engine.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        cutoff = now + timezone.timedelta(days=7)

        events = [_serialize_event(e) for e in _event_qs()]

        live = [e for e in events if e['is_live']]
        upcoming = [
            e for e in events
            if not e['is_live'] and not e['is_past']
            and e['scheduled_at'] and e['scheduled_at'] <= cutoff.isoformat()
        ]
        vod = [e for e in events if e['is_past']][:12]

        # Merge in native broadcasts
        native_broadcasts = BroadcastSchedule.objects.filter(
            status__in=['scheduled', 'live']
        ).order_by('scheduled_at')[:20]

        for b in native_broadcasts:
            entry = {
                'id':              str(b.id),
                'title':           b.title,
                'description':     b.description,
                'scheduled_at':    b.scheduled_at.isoformat(),
                'stream_url':      b.viewer_hls_url,
                'embed_url':       b.viewer_hls_url,
                'embed_type':      'hls',
                'duration_minutes': b.duration_minutes,
                'is_live':         b.status == 'live',
                'is_past':         b.status == 'ended',
                'broadcast_id':    str(b.id),
            }
            if b.status == 'live':
                live.insert(0, entry)
            else:
                upcoming.append(entry)

        return Response({
            'live':     live,
            'upcoming': upcoming,
            'vod':      vod,
        })


# ── Broadcast scheduling (Level 3+) ─────────────────────────────────────────

def _serialize_broadcast(b):
    return {
        'id':               str(b.id),
        'title':            b.title,
        'description':      b.description,
        'scheduled_at':     b.scheduled_at.isoformat(),
        'duration_minutes': b.duration_minutes,
        'status':           b.status,
        'rtmp_ingest_url':  b.rtmp_ingest_url,
        'viewer_hls_url':   b.viewer_hls_url,
        'vod_url':          b.vod_url,
        'stream_key':       b.stream_key,
        'created_at':       b.created_at.isoformat(),
    }


class BroadcastListCreateView(APIView):
    """
    GET  /api/video/broadcasts/        — list schedules for the user's tenant
    POST /api/video/broadcasts/        — schedule a new broadcast (Level 3+)
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.query_params.get('tenant_id')
        qs = BroadcastSchedule.objects.all().order_by('-scheduled_at')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        return Response([_serialize_broadcast(b) for b in qs[:50]])

    def post(self, request):
        title          = request.data.get('title', '').strip()
        scheduled_at   = request.data.get('scheduled_at', '').strip()
        tenant_id      = request.data.get('tenant_id', '').strip()
        duration       = int(request.data.get('duration_minutes', 60))
        description    = request.data.get('description', '').strip()
        gathering_id   = request.data.get('gathering_record_id')

        if not title or not scheduled_at or not tenant_id:
            return Response({'error': 'title, scheduled_at, and tenant_id are required'}, status=400)

        from django.utils.dateparse import parse_datetime
        dt = parse_datetime(scheduled_at)
        if dt is None:
            return Response({'error': 'scheduled_at must be ISO 8601'}, status=400)

        from tenants.models import Tenant
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return Response({'error': 'Tenant not found'}, status=404)

        broadcast = BroadcastSchedule.objects.create(
            tenant=tenant,
            created_by=request.user,
            title=title,
            description=description,
            scheduled_at=dt,
            duration_minutes=duration,
            gathering_record_id=gathering_id or None,
        )

        return Response(_serialize_broadcast(broadcast), status=201)


class BroadcastDetailView(APIView):
    """
    GET    /api/video/broadcasts/{id}/  — detail
    PATCH  /api/video/broadcasts/{id}/  — update title/description/scheduled_at
    DELETE /api/video/broadcasts/{id}/  — cancel
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _get(self, broadcast_id):
        try:
            return BroadcastSchedule.objects.get(id=broadcast_id)
        except BroadcastSchedule.DoesNotExist:
            return None

    def get(self, request, broadcast_id):
        b = self._get(broadcast_id)
        if not b:
            return Response({'error': 'Not found'}, status=404)
        return Response(_serialize_broadcast(b))

    def patch(self, request, broadcast_id):
        b = self._get(broadcast_id)
        if not b:
            return Response({'error': 'Not found'}, status=404)
        if b.status in ('live', 'ended'):
            return Response({'error': 'Cannot edit a live or ended broadcast'}, status=400)

        for field in ('title', 'description', 'duration_minutes'):
            if field in request.data:
                setattr(b, field, request.data[field])
        if 'scheduled_at' in request.data:
            from django.utils.dateparse import parse_datetime
            dt = parse_datetime(request.data['scheduled_at'])
            if dt:
                b.scheduled_at = dt
        b.save()
        return Response(_serialize_broadcast(b))

    def delete(self, request, broadcast_id):
        b = self._get(broadcast_id)
        if not b:
            return Response({'error': 'Not found'}, status=404)
        b.status = 'cancelled'
        b.save(update_fields=['status'])
        return Response(status=204)


# ── Go engine webhooks (stream start / end) ──────────────────────────────────

class StreamStartWebhookView(APIView):
    """
    POST /api/video/stream/start/
    Called by the Go Video Engine (stream.Handler) when MediaMTX receives RTMP.
    Marks the broadcast live and fires community notifications.
    Authenticated by shared API key.
    """

    def post(self, request):
        _require_engine_key(request)
        stream_key = request.data.get('stream_key', '').strip()
        hls_url    = request.data.get('hls_url', '').strip()

        if not stream_key:
            return Response({'error': 'stream_key required'}, status=400)

        try:
            broadcast = BroadcastSchedule.objects.get(stream_key=stream_key)
        except BroadcastSchedule.DoesNotExist:
            return Response({'error': 'Unknown stream key'}, status=404)

        broadcast.status  = 'live'
        broadcast.hls_url = hls_url
        broadcast.save(update_fields=['status', 'hls_url', 'updated_at'])

        # Fire community notifications to all active members of the tenant.
        _notify_broadcast_start(broadcast)

        return Response({'status': 'live', 'broadcast_id': str(broadcast.id)})


class StreamEndWebhookView(APIView):
    """
    POST /api/video/stream/end/
    Called by the Go Video Engine after archive compilation completes.
    Marks the broadcast ended and stores the VOD URL.
    """

    def post(self, request):
        _require_engine_key(request)
        stream_key = request.data.get('stream_key', '').strip()
        vod_url    = request.data.get('vod_url', '').strip()

        if not stream_key:
            return Response({'error': 'stream_key required'}, status=400)

        try:
            broadcast = BroadcastSchedule.objects.get(stream_key=stream_key)
        except BroadcastSchedule.DoesNotExist:
            return Response({'error': 'Unknown stream key'}, status=404)

        broadcast.status  = 'ended'
        broadcast.vod_url = vod_url
        broadcast.save(update_fields=['status', 'vod_url', 'updated_at'])

        return Response({'status': 'ended', 'vod_url': vod_url})


# ── Helpers ──────────────────────────────────────────────────────────────────

def _require_engine_key(request):
    api_key = getattr(settings, 'MEDIA_ENGINE_API_KEY', 'dev-key')
    auth = request.headers.get('Authorization', '')
    if auth != f'Bearer {api_key}':
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied('Invalid engine API key')


def _notify_broadcast_start(broadcast):
    """Fan-out in-app notifications to all active members of the broadcast tenant."""
    from notifications.service import create_notification
    from accounts.models import UserPermission

    members = UserPermission.objects.filter(
        tenant=broadcast.tenant,
        is_active=True,
    ).select_related('user').values_list('user', flat=True)

    from accounts.models import User
    users = User.objects.filter(id__in=members, is_active=True)

    for user in users:
        create_notification(
            user=user,
            notification_type='announcement',
            title=f'Live now: {broadcast.title}',
            body='A live broadcast has started in your community. Tap to watch.',
            data={
                'broadcast_id': str(broadcast.id),
                'hls_url':      broadcast.hls_url or broadcast.viewer_hls_url,
                'url':          f'/video/watch/{broadcast.id}/',
            },
        )
