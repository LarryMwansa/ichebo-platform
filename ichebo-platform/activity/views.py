# activity/views.py — Django template views + HTMX partial views
import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Activity, ActivityLog


def _user_level(user):
    return getattr(user, 'competence_level', 0)


PERSONAL_TYPES = ['task', 'habit', 'goal', 'reminder', 'skill']
ALL_TYPES = ['task', 'habit', 'goal', 'event', 'campaign', 'project', 'reminder', 'skill']
MINISTRY_TYPES = ['campaign', 'project', 'task', 'event']

TYPE_LABELS = {
    'task': 'Tasks', 'habit': 'Habits', 'goal': 'Goals',
    'event': 'Events', 'campaign': 'Campaigns', 'project': 'Projects',
    'reminder': 'Reminders', 'skill': 'Skills',
}


@login_required
def activity_detail(request, activity_id):
    activity = get_object_or_404(
        Activity, id=activity_id, deleted_at__isnull=True
    )
    
    # Breadcrumb: find where we came from
    via_record = None
    via_id = request.GET.get('via')
    if via_id:
        from records.models import Record
        via_record = Record.objects.filter(id=via_id).first()

    context = {
        'activity': activity,
        'via_record': via_record,
        'user_level': _user_level(request.user),
        'active_app': 'activity',
        'ws_page_title': activity.title,
        'now': timezone.now(),
    }

    if request.headers.get('HX-Request'):
        return render(request, 'activity/partials/activity_detail_stage.html', context)
    return render(request, 'activity/activity_detail.html', context)


# ── My Activities home ────────────────────────────────────────────────────────

@login_required
def my_activities(request):
    user = request.user
    tab = request.GET.get('tab', 'personal')
    is_htmx = bool(request.headers.get('HX-Request'))

    # ── HTMX tab dispatch: return only the body partial ──────────────────────
    if is_htmx and tab == 'ministry':
        return _ministry_partial(request)

    if is_htmx and tab == 'calendar':
        return _calendar_partial(request)

    # ── Personal tab (default) ────────────────────────────────────────────────
    active_type = request.GET.get('type', '')

    qs = Activity.objects.filter(
        assigned_to=user,
        deleted_at__isnull=True,
        status__in=['pending', 'in_progress'],
    ).exclude(activity_type__in=['programme', 'lesson']).order_by('due_at', '-created_at')

    if active_type and active_type in ALL_TYPES:
        qs = qs.filter(activity_type=active_type)

    overdue = qs.filter(due_at__isnull=False, due_at__lt=timezone.now())
    due_today = qs.filter(due_at__date=timezone.now().date()).exclude(
        due_at__lt=timezone.now()
    )
    upcoming = qs.exclude(
        id__in=list(overdue.values_list('id', flat=True)) +
               list(due_today.values_list('id', flat=True))
    )

    activity_types = [(slug, TYPE_LABELS.get(slug, slug)) for slug in ALL_TYPES]

    personal_ctx = {
        'overdue':        overdue,
        'due_today':      due_today,
        'upcoming':       upcoming,
        'active_type':    active_type,
        'activity_types': activity_types,
        'overdue_count':  overdue.count(),
        'active_count':   qs.count(),
        'due_today_count': due_today.count(),
    }

    if is_htmx:
        return render(request, 'activity/partials/_m_personal.html', personal_ctx)

    return render(request, 'activity/my_activities.html', {
        **personal_ctx,
        'user_level':    _user_level(user),
        'active_app':    'activity',
        'ws_page_title': 'Activity',
        'active_tab':    tab,
    })


def _ministry_partial(request):
    """Return the ministry tab body partial (used by HTMX tab dispatch)."""
    user = request.user
    active_type = request.GET.get('type', '')
    assigned_tab = request.GET.get('assigned', 'all')

    qs = Activity.objects.filter(
        deleted_at__isnull=True,
        activity_type__in=MINISTRY_TYPES,
        status__in=['pending', 'in_progress'],
    ).order_by('due_at', '-created_at')

    if assigned_tab == 'mine':
        qs = qs.filter(assigned_to=user)
    if active_type and active_type in MINISTRY_TYPES:
        qs = qs.filter(activity_type=active_type)

    overdue_qs = qs.filter(due_at__isnull=False, due_at__lt=timezone.now())

    return render(request, 'activity/partials/_m_ministry.html', {
        'activities':    qs,
        'active_type':   active_type,
        'assigned_tab':  assigned_tab,
        'ministry_types': [(slug, TYPE_LABELS.get(slug, slug)) for slug in MINISTRY_TYPES],
        'now':           timezone.now(),
        'active_count':  qs.count(),
        'overdue_count': overdue_qs.count(),
    })


