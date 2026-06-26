from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tenants.models import Tenant

from .services import resolve_now_playing


class NowPlayingView(APIView):
    """GET /api/broadcast/now/?tenant_id={uuid}

    Returns the current channel content for the given tenant, resolved
    via the four-level fallback hierarchy (ADR-024). Called by the
    Flutter mobile app (polled every 60s) and, once built, the
    sceptre.ichebo.org HTMX now-playing strip (same interval).

    SessionAuthentication + TokenAuthentication, matching the
    established pattern for endpoints reachable from both a browser
    session and the mobile app (see media/views.py).
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.query_params.get('tenant_id')
        if not tenant_id:
            return Response(
                {'error': 'tenant_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except (Tenant.DoesNotExist, ValidationError):
            return Response(
                {'error': 'Tenant not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(resolve_now_playing(tenant), status=status.HTTP_200_OK)
