import django_filters
from django.utils import timezone
from .models import Activity

class ActivityFilter(django_filters.FilterSet):
    # Standard field filters
    activity_type = django_filters.CharFilter(field_name='activity_type')
    status = django_filters.CharFilter(field_name='status')
    assigned_to = django_filters.UUIDFilter(field_name='assigned_to__id')
    tenant_id = django_filters.UUIDFilter(field_name='tenant__id')
    parent_activity_id = django_filters.UUIDFilter(field_name='parent_activity__id')
    source_app = django_filters.CharFilter(
        field_name='metadata__source_app', lookup_expr='exact'
    )

    # Computed filters
    due_today = django_filters.BooleanFilter(method='filter_due_today')
    overdue = django_filters.BooleanFilter(method='filter_overdue')

    def filter_due_today(self, queryset, name, value):
        if value:
            today = timezone.localtime(timezone.now()).date()
            return queryset.filter(
                due_at__date=today,
                status__in=['pending', 'in_progress']
            )
        return queryset

    def filter_overdue(self, queryset, name, value):
        if value:
            now = timezone.now()
            return queryset.filter(
                due_at__lt=now,
                status__in=['pending', 'in_progress']
            )
        return queryset

    class Meta:
        model = Activity
        fields = ['activity_type', 'status', 'assigned_to', 'tenant_id',
                  'parent_activity_id', 'due_today', 'overdue', 'source_app']