def _calendar_partial(request):
    """Return the calendar tab body partial (used by HTMX tab dispatch)."""
    from calendar_app.views import _MONTH_NAMES, _DAY_HEADERS, _events_by_date, _event_time
    from calendar_app.service import get_calendar_events
    import calendar as cal_module
    from datetime import date, timedelta

    cal_view = request.GET.get('view', 'month')
    today = date.today()

    if cal_view == 'week':
        date_str = request.GET.get('date', '')
        try:
            base = date.fromisoformat(date_str) if date_str else today
        except ValueError:
            base = today
        monday = base - timedelta(days=base.weekday())
        days = [monday + timedelta(days=i) for i in range(7)]
        raw_events = get_calendar_events(request.user, days[0], days[6])
        grouped = _events_by_date(raw_events)
        week_days = []
        for d in days:
            ev_list = grouped.get(d.isoformat(), [])
            week_days.append({
                'date': d,
                'iso': d.isoformat(),
                'day': d.day,
                'weekday_short': _DAY_HEADERS[d.weekday()],
                'is_today': d == today,
                'events': [{**ev, 'time': _event_time(ev)} for ev in ev_list],
            })
        prev_monday = monday - timedelta(days=7)
        next_monday = monday + timedelta(days=7)
        return render(request, 'activity/partials/_m_calendar.html', {
            'cal_view':          'week',
            'week_days':         week_days,
            'week_event_count':  sum(len(wd['events']) for wd in week_days),
            'week_label':        f'{monday.strftime("%-d %b")} – {days[6].strftime("%-d %b %Y")}',
            'prev_date':         prev_monday.isoformat(),
            'next_date':         next_monday.isoformat(),
            'today':             today,
            'active_count':      0,
            'overdue_count':     0,
        })

    # Month view (default)
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except ValueError:
        year, month = today.year, today.month
    month = max(1, min(12, month))
    cal_filter = request.GET.get('filter', '')

    cal_obj = cal_module.Calendar(firstweekday=0)
    weeks = cal_obj.monthdatescalendar(year, month)
    from_date, to_date = weeks[0][0], weeks[-1][6]
    raw_events = get_calendar_events(request.user, from_date, to_date)
    if cal_filter == 'personal':
        raw_events = [e for e in raw_events if not e.get('tenant_id')]
    elif cal_filter == 'institutional':
        raw_events = [e for e in raw_events if e.get('tenant_id')]
    now_iso = today.isoformat()
    for ev in raw_events:
        ev_date = (ev.get('scheduled_at') or ev.get('due_at') or '')[:10]
        ev['is_overdue'] = bool(ev_date and ev_date < now_iso and ev.get('status') != 'completed')
    grouped = _events_by_date(raw_events)
    grid = []
    for week in weeks:
        row = []
        for d in week:
            ev_list = grouped.get(d.isoformat(), [])
            row.append({
                'date': d, 'iso': d.isoformat(), 'day': d.day,
                'in_month': d.month == month, 'is_today': d == today,
                'events': ev_list[:3], 'overflow': max(0, len(ev_list) - 3),
            })
        grid.append(row)
    first = date(year, month, 1)
    prev_first = first - timedelta(days=1)
    next_first = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    month_event_count = sum(len(cell['events']) for week in grid for cell in week if cell['in_month'])
    return render(request, 'activity/partials/_m_calendar.html', {
        'cal_view':          'month',
        'year':              year,
        'month':             month,
        'month_name':        _MONTH_NAMES[month],
        'grid':              grid,
        'today':             today,
        'cal_filter':        cal_filter,
        'prev_year':         prev_first.year,
        'prev_month':        prev_first.month,
        'next_year':         next_first.year,
        'next_month':        next_first.month,
        'month_event_count': month_event_count,
        'active_count':      0,
        'overdue_count':     0,
    })


# ── HTMX: create activity ─────────────────────────────────────────────────────

