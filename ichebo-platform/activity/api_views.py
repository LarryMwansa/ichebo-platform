import uuid
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Activity, ActivityLog
from .serializers import ActivitySerializer, ActivityLogSerializer
from .filters import ActivityFilter

@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok", "app": "activity"})

class ActivityViewSet(viewsets.ModelViewSet):
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ActivityFilter

    def get_queryset(self):
        user = self.request.user
        surface = self.request.query_params.get('surface')

        qs = Activity.objects.filter(deleted_at__isnull=True)

        if surface == 'personal':
            return qs.filter(created_by=user, tenant__isnull=True)

        if surface == 'ministry':
            user_tenant_ids = user.tenant_permissions.filter(
                is_active=True
            ).values_list('tenant_id', flat=True)
            return qs.filter(tenant_id__in=user_tenant_ids)

        user_tenant_ids = user.tenant_permissions.filter(
            is_active=True
        ).values_list('tenant_id', flat=True)

        personal = qs.filter(created_by=user, tenant__isnull=True)
        assigned = qs.filter(assigned_to=user, tenant_id__in=user_tenant_ids)

        return (personal | assigned).distinct()

    def perform_create(self, serializer):
        user = self.request.user
        user_level = user.competence_level

        assigned_to = serializer.validated_data.get('assigned_to')
        if assigned_to and assigned_to != user and user_level < 3:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only stewards (Level 3+) may assign activities to other users.")

        metadata = serializer.validated_data.get('metadata', {})
        if metadata.get('is_template') and user_level < 4:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only Senior Stewards (Level 4+) may create activity templates.")

        serializer.save(created_by=user)

    def perform_update(self, serializer):
        instance = self.get_object()
        old_status = instance.status
        old_assigned = instance.assigned_to_id

        updated = serializer.save()

        if updated.status != old_status:
            ActivityLog.objects.create(
                activity=updated,
                tenant=updated.tenant,
                created_by=self.request.user,
                event_type='status_changed',
                previous_value=old_status,
                new_value=updated.status
            )

        if updated.assigned_to_id != old_assigned:
            ActivityLog.objects.create(
                activity=updated,
                tenant=updated.tenant,
                created_by=self.request.user,
                event_type='assigned',
                previous_value=str(old_assigned),
                new_value=str(updated.assigned_to_id)
            )

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['deleted_at'])

    @action(detail=True, methods=['post'], url_path='instantiate')
    def instantiate(self, request, pk=None):
        user = request.user
        user_level = user.competence_level
        if user_level < 2:
            return Response(
                {"detail": "Level 2 or above required to instantiate templates."},
                status=status.HTTP_403_FORBIDDEN
            )

        template = self.get_object()
        if not template.metadata.get('is_template'):
            return Response(
                {"detail": "This activity is not a template."},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_activity = Activity.objects.create(
            tenant=template.tenant,
            created_by=user,
            activity_type=template.activity_type,
            title=template.title,
            description=template.description,
            recurrence=template.recurrence,
            recurrence_rule=template.recurrence_rule,
            kgs_pillar=template.kgs_pillar,
            kgs_pathway=template.kgs_pathway,
            status='pending',
            progress=0,
            assigned_to=user,
            metadata={
                **template.metadata,
                'is_template': False,
                'template_id': str(template.id),
                'source_app': 'activity',
            }
        )

        ActivityLog.objects.create(
            activity=new_activity,
            tenant=new_activity.tenant,
            created_by=user,
            event_type='created',
            new_value=f'Instantiated from template {template.id}'
        )

        serializer = self.get_serializer(new_activity)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
