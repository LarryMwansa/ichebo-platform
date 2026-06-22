# community/views.py — All Django template views + HTMX partials
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from records.models import Record, Relationship
from activity.models import Activity
from accounts.models import User
from tenants.models import Tenant, UserPermission
from .models import MembershipRequest
from .services import resolve_steward_for_tenant
from .constants import (
    KGS_SERVICE_ORDERS, KGS_SERVICE_ORDER_CHOICES,
    KGS_PARTICIPATION_STAGES, KGS_COMPETENCE_LABELS,
)

SUPPORT_REQUEST_RESPONSE_WINDOW_HOURS = 72


# ── Helpers ───────────────────────────────────────────────────────────────────

def _user_level(user):
    return getattr(user, 'competence_level', 0)


def _require_level(request, min_level):
    return _user_level(request.user) >= min_level


def _get_user_permissions(user):
    """Retrieve active UserPermission rows for a user via Django ORM."""
    # UserPermission imported at module level
    return list(
        UserPermission.objects.filter(user=user, is_active=True)
        .select_related('tenant')
        .order_by('-level')
    )


def _get_scope_permissions(scope_tenant, filters=None):
    """All active UserPermissions within a steward's scope tenant."""
    # UserPermission imported at module level

    qs = UserPermission.objects.filter(
        is_active=True,
        tenant__path__startswith=scope_tenant.path if scope_tenant else '',
    ).select_related('user', 'tenant')

    if filters:
        if filters.get('level'):
            qs = qs.filter(level=filters['level'])
        if filters.get('service_order'):
            qs = qs.filter(metadata__service_order=filters['service_order'])
        if filters.get('search'):
            qs = qs.filter(user__display_name__icontains=filters['search'])

    return qs.order_by('user__display_name')


# ── My Community surface (C) ──────────────────────────────────────────────────

@login_required
def _render_induction_hub(request, user, induction_perm):
    """Render the Induction Hub for a Level 0 seeker who is placed in the induction tenant."""
    from django.db.models import Q

    induction_tenant = induction_perm.tenant

    # Active induction programmes
    programmes = list(
        Record.objects.filter(
            record_family='learning',
            record_type='induction',
            status='active',
            deleted_at__isnull=True,
        ).order_by('title')
    )

    # User's enrolment activities for those programmes
    programme_ids = [str(p.id) for p in programmes]
    enrolments = {
        a.metadata.get('programme_record_id'): a
        for a in Activity.objects.filter(
            assigned_to=user,
            activity_type='programme',
            metadata__programme_record_id__in=programme_ids,
        )
    }

    # Build programme cards with enrolment state
    programme_cards = []
    for p in programmes:
        enrolment = enrolments.get(str(p.id))
        programme_cards.append({
            'programme': p,
            'enrolment': enrolment,
            'progress': enrolment.progress if enrolment else 0,
            'status': enrolment.status if enrolment else 'not_enrolled',
        })

    # Induction announcements scoped to the induction tenant
    announcements = list(
        Record.objects.filter(
            record_family='community',
            record_type='announcement',
            status='active',
            deleted_at__isnull=True,
        ).filter(
            Q(tenant_id=induction_tenant.id) | Q(tenant_id__isnull=True)
        ).order_by('-created_at')[:3]
    )

    all_complete = bool(programme_cards) and all(
        c['status'] == 'completed' for c in programme_cards
    )

    return render(request, 'community/induction_hub.html', {
        'induction_perm':   induction_perm,
        'induction_tenant': induction_tenant,
        'programme_cards':  programme_cards,
        'announcements':    announcements,
        'all_complete':     all_complete,
        'user':             user,
        'active_app':       'community',
        'ws_page_title':    'Induction Hub',
        'active_community_tab': 'home',
    })


# ── My Community surface (C) ──────────────────────────────────────────────────