@login_required
def htmx_create_activity(request):
    if request.method == 'POST':
        activity_type = request.POST.get('activity_type', 'task')
        title = request.POST.get('title', '').strip()
        if not title:
            return HttpResponse('<div class="badge-unit" style="background: var(--danger); color: #fff;">Title is required</div>', status=400)

        due_raw = request.POST.get('due_at', '').strip()
        due_at = None
        if due_raw:
            try:
                from django.utils.dateparse import parse_datetime, parse_date
                due_at = parse_datetime(due_raw) or (
                    timezone.make_aware(
                        timezone.datetime.combine(parse_date(due_raw), timezone.datetime.min.time())
                    ) if parse_date(due_raw) else None
                )
            except Exception:
                pass

        recurrence = request.POST.get('recurrence', 'none')
        kgs_pathway = request.POST.get('kgs_pathway', '') or None

        activity = Activity.objects.create(
            activity_type=activity_type,
            title=title,
            assigned_to=request.user,
            created_by=request.user,
            status='pending',
            progress=0,
            due_at=due_at,
            recurrence=recurrence,
            kgs_pathway=kgs_pathway,
            metadata={'source_app': 'activity'},
        )

        from django.urls import reverse
        from django.template.loader import render_to_string

        # Rebuild the personal activity lists for the updated canvas
        qs = Activity.objects.filter(
            assigned_to=request.user,
            deleted_at__isnull=True,
            status__in=['pending', 'in_progress'],
        ).exclude(activity_type__in=['programme', 'lesson']).order_by('due_at', '-created_at')

        overdue   = qs.filter(due_at__isnull=False, due_at__lt=timezone.now())
        due_today = qs.filter(due_at__date=timezone.now().date()).exclude(due_at__lt=timezone.now())
        upcoming  = qs.exclude(
            id__in=list(overdue.values_list('id', flat=True)) +
                   list(due_today.values_list('id', flat=True))
        )

        page_html = render_to_string('activity/partials/_d_personal.html', {
            'overdue':        overdue,
            'due_today':      due_today,
            'upcoming':       upcoming,
            'active_type':    '',
            'activity_types': [(slug, TYPE_LABELS.get(slug, slug)) for slug in ALL_TYPES],
            'overdue_count':  overdue.count(),
            'active_count':   qs.count(),
            'due_today_count': due_today.count(),
        }, request=request)

        oob_html = f'<div><div id="ics-canvas" hx-swap-oob="innerHTML">{page_html}</div></div>'
        home_url = reverse('activity:activity-home')
        response = HttpResponse(oob_html, content_type='text/html')
        response['HX-Trigger'] = json.dumps({'activityCreated': None, 'closeDrawer': None})
        response['HX-Push-Url'] = home_url
        return response

    activity_types = [(slug, TYPE_LABELS.get(slug, slug)) for slug in ALL_TYPES]
    # GET — return the create form
    return render(request, 'activity/partials/create_form.html', {
        'activity_types': activity_types,
    })


# ── HTMX: mark activity complete ─────────────────────────────────────────────

@login_required
def htmx_complete_activity(request, activity_id):
    if request.method != 'POST':
        return HttpResponse(status=405)

    activity = get_object_or_404(
        Activity, id=activity_id, assigned_to=request.user, deleted_at__isnull=True
    )
    old_status = activity.status
    activity.status = 'completed'
    activity.progress = 100
    activity.save(update_fields=['status', 'progress', 'updated_at'])

    ActivityLog.objects.create(
        activity=activity,
        created_by=request.user,
        event_type='status_changed',
        previous_value=old_status,
        new_value='completed',
    )

    if request.GET.get('redirect') == 'detail':
        from django.urls import reverse
        response = HttpResponse(status=204)
        response['HX-Redirect'] = reverse('activity:activity-detail', kwargs={'activity_id': activity.id})
        return response

    return render(request, 'activity/partials/_completed_item.html', {
        'activity': activity,
    })


# ── HTMX: edit activity ──────────────────────────────────────────────────────

