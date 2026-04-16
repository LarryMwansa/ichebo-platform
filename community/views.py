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
from learn.models import CertificationConfirmation

from .models import MembershipRequest
from .constants import (
    KGS_SERVICE_ORDERS, KGS_SERVICE_ORDER_CHOICES,
    KGS_PARTICIPATION_STAGES, KGS_COMPETENCE_LABELS,
)


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
def my_community(request):
    """My Community — member surface. Level 1+ only."""
    user = request.user
    level = _user_level(user)

    if level < 1:
        return render(request, 'community/seeker_gate.html')

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

        announcements = list(
            Record.objects.filter(
                record_family='community',
                record_type='announcement',
                status='active',
                deleted_at__isnull=True,
            ).filter(
                # tenant scoping — filter by tenant FK if available, else no filter
                **({'tenant_id': tenant.id} if hasattr(Record, 'tenant') else {})
            ).order_by('-created_at')[:5]
        )

        now = timezone.now()
        upcoming_gatherings = list(
            Activity.objects.filter(
                activity_type='event',
                status__in=['pending', 'in_progress'],
                metadata__source_app='community',
            ).filter(
                **({'tenant_id': tenant.id} if hasattr(Activity, 'tenant') else {})
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
    })


# ── Management home (D.1) ─────────────────────────────────────────────────────

@login_required
def management_home(request):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html', {'min_level': 3}, status=403)

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

        announcements = list(
            Record.objects.filter(
                record_family='community',
                record_type='announcement',
                status='active',
                deleted_at__isnull=True,
            ).order_by('-created_at')[:3]
        )

        now = timezone.now()
        gatherings = list(
            Activity.objects.filter(
                activity_type='event',
                status__in=['pending', 'in_progress'],
                metadata__source_app='community',
            ).order_by('scheduled_at')[:5]
        )

    return render(request, 'community/management.html', {
        'primary_perm':  primary_perm,
        'scope_tenant':  scope_tenant,
        'member_count':  member_count,
        'announcements': announcements,
        'gatherings':    gatherings,
    })


# ── Member directory (D.2) ────────────────────────────────────────────────────

@login_required
def member_directory(request):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html', {'min_level': 3}, status=403)

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
        'members':       members,
        'scope_tenant':  scope_tenant,
        'filter_order':  filter_order,
        'filter_level':  filter_level,
        'search_q':      search_q,
        'order_choices': KGS_SERVICE_ORDER_CHOICES,
        'level_choices': [
            (0, 'Seeker'), (1, 'Member'), (2, 'Disciple'),
            (3, 'Steward'), (4, 'Senior Steward'), (5, 'Architect')
        ],
    })


# ── Formation pipeline (D.3) ──────────────────────────────────────────────────

@login_required
def formation_pipeline(request):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html', {'min_level': 3}, status=403)

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
        'pipeline_display': pipeline_display,
        'total': len(all_members),
    })


# ── Member profile (F.1) ──────────────────────────────────────────────────────

@login_required
def member_profile(request, member_id):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html', {'min_level': 3}, status=403)

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

    return render(request, 'community/member_profile.html', {
        'member_perm':    member_perm,
        'member_user':    member_user,
        'gifts':          gifts,
        'certifications': certifications,
        'shepherds':      shepherds,
        'order_choices':  KGS_SERVICE_ORDER_CHOICES,
        'level_label':    level_label,
        'stage_info':     stage_info,
    })


# ── Gatherings list (C.1) ────────────────────────────────────────────────────

@login_required
def gatherings_list(request):
    """Upcoming gatherings for the user's tenant. Level 1+."""
    user = request.user
    if _user_level(user) < 1:
        return render(request, 'community/seeker_gate.html')

    perms = _get_user_permissions(user)
    primary_perm = perms[0] if perms else None
    tenant = primary_perm.tenant if primary_perm else None

    now = timezone.now()
    qs = Record.objects.filter(
        record_family='community',
        record_type='gathering',
        status__in=['active', 'pending'],
        deleted_at__isnull=True,
    ).order_by('custom_fields__scheduled_at')

    if tenant:
        qs = qs.filter(tenant_id=tenant.id)

    if request.headers.get('HX-Request'):
        return render(request, 'community/partials/gathering_list.html', {
            'gatherings': qs[:20],
            'now': now,
        })

    return render(request, 'community/gatherings.html', {
        'gatherings': qs[:20],
        'now': now,
        'level': _user_level(user),
    })


