from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.db.models import Q

from records.models import Record
from records.serializers import RecordSerializer
from activity.models import Activity
from activity.serializers import ActivitySerializer
from notifications.models import Notification
from notifications.serializers import NotificationSerializer

class SyncChangesView(APIView):
    """
    Delta Sync API for mobile/offline support.
    Returns all Records, Activities, and Notifications modified after the 'since' timestamp.
    Includes hierarchical visibility for stewards.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        since_str = request.query_params.get('since')
        since = parse_datetime(since_str) if since_str else None

        user = request.user
        
        # Identification of oversight tenants for stewards
        steward_roles = [
            'branch-steward', 'district-steward', 'provincial-steward',
            'national-steward', 'regional-steward', 'continental-steward',
            'global-steward', 'admin'
        ]
        user_perms = user.tenant_permissions.all().select_related('tenant')
        direct_tenant_ids = [p.tenant_id for p in user_perms]
        oversight_paths = [p.tenant.path for p in user_perms if p.role in steward_roles]

        # 1. Records
        record_qs = Record.objects.filter(deleted_at__isnull=True)
        if since:
            record_qs = record_qs.filter(updated_at__gte=since)
        
        record_filter = Q(created_by=user) | Q(tenant_id__in=direct_tenant_ids) | \
                        Q(record_class='governance', permissions_data__visibility='global')
        
        for path in oversight_paths:
            record_filter |= Q(tenant__path__startswith=path)
        
        record_qs = record_qs.filter(record_filter).distinct()

        # 2. Activities
        activity_qs = Activity.objects.filter(deleted_at__isnull=True)
        if since:
            activity_qs = activity_qs.filter(updated_at__gte=since)
            
        activity_filter = Q(created_by=user) | Q(assigned_to=user) | Q(tenant_id__in=direct_tenant_ids)
        
        for path in oversight_paths:
            activity_filter |= Q(tenant__path__startswith=path)

        activity_qs = activity_qs.filter(activity_filter).distinct()

        # 3. Notifications
        notification_qs = Notification.objects.filter(user=user)
        if since:
            notification_qs = notification_qs.filter(updated_at__gte=since)

        return Response({
            'records': RecordSerializer(record_qs, many=True).data,
            'activities': ActivitySerializer(activity_qs, many=True).data,
            'notifications': NotificationSerializer(notification_qs, many=True).data,
            'server_timestamp': timezone.now().isoformat()
        })
