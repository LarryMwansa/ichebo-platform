from django.db.models import Q
from django.utils import timezone
from .models import Tenant, TenantInvitation, UserPermission


class InvitationError(Exception):
    pass


def get_oversight_tenant_ids(user):
    """Every tenant id a user can see: tenants they have a direct
    UserPermission on, plus every descendant of a tenant where they hold a
    steward role (UserPermission.STEWARD_ROLES) — e.g. a global-steward on
    Prime Tenancy (path '/global/') oversees every tenant whose path starts
    with that prefix, not just Prime itself. Superusers see every tenant,
    matching TenantViewSet's existing superuser behavior.

    This logic previously existed only in tenants/views.py's TenantViewSet
    (the DRF API) — every template-rendered page (steward_dashboard,
    my_tenants, tenant_detail's is_steward check, community's
    _get_user_permissions) checked direct UserPermission rows only, so a
    global-steward's own descendant tenants were invisible to them outside
    the API. Found 2026-06-24 when a freshly-seeded community
    (seed_genesis_sceptre_community, which creates the Tenant row but never
    grants anyone a UserPermission on it) was invisible to a global-steward
    who should have had oversight of it automatically.
    """
    if user.is_superuser:
        return set(Tenant.objects.values_list('id', flat=True))

    direct_tenant_ids = set(
        UserPermission.objects.filter(user=user, is_active=True)
        .values_list('tenant_id', flat=True)
    )

    oversight_perms = (
        UserPermission.objects
        .filter(user=user, is_active=True, role__in=UserPermission.STEWARD_ROLES)
        .select_related('tenant')
    )
    if not oversight_perms:
        return direct_tenant_ids

    q = Q(id__in=direct_tenant_ids)
    for perm in oversight_perms:
        q |= Q(path__startswith=perm.tenant.path)
    return set(Tenant.objects.filter(q).values_list('id', flat=True))


def send_invitation(tenant, email, invited_by):
    """Create a TenantInvitation for an email address and fire the invitation_sent signal."""
    if UserPermission.objects.filter(
        tenant=tenant, user__email=email, is_active=True
    ).exists():
        raise InvitationError("This person is already an active member of this community.")

    existing = TenantInvitation.objects.filter(
        tenant=tenant, email=email, status='pending'
    ).first()
    if existing and not existing.is_expired:
        raise InvitationError("A pending invitation for this email already exists.")

    invitation = TenantInvitation.objects.create(
        tenant=tenant,
        email=email,
        invited_by=invited_by,
    )

    from notifications.signals import invitation_sent
    invitation_sent.send(
        sender=TenantInvitation,
        tenant=tenant,
        email=email,
        invited_by=invited_by,
        token=invitation.token,
    )

    return invitation


def accept_invitation(token, user):
    """Accept a TenantInvitation. Returns the created UserPermission."""
    try:
        invitation = TenantInvitation.objects.select_related('tenant').get(token=token)
    except TenantInvitation.DoesNotExist:
        raise InvitationError("This invitation link is invalid.")

    if invitation.status != 'pending':
        raise InvitationError(f"This invitation has already been {invitation.status}.")

    if timezone.now() > invitation.expires_at:
        invitation.status = 'expired'
        invitation.save(update_fields=['status'])
        raise InvitationError("This invitation has expired. Ask the steward to send a new one.")

    if user.email.lower() != invitation.email.lower():
        raise InvitationError(
            f"This invitation was sent to {invitation.email}. "
            "Please log in with that account to accept."
        )

    if user.competence_level < 1:
        raise InvitationError(
            "You must complete the Induction Programme before joining a community. "
            "Your formation journey comes first."
        )

    if UserPermission.objects.filter(
        tenant=invitation.tenant, user=user, is_active=True
    ).exists():
        invitation.status = 'accepted'
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=['status', 'accepted_at'])
        raise InvitationError("You are already a member of this community.")

    perm = UserPermission.objects.create(
        tenant=invitation.tenant,
        user=user,
        created_by=user,
        granted_by=user,
        tenant_path=invitation.tenant.path,
        role='disciple',
        level=user.competence_level,
        is_active=True,
    )

    invitation.status = 'accepted'
    invitation.accepted_at = timezone.now()
    invitation.save(update_fields=['status', 'accepted_at'])

    return perm


def remove_member(tenant, user, removed_by):
    """Deactivate a member's UserPermission and notify the removed user."""
    perms = UserPermission.objects.filter(tenant=tenant, user=user, is_active=True)
    if not perms.exists():
        raise InvitationError("This user is not an active member of this community.")
    perms.update(is_active=False)

    from notifications.signals import member_removed_signal
    member_removed_signal.send(sender=UserPermission, user=user, tenant=tenant)


def has_domain_steward(agency_tenant):
    """Return True if the agency tenant has at least one active Level 3+ steward."""
    return UserPermission.objects.filter(
        tenant=agency_tenant,
        is_active=True,
        level__gte=3,
    ).exists()


def formation_authority_user(request_user):
    """
    Return the effective authority for formation/induction decisions.
    Normally: any active steward of the Formation & Teaching agency tenant.
    Executive privilege: if none exists, falls back to the requesting user
    if they are Level 5 (Prime Tenancy authority).
    """
    try:
        formation_tenant = Tenant.objects.get(slug='formation-teaching')
    except Tenant.DoesNotExist:
        return request_user if request_user.competence_level >= 5 else None

    if has_domain_steward(formation_tenant):
        return formation_tenant
    if request_user.competence_level >= 5:
        return request_user
    return None
