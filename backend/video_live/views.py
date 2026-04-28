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

    event._stream_url = stream_url
    event._embed_url = get_embed_url(stream_url)
    event._embed_type = get_embed_type(stream_url)
    event._duration = duration
    event._is_live = is_live
    event._is_past = is_past
    return event


# ---------------------------------------------------------------------------
# Home — now playing + upcoming
# ---------------------------------------------------------------------------

@login_required
def video_home(request):
    now = timezone.now()
    events = [_annotate_event(e) for e in _event_qs()]
    live = [e for e in events if e._is_live]
    upcoming = [
        e for e in events
        if not e._is_live and not e._is_past
        and e.scheduled_at and e.scheduled_at <= now + timezone.timedelta(days=7)
    ]
    recent_vod = [e for e in events if e._is_past][:6]

    return render(request, 'video_live/home.html', {
        'live': live,
        'upcoming': upcoming,
        'recent_vod': recent_vod,
        'can_manage': request.user.competence_level >= 3,
    })


# ---------------------------------------------------------------------------
# Live — current stream with HTMX auto-refresh
# ---------------------------------------------------------------------------

@login_required
def video_live_view(request):
    events = [_annotate_event(e) for e in _event_qs()]
    live = [e for e in events if e._is_live]

    if request.headers.get('HX-Request'):
        return render(request, 'video_live/_live_player.html', {'live': live})

    return render(request, 'video_live/live.html', {'live': live})


# ---------------------------------------------------------------------------
# Schedule — next 7 days
# ---------------------------------------------------------------------------

@login_required
def video_schedule(request):
    now = timezone.now()
    cutoff = now + timezone.timedelta(days=7)
    upcoming = [
        _annotate_event(e) for e in _event_qs()
        if e.scheduled_at and now <= e.scheduled_at <= cutoff
    ]
    return render(request, 'video_live/schedule.html', {
        'upcoming': upcoming,
        'can_manage': request.user.competence_level >= 3,
    })


# ---------------------------------------------------------------------------
# VOD Library
# ---------------------------------------------------------------------------

@login_required
def video_vod(request):
    all_events = [_annotate_event(e) for e in _event_qs()]
    vod = [e for e in all_events if e._is_past]
    return render(request, 'video_live/vod.html', {'vod': vod})


# ---------------------------------------------------------------------------
# Watch — individual event player
# ---------------------------------------------------------------------------

@login_required
def video_watch(request, event_id):
    event = get_object_or_404(Activity, id=event_id, activity_type='event', deleted_at__isnull=True)
    _annotate_event(event)
    return render(request, 'video_live/watch.html', {'event': event})


# ---------------------------------------------------------------------------
# Manage — steward event creation (Level 3+)
# ---------------------------------------------------------------------------

@login_required
def video_manage(request):
    if request.user.competence_level < 3:
        return redirect('video_live:home')

    events = list(_event_qs().order_by('-scheduled_at')[:30])
    for e in events:
        _annotate_event(e)

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
                return redirect('video_live:manage')

    return render(request, 'video_live/manage.html', {
        'events': events,
        'error': error,
    })


@login_required
@require_POST
def video_delete_event(request, event_id):
    if request.user.competence_level < 3:
        return redirect('video_live:home')
    event = get_object_or_404(Activity, id=event_id, activity_type='event')
    event.deleted_at = timezone.now()
    event.save(update_fields=['deleted_at'])
    return redirect('video_live:manage')
