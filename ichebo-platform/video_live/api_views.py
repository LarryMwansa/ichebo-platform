from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from activity.models import Activity
from .models import BroadcastSchedule
from .utils import get_embed_type, get_embed_url


def _event_qs(tenant_id=None):
    qs = (
        Activity.objects
        .filter(activity_type='event', deleted_at__isnull=True)
        .exclude(metadata__stream_url=None)
        .exclude(metadata__stream_url='')
        .order_by('scheduled_at')
    )
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)
    return qs


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
        tenant_id = request.query_params.get('tenant_id')

        events = [_serialize_event(e) for e in _event_qs(tenant_id=tenant_id)]

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
        )
        if tenant_id:
            native_broadcasts = native_broadcasts.filter(tenant_id=tenant_id)
        native_broadcasts = native_broadcasts.order_by('scheduled_at')[:20]

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
    POST /video/api/stream/start/
    Called by MediaMTX's runOnReady hook (configured with just the stream
    key — MediaMTX has no knowledge of Django's data model) when a
    broadcaster's RTMP connection is accepted.

    The Go engine's own /engine/stream/start requires a record_id, which
    only Django's BroadcastSchedule table can resolve from the stream key.
    So the real chain is MediaMTX -> Django (here) -> Go engine, not
    MediaMTX -> Go engine directly as stream.Handler's comment originally
    implied — completed here since BroadcastSchedule.id *is* the record_id
    the engine's session registry expects (Chizola, 2026-06-23, while
    deploying the video VPS and finding this handshake was never wired up
    end-to-end).

    Authenticated by shared API key — same MEDIA_ENGINE_API_KEY used for
    the engine's outbound webhooks, since this is also an
    engine/infra-originated call, not a browser/user request.

    authentication_classes is explicitly emptied (not just left at the
    project default) because DRF's global DEFAULT_PERMISSION_CLASSES is
    IsAuthenticated — confirmed by direct test that the global default
    rejects this view with 401 before _require_engine_key's own bearer
    check ever runs, even with a correct key. The same bug was found in
    media.views.TranscodeCompleteWebhookView, a pre-existing, unrelated
    view whose docstring made the identical "authenticated by shared API
    key" claim without actually overriding the class-level default —
    meaning that webhook has likely never worked end-to-end since it was
    written. Fixed here and there in the same pass (Chizola, 2026-06-23).
    """
    authentication_classes = []
    permission_classes = []

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

        # Tell the Go engine the session is real, now that we have the
        # record_id it requires. Best-effort: the broadcast is already
        # marked live and viewers can already be notified even if this
        # particular call fails — DVR archiving (which depends on the
        # engine's session registry knowing about this stream) degrading
        # is a real but secondary failure mode, not one that should block
        # marking the broadcast live for viewers.
        _start_engine_session(broadcast, hls_url)

        return Response({'status': 'live', 'broadcast_id': str(broadcast.id)})


class StreamEndWebhookView(APIView):
    """
    POST /video/api/stream/end/
    Called by MediaMTX's runOnNotReady hook (same reasoning as
    StreamStartWebhookView above — MediaMTX only has the stream key, not
    Django's data model) when the broadcaster's RTMP connection closes.

    This fires immediately on disconnect, before archiving — vod_url is
    NOT yet known at this point, archiving (DVR -> MP4 remux, taking up to
    the archiver's 2-hour timeout for a long broadcast) happens
    asynchronously afterward. vod_url is filled in later by
    TranscodeCompleteWebhookView (/api/media/transcode-complete/) once the
    Go engine's Archiver finishes — see that view for the matching
    BroadcastSchedule branch added in the same pass as this fix
    (Chizola, 2026-06-23).

    See StreamStartWebhookView's docstring for why authentication_classes
    is explicitly emptied here.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        _require_engine_key(request)
        stream_key = request.data.get('stream_key', '').strip()

        if not stream_key:
            return Response({'error': 'stream_key required'}, status=400)

        try:
            broadcast = BroadcastSchedule.objects.get(stream_key=stream_key)
        except BroadcastSchedule.DoesNotExist:
            return Response({'error': 'Unknown stream key'}, status=404)

        broadcast.status = 'ended'
        broadcast.save(update_fields=['status', 'updated_at'])

        # Trigger the engine's session end + async archive compilation.
        _end_engine_session(broadcast)

        return Response({'status': 'ended', 'broadcast_id': str(broadcast.id)})


# ── Helpers ──────────────────────────────────────────────────────────────────

def _require_engine_key(request):
    api_key = getattr(settings, 'MEDIA_ENGINE_API_KEY', 'dev-key')
    auth = request.headers.get('Authorization', '')
    if auth != f'Bearer {api_key}':
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied('Invalid engine API key')


def _start_engine_session(broadcast, hls_url):
    """Register the live session with the Go engine now that we have the
    record_id it requires (BroadcastSchedule.id). Logs and swallows
    failures rather than raising — see the docstring above on why this is
    best-effort relative to marking the broadcast live for viewers."""
    import logging
    from media.engine_client import post_with_retry

    logger = logging.getLogger(__name__)
    engine_url = getattr(settings, 'MEDIA_ENGINE_URL', 'http://localhost:8090')
    try:
        post_with_retry(
            f'{engine_url}/engine/stream/start',
            json={
                'stream_key': broadcast.stream_key,
                'record_id': str(broadcast.id),
                'tenant_id': str(broadcast.tenant_id),
                'hls_base_url': hls_url,
            },
            timeout=15,
        )
    except Exception as exc:
        logger.error(
            'Failed to register stream session with Go engine for broadcast %s: %s',
            broadcast.id, exc,
        )


def _end_engine_session(broadcast):
    """Tell the Go engine the stream ended, so it can finalize/archive the
    session. Same best-effort posture as _start_engine_session."""
    import logging
    from media.engine_client import post_with_retry

    logger = logging.getLogger(__name__)
    engine_url = getattr(settings, 'MEDIA_ENGINE_URL', 'http://localhost:8090')
    try:
        post_with_retry(
            f'{engine_url}/engine/stream/end',
            json={'stream_key': broadcast.stream_key},
            timeout=15,
        )
    except Exception as exc:
        logger.error(
            'Failed to notify Go engine of stream end for broadcast %s: %s',
            broadcast.id, exc,
        )


def _notify_broadcast_start(broadcast):
    """Fan-out in-app notifications to all active members of the broadcast tenant."""
    from notifications.service import create_notification
    from tenants.models import UserPermission

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
