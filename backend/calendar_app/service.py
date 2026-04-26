from django.utils.dateparse import parse_datetime
from activity.models import Activity
from django.db.models import Q as models_Q

def get_calendar_events(user, from_date, to_date, tenant_id=None,
                        activity_type=None, source_app=None):
    """
    Aggregate Activity objects with scheduled_at or due_at in range.
    """
    user_tenant_ids = list(
        user.tenant_permissions.filter(is_active=True).values_list('tenant_id', flat=True)
    )

    qs = Activity.objects.filter(deleted_at__isnull=True).filter(
        models_Q(created_by=user, tenant__isnull=True) |
        models_Q(tenant_id__in=user_tenant_ids)
    )

    qs = qs.filter(
        models_Q(scheduled_at__date__gte=from_date, scheduled_at__date__lte=to_date) |
        models_Q(due_at__date__gte=from_date, due_at__date__lte=to_date)
    )

    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)
    if activity_type:
        qs = qs.filter(activity_type=activity_type)
    if source_app:
        qs = qs.filter(metadata__source_app=source_app)

    events = []
    for activity in qs.order_by('scheduled_at', 'due_at'):
        events.append({
            'id': str(activity.id),
            'source_type': 'activity',
            'source_app': activity.metadata.get('source_app', 'activity'),
            'title': activity.title,
            'scheduled_at': activity.scheduled_at.isoformat() if activity.scheduled_at else None,
            'due_at': activity.due_at.isoformat() if activity.due_at else None,
            'activity_type': activity.activity_type,
            'record_type': None,
            'tenant_id': str(activity.tenant_id) if activity.tenant_id else None,
            'status': activity.status,
            'kgs_pillar': activity.kgs_pillar,
            'kgs_pathway': activity.kgs_pathway,
        })

    return events
