from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Activity, ActivityLog
from .serializers import ActivitySerializer, ActivityLogSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def activity_list_create(request):
    """List activities or create a new activity."""
    if request.method == 'GET':
        queryset = Activity.objects.filter(deleted_at__isnull=True)

        tenant = request.query_params.get('tenant')
        if tenant:
            queryset = queryset.filter(tenant_id=tenant)

        activity_type = request.query_params.get('activity_type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)

        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        assigned_to = request.query_params.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)

        page_size = 20
        page = request.query_params.get('page', 1)
        try:
            page = int(page)
        except (ValueError, TypeError):
            page = 1

        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        activities = queryset.order_by('-created_at')[start:end]
        serializer = ActivitySerializer(activities, many=True)
        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data,
        })

    serializer = ActivitySerializer(data=request.data)
    if serializer.is_valid():
        activity = serializer.save(created_by=request.user)
        ActivityLog.objects.create(
            tenant=activity.tenant,
            created_by=request.user,
            activity=activity,
            event_type='created',
            previous_value=None,
            new_value=serializer.data,
            note='Activity created',
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def activity_detail(request, pk):
    """Retrieve, update, or soft-delete a specific activity."""
    activity = get_object_or_404(Activity, pk=pk, deleted_at__isnull=True)

    if request.method == 'GET':
        serializer = ActivitySerializer(activity)
        return Response(serializer.data)

    if request.method == 'PATCH':
        previous_status = activity.status
        previous_progress = activity.progress
        previous_assigned = activity.assigned_to_id

        serializer = ActivitySerializer(activity, data=request.data, partial=True)
        if serializer.is_valid():
            activity = serializer.save()

            if previous_status != activity.status:
                ActivityLog.objects.create(
                    tenant=activity.tenant,
                    created_by=request.user,
                    activity=activity,
                    event_type='status_changed',
                    previous_value=previous_status,
                    new_value=activity.status,
                    note='Activity status changed',
                )

            if previous_progress != activity.progress:
                ActivityLog.objects.create(
                    tenant=activity.tenant,
                    created_by=request.user,
                    activity=activity,
                    event_type='progress_updated',
                    previous_value=previous_progress,
                    new_value=activity.progress,
                    note='Activity progress updated',
                )

            if previous_assigned != activity.assigned_to_id:
                ActivityLog.objects.create(
                    tenant=activity.tenant,
                    created_by=request.user,
                    activity=activity,
                    event_type='assigned',
                    previous_value=previous_assigned,
                    new_value=activity.assigned_to_id,
                    note='Activity assignment changed',
                )

            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    activity.deleted_at = timezone.now()
    activity.save()
    return Response({'detail': 'Activity soft-deleted'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def activity_logs(request, pk):
    """Retrieve the activity log history for a specific activity."""
    activity = get_object_or_404(Activity, pk=pk)
    logs = activity.logs.order_by('-created_at')
    serializer = ActivityLogSerializer(logs, many=True)
    return Response({'results': serializer.data})
