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
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        since_str = request.query_params.get('since')
        since = parse_datetime(since_str) if since_str else None

        user = request.user
        
        # 1. Records
        # Visibility: Created by user OR in user's tenants OR global governance records
        record_qs = Record.objects.filter(deleted_at__isnull=True)
        if since:
            record_qs = record_qs.filter(updated_at__gte=since)
        
        user_tenant_ids = user.tenant_permissions.values_list('tenant_id', flat=True)
        
        record_qs = record_qs.filter(
            Q(created_by=user) | 
            Q(tenant_id__in=user_tenant_ids) |
            Q(record_class='governance', permissions_data__visibility='global')
        ).distinct()

        # 2. Activities
        # Visibility: Created by user OR assigned to user
        activity_qs = Activity.objects.filter(deleted_at__isnull=True)
        if since:
            activity_qs = activity_qs.filter(updated_at__gte=since)
            
        activity_qs = activity_qs.filter(
            Q(created_by=user) | Q(assigned_to=user)
        ).distinct()

        # 3. Notifications
        # Visibility: Only the user's notifications
        notification_qs = Notification.objects.filter(user=user)
        if since:
            notification_qs = notification_qs.filter(updated_at__gte=since)

        return Response({
            'records': RecordSerializer(record_qs, many=True).data,
            'activities': ActivitySerializer(activity_qs, many=True).data,
            'notifications': NotificationSerializer(notification_qs, many=True).data,
            'server_timestamp': timezone.now().isoformat()
        })
