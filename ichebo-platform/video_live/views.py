from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from activity.models import Activity
from .utils import get_embed_type, get_embed_url


def _event_qs(tenant=None):
    """Optional tenant filter — existing global callers (steward-facing
    schedule/VOD/manage views) pass nothing and keep current behaviour.
    The Community-scoped live room passes the member's tenant explicitly."""
    qs = (
        Activity.objects
        .filter(activity_type='event', deleted_at__isnull=True)
        .exclude(metadata__stream_url=None)
        .exclude(metadata__stream_url='')
        .order_by('scheduled_at')
    )
    if tenant is not None:
        qs = qs.filter(tenant=tenant)
    return qs


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
    from collections import defaultdict
    import datetime as dt

    now = timezone.now()
    weeks = int(request.GET.get('weeks', 1))
    weeks = max(1, min(weeks, 4))  # clamp 1–4
    cutoff = now + timezone.timedelta(weeks=weeks)

    all_events = [_annotate_event(e) for e in _event_qs()]
    live = [e for e in all_events if e['is_live']]
    upcoming = [
        e for e in all_events
        if e['scheduled_at'] and now <= e['scheduled_at'] <= cutoff
    ]

    # Build a list of day buckets for the window
    today = now.date()
    days = []
    for i in range(weeks * 7):
        day = today + dt.timedelta(days=i)
        days.append({
            'date': day,
            'label': day.strftime('%A'),          # Monday
            'short': day.strftime('%d %b'),        # 08 May
            'is_today': day == today,
            'events': [
                e for e in upcoming
                if e['scheduled_at'] and e['scheduled_at'].date() == day
            ],
        })

    return render(request, 'video_live/schedule.html', {
        'days': days,
        'upcoming': upcoming,
        'live': live,
        'weeks': weeks,
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


# ---------------------------------------------------------------------------
# Studio — playout scheduler (Level 3+)
# ---------------------------------------------------------------------------

def _get_fallback():
    """Return the studio fallback Activity, or None."""
    return Activity.objects.filter(
        activity_type='event',
        deleted_at__isnull=True,
        metadata__studio_fallback=True,
    ).first()


def _studio_context(request):
    """Shared context for the studio view and its partials."""
    import datetime as dt
    now = timezone.now()
    all_events = [_annotate_event(e) for e in _event_qs()]
    live   = [e for e in all_events if e['is_live']]
    upcoming = [e for e in all_events if not e['is_live'] and not e['is_past']]
    fallback_obj = _get_fallback()
    fallback = _annotate_event(fallback_obj) if fallback_obj else None

    # Build today's timeline: 48 half-hour slots
    today = now.date()
    slots = []
    for h in range(24):
        for m in (0, 30):
            slot_dt = timezone.make_aware(
                dt.datetime.combine(today, dt.time(h, m))
            )
            slot_end = slot_dt + dt.timedelta(minutes=30)
            booked = [
                e for e in all_events
                if e['scheduled_at'] and
                   slot_dt <= e['scheduled_at'] < slot_end
            ]
            slots.append({
                'label': f'{h:02d}:{m:02d}',
                'dt':    slot_dt,
                'is_past': slot_end < now,
                'is_now':  slot_dt <= now < slot_end,
                'events':  booked,
            })

    return {
        'live':        live,
        'upcoming':    upcoming,
        'fallback':    fallback,
        'slots':       slots,
        'now':         now,
        'slot_size':   30,
        'can_manage':  True,
        'active_app':  'video',
        'active_video_tab': 'studio',
        'vod_count':   len([e for e in all_events if e['is_past']]),
    }


@login_required
def video_studio(request):
    if request.user.competence_level < 3:
        return redirect('video_live:home')
    ctx = _studio_context(request)
    return render(request, 'video_live/studio.html', ctx)


@login_required
def htmx_studio_now_playing(request):
    if request.user.competence_level < 3:
        return HttpResponse(status=403)
    ctx = _studio_context(request)
    return render(request, 'video_live/partials/studio_now_playing.html', ctx)


@login_required
def htmx_studio_timeline(request):
    if request.user.competence_level < 3:
        return HttpResponse(status=403)
    ctx = _studio_context(request)
    return render(request, 'video_live/partials/studio_timeline.html', ctx)


@login_required
def htmx_studio_quick_schedule(request):
    if request.user.competence_level < 3:
        return HttpResponse(status=403)
    slot_label = request.GET.get('slot', '')
    if request.method == 'POST':
        import json
        from django.contrib import messages
        from django.utils.dateparse import parse_datetime
        title       = request.POST.get('title', '').strip()
        stream_url  = request.POST.get('stream_url', '').strip()
        scheduled_at_str = request.POST.get('scheduled_at', '').strip()
        duration    = request.POST.get('duration_minutes', '60').strip()
        error = None
        if not title:
            error = 'Title is required.'
        elif not stream_url:
            error = 'Stream URL is required.'
        elif not scheduled_at_str:
            error = 'Date/time is required.'
        else:
            scheduled_at = parse_datetime(scheduled_at_str)
            if not scheduled_at:
                error = 'Invalid date/time.'
            else:
                if timezone.is_naive(scheduled_at):
                    scheduled_at = timezone.make_aware(scheduled_at)
                Activity.objects.create(
                    activity_type='event',
                    title=title,
                    scheduled_at=scheduled_at,
                    status='pending',
                    created_by=request.user,
                    metadata={
                        'stream_url': stream_url,
                        'duration_minutes': int(duration) if duration.isdigit() else 60,
                        'source_app': 'video_live',
                    },
                )
                resp = HttpResponse(status=204)
                resp['HX-Trigger'] = 'studioRefresh'
                resp['X-WS-Toast'] = json.dumps([
                    {'level': 'success', 'message': f'"{title}" added to the schedule.'}
                ])
                return resp
        return render(request, 'video_live/partials/studio_quick_schedule.html', {
            'slot_label': slot_label, 'error': error,
        })
    return render(request, 'video_live/partials/studio_quick_schedule.html', {
        'slot_label': slot_label,
    })


@login_required
def htmx_studio_set_fallback(request):
    if request.user.competence_level < 3:
        return HttpResponse(status=403)
    import json
    if request.method == 'POST':
        from django.contrib import messages
        stream_url = request.POST.get('fallback_url', '').strip()
        label      = request.POST.get('fallback_label', 'Default Loop').strip() or 'Default Loop'
        # Remove any existing fallback
        Activity.objects.filter(
            activity_type='event',
            deleted_at__isnull=True,
            metadata__studio_fallback=True,
        ).update(deleted_at=timezone.now())
        if stream_url:
            Activity.objects.create(
                activity_type='event',
                title=label,
                status='pending',
                created_by=request.user,
                metadata={
                    'stream_url': stream_url,
                    'studio_fallback': True,
                    'source_app': 'video_live',
                },
            )
        fallback_obj = _get_fallback()
        from video_live.utils import get_embed_url, get_embed_type
        fallback = _annotate_event(fallback_obj) if fallback_obj else None
        resp = render(request, 'video_live/partials/studio_fallback_form.html', {
            'fallback': fallback, 'saved': True,
        })
        resp['X-WS-Toast'] = json.dumps([
            {'level': 'success', 'message': 'Fallback video updated.'}
        ])
        return resp
    fallback_obj = _get_fallback()
    fallback = _annotate_event(fallback_obj) if fallback_obj else None
    return render(request, 'video_live/partials/studio_fallback_form.html', {
        'fallback': fallback,
    })



@login_required
def video_library(request):
    from records.models import Record
    videos = Record.objects.filter(
        record_family='media',
        deleted_at__isnull=True,
    ).order_by('-created_at')[:50]
    return render(request, 'video_live/library.html', {
        'videos': videos,
        'can_manage': request.user.competence_level >= 3,
        'active_video_tab': 'library',
    })