@login_required
def my_community(request):
    """My Community — member surface. Level 0 sees Induction Hub; Level 1+ sees full hub."""
    user = request.user
    level = _user_level(user)

    if level < 1:
        # Level 0 — check for induction tenant membership before showing seeker gate
        induction_perm = UserPermission.objects.filter(
            user=user,
            tenant__tier='induction',
            is_active=True,
        ).select_related('tenant').first()

        if induction_perm:
            return _render_induction_hub(request, user, induction_perm)

        return render(request, 'community/seeker_gate.html', {
            'active_app': 'community',
            'ws_page_title': 'Community',
        })

    perms = _get_user_permissions(user)
    primary_perm = perms[0] if perms else None
    shepherd = None
    service_order = None
    announcements = []
    upcoming_gatherings = []
    gifts_count = 0

    if primary_perm:
        tenant = primary_perm.tenant
        meta = primary_perm.metadata or {}
        service_order = meta.get('service_order')

        shepherd_id = meta.get('shepherd_id')
        if shepherd_id:
            try:
                shepherd = User.objects.get(id=shepherd_id)
            except User.DoesNotExist:
                pass

        from django.db.models import Q
        announcements = list(
            Record.objects.filter(
                record_family='community',
                record_type='announcement',
                status='active',
                deleted_at__isnull=True,
            ).filter(
                Q(tenant_id=tenant.id) | Q(tenant_id__isnull=True)
            ).order_by('-created_at')[:5]
        )

        now = timezone.now()
        upcoming_gatherings = list(
            Activity.objects.filter(
                activity_type='event',
                status__in=['pending', 'in_progress'],
                metadata__source_app='community',
            ).filter(
                Q(tenant_id=tenant.id) | Q(tenant_id__isnull=True)
            ).order_by('scheduled_at')[:10]
        )

        gifts_count = Activity.objects.filter(
            activity_type='skill',
            created_by=user,
            status='active',
        ).count()

    stage_info = KGS_PARTICIPATION_STAGES.get(level, ('Member', 'Formation'))
    level_label = KGS_COMPETENCE_LABELS.get(level, 'Member')

    return render(request, 'community/my_community.html', {
        'primary_perm':        primary_perm,
        'shepherd':            shepherd,
        'service_order':       service_order,
        'announcements':       announcements,
        'upcoming_gatherings': upcoming_gatherings,
        'gifts_count':         gifts_count,
        'level':               level,
        'level_label':         level_label,
        'stage_name':          stage_info[0],
        'participation_stage': stage_info[1],
        'participation_steps': range(1, 6),
        'active_app':          'community',
        'active_community_tab': 'home',
    })


# ── Management home (D.1) ─────────────────────────────────────────────────────

@login_required
def management_home(request):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html', {'min_level': 3, 'active_app': 'community', 'ws_page_title': 'Community'}, status=403)

    perms = _get_user_permissions(request.user)
    primary_perm = perms[0] if perms else None
    scope_tenant = primary_perm.tenant if primary_perm else None

    member_count = 0
    announcements = []
    gatherings = []

    if scope_tenant:
        # UserPermission imported at module level
        member_count = UserPermission.objects.filter(
            is_active=True,
            tenant__path__startswith=scope_tenant.path,
        ).count()

        from django.db.models import Q
        announcements = list(
            Record.objects.filter(
                record_family='community',
                record_type='announcement',
                status='active',
                deleted_at__isnull=True,
            ).filter(
                Q(tenant_id=scope_tenant.id) | Q(tenant_id__isnull=True)
            ).order_by('-created_at')[:3]
        )

        now = timezone.now()
        gatherings = list(
            Activity.objects.filter(
                activity_type='event',
                status__in=['pending', 'in_progress'],
                metadata__source_app='community',
            ).filter(
                Q(tenant_id=scope_tenant.id) | Q(tenant_id__isnull=True)
            ).order_by('scheduled_at')[:5]
        )

    return render(request, 'community/management.html', {
        'primary_perm':        primary_perm,
        'scope_tenant':        scope_tenant,
        'member_count':        member_count,
        'announcements':       announcements,
        'gatherings':          gatherings,
        'active_app':          'community',
        'ws_page_title':       'Community',
        'active_community_tab': 'management',
    })


# ── Member directory (D.2) ────────────────────────────────────────────────────

@login_required
def member_directory(request):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html', {'min_level': 3, 'active_app': 'community', 'ws_page_title': 'Community'}, status=403)

    perms = _get_user_permissions(request.user)
    primary_perm = perms[0] if perms else None
    scope_tenant = primary_perm.tenant if primary_perm else None

    filter_order = request.GET.get('order', '')
    filter_level = request.GET.get('level', '')
    search_q = request.GET.get('q', '')

    members = _get_scope_permissions(scope_tenant, {
        'level': filter_level,
        'service_order': filter_order,
        'search': search_q,
    })[:50]

    return render(request, 'community/member_directory.html', {
        'members':             members,
        'scope_tenant':        scope_tenant,
        'filter_order':        filter_order,
        'filter_level':        filter_level,
        'search_q':            search_q,
        'order_choices':       KGS_SERVICE_ORDER_CHOICES,
        'level_choices': [
            (0, 'Seeker'), (1, 'Member'), (2, 'Disciple'),
            (3, 'Steward'), (4, 'Senior Steward'), (5, 'Architect')
        ],
        'active_app':          'community',
        'ws_page_title':       'Members',
        'active_community_tab': 'members',
    })


