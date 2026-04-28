from django.utils import timezone
from .models import Tenant, TenantInvitation, UserPermission


class InvitationError(Exception):
    pass


def send_invitation(tenant, email, invited_by):
    """Create a TenantInvitation for an email address. Caller handles email delivery."""
    if UserPermission.objects.filter(
        tenant=tenant, user__email=email, is_active=True
    ).exists():
        raise InvitationError("This person is already an active member of this community.")

    existing = TenantInvitation.objects.filter(
        tenant=tenant, email=email, status='pending'
    ).first()
    if existing and not existing.is_expired:
        raise InvitationError("A pending invitation for this email already exists.")

    return TenantInvitation.objects.create(
        tenant=tenant,
        email=email,
        invited_by=invited_by,
    )


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
    """Deactivate a member's UserPermission. Does not delete the record."""
    perms = UserPermission.objects.filter(tenant=tenant, user=user, is_active=True)
    if not perms.exists():
        raise InvitationError("This user is not an active member of this community.")
    perms.update(is_active=False)


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
