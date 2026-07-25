"""
sceptre.ichebo.org — participant and steward views.
"""
from django.shortcuts import render, redirect

from sceptre.auth import require_sceptre_participant, require_sceptre_steward, is_steward


def _get_tenant_for_user(user):
    """Resolve the user's active community tenant — their highest-level
    UserPermission, matching the established pattern
    (community/views.py:_get_user_permissions). Without .order_by('-level'),
    a user with multiple UserPermission rows would resolve to an
    arbitrary one rather than their highest-level tenant."""
    from tenants.models import UserPermission
    perm = (
        UserPermission.objects.filter(user=user, is_active=True)
        .select_related('tenant')
        .order_by('-level')
        .first()
    )
    return perm.tenant if perm else None


@require_sceptre_participant
def participant_home(request):
    """
    Participant home — channel video first, schedule sidebar, VOD grid,
    series/programmes grid, notification CTA.
    """
    from django.db.models import Q
    from records.models import Record

    tenant = _get_tenant_for_user(request.user)
    user_is_steward = is_steward(request.user)

    # Recent broadcasts — last 6 records with video content for this tenant.
    # Gracefully empty when no broadcasts exist yet.
    recent_broadcasts = []
    if tenant:
        recent_broadcasts = list(
            Record.objects.filter(
                record_family='broadcast',
                deleted_at__isnull=True,
            ).filter(
                Q(tenant_id=tenant.id) | Q(tenant_id__isnull=True)
            ).order_by('-created_at')[:6]
        )

    # Programmes — tenant's active Learn programmes (max 8).
    # Imported inline to avoid a hard dependency on learn app at module level.
    programmes = []
    try:
        from learn.models import Programme
        if tenant:
            programmes = list(
                Programme.objects.filter(
                    tenant=tenant,
                    is_active=True,
                    deleted_at__isnull=True,
                ).order_by('order', 'name')[:8]
            )
    except Exception:
        pass  # learn app may not be available or Programme model may differ

    # Schedule — upcoming ChannelSlots for this tenant.
    schedule = []
    try:
        from broadcast.models import ChannelSlot
        if tenant:
            schedule = list(
                ChannelSlot.objects.filter(
                    tenant=tenant,
                    deleted_at__isnull=True,
                ).order_by('day_of_week', 'start_time')[:6]
            )
    except Exception:
        pass

    return render(request, 'sceptre/home/home.html', {
        'tenant': tenant,
        'tenant_id': str(tenant.id) if tenant else '',
        'is_steward': user_is_steward,
        'recent_broadcasts': recent_broadcasts,
        'programmes': programmes,
        'schedule': schedule,
    })


@require_sceptre_participant
def now_playing_partial(request):
    """
    HTMX partial — resolves the current channel content and returns the
    now-playing strip. Called by hx-trigger='every 60s' from the home
    template. Calls broadcast.services.resolve_now_playing(tenant)
    directly — no HTTP round-trip to this server's own API.
    """
    from broadcast.services import resolve_now_playing

    tenant = _get_tenant_for_user(request.user)
    now_playing = resolve_now_playing(tenant) if tenant else None

    return render(request, 'sceptre/home/_now_playing.html', {
        'now_playing': now_playing,
        'tenant_id': str(tenant.id) if tenant else '',
    })


@require_sceptre_participant
def community_area(request):
    """Community area — announcements, gatherings, community info summary."""
    tenant = _get_tenant_for_user(request.user)
    user_is_steward = is_steward(request.user)

    from django.db.models import Q
    from records.models import Record

    # Tenant-wide announcements (tenant_id IS NULL) are included via Q(),
    # matching the established pattern in community/views.py.
    announcements = [] if not tenant else list(
        Record.objects.filter(
            record_family='community',
            record_type='announcement',
            status='active',
            deleted_at__isnull=True,
        ).filter(
            Q(tenant_id=tenant.id) | Q(tenant_id__isnull=True)
        ).order_by('-created_at')[:5]
    )

    return render(request, 'sceptre/community/community.html', {
        'tenant': tenant,
        'announcements': announcements,
        'is_steward': user_is_steward,
    })


@require_sceptre_participant
def learn_summary(request):
    """Learn — in-surface summary of enrolled programmes, with link to learn.ichebo.org."""
    tenant = _get_tenant_for_user(request.user)
    user_is_steward = is_steward(request.user)

    programmes = []
    try:
        from learn.models import Programme
        if tenant:
            programmes = list(
                Programme.objects.filter(
                    tenant=tenant,
                    is_active=True,
                    deleted_at__isnull=True,
                ).order_by('order', 'name')[:8]
            )
    except Exception:
        pass

    return render(request, 'sceptre/learn/learn.html', {
        'tenant': tenant,
        'is_steward': user_is_steward,
        'programmes': programmes,
    })


@require_sceptre_participant
def bible_redirect(request):
    """Bible — redirect to bible.ichebo.org."""
    return redirect('https://bible.ichebo.org/')


@require_sceptre_participant
def support_redirect(request):
    """Support — redirect to the community support request list on app.ichebo.org."""
    return redirect('https://app.ichebo.org/community/support/')


@require_sceptre_participant
def profile_summary(request):
    """Profile summary — interim until identity.ichebo.org ships."""
    user_is_steward = is_steward(request.user)
    tenant = _get_tenant_for_user(request.user)
    return render(request, 'sceptre/profile/profile.html', {
        'is_steward': user_is_steward,
        'tenant': tenant,
    })


