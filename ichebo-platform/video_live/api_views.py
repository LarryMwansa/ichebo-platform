from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BroadcastSchedule

# ── Go engine webhooks (stream start / end) ──────────────────────────────────
#
# This is the only surviving surface of the old video_live app. The mobile
# feed/CRUD endpoints that used to live in this file (VideoFeedView,
# BroadcastListCreateView, BroadcastDetailView) were deleted 2026-06-24 along
# with the rest of video_live's standalone app (video-direction-v2-plan.md)
# — they had zero Flutter client code consuming them (mobile/lib does not
# exist yet) and would have been speculative scaffolding rather than working
# infrastructure. BroadcastSchedule itself, and these two webhook views,
# stay: the Go engine and MediaMTX call them directly and Community's
# digital-Gathering flow (community/views.py) creates BroadcastSchedule rows
# directly now.


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
                # Viewers watch from Community's live-service room, which
                # resolves the tenant's current broadcast itself — there is
                # no per-broadcast watch page anymore (video_live/watch.html
                # was deleted along with the rest of the standalone app).
                'url':          '/community/live/',
            },
        )
