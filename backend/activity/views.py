# activity/views.py — Django template views + HTMX partial views
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

    return render(request, 'activity/activity_detail.html', {
        'activity': activity,
        'via_record': via_record,
        'user_level': _user_level(request.user),
    })


# ── My Activities home ────────────────────────────────────────────────────────

@login_required
def my_activities(request):
    user = request.user
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

    if request.headers.get('HX-Request'):
        return render(request, 'activity/partials/activity_list.html', {
            'activities': qs,
            'active_type': active_type,
        })

    activity_types = [(slug, TYPE_LABELS.get(slug, slug)) for slug in ALL_TYPES]

    return render(request, 'activity/my_activities.html', {
        'overdue':       overdue,
        'due_today':     due_today,
        'upcoming':      upcoming,
        'active_type':   active_type,
        'activity_types': activity_types,
        'user_level':    _user_level(user),
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

        response = render(request, 'activity/partials/activity_card.html', {
            'activity': activity,
        })
        response['HX-Trigger'] = 'activityCreated'
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
        return render(request, 'activity/partials/activity_card.html', {'activity': activity})

    activity_types = [(slug, TYPE_LABELS.get(slug, slug)) for slug in ALL_TYPES]
    # GET — return edit form pre-populated
    return render(request, 'activity/partials/edit_form.html', {
        'activity': activity,
        'activity_types': activity_types,
    })


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
    })


@login_required
def calendar_view(request):
    user = request.user

    qs = Activity.objects.filter(
        assigned_to=user,
        deleted_at__isnull=True,
        due_at__isnull=False,
    ).exclude(activity_type__in=['programme', 'lesson']).order_by('due_at')

    return render(request, 'activity/calendar_view.html', {
        'activities': qs,
        'user_level': _user_level(user),
        'now': timezone.now(),
    })


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