# ── Formation pipeline (D.3) ──────────────────────────────────────────────────

@login_required
def formation_pipeline(request):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html', {'min_level': 3, 'active_app': 'community', 'ws_page_title': 'Community'}, status=403)

    perms = _get_user_permissions(request.user)
    primary_perm = perms[0] if perms else None
    scope_tenant = primary_perm.tenant if primary_perm else None

    all_members = list(_get_scope_permissions(scope_tenant))

    pipeline = {lvl: [] for lvl in range(6)}
    for m in all_members:
        lvl = getattr(m, 'level', 0) or 0
        pipeline[lvl].append(m)

    pipeline_display = [
        {
            'level':   lvl,
            'label':   KGS_COMPETENCE_LABELS.get(lvl, f'Level {lvl}'),
            'stage':   KGS_PARTICIPATION_STAGES.get(lvl, ('', ''))[1],
            'members': pipeline[lvl],
            'count':   len(pipeline[lvl]),
        }
        for lvl in range(6)
    ]

    return render(request, 'community/formation_pipeline.html', {
        'pipeline_display':    pipeline_display,
        'total':               len(all_members),
        'active_app':          'community',
        'ws_page_title':       'Pipeline',
        'active_community_tab': 'pipeline',
    })


# ── Member profile (F.1) ──────────────────────────────────────────────────────

@login_required
def member_profile(request, member_id):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html', {'min_level': 3, 'active_app': 'community', 'ws_page_title': 'Community'}, status=403)

    # UserPermission imported at module level

    perms = _get_user_permissions(request.user)
    primary_perm = perms[0] if perms else None
    scope_tenant = primary_perm.tenant if primary_perm else None

    try:
        member_user = User.objects.get(id=member_id)
    except User.DoesNotExist:
        return render(request, 'community/locked.html',
                      {'min_level': 3, 'message': 'Member not found.'}, status=404)

    member_perm = UserPermission.objects.filter(
        user=member_user, is_active=True,
        *(
            [{'tenant__path__startswith': scope_tenant.path}]
            if scope_tenant else [{}]
        )[0].items()
    ).first()

    if not member_perm:
        return render(request, 'community/locked.html',
                      {'min_level': 3, 'message': 'Member not in your scope.'}, status=404)

    gifts = list(Activity.objects.filter(
        activity_type='skill', created_by=member_user, status='active'
    ))
    certifications = list(Record.objects.filter(
        record_family='learning', record_type='certification',
        created_by=member_user, status='active', deleted_at__isnull=True
    ).order_by('-created_at'))

    shepherds = list(UserPermission.objects.filter(
        is_active=True, level__gte=3,
        **(
            {'tenant__path__startswith': scope_tenant.path}
            if scope_tenant else {}
        )
    ).select_related('user'))

    level = _user_level(member_user)
    level_label = KGS_COMPETENCE_LABELS.get(level, f'Level {level}')
    stage_info = KGS_PARTICIPATION_STAGES.get(level, ('Member', 'Formation'))

    is_htmx = bool(request.headers.get('HX-Request'))
    return render(request, 'community/member_profile.html', {
        'member_perm':         member_perm,
        'member_user':         member_user,
        'gifts':               gifts,
        'certifications':      certifications,
        'shepherds':           shepherds,
        'order_choices':       KGS_SERVICE_ORDER_CHOICES,
        'level_label':         level_label,
        'stage_info':          stage_info,
        'user_level':          _user_level(request.user),
        'active_app':          'community',
        'ws_page_title':       member_user.display_name or member_user.email,
        'active_community_tab': 'members',
        'is_htmx':             is_htmx,
    })


# ── Gatherings list (C.1) ────────────────────────────────────────────────────

@login_required
def gatherings_list(request):
    """Upcoming gatherings for the user's tenant. Level 1+."""
    user = request.user
    if _user_level(user) < 1:
        return render(request, 'community/seeker_gate.html', {
            'active_app': 'community', 'ws_page_title': 'Community',
        })

    perms = _get_user_permissions(user)
    primary_perm = perms[0] if perms else None
    tenant = primary_perm.tenant if primary_perm else None

    now = timezone.now()
    from django.db.models import Q
    qs = Record.objects.filter(
        record_family='community',
        record_type='gathering',
        status__in=['active', 'pending'],
        deleted_at__isnull=True,
    ).order_by('custom_fields__scheduled_at')

    if tenant:
        qs = qs.filter(Q(tenant_id=tenant.id) | Q(tenant_id__isnull=True))

    if request.headers.get('HX-Request'):
        return render(request, 'community/partials/gathering_list.html', {
            'gatherings': qs[:20],
            'now': now,
        })

    return render(request, 'community/gatherings.html', {
        'gatherings': qs[:20],
        'now': now,
        'level': _user_level(user),
        'is_steward': _user_level(user) >= 3,
        'active_app': 'community',
        'active_community_tab': 'gatherings',
    })


