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
    Participant home — channel video first, four quick-access tiles below.
    """
    tenant = _get_tenant_for_user(request.user)
    user_is_steward = is_steward(request.user)

    return render(request, 'sceptre/home/home.html', {
        'tenant': tenant,
        'tenant_id': str(tenant.id) if tenant else '',
        'is_steward': user_is_steward,
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
    """Learn summary — interim until learn.ichebo.org ships."""
    user_is_steward = is_steward(request.user)
    return render(request, 'sceptre/learn/learn.html', {
        'is_steward': user_is_steward,
    })


@require_sceptre_participant
def bible_redirect(request):
    """Bible — redirect to bible.ichebo.org once that surface is built;
    interim: redirect to the existing Bible app."""
    return redirect('/bible/')


@require_sceptre_participant
def support_redirect(request):
    """Support — redirect to the community support request list."""
    return redirect('/community/support/')


@require_sceptre_participant
def profile_summary(request):
    """Profile summary — interim until identity.ichebo.org ships."""
    user_is_steward = is_steward(request.user)
    return render(request, 'sceptre/profile/profile.html', {
        'is_steward': user_is_steward,
    })


# ── Steward views ──────────────────────────────────────────────────────────

@require_sceptre_steward
def steward_members(request):
    """Member roster — delegate to community app's member management."""
    return redirect('/community/members/')


@require_sceptre_steward
def steward_gatherings(request):
    return redirect('/community/gatherings/')


@require_sceptre_steward
def steward_formation(request):
    return redirect('/community/pipeline/')


@require_sceptre_steward
def steward_announcements(request):
    # Announcement authorship is composed inline on the steward
    # dashboard via the community/htmx/announcement/create/ HTMX
    # endpoint — there is no separate authorship page to redirect to.
    return redirect('/community/management/')


@require_sceptre_steward
def steward_support_redirect(request):
    return redirect('/community/support/')


@require_sceptre_steward
def steward_settings(request):
    return render(request, 'sceptre/steward/settings.html', {
        'is_steward': True,
    })
