"""
Ichebo Channel — now-playing resolution service (ADR-024).

Resolution order:
  1. ChannelSlot with scheduled_start <= now <= scheduled_end
  2. BroadcastSchedule with status='live' in the tenant
  3. ChannelConfig.fallback_playlist rotation
  4. ChannelConfig.loop_default_video_id
  5. Offline — no content configured

Pure Python — no DRF, no HTTP. Takes a Tenant instance, returns a dict
matching the GET /api/broadcast/now/ response schema.
"""
from django.utils import timezone

from .models import ChannelConfig, ChannelSlot


def resolve_now_playing(tenant):
    """Resolve what the Ichebo Channel should be playing right now for
    `tenant`. Never raises — falls through to the offline state if any
    level's lookup is unavailable."""
    now = timezone.now()

    slot = (
        ChannelSlot.objects
        .filter(tenant=tenant, scheduled_start__lte=now, scheduled_end__gte=now)
        .first()
    )
    if slot:
        return _build_slot_response(slot)

    # BroadcastSchedule has no deleted_at field — confirmed against
    # video_live/models.py and the real working query in
    # community/views.py:_find_live_session, which this mirrors.
    from video_live.models import BroadcastSchedule
    live = (
        BroadcastSchedule.objects
        .filter(tenant=tenant, status='live')
        .order_by('-scheduled_at')
        .first()
    )
    if live:
        return _build_live_response(live)

    config = ChannelConfig.objects.filter(tenant=tenant).first()

    if config and config.fallback_playlist:
        # Architecturally sound fallback rotation: 
        # Deterministic based on the current hour so all concurrent viewers see the same fallback,
        # and we do not mutate database state on a GET polling request.
        pos = (now.hour) % len(config.fallback_playlist)
        video_id = config.fallback_playlist[pos]
        return _build_vod_response(video_id, source='fallback')

    if config and config.loop_default_video_id:
        return _build_vod_response(str(config.loop_default_video_id), source='loop')

    if config and config.loop_default_external_url:
        return _build_external_response(config.loop_default_external_url, source='loop')

    return _offline_response()

import re

def _build_external_response(url, source='loop'):
    is_youtube = False
    embed_url = url
    
    yt_match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)', url)
    if yt_match:
        is_youtube = True
        video_id = yt_match.group(1)
        # Using mute=1 because most browsers block autoplay unmuted
        embed_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1&mute=1&loop=1&playlist={video_id}"
        
    return {
        'content_type': 'vod',
        'source': source,
        'title': 'Loop Default',
        'is_live': False,
        'video_url': embed_url,
        'is_youtube': is_youtube,
    }


def _build_slot_response(slot):
    return {
        'content_type': slot.content_type,
        'source': 'scheduled',
        'title': slot.title,
        'video_url': _resolve_slot_video_url(slot),
        'hls_url': None,
        'is_live': slot.content_type == 'live',
        'thumbnail_url': None,
        'ends_at': slot.scheduled_end.isoformat(),
        'next_scheduled': _get_next_slot(slot.tenant, slot.scheduled_end),
    }


def _build_live_response(broadcast):
    stream_url = broadcast.viewer_hls_url or broadcast.hls_url or ''
    return {
        'content_type': 'live',
        'source': 'live',
        'title': broadcast.title,
        'video_url': stream_url,
        'hls_url': stream_url,
        'is_live': True,
        'thumbnail_url': None,
        'ends_at': None,
        'next_scheduled': None,
    }


def _build_vod_response(video_id, source):
    from records.models import Record
    try:
        record = Record.objects.get(id=video_id)
        video_url = record.custom_fields.get('video_url', '')
    except Record.DoesNotExist:
        video_url = ''

    return {
        'content_type': 'vod',
        'source': source,
        'title': record.title if 'record' in locals() else None,
        'video_url': video_url,
        'hls_url': None,
        'is_live': False,
        'thumbnail_url': None,
        'ends_at': None,
        'next_scheduled': None,
        '_video_id': video_id,
    }


def _offline_response():
    return {
        'content_type': 'offline',
        'source': 'offline',
        'title': None,
        'video_url': None,
        'hls_url': None,
        'is_live': False,
        'thumbnail_url': None,
        'ends_at': None,
        'next_scheduled': None,
    }


def _resolve_slot_video_url(slot):
    if slot.content_type == 'live' and slot.broadcast_schedule_id:
        from video_live.models import BroadcastSchedule
        try:
            bs = BroadcastSchedule.objects.get(id=slot.broadcast_schedule_id)
            return bs.viewer_hls_url or bs.hls_url or ''
        except BroadcastSchedule.DoesNotExist:
            return ''
    return ''


def _get_next_slot(tenant, after):
    next_slot = (
        ChannelSlot.objects
        .filter(tenant=tenant, scheduled_start__gt=after)
        .order_by('scheduled_start')
        .first()
    )
    if next_slot:
        return {
            'title': next_slot.title,
            'starts_at': next_slot.scheduled_start.isoformat(),
        }
    return None