# ── Gathering / Announcement detail (C.2) ────────────────────────────────────

@login_required
def community_detail(request, record_id):
    """Detail view for a gathering or announcement. Level 1+."""
    if _user_level(request.user) < 1:
        return render(request, 'community/seeker_gate.html', {
            'active_app': 'community', 'ws_page_title': 'Community',
        })

    record = get_object_or_404(
        Record,
        id=record_id,
        record_family='community',
        record_type__in=['gathering', 'announcement'],
        deleted_at__isnull=True,
    )

    linked_activity = None
    if record.record_type == 'gathering':
        from records.models import Relationship
        rel = Relationship.objects.filter(
            from_record=record,
            relationship_type='aligns_with',
        ).first()
        if rel:
            act_id = (rel.metadata or {}).get('linked_activity_id')
            if act_id:
                try:
                    linked_activity = Activity.objects.get(id=act_id)
                except Activity.DoesNotExist:
                    pass

    return render(request, 'community/community_detail.html', {
        'record': record,
        'linked_activity': linked_activity,
        'level': _user_level(request.user),
        'is_steward': _user_level(request.user) >= 3,
        'active_app': 'community',
        'active_community_tab': 'home',
    })


# ── HTMX: gatherings list partial (C.1) ──────────────────────────────────────

@login_required
def htmx_gatherings_list(request):
    """HTMX partial: upcoming gatherings list for the user's tenant."""
    user = request.user
    perms = _get_user_permissions(user)
    primary_perm = perms[0] if perms else None
    tenant = primary_perm.tenant if primary_perm else None

    from django.db.models import Q
    qs = Record.objects.filter(
        record_family='community',
        record_type='gathering',
        status__in=['active', 'pending'],
        deleted_at__isnull=True,
    ).order_by('custom_fields__scheduled_at')

    if tenant:
        qs = qs.filter(Q(tenant_id=tenant.id) | Q(tenant_id__isnull=True))

    return render(request, 'community/partials/gathering_list.html', {
        'gatherings': qs[:20],
        'now': timezone.now(),
    })


# ── HTMX: announcement list (E.1) ────────────────────────────────────────────

@login_required
def htmx_announcement_list(request):
    if not _require_level(request, 3):
        return HttpResponse('')

    announcements = list(
        Record.objects.filter(
            record_family='community',
            record_type='announcement',
            deleted_at__isnull=True,
        ).order_by('-created_at')[:20]
    )
    return render(request, 'community/partials/announcement_list.html',
                  {'announcements': announcements})


# ── HTMX: create announcement (E.1) ──────────────────────────────────────────

@login_required
def htmx_create_announcement(request):
    if not _require_level(request, 3):
        return HttpResponse('')

    if request.method == 'POST':
        perms = _get_user_permissions(request.user)
        primary_perm = perms[0] if perms else None
        tenant = primary_perm.tenant if primary_perm else None

        Record.objects.create(
            created_by=request.user,
            record_class='organizational',
            record_family='community',
            record_type='announcement',
            origin='user',
            title=request.POST.get('title', '').strip(),
            content=request.POST.get('content', '').strip(),
            status='active',
            tenant=tenant,
            metadata={'source_app': 'community'},
            permissions_data={'visibility': 'tenant', 'required_level': 1,
                              'roles_allowed': [], 'can_edit': []},
        )
        return htmx_announcement_list(request)

    return render(request, 'community/partials/announcement_form.html')


# ── HTMX: archive announcement (E.1) ─────────────────────────────────────────

@login_required
def htmx_archive_announcement(request, record_id):
    if not _require_level(request, 3):
        return HttpResponse('')

    Record.objects.filter(id=record_id, record_family='community',
                          record_type='announcement').update(status='archived')
    return htmx_announcement_list(request)


# ── HTMX: create gathering dual-write (E.2) ───────────────────────────────────

