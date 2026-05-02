from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from .models import ServiceOrder, Tenant, TenantInvitation, UserPermission
from .service import InvitationError, accept_invitation, remove_member, send_invitation

TIER_STEWARD_ROLE = {
    'handbook':           'branch-steward',
    'church_node':        'branch-steward',
    'church_collective':  'branch-steward',
    'district':           'district-steward',
    'provincial':         'provincial-steward',
    'national':           'national-steward',
    'regional':           'regional-steward',
    'continental':        'continental-steward',
    'global':             'global-steward',
}

TIER_LABELS = dict(Tenant.TIER_CHOICES)
AFFILIATION_LABELS = dict(Tenant.AFFILIATION_CHOICES)

SELF_SERVICE_TIERS = [
    t for t in Tenant.TIER_CHOICES
    if t[0] not in ('handbook', 'induction', 'global')
]


def _user_level(user):
    return getattr(user, 'competence_level', 0)


def _make_unique_slug(base_slug):
    slug = base_slug
    counter = 1
    while Tenant.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


def _is_steward_of(user, tenant):
    steward_roles = {
        'branch-steward', 'district-steward', 'provincial-steward',
        'national-steward', 'regional-steward', 'continental-steward',
        'global-steward', 'admin',
    }
    return UserPermission.objects.filter(
        tenant=tenant, user=user, is_active=True, role__in=steward_roles
    ).exists()


# ---------------------------------------------------------------------------
# Steward Dashboard Home
# ---------------------------------------------------------------------------

@login_required
def steward_dashboard(request):
    user = request.user
    level = _user_level(user)

    # Tenants this user stewards (non-agency)
    steward_roles = {
        'branch-steward', 'district-steward', 'provincial-steward',
        'national-steward', 'regional-steward', 'continental-steward',
        'global-steward', 'admin',
    }
    my_steward_perms = (
        UserPermission.objects
        .filter(user=user, is_active=True, role__in=steward_roles)
        .select_related('tenant')
        .order_by('tenant__name')
    )
    my_tenants = [p.tenant for p in my_steward_perms if not p.tenant.is_agency]

    # Agency tenants (Prime Tenancy oversight — Level 5 only)
    agency_tenants = []
    if level >= 5:
        agency_tenants = (
            Tenant.objects
            .filter(is_agency=True, tier='global')
            .exclude(slug='prime')
            .order_by('name')
        )

    # Pending invitations across steward tenants
    pending_invitations = (
        TenantInvitation.objects
        .filter(tenant__in=my_tenants, status='pending')
        .select_related('tenant')
        .order_by('-created_at')[:10]
    )

    return render(request, 'tenants/steward_dashboard.html', {
        'my_tenants': my_tenants,
        'agency_tenants': agency_tenants,
        'pending_invitations': pending_invitations,
        'can_create': level >= 3,
        'is_prime': level >= 5,
        'active_app': 'tenancy',
    })


# ---------------------------------------------------------------------------
# My Communities (member view — kept for non-stewards)
# ---------------------------------------------------------------------------

@login_required
def my_tenants(request):
    user = request.user
    level = _user_level(user)
    perms = (
        UserPermission.objects
        .filter(user=user, is_active=True)
        .select_related('tenant')
        .order_by('tenant__name')
    )
    can_create = level >= 3
    return render(request, 'tenants/my_tenants.html', {
        'perms': perms,
        'can_create': can_create,
        'active_app': 'tenancy',
    })


# ---------------------------------------------------------------------------
# Tenant Detail
# ---------------------------------------------------------------------------

