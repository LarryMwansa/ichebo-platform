from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from activity.models import Activity
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

        return Response({
            'live':     live,
            'upcoming': upcoming,
            'vod':      vod,
        })