@login_required
def htmx_edit_activity(request, activity_id):
    activity = get_object_or_404(
        Activity, id=activity_id, created_by=request.user, deleted_at__isnull=True
    )

    if request.GET.get('show') == '1':
        return render(request, 'activity/partials/activity_card.html', {'activity': activity})

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if title:
            activity.title = title
        due_raw = request.POST.get('due_at', '').strip()
        if due_raw:
            try:
                from django.utils.dateparse import parse_datetime, parse_date
                activity.due_at = parse_datetime(due_raw) or (
                    timezone.make_aware(
                        timezone.datetime.combine(parse_date(due_raw), timezone.datetime.min.time())
                    ) if parse_date(due_raw) else activity.due_at
                )
            except Exception:
                pass
        recurrence = request.POST.get('recurrence')
        if recurrence:
            activity.recurrence = recurrence
        activity.save(update_fields=['title', 'due_at', 'recurrence', 'updated_at'])
        ActivityLog.objects.create(
            activity=activity,
            created_by=request.user,
            event_type='edited',
        )
        # Drawer save → render updated stage partial with OOB swap into #ics-canvas,
        # close drawer via HX-Trigger, and update the browser URL via HX-Push-Url.
        if request.headers.get('HX-Target') == 'drawerInner':
            from django.urls import reverse
            from django.template.loader import render_to_string
            stage_html = render_to_string(
                'activity/partials/activity_detail_stage.html',
                {'activity': activity, 'user_level': _user_level(request.user), 'now': timezone.now()},
                request=request,
            )
            detail_url = reverse('activity:activity-detail', kwargs={'activity_id': activity.id})
            # Wrap in a throwaway div: HTMX's querySelectorAll('[hx-swap-oob]')
            # does NOT match the root element of the parsed fragment, only descendants.
            oob_html = f'<div><div id="ics-canvas" hx-swap-oob="innerHTML">{stage_html}</div></div>'
            response = HttpResponse(oob_html, content_type='text/html')
            response['HX-Trigger'] = json.dumps({'activityCreated': None})
            response['HX-Push-Url'] = detail_url
            return response
        return render(request, 'activity/partials/activity_card.html', {'activity': activity})

    activity_types = [(slug, TYPE_LABELS.get(slug, slug)) for slug in ALL_TYPES]
    # Drawer GET → mobile form; direct URL → redirect to detail page
    if request.headers.get('HX-Target') == 'drawerInner':
        return render(request, 'activity/partials/edit_form.html', {
            'activity': activity,
            'activity_types': activity_types,
        })
    # Direct URL access — redirect to detail page with edit intent
    from django.shortcuts import redirect
    return redirect('activity:activity-detail', activity_id=activity.id)


# ── HTMX: delete activity ─────────────────────────────────────────────────────

@login_required
def htmx_delete_activity(request, activity_id):
    if request.method != 'POST':
        return HttpResponse(status=405)

    activity = get_object_or_404(
        Activity, id=activity_id, created_by=request.user, deleted_at__isnull=True
    )
    activity.deleted_at = timezone.now()
    activity.save(update_fields=['deleted_at'])
    ActivityLog.objects.create(
        activity=activity,
        created_by=request.user,
        event_type='deleted',
    )
    return HttpResponse('')


# ── HTMX: activity list partial ───────────────────────────────────────────────

@login_required
def htmx_activity_list(request):
    user = request.user
    activity_type = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')

    qs = Activity.objects.filter(
        assigned_to=user,
        deleted_at__isnull=True,
    ).exclude(activity_type__in=['programme', 'lesson']).order_by('due_at', '-created_at')

    if activity_type and activity_type in ALL_TYPES:
        qs = qs.filter(activity_type=activity_type)

    if status_filter:
        qs = qs.filter(status=status_filter)
    else:
        qs = qs.filter(status__in=['pending', 'in_progress'])

    return render(request, 'activity/partials/activity_list.html', {
        'activities':  qs,
        'active_type': activity_type,
    })


@login_required
def ministry(request):
    user = request.user
    active_type = request.GET.get('type', '')
    assigned_tab = request.GET.get('tab', 'all')  # 'all' or 'mine'

    qs = Activity.objects.filter(
        deleted_at__isnull=True,
        activity_type__in=MINISTRY_TYPES,
        status__in=['pending', 'in_progress'],
    ).order_by('due_at', '-created_at')

    if assigned_tab == 'mine':
        qs = qs.filter(assigned_to=user)

    if active_type and active_type in MINISTRY_TYPES:
        qs = qs.filter(activity_type=active_type)

    ministry_types = [(slug, TYPE_LABELS.get(slug, slug)) for slug in MINISTRY_TYPES]

    return render(request, 'activity/ministry.html', {
        'activities': qs,
        'active_type': active_type,
        'assigned_tab': assigned_tab,
        'ministry_types': ministry_types,
        'user_level': _user_level(user),
        'now': timezone.now(),
        'active_app': 'activity',
        'ws_page_title': 'Activity',
    })


@login_required
def calendar_view(request):
    from calendar_app.views import month_view
    return month_view(request)


@login_required
def htmx_set_activity_link(request, activity_id):
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    activity = get_object_or_404(
        Activity, id=activity_id, created_by=request.user, deleted_at__isnull=True
    )
    record_id = request.POST.get('record_id')
    if record_id:
        from records.models import Record
        record = get_object_or_404(Record, id=record_id)
        activity.linked_record = record
        activity.save(update_fields=['linked_record', 'updated_at'])
    
    # Return HX-Redirect to refresh the full detail page with the new link
    from django.urls import reverse
    response = HttpResponse(status=204)
    response['HX-Redirect'] = reverse('activity:activity-detail', kwargs={'activity_id': activity.id})
    return response