@login_required
def htmx_create_gathering(request):
    if not _require_level(request, 3):
        return HttpResponse('')

    if request.method == 'POST':
        from django.db import transaction

        perms = _get_user_permissions(request.user)
        primary_perm = perms[0] if perms else None
        tenant = primary_perm.tenant if primary_perm else None

        title        = request.POST.get('title', '').strip()
        description  = request.POST.get('description', '').strip() or None
        fmt          = request.POST.get('format', 'in_person')
        location     = request.POST.get('location', '').strip() or None
        stream_url   = request.POST.get('stream_url', '').strip() or None
        capacity     = request.POST.get('capacity', '').strip() or None
        scheduled_at = request.POST.get('scheduled_at', '').strip() or None

        try:
            with transaction.atomic():
                gathering_record = Record.objects.create(
                    created_by=request.user,
                    record_class='organizational',
                    record_family='community',
                    record_type='gathering',
                    origin='user',
                    title=title,
                    content=description,
                    status='active',
                    tenant=tenant,
                    metadata={'source_app': 'community'},
                    permissions_data={'visibility': 'tenant', 'required_level': 1,
                                      'roles_allowed': [], 'can_edit': []},
                    custom_fields={
                        'format':       fmt,
                        'location':     location,
                        'stream_url':   stream_url,
                        'capacity':     int(capacity) if capacity else None,
                        'scheduled_at': scheduled_at,
                    },
                )

                event_activity = Activity.objects.create(
                    created_by=request.user,
                    activity_type='event',
                    title=title,
                    description=description,
                    scheduled_at=scheduled_at or None,
                    status='pending',
                    kgs_pathway='community_life',
                    tenant=tenant,
                    metadata={'source_app': 'community'},
                )

                Relationship.objects.create(
                    created_by=request.user,
                    from_record=gathering_record,
                    to_record_id=None,          # Activity is not a Record; store FK in metadata
                    relationship_type='aligns_with',
                    direction='directed',
                    metadata={'linked_activity_id': str(event_activity.id)},
                )

        except Exception as exc:
            return HttpResponse(
                f'<p style="color:var(--error)">Failed to schedule gathering: {exc}</p>'
            )

        return HttpResponse(
            f'<div class="announcement-card" style="border-color:var(--success)">'
            f'<div class="announcement-title">✓ Gathering scheduled: {title}</div>'
            f'</div>'
        )

    return render(request, 'community/partials/gathering_form.html')


# ── HTMX: cancel gathering (E.2) ─────────────────────────────────────────────

@login_required
def htmx_cancel_gathering(request, record_id):
    if not _require_level(request, 3):
        return HttpResponse('')

    from django.db import transaction

    record = Record.objects.filter(
        id=record_id, record_family='community', record_type='gathering'
    ).first()

    if record:
        with transaction.atomic():
            record.status = 'cancelled'
            record.save(update_fields=['status', 'updated_at'])

            # Cancel linked activity via Relationship metadata
            rel = Relationship.objects.filter(
                from_record=record, relationship_type='aligns_with'
            ).first()
            if rel:
                act_id = (rel.metadata or {}).get('linked_activity_id')
                if act_id:
                    Activity.objects.filter(id=act_id).update(status='cancelled')

    return HttpResponse(
        '<div class="gathering-card" style="opacity:0.5">'
        '<div class="gathering-title">Gathering cancelled</div></div>'
    )


# ── HTMX: set shepherd (F.2) ──────────────────────────────────────────────────

@login_required
def htmx_set_shepherd(request, permission_id):
    if not _require_level(request, 3) or request.method != 'POST':
        return HttpResponse('')

    # UserPermission imported at module level

    perm = UserPermission.objects.filter(id=permission_id).first()
    if perm:
        shepherd_id = request.POST.get('shepherd_id', '').strip() or None
        meta = dict(perm.metadata or {})
        if shepherd_id:
            meta['shepherd_id'] = shepherd_id
        else:
            meta.pop('shepherd_id', None)
        perm.metadata = meta
        perm.save(update_fields=['metadata'])

        label = 'No shepherd assigned'
        if shepherd_id:
            try:
                sh = User.objects.get(id=shepherd_id)
                label = sh.display_name or sh.email
            except User.DoesNotExist:
                label = 'Shepherd assigned'

        return HttpResponse(
            f'<div class="info-card-value" id="shepherd-value">✓ {label}</div>'
        )

    return HttpResponse('<div class="info-card-value" id="shepherd-value">Error</div>')


# ── HTMX: set service order (F.2) ─────────────────────────────────────────────

@login_required
def htmx_set_order(request, permission_id):
    if not _require_level(request, 3) or request.method != 'POST':
        return HttpResponse('')

    # UserPermission imported at module level

    perm = UserPermission.objects.filter(id=permission_id).first()
    if perm:
        service_order = request.POST.get('service_order', '').strip() or None
        meta = dict(perm.metadata or {})
        if service_order:
            meta['service_order'] = service_order
        else:
            meta.pop('service_order', None)
        perm.metadata = meta
        perm.save(update_fields=['metadata'])

        label = service_order if service_order else 'No service order assigned'
        return HttpResponse(
            f'<div class="info-card-value" id="order-value">✓ {label}</div>'
        )

    return HttpResponse('<div class="info-card-value" id="order-value">Error</div>')