# ── Public views (no auth required) ───────────────────────────────────────

def community_directory(request):
    """
    Public community directory — no login required.
    Adapted from v1 find-a-church.html; serves dynamic Tenant data.
    GET params: ?q=  ?theme=  ?format=  ?status=
    """
    from tenants.models import Tenant

    qs = Tenant.objects.filter(
        status='active',
        deleted_at__isnull=True,
        is_agency=False,
        tier='church_node',
    ).order_by('name')

    q = request.GET.get('q', '').strip()
    theme = request.GET.get('theme', '').strip()
    fmt = request.GET.get('format', '').strip()
    status_filter = request.GET.get('status', '').strip()

    if q:
        from django.db.models import Q as DQ
        qs = qs.filter(
            DQ(name__icontains=q) |
            DQ(community_theme__icontains=q) |
            DQ(area_of_operation__icontains=q)
        )
    if theme:
        qs = qs.filter(community_theme__icontains=theme)

    communities = list(qs[:60])

    # Distinct theme list for filter chips
    themes = list(
        Tenant.objects.filter(
            status='active', deleted_at__isnull=True,
            is_agency=False, tier='church_node',
        ).exclude(community_theme='')
        .values_list('community_theme', flat=True)
        .distinct()
        .order_by('community_theme')[:20]
    )

    return render(request, 'sceptre/community/directory.html', {
        'communities': communities,
        'themes': themes,
        'total_count': len(communities),
        'q': q,
        'theme': theme,
    })


def community_profile(request, slug):
    """
    Public community profile page — no login required.
    Resolves Tenant by slug; 404 if not found or not active.
    """
    from django.shortcuts import get_object_or_404
    from tenants.models import Tenant, UserPermission

    community = get_object_or_404(
        Tenant,
        slug=slug,
        deleted_at__isnull=True,
    )

    # Member count
    member_count = UserPermission.objects.filter(
        tenant=community,
        is_active=True,
        deleted_at__isnull=True,
    ).count()

    # Public steward names
    stewards = list(
        UserPermission.objects.filter(
            tenant=community,
            role__in=UserPermission.STEWARD_ROLES,
            is_active=True,
            deleted_at__isnull=True,
        ).select_related('user').values_list('user__first_name', 'user__last_name')[:5]
    )
    steward_names = [f"{fn} {ln}".strip() for fn, ln in stewards]

    # Recent broadcasts for this community
    recent_broadcasts = []
    try:
        from records.models import Record
        recent_broadcasts = list(
            Record.objects.filter(
                record_family='broadcast',
                tenant=community,
                deleted_at__isnull=True,
            ).order_by('-created_at')[:3]
        )
    except Exception:
        pass

    return render(request, 'sceptre/community/profile.html', {
        'community': community,
        'member_count': member_count,
        'steward_names': steward_names,
        'recent_broadcasts': recent_broadcasts,
    })


# ── Steward views ──────────────────────────────────────────────────────────

@require_sceptre_steward
def steward_members(request):
    """Native Sceptre member roster."""
    from tenants.models import UserPermission
    tenant = _get_tenant_for_user(request.user)
    members = UserPermission.objects.filter(
        tenant=tenant, is_active=True
    ).select_related('user').order_by('-level', 'user__first_name')
    return render(request, 'sceptre/steward/members.html', {'members': members})


@require_sceptre_steward
def steward_gatherings(request):
    """Native Sceptre gatherings list."""
    from records.models import Record
    from django.utils import timezone
    tenant = _get_tenant_for_user(request.user)
    now = timezone.now()
    gatherings = Record.objects.filter(
        record_family='community', record_type='gathering', tenant=tenant
    ).order_by('custom_fields__scheduled_at')
    
    upcoming = gatherings.filter(custom_fields__scheduled_at__gte=now.isoformat())
    past = gatherings.filter(custom_fields__scheduled_at__lt=now.isoformat()).order_by('-custom_fields__scheduled_at')[:10]
    return render(request, 'sceptre/steward/gatherings.html', {
        'upcoming': upcoming, 'past': past
    })


@require_sceptre_steward
def steward_formation(request):
    """Native Sceptre formation pipeline."""
    from tenants.models import UserPermission
    tenant = _get_tenant_for_user(request.user)
    members = UserPermission.objects.filter(tenant=tenant, is_active=True).select_related('user')
    seekers = members.filter(level=0).order_by('user__first_name')
    disciples = members.filter(level__in=[1, 2]).order_by('user__first_name')
    stewards = members.filter(level__gte=3).order_by('-level', 'user__first_name')
    
    return render(request, 'sceptre/steward/formation.html', {
        'seekers': seekers, 'disciples': disciples, 'stewards': stewards
    })


@require_sceptre_steward
def steward_announcements(request):
    """Native Sceptre announcements list."""
    from records.models import Record
    tenant = _get_tenant_for_user(request.user)
    announcements = Record.objects.filter(
        record_family='community', record_type='announcement', tenant=tenant
    ).order_by('-created_at')
    return render(request, 'sceptre/steward/announcements.html', {'announcements': announcements})


@require_sceptre_steward
def steward_support_redirect(request):
    return redirect('https://app.ichebo.org/community/support/')


@require_sceptre_steward
def steward_settings(request):
    return render(request, 'sceptre/steward/settings.html', {
        'is_steward': True,
    })
