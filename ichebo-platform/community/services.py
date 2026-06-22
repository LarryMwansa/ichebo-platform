# community/services.py — shared business logic for the Community app, called
# from views.py. Kept separate from views so it can be unit tested without
# the HTTP request/response cycle.
from tenants.models import UserPermission


def resolve_steward_for_tenant(tenant):
    """Resolve the steward responsible for a tenant, for routing a new
    support request.

    Order:
      1. Active UserPermission with a '*-steward' role for this tenant
      2. Fallback to Tenant.coordinator_user
      3. None — caller must handle the "needs routing" case; never guess.
    """
    if tenant is None:
        return None

    steward_perm = (
        UserPermission.objects.filter(
            tenant=tenant, is_active=True, role__endswith='-steward',
        )
        .select_related('user')
        .order_by('-level')
        .first()
    )
    if steward_perm:
        return steward_perm.user

    if tenant.coordinator_user_id:
        return tenant.coordinator_user

    return None