# ── HTMX: deactivate member (F.2) ─────────────────────────────────────────────

@login_required
def htmx_deactivate_member(request, permission_id):
    if not _require_level(request, 3) or request.method != 'POST':
        return HttpResponse('')

    # UserPermission imported at module level

    UserPermission.objects.filter(id=permission_id).update(is_active=False)

    return HttpResponse(
        '<div class="announcement-card" style="border-color:var(--error)">'
        '<div class="announcement-title" style="color:var(--error)">Membership deactivated.</div>'
        '</div>'
    )


# ── HTMX: manual email verification (Level 4+) ───────────────────────────────

@login_required
def htmx_verify_member(request, member_id):
    """Manually verify a user stuck in pending_verification. Level 4+ only."""
    if not _require_level(request, 4) or request.method != 'POST':
        return HttpResponse('')

    try:
        member = User.objects.get(id=member_id)
    except User.DoesNotExist:
        return HttpResponse('')

    if member.status != 'pending_verification':
        return HttpResponse(
            '<div style="font-size:12px;color:var(--muted);padding:8px 0;">Already verified.</div>'
        )

    member.status = 'seeker'
    member.save(update_fields=['status'])
    member.verification_tokens.all().delete()

    return HttpResponse(
        '<div style="font-size:12px;font-weight:700;color:var(--primary);padding:8px 0;">'
        '<span class="material-symbols-outlined" style="font-size:14px;vertical-align:middle;margin-right:4px;">verified</span>'
        'Email verified manually. Account is now active.'
        '</div>'
    )


# ── HTMX: member search (F.2) ─────────────────────────────────────────────────

@login_required
def htmx_member_search(request):
    if not _require_level(request, 2):
        return HttpResponse('')

    perms = _get_user_permissions(request.user)
    primary_perm = perms[0] if perms else None
    scope_tenant = primary_perm.tenant if primary_perm else None

    members = _get_scope_permissions(scope_tenant, {
        'search': request.GET.get('q', ''),
        'level': request.GET.get('level', ''),
        'service_order': request.GET.get('order', ''),
    })[:50]

    return render(request, 'community/partials/member_list.html', {'members': members})


# ── Membership request flow ───────────────────────────────────────────────────

def _get_induction_programmes():
    """
    Return all active globally-required induction programmes.
    These are Learn Records with record_type='induction', managed by Level 4-5.
    """
    return list(
        Record.objects.filter(
            record_family='learning',
            record_type='induction',
            status='active',
            deleted_at__isnull=True,
        ).order_by('title')
    )


def _induction_status(user):
    """
    Return (required, pending) where:
      required — list of all active induction Records
      pending  — subset the user has not yet completed
    Completion is signalled by a completed Activity referencing the programme.
    """
    required = _get_induction_programmes()
    if not required:
        return required, []

    completed_ids = set(
        Activity.objects.filter(
            assigned_to=user,
            status='completed',
            metadata__programme_record_id__in=[str(r.id) for r in required],
        ).values_list('metadata__programme_record_id', flat=True)
    )
    pending = [r for r in required if str(r.id) not in completed_ids]
    return required, pending


@login_required
def htmx_orientation_check(request):
    """
    GET ?tenant_id=<uuid>
    Returns the orientation status partial after a tenant is selected:
    - No global induction programmes exist → request form shown immediately
    - All inductions completed → request form unlocked
    - Outstanding inductions → list of required programmes with links
    """
    tenant_id = request.GET.get('tenant_id', '').strip()
    user = request.user

    if not tenant_id:
        return HttpResponse('')

    try:
        tenant = Tenant.objects.get(id=tenant_id, status='active')
    except Tenant.DoesNotExist:
        return HttpResponse('<p class="form-error">Community not found.</p>')

    required, pending = _induction_status(user)
    mobile = request.GET.get('mobile') == '1'

    already_pending = MembershipRequest.objects.filter(
        user=user, tenant=tenant, status='pending'
    ).exists()

    return render(request, 'community/partials/orientation_check.html', {
        'tenant':          tenant,
        'required':        required,
        'pending':         pending,
        'all_done':        len(pending) == 0,
        'already_pending': already_pending,
        'mobile':          mobile,
    })


