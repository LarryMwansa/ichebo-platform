from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from .models import Record, Relationship
from .serializers import RecordSerializer, RelationshipSerializer
from accounts.permissions import check_record_permission
from governance.services import get_linked_records

class RecordViewSet(viewsets.ModelViewSet):
    serializer_class = RecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter out soft-deleted records
        qs = Record.objects.filter(deleted_at__isnull=True)
        # Apply filtering by family, type, and class
        record_family = self.request.query_params.get('record_family')
        record_type = self.request.query_params.get('record_type')
        record_class = self.request.query_params.get('record_class')
        tenant_id = self.request.query_params.get('tenant_id')
        created_by = self.request.query_params.get('created_by')

        if record_family:
            qs = qs.filter(record_family=record_family)
        if record_type:
            qs = qs.filter(record_type=record_type)
        if record_class:
            qs = qs.filter(record_class=record_class)
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        if created_by:
            qs = qs.filter(created_by_id=created_by)

        # Apply permissions check manually here (for lists, typically you might filter by DB directly)
        # However, for MVP, we just grab query and let specific retrieval handle checks where possible
        # A true production filter would embed check_record_permission logic into Q objects.
        return qs

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not check_record_permission(request.user, instance):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to view this record.")
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def related(self, request, pk=None):
        record = self.get_object()
        grouped = get_linked_records(record.id)
        result = {}
        for rel_type, entries in grouped.items():
            result[rel_type] = []
            for entry in entries:
                item = {
                    'direction': entry['direction'],
                    'relationship_id': str(entry['rel'].id),
                    'strength': entry['rel'].strength,
                    'notes': entry['rel'].notes,
                }
                if entry.get('bible_verse'):
                    bv = entry['bible_verse']
                    item['bible_verse'] = {
                        'id': bv.id,
                        'reference': str(bv),
                        'text': bv.text,
                    }
                elif entry.get('record'):
                    r = entry['record']
                    item['record'] = {
                        'id': str(r.id),
                        'title': r.title,
                        'record_type': r.record_type,
                        'record_family': r.record_family,
                        'status': r.status,
                    }
                result[rel_type].append(item)
        return Response(result)

class RelationshipViewSet(viewsets.ModelViewSet):
    serializer_class = RelationshipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Relationship.objects.filter(deleted_at__isnull=True)
        from_record_id = self.request.query_params.get('from_record_id')
        to_record_id = self.request.query_params.get('to_record_id')

        if from_record_id:
            qs = qs.filter(from_record_id=from_record_id)
        if to_record_id:
            qs = qs.filter(to_record_id=to_record_id)

        return qs

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()