# ── Gathering / Announcement detail (C.2) ────────────────────────────────────

@login_required
def community_detail(request, record_id):
    """Detail view for a gathering or announcement. Level 1+."""
    if _user_level(request.user) < 1:
        return render(request, 'community/seeker_gate.html')

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
    })


# ── HTMX: gatherings list partial (C.1) ──────────────────────────────────────

@login_required
def htmx_gatherings_list(request):
    """HTMX partial: upcoming gatherings list for the user's tenant."""
    user = request.user
    perms = _get_user_permissions(user)
    primary_perm = perms[0] if perms else None
    tenant = primary_perm.tenant if primary_perm else None

    qs = Record.objects.filter(
        record_family='community',
        record_type='gathering',
        status__in=['active', 'pending'],
        deleted_at__isnull=True,
    ).order_by('custom_fields__scheduled_at')

    if tenant:
        qs = qs.filter(tenant_id=tenant.id)

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

        Record.objects.create(
            created_by=request.user,
            record_class='organizational',
            record_family='community',
            record_type='announcement',
            origin='user',
            title=request.POST.get('title', '').strip(),
            content=request.POST.get('content', '').strip(),
            status='active',
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

    already_pending = MembershipRequest.objects.filter(
        user=user, tenant=tenant, status='pending'
    ).exists()

    return render(request, 'community/partials/orientation_check.html', {
        'tenant':          tenant,
        'required':        required,
        'pending':         pending,
        'all_done':        len(pending) == 0,
        'already_pending': already_pending,
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
    tenants = Tenant.objects.filter(status='active').order_by('name')[:50]
    return render(request, 'community/partials/membership_request_form.html', {
        'tenants': tenants,
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

            # Grant Beginner membership — get_or_create prevents duplicate re-approvals
            UserPermission.objects.get_or_create(
                tenant=membership_req.tenant,
                user=membership_req.user,
                role='beginner',
                defaults={
                    'created_by': request.user,
                    'granted_by': request.user,
                    'tenant_path': membership_req.tenant.path,
                    'level': 1,
                    'is_active': True,
                },
            )

            # Advance competence_level from Seeker (0) to Beginner (1)
            applicant = membership_req.user
            prev_level = applicant.competence_level
            if prev_level < 1:
                applicant.competence_level = 1
                applicant.save(update_fields=['competence_level'])

            # Create the Induction / Tenant Membership Certification Record
            # This is the first entry on the applicant's formation pathway.
            cert_record = Record.objects.create(
                created_by=request.user,
                record_class='personal',
                record_family='learning',
                record_type='certification',
                origin='system',
                title=f'Induction Certification — {membership_req.tenant.name}',
                content=(
                    f'Received into {membership_req.tenant.name} as a Beginner. '
                    f'First step on the Kingdom Governance pathway.'
                ),
                status='active',
                metadata={
                    'source_app': 'community',
                    'certification_type': 'induction',
                    'tenant_id': str(membership_req.tenant.id),
                },
            )

            # Confirm it — the steward's approval IS the certification event
            CertificationConfirmation.objects.create(
                certification_record_id=cert_record.id,
                confirmed_by=request.user,
                learner_id=applicant.id,
                previous_competence_level=prev_level,
                new_competence_level=1,
                notes=(
                    f'Induction certification issued on membership approval '
                    f'for {membership_req.tenant.name}.'
                ),
            )

        else:
            membership_req.status = 'denied'
            membership_req.save()

    return render(request, 'community/partials/membership_request_card.html', {
        'req': membership_req,
        'reviewed': True,
    })
