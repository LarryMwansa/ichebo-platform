from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

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


def _annotate_event(event):
    """Return a plain dict safe for Django templates (no underscore attributes)."""
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
        'id':          event.id,
        'title':       event.title,
        'description': event.description,
        'scheduled_at': event.scheduled_at,
        'stream_url':  stream_url,
        'embed_url':   get_embed_url(stream_url),
        'embed_type':  get_embed_type(stream_url),
        'duration':    duration,
        'is_live':     is_live,
        'is_past':     is_past,
    }


# ---------------------------------------------------------------------------
# Home — now playing + upcoming
# ---------------------------------------------------------------------------

@login_required
def video_home(request):
    now = timezone.now()
    events = [_annotate_event(e) for e in _event_qs()]
    live = [e for e in events if e['is_live']]
    upcoming = [
        e for e in events
        if not e['is_live'] and not e['is_past']
        and e['scheduled_at'] and e['scheduled_at'] <= now + timezone.timedelta(days=7)
    ]
    recent_vod = [e for e in events if e['is_past']][:6]

    all_vod = [e for e in events if e['is_past']]
    return render(request, 'video_live/home.html', {
        'live': live,
        'upcoming': upcoming,
        'recent_vod': recent_vod[:6],
        'can_manage': request.user.competence_level >= 3,
        'active_app': 'video',
        'active_video_tab': 'home',
        'ws_page_title': 'Video',
        'vod_count': len(all_vod),
    })


# ---------------------------------------------------------------------------
# Live — current stream with HTMX auto-refresh
# ---------------------------------------------------------------------------

@login_required
def video_live_view(request):
    events = [_annotate_event(e) for e in _event_qs()]
    live = [e for e in events if e['is_live']]

    if request.headers.get('HX-Request'):
        return render(request, 'video_live/_live_player.html', {'live': live})

    all_events = [_annotate_event(e) for e in _event_qs()]
    upcoming = [e for e in all_events if not e['is_live'] and not e['is_past']]
    return render(request, 'video_live/live.html', {
        'live': live,
        'upcoming': upcoming,
        'can_manage': request.user.competence_level >= 3,
        'active_app': 'video',
        'active_video_tab': 'live',
        'vod_count': len([e for e in all_events if e['is_past']]),
    })


# ---------------------------------------------------------------------------
# Schedule — next 7 days
# ---------------------------------------------------------------------------

@login_required
def video_schedule(request):
    now = timezone.now()
    cutoff = now + timezone.timedelta(days=7)
    all_events = [_annotate_event(e) for e in _event_qs()]
    upcoming = [
        e for e in all_events
        if e['scheduled_at'] and now <= e['scheduled_at'] <= cutoff
    ]
    live = [e for e in all_events if e['is_live']]
    return render(request, 'video_live/schedule.html', {
        'upcoming': upcoming,
        'live': live,
        'can_manage': request.user.competence_level >= 3,
        'active_app': 'video',
        'active_video_tab': 'schedule',
        'ws_page_title': 'Video',
        'vod_count': len([e for e in all_events if e['is_past']]),
    })


# ---------------------------------------------------------------------------
# VOD Library
# ---------------------------------------------------------------------------

@login_required
def video_vod(request):
    all_events = [_annotate_event(e) for e in _event_qs()]
    vod = [e for e in all_events if e['is_past']]
    live = [e for e in all_events if e['is_live']]
    upcoming = [e for e in all_events if not e['is_live'] and not e['is_past']]
    return render(request, 'video_live/vod.html', {
        'vod': vod,
        'live': live,
        'upcoming': upcoming,
        'can_manage': request.user.competence_level >= 3,
        'active_app': 'video',
        'active_video_tab': 'vod',
        'ws_page_title': 'Video',
        'vod_count': len(vod),
    })


# ---------------------------------------------------------------------------
# Watch — individual event player
# ---------------------------------------------------------------------------

@login_required
def video_watch(request, event_id):
    activity = get_object_or_404(Activity, id=event_id, activity_type='event', deleted_at__isnull=True)
    event = _annotate_event(activity)
    all_events = [_annotate_event(e) for e in _event_qs()]
    upcoming = [e for e in all_events if not e['is_live'] and not e['is_past']]
    live = [e for e in all_events if e['is_live']]
    return render(request, 'video_live/watch.html', {
        'event': event,
        'live': live,
        'upcoming': upcoming,
        'can_manage': request.user.competence_level >= 3,
        'active_app': 'video',
        'active_video_tab': 'home',
        'vod_count': len([e for e in all_events if e['is_past']]),
    })


# ---------------------------------------------------------------------------
# Manage — steward event creation (Level 3+)
# ---------------------------------------------------------------------------

@login_required
def video_manage(request):
    if request.user.competence_level < 3:
        return redirect('video_live:home')

    events = [_annotate_event(e) for e in _event_qs().order_by('-scheduled_at')[:30]]

    error = None
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        stream_url = request.POST.get('stream_url', '').strip()
        scheduled_at_str = request.POST.get('scheduled_at', '').strip()
        duration = request.POST.get('duration_minutes', '60').strip()
        description = request.POST.get('description', '').strip()

        if not title:
            error = 'Title is required.'
        elif not stream_url:
            error = 'Stream URL is required.'
        elif not scheduled_at_str:
            error = 'Broadcast date/time is required.'
        else:
            from django.utils.dateparse import parse_datetime
            scheduled_at = parse_datetime(scheduled_at_str)
            if not scheduled_at:
                error = 'Invalid date/time format. Use YYYY-MM-DDTHH:MM.'
            else:
                if timezone.is_naive(scheduled_at):
                    scheduled_at = timezone.make_aware(scheduled_at)
                from django.contrib import messages as _messages
                Activity.objects.create(
                    activity_type='event',
                    title=title,
                    description=description or None,
                    scheduled_at=scheduled_at,
                    status='pending',
                    created_by=request.user,
                    metadata={
                        'stream_url': stream_url,
                        'duration_minutes': int(duration) if duration.isdigit() else 60,
                        'source_app': 'video_live',
                    },
                )
                _messages.success(request, f'"{title}" scheduled successfully.')
                return redirect('video_live:manage')

    all_events_ann = [_annotate_event(e) for e in _event_qs()]
    upcoming = [e for e in all_events_ann if not e['is_live'] and not e['is_past']]
    live = [e for e in all_events_ann if e['is_live']]
    return render(request, 'video_live/manage.html', {
        'events': events,
        'error': error,
        'live': live,
        'upcoming': upcoming,
        'can_manage': True,
        'active_app': 'video',
        'active_video_tab': 'manage',
        'ws_page_title': 'Video',
        'vod_count': len([e for e in all_events_ann if e['is_past']]),
    })


@login_required
@require_POST
def video_delete_event(request, event_id):
    from django.contrib import messages
    if request.user.competence_level < 3:
        return redirect('video_live:home')
    event = get_object_or_404(Activity, id=event_id, activity_type='event')
    title = event.title
    event.deleted_at = timezone.now()
    event.save(update_fields=['deleted_at'])
    messages.success(request, f'"{title}" has been deleted.')
    return redirect('video_live:manage')
