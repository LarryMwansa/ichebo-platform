from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Record, Relationship
from .serializers import RecordSerializer, RelationshipSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def record_list_create(request):
    """
    List records (filters out soft-deleted) or create a new record.
    Filters: tenant, record_family, record_type, record_class
    """
    if request.method == 'GET':
        # Filter out soft-deleted records
        queryset = Record.objects.filter(deleted_at__isnull=True)

        # Apply optional filters
        tenant = request.query_params.get('tenant')
        if tenant:
            queryset = queryset.filter(tenant_id=tenant)

        record_family = request.query_params.get('record_family')
        if record_family:
            queryset = queryset.filter(record_family=record_family)

        record_type = request.query_params.get('record_type')
        if record_type:
            queryset = queryset.filter(record_type=record_type)

        record_class = request.query_params.get('record_class')
        if record_class:
            queryset = queryset.filter(record_class=record_class)

        # Paginate
        page_size = 20
        page = request.query_params.get('page', 1)
        try:
            page = int(page)
        except (ValueError, TypeError):
            page = 1

        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        records = queryset.order_by('-created_at')[start:end]

        serializer = RecordSerializer(records, many=True)
        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })

    elif request.method == 'POST':
        serializer = RecordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def record_detail(request, pk):
    """
    Retrieve, update, or soft-delete a specific record.
    """
    record = get_object_or_404(Record, pk=pk, deleted_at__isnull=True)

    if request.method == 'GET':
        serializer = RecordSerializer(record)
        return Response(serializer.data)

    elif request.method == 'PATCH':
        serializer = RecordSerializer(record, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        # Soft delete: set deleted_at
        record.deleted_at = timezone.now()
        record.save()
        return Response({'detail': 'Record soft-deleted'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def record_relationships(request, pk):
    """
    List all relationships for a specific record (both incoming and outgoing).
    """
    record = get_object_or_404(Record, pk=pk, deleted_at__isnull=True)

    # Get both outgoing and incoming relationships (excluding soft-deleted)
    outgoing = record.outgoing_relationships.filter(deleted_at__isnull=True)
    incoming = record.incoming_relationships.filter(deleted_at__isnull=True)

    all_relationships = list(outgoing) + list(incoming)
    serializer = RelationshipSerializer(all_relationships, many=True)
    return Response({'relationships': serializer.data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def relationship_create(request):
    """
    Create a new relationship between two records.
    """
    serializer = RelationshipSerializer(data=request.data)
    if serializer.is_valid():
        # Verify both records exist and are not soft-deleted
        from_record_id = request.data.get('from_record')
        to_record_id = request.data.get('to_record')

        from_record = get_object_or_404(Record, pk=from_record_id, deleted_at__isnull=True)
        to_record = get_object_or_404(Record, pk=to_record_id, deleted_at__isnull=True)

        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def relationship_delete(request, pk):
    """
    Soft-delete a relationship.
    """
    relationship = get_object_or_404(Relationship, pk=pk, deleted_at__isnull=True)
    relationship.deleted_at = timezone.now()
    relationship.save()
    return Response({'detail': 'Relationship soft-deleted'}, status=status.HTTP_204_NO_CONTENT)
