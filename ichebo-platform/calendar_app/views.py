import calendar
from collections import defaultdict
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as http_status

from .service import get_calendar_events


# ---------------------------------------------------------------------------
# DRF API — events feed
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def calendar_events(request):
    from_str = request.query_params.get('from')
    to_str = request.query_params.get('to')
    tenant_id = request.query_params.get('tenant_id')
    activity_type = request.query_params.get('activity_type')
    source_app = request.query_params.get('source_app')

    from_date = parse_date(from_str) if from_str else date.today()
    to_date = parse_date(to_str) if to_str else from_date + timedelta(days=30)

    if from_date > to_date:
        return Response(
            {"detail": "'from' must be before or equal to 'to'."},
            status=http_status.HTTP_400_BAD_REQUEST
        )

    events = get_calendar_events(
        user=request.user,
        from_date=from_date,
        to_date=to_date,
        tenant_id=tenant_id,
        activity_type=activity_type,
        source_app=source_app,
    )

    return Response({'events': events, 'count': len(events)})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MONTH_NAMES = [
    '', 'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]

_DAY_HEADERS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def _events_by_date(events):
    """Group events list (from service) into a dict keyed by ISO date string."""
    grouped = defaultdict(list)
    for ev in events:
        key = (ev['scheduled_at'] or ev['due_at'] or '')[:10]
        if key:
            grouped[key].append(ev)
    return grouped


def _event_time(ev):
    """Return HH:MM string from the event's scheduled_at or due_at, or ''."""
    ts = ev.get('scheduled_at') or ev.get('due_at') or ''
    return ts[11:16] if len(ts) >= 16 else ''


# ---------------------------------------------------------------------------
# Month view
# ---------------------------------------------------------------------------

@login_required
def month_view(request):
    today = date.today()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except ValueError:
        year, month = today.year, today.month

    # Clamp
    month = max(1, min(12, month))

    cal = calendar.Calendar(firstweekday=0)  # Monday-first
    weeks = cal.monthdatescalendar(year, month)  # list of 7-element date lists

    from_date = weeks[0][0]
    to_date = weeks[-1][6]

    # Filter: 'personal' = only mine, 'institutional' = only tenant, '' = all
    cal_filter = request.GET.get('filter', '')

    raw_events = get_calendar_events(request.user, from_date, to_date)

    # Apply filter
    if cal_filter == 'personal':
        raw_events = [e for e in raw_events if not e.get('tenant_id')]
    elif cal_filter == 'institutional':
        raw_events = [e for e in raw_events if e.get('tenant_id')]

    # Annotate overdue
    now_iso = date.today().isoformat()
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
                'date': d,
                'iso': d.isoformat(),
                'day': d.day,
                'in_month': d.month == month,
                'is_today': d == today,
                'events': ev_list[:3],
                'overflow': max(0, len(ev_list) - 3),
            })
        grid.append(row)

    # Prev / next
    first = date(year, month, 1)
    prev_first = first - timedelta(days=1)
    next_first = (first.replace(day=28) + timedelta(days=4)).replace(day=1)

    month_event_count = sum(len(cell['events']) for week in grid for cell in week if cell['in_month'])

    ctx = {
        'view': 'month',
        'year': year,
        'month': month,
        'month_name': _MONTH_NAMES[month],
        'day_headers': _DAY_HEADERS,
        'grid': grid,
        'today': today,
        'cal_filter': cal_filter,
        'prev_year': prev_first.year,
        'prev_month': prev_first.month,
        'next_year': next_first.year,
        'next_month': next_first.month,
        'month_event_count': month_event_count,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'calendar/_month_grid.html', ctx)
    return render(request, 'calendar/month.html', ctx)


# ---------------------------------------------------------------------------
# Week view
# ---------------------------------------------------------------------------

@login_required
def week_view(request):
    today = date.today()
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
            'events': [
                {**ev, 'time': _event_time(ev)} for ev in ev_list
            ],
        })

    prev_monday = monday - timedelta(days=7)
    next_monday = monday + timedelta(days=7)

    week_event_count = sum(len(wd['events']) for wd in week_days)

    ctx = {
        'view': 'week',
        'monday': monday,
        'week_days': week_days,
        'today': today,
        'prev_date': prev_monday.isoformat(),
        'next_date': next_monday.isoformat(),
        'today_date': today.isoformat(),
        'week_label': f'{monday.strftime("%-d %b")} – {days[6].strftime("%-d %b %Y")}',
        'week_event_count': week_event_count,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'calendar/_week_grid.html', ctx)
    return render(request, 'calendar/week.html', ctx)