@login_required
def htmx_request_membership(request):
    """
    GET  → tenant picker form (selecting a tenant triggers orientation check via HTMX)
    POST → create MembershipRequest; global induction gate + idempotency guard
    """
    user = request.user

    if request.method == 'POST':
        tenant_id = request.POST.get('tenant_id', '').strip()
        note = request.POST.get('note', '').strip() or None

        if not tenant_id:
            return HttpResponse(
                '<p class="form-error">Please select a community.</p>'
            )

        try:
            tenant = Tenant.objects.get(id=tenant_id, status='active')
        except Tenant.DoesNotExist:
            return HttpResponse(
                '<p class="form-error">Community not found.</p>'
            )

        # Server-side global induction gate — cannot be bypassed from the browser
        _, pending = _induction_status(user)
        if pending:
            return HttpResponse(
                '<p class="form-error">Please complete all required induction programmes '
                'before submitting a membership request.</p>',
                status=403,
            )

        # One pending request per user per tenant — idempotency guard
        existing = MembershipRequest.objects.filter(
            user=user, tenant=tenant, status='pending'
        ).first()
        if existing:
            return render(
                request,
                'community/partials/membership_request_sent.html',
                {'tenant': tenant, 'already_pending': True},
            )

        MembershipRequest.objects.create(
            user=user,
            tenant=tenant,
            created_by=user,
            note=note,
        )
        return render(
            request,
            'community/partials/membership_request_sent.html',
            {'tenant': tenant, 'already_pending': False},
        )

    # GET — tenant picker; orientation check loads via HTMX on tenant change
    mobile = request.GET.get('mobile') == '1'
    tenants = Tenant.objects.filter(status='active').order_by('name')[:50]
    return render(request, 'community/partials/membership_request_form.html', {
        'tenants': tenants,
        'mobile':  mobile,
    })


@login_required
def htmx_pending_requests(request):
    """
    GET → list of pending MembershipRequests within the steward's scope.
    Level 3+ only.
    """
    if not _require_level(request, 3):
        return HttpResponse('')

    perms = _get_user_permissions(request.user)
    primary_perm = perms[0] if perms else None
    scope_tenant = primary_perm.tenant if primary_perm else None

    qs = MembershipRequest.objects.filter(
        status='pending'
    ).select_related('user', 'tenant').order_by('created_at')

    if scope_tenant:
        qs = qs.filter(tenant__path__startswith=scope_tenant.path)

    return render(request, 'community/partials/membership_requests.html', {
        'requests': qs[:30],
    })


@login_required
def htmx_review_request(request, request_id):
    """
    POST → approve or deny a pending MembershipRequest.
    Level 3+ only.

    action=approve →
        - Creates UserPermission (role='beginner', level=1)
        - Advances user.competence_level to 1 (Beginner)
        - Creates an Induction/Tenant Membership CertificationConfirmation
          (the steward's approval IS the formal Level 0→1 certification event)
    action=deny → marks denied
    Returns the updated request card HTML.
    """
    if not _require_level(request, 3) or request.method != 'POST':
        return HttpResponse('', status=403)

    membership_req = get_object_or_404(MembershipRequest, id=request_id, status='pending')
    action = request.POST.get('action', '')

    if action not in ('approve', 'deny'):
        return HttpResponse('<p class="form-error">Invalid action.</p>', status=400)

    with transaction.atomic():
        membership_req.reviewed_by = request.user
        membership_req.reviewed_at = timezone.now()

        if action == 'approve':
            membership_req.status = 'approved'
            membership_req.save()

            # Grant tenant membership — get_or_create prevents duplicate re-approvals.
            # competence_level is NOT written here — level advancement only happens
            # via POST /api/learn/certifications/{id}/confirm/ (locked ADR).
            UserPermission.objects.get_or_create(
                tenant=membership_req.tenant,
                user=membership_req.user,
                role='disciple',
                defaults={
                    'created_by': request.user,
                    'granted_by': request.user,
                    'tenant_path': membership_req.tenant.path,
                    'level': membership_req.user.competence_level,
                    'is_active': True,
                },
            )

        else:
            membership_req.status = 'denied'
            membership_req.save()

    return render(request, 'community/partials/membership_request_card.html', {
        'req': membership_req,
        'reviewed': True,
    })


# ── Support requests — member-to-steward, SLA-tracked ────────────────────────
# See .docs/plans/community-support-requests-plan.md