@login_required
def tenant_detail(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    user = request.user
    level = _user_level(user)

    # Must be steward of this tenant, or Level 5 for agency tenants
    is_steward = _is_steward_of(user, tenant)
    if not is_steward and not (level >= 5 and tenant.is_agency):
        return redirect('tenants:steward-dashboard')

    members = (
        UserPermission.objects
        .filter(tenant=tenant, is_active=True)
        .select_related('user')
        .order_by('user__email')
    )
    invitations = (
        TenantInvitation.objects
        .filter(tenant=tenant)
        .order_by('-created_at')[:20]
    )
    service_orders = ServiceOrder.objects.filter(is_active=True)

    return render(request, 'tenants/tenant_detail.html', {
        'tenant': tenant,
        'members': members,
        'invitations': invitations,
        'service_orders': service_orders,
        'is_steward': is_steward,
        'can_invite': is_steward or level >= 5,
        'active_app': 'tenancy',
    })


# ---------------------------------------------------------------------------
# Invite Member
# ---------------------------------------------------------------------------

@login_required
@require_POST
def invite_member(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    user = request.user
    level = _user_level(user)

    if not (_is_steward_of(user, tenant) or (level >= 5 and tenant.is_agency)):
        return redirect('tenants:steward-dashboard')

    email = request.POST.get('email', '').strip().lower()
    error = None

    if not email:
        error = 'An email address is required.'
    else:
        try:
            send_invitation(tenant, email, invited_by=user)
        except InvitationError as e:
            error = str(e)

    if error:
        members = (
            UserPermission.objects
            .filter(tenant=tenant, is_active=True)
            .select_related('user')
            .order_by('user__email')
        )
        invitations = (
            TenantInvitation.objects
            .filter(tenant=tenant)
            .order_by('-created_at')[:20]
        )
        service_orders = ServiceOrder.objects.filter(is_active=True)
        return render(request, 'tenants/tenant_detail.html', {
            'tenant': tenant,
            'members': members,
            'invitations': invitations,
            'service_orders': service_orders,
            'is_steward': True,
            'can_invite': True,
            'invite_error': error,
            'invite_email': email,
        })

    return redirect('tenants:tenant-detail', tenant_id=tenant.id)


# ---------------------------------------------------------------------------
# Assign Role / Service Order
# ---------------------------------------------------------------------------

@login_required
@require_POST
def assign_member_role(request, tenant_id, perm_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    perm = get_object_or_404(UserPermission, id=perm_id, tenant=tenant, is_active=True)
    user = request.user
    level = _user_level(user)

    if not (_is_steward_of(user, tenant) or (level >= 5 and tenant.is_agency)):
        return redirect('tenants:steward-dashboard')

    role = request.POST.get('role', '').strip()
    service_order_slug = request.POST.get('service_order', '').strip()

    valid_roles = [r[0] for r in UserPermission.ROLE_CHOICES]
    if role and role in valid_roles:
        perm.role = role

    metadata = perm.metadata or {}
    if service_order_slug:
        if ServiceOrder.objects.filter(slug=service_order_slug, is_active=True).exists():
            metadata['service_order'] = service_order_slug
    else:
        metadata.pop('service_order', None)

    perm.metadata = metadata
    perm.save(update_fields=['role', 'metadata'])

    return redirect('tenants:tenant-detail', tenant_id=tenant.id)


# ---------------------------------------------------------------------------
# Remove Member
# ---------------------------------------------------------------------------

@login_required
@require_POST
def remove_member_view(request, tenant_id, perm_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    perm = get_object_or_404(UserPermission, id=perm_id, tenant=tenant, is_active=True)
    user = request.user
    level = _user_level(user)

    if not (_is_steward_of(user, tenant) or (level >= 5 and tenant.is_agency)):
        return redirect('tenants:steward-dashboard')

    try:
        remove_member(tenant, perm.user, removed_by=user)
    except InvitationError:
        pass

    return redirect('tenants:tenant-detail', tenant_id=tenant.id)


# ---------------------------------------------------------------------------
# Accept Invitation (public — token auth)
# ---------------------------------------------------------------------------

def invitation_accept(request, token):
    try:
        invitation = TenantInvitation.objects.select_related('tenant').get(token=token)
    except TenantInvitation.DoesNotExist:
        return render(request, 'tenants/invitation_invalid.html', {
            'reason': 'This invitation link is invalid.'
        })

    if invitation.is_expired or invitation.status != 'pending':
        return render(request, 'tenants/invitation_invalid.html', {
            'reason': (
                'This invitation has expired or has already been used. '
                'Ask the steward to send a new invitation.'
            )
        })

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(f'/accounts/login/?next=/steward/invite/accept/{token}/')
        try:
            accept_invitation(token, request.user)
            return render(request, 'tenants/invitation_accepted.html', {
                'tenant': invitation.tenant,
            })
        except InvitationError as e:
            return render(request, 'tenants/invitation_invalid.html', {'reason': str(e)})

    return render(request, 'tenants/invitation_accept.html', {
        'invitation': invitation,
        'user_authenticated': request.user.is_authenticated,
    })


# ---------------------------------------------------------------------------
# Tenant Create / Created (existing, cleaned up)
# ---------------------------------------------------------------------------

@login_required
def create_tenant(request):
    if _user_level(request.user) < 3:
        return redirect('tenants:steward-dashboard')

    errors = {}
    form_data = {}

    # Only non-agency active tenants as parent candidates
    all_active_tenants = list(
        Tenant.objects.filter(status='active', is_agency=False).order_by('name')
    )

    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        tier        = request.POST.get('tier', '').strip()
        affiliation = request.POST.get('affiliation', '').strip()
        description = request.POST.get('description', '').strip()
        parent_id   = request.POST.get('parent_id', '').strip()

        form_data = {
            'name': name, 'tier': tier,
            'affiliation': affiliation,
            'description': description,
            'parent_id': parent_id,
        }

        valid_tiers        = [t[0] for t in SELF_SERVICE_TIERS]
        valid_affiliations = [a[0] for a in Tenant.AFFILIATION_CHOICES]

        if not name:
            errors['name'] = 'Name is required.'
        if tier not in valid_tiers:
            errors['tier'] = 'Select a valid tier.'
        if affiliation not in valid_affiliations:
            errors['affiliation'] = 'Select a valid affiliation.'

        parent = None
        if parent_id:
            try:
                parent = Tenant.objects.get(id=parent_id, status='active', is_agency=False)
            except Tenant.DoesNotExist:
                errors['parent_id'] = 'Selected parent does not exist.'

        if not errors:
            base_slug = slugify(name)[:190]
            slug      = _make_unique_slug(base_slug)
            path      = f"{parent.path}{slug}/" if parent else f"/{slug}/"
            role      = TIER_STEWARD_ROLE.get(tier, 'branch-steward')

            tenant = Tenant.objects.create(
                created_by=request.user,
                coordinator_user=request.user,
                name=name, slug=slug, path=path,
                tier=tier, affiliation=affiliation,
                status='active',
                description=description or None,
                parent=parent,
            )
            UserPermission.objects.create(
                tenant=tenant, user=request.user,
                created_by=request.user, granted_by=request.user,
                tenant_path=path, role=role,
                level=_user_level(request.user),
                is_active=True,
            )
            return redirect('tenants:tenant-created', tenant_id=tenant.id)

    return render(request, 'tenants/create_tenant.html', {
        'form_data': form_data,
        'errors': errors,
        'tier_choices': SELF_SERVICE_TIERS,
        'affiliation_choices': Tenant.AFFILIATION_CHOICES,
        'all_active_tenants': all_active_tenants,
        'active_app': 'tenancy',
    })


@login_required
def tenant_created(request, tenant_id):
    tenant = get_object_or_404(
        Tenant, id=tenant_id,
        permissions__user=request.user, permissions__is_active=True
    )
    return render(request, 'tenants/tenant_created.html', {'tenant': tenant})
