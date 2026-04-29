from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tenants.models import UserPermission


@api_view(['GET'])
@permission_classes([AllowAny])
def community_health(request):
    return Response({'status': 'ok', 'app': 'community'})


class MemberListView(APIView):
    """
    GET /api/community/members/
    Returns the member list scoped to the authenticated user's primary tenant.
    Query params:
        q       — search display_name (icontains)
        level   — filter by competence level (int)
        page    — 1-based page number (default 1)
        page_size — results per page (default 30, max 100)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        q = request.query_params.get('q', '').strip()
        level_filter = request.query_params.get('level', '').strip()
        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except ValueError:
            page = 1
        try:
            page_size = min(100, max(1, int(request.query_params.get('page_size', 30))))
        except ValueError:
            page_size = 30

        # Scope to the user's primary active tenant
        primary = (
            user.tenant_permissions
            .filter(is_active=True)
            .select_related('tenant')
            .order_by('granted_at')
            .first()
        )
        scope_path = primary.tenant.path if primary else ''

        qs = (
            UserPermission.objects
            .filter(is_active=True, tenant__path__startswith=scope_path)
            .select_related('user', 'tenant')
            .order_by('user__display_name', 'user__email')
        )

        if q:
            qs = qs.filter(user__display_name__icontains=q)
        if level_filter:
            try:
                qs = qs.filter(level=int(level_filter))
            except ValueError:
                pass

        total = qs.count()
        offset = (page - 1) * page_size
        members = qs[offset: offset + page_size]

        data = []
        for perm in members:
            u = perm.user
            data.append({
                'id': str(u.id),
                'display_name': u.display_name or u.email,
                'email': u.email,
                'avatar_url': u.avatar_url,
                'competence_level': u.competence_level,
                'role': perm.role,
                'level': perm.level,
                'service_order': (perm.metadata or {}).get('service_order'),
                'tenant_name': perm.tenant.name,
                'joined_at': perm.granted_at.isoformat(),
            })

        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': data,
        })