@login_required
def htmx_create_support_request(request):
    """
    GET  → request form
    POST → create a support_request Record, routed to a steward.
    """
    user = request.user

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()

        if not title or not content:
            return HttpResponse(
                '<p class="form-error">Please enter a subject and a description.</p>'
            )

        perms = _get_user_permissions(user)
        primary_perm = perms[0] if perms else None
        tenant = primary_perm.tenant if primary_perm else None

        steward = resolve_steward_for_tenant(tenant)
        response_due_at = timezone.now() + timedelta(hours=SUPPORT_REQUEST_RESPONSE_WINDOW_HOURS)

        record = Record.objects.create(
            tenant=tenant,
            created_by=user,
            record_class='organizational',
            record_family='community',
            record_type='support_request',
            title=title,
            content=content,
            status='submitted',
            custom_fields={
                'response_due_at': response_due_at.isoformat(),
                'acknowledged_at': None,
                'resolved_at': None,
                'assigned_steward_id': str(steward.id) if steward else None,
            },
            permissions_data={'visibility': 'member_and_assigned_steward'},
        )

        return render(request, 'community/partials/support_request_sent.html', {
            'record': record,
            'needs_routing': steward is None,
        })

    return render(request, 'community/partials/support_request_form.html')


@login_required
def htmx_my_support_requests(request):
    """GET → the current member's own submitted support requests, read-only."""
    qs = Record.objects.filter(
        record_family='community',
        record_type='support_request',
        created_by=request.user,
        deleted_at__isnull=True,
    ).order_by('-created_at')[:30]

    return render(request, 'community/partials/my_support_requests.html', {
        'requests': qs,
    })


@login_required
def support_requests_queue(request):
    """
    /community/support/ — steward queue view. Level 3+ / steward role only.
    Lists support requests for tenants within the viewer's scope, soonest
    response-due-date first, with overdue items flagged.
    """
    if not _require_level(request, 3):
        return render(request, 'community/locked.html', {
            'min_level': 3, 'active_app': 'community', 'ws_page_title': 'Community',
        }, status=403)

    perms = _get_user_permissions(request.user)
    primary_perm = perms[0] if perms else None
    scope_tenant = primary_perm.tenant if primary_perm else None

    qs = Record.objects.filter(
        record_family='community',
        record_type='support_request',
        deleted_at__isnull=True,
    ).select_related('created_by', 'tenant')

    if scope_tenant:
        qs = qs.filter(tenant__path__startswith=scope_tenant.path)

    status_filter = request.GET.get('status', '')
    if status_filter == 'open':
        qs = qs.filter(status='submitted')
    elif status_filter == 'acknowledged':
        qs = qs.filter(status='active')
    elif status_filter == 'resolved':
        qs = qs.filter(status='completed')
    elif status_filter == 'needs_routing':
        qs = qs.filter(custom_fields__assigned_steward_id__isnull=True)

    requests_list = list(qs.exclude(status='completed').order_by('created_at')) + \
        list(qs.filter(status='completed').order_by('-created_at')[:20])

    now = timezone.now()
    rows = []
    for r in requests_list:
        due_at_raw = (r.custom_fields or {}).get('response_due_at')
        due_at = None
        overdue = False
        if due_at_raw:
            from django.utils.dateparse import parse_datetime
            due_at = parse_datetime(due_at_raw)
            if due_at and r.status != 'completed' and now > due_at:
                overdue = True
        rows.append({
            'record': r,
            'due_at': due_at,
            'overdue': overdue,
            'needs_routing': not (r.custom_fields or {}).get('assigned_steward_id'),
        })

    return render(request, 'community/support_requests_queue.html', {
        'rows': rows,
        'status_filter': status_filter,
        'active_app': 'community',
        'ws_page_title': 'Support Requests',
        'active_community_tab': 'support',
    })


@login_required
def htmx_acknowledge_support_request(request, record_id):
    """POST → steward marks a request acknowledged ('active') or resolved ('completed')."""
    if not _require_level(request, 3) or request.method != 'POST':
        return HttpResponse('', status=403)

    record = get_object_or_404(
        Record, id=record_id, record_family='community', record_type='support_request',
    )
    action = request.POST.get('action', '')

    if action == 'acknowledge' and record.status == 'submitted':
        record.status = 'active'
        record.custom_fields['acknowledged_at'] = timezone.now().isoformat()
        record.save(update_fields=['status', 'custom_fields'])
    elif action == 'resolve':
        record.status = 'completed'
        record.custom_fields['resolved_at'] = timezone.now().isoformat()
        record.save(update_fields=['status', 'custom_fields'])
    else:
        return HttpResponse('<p class="form-error">Invalid action.</p>', status=400)

    return render(request, 'community/partials/support_request_row.html', {
        'record': record,
    })


# ── HTMX: FAB action sheet ────────────────────────────────────────────────────

@login_required
def htmx_fab_sheet(request):
    return render(request, 'community/partials/_fab_sheet.html')
