from datetime import date, timedelta
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as http_status
from .service import get_calendar_events

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
