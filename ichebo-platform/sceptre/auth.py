"""
View decorators for sceptre.ichebo.org access control.

Participant gate: competence_level >= 1, OR an active UserPermission on
an induction-tier tenant (0b/seeker — placed in induction but not yet in
a real Sceptre Community). A 0a/visitor with no induction placement at
all is correctly excluded — their front door is join.ichebo.org, not
this surface. Mirrors community/views.py:my_community's existing
Level-0 branch; not a new rule.

Steward gate: Level 3+ OR a role in UserPermission.STEWARD_ROLES.

Induction steward gate: Stewards of the Induction tenant, PLUS stewards
on Prime Tenancy (global oversight), Formation & Teaching, and Community
Life & Care — the three agencies constitutionally responsible for
Induction. Where no Formation & Teaching or Community Life & Care steward
exists, Prime Tenancy stewards carry the responsibility automatically via
their global oversight scope.
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from tenants.models import UserPermission

STEWARD_LEVELS = (3, 4, 5)

# Agency tenants constitutionally responsible for the Induction tenant.
# Stewards on any of these can access Induction steward panels on sceptre.
INDUCTION_OVERSIGHT_SLUGS = frozenset([
    'prime',
    'formation-teaching',
    'community-life-care',
])


def _is_seeker_or_above(user):
    """0b+ — see this file's module docstring."""
    if user.competence_level >= 1:
        return True
    return UserPermission.objects.filter(
        user=user, tenant__tier='induction', is_active=True,
    ).exists()


def _is_induction_steward(user):
    """True if the user can steward the Induction tenant.

    Passes for:
    - Direct steward role on the Induction tenant itself
    - Steward on Prime Tenancy (global oversight of all tenants)
    - Steward on Formation & Teaching or Community Life & Care
      (constitutionally responsible for Induction)
    """
    return UserPermission.objects.filter(
        user=user,
        is_active=True,
        role__in=UserPermission.STEWARD_ROLES,
        tenant__slug__in=INDUCTION_OVERSIGHT_SLUGS | {'induction'},
    ).exists()


def _get_user_tenant(user):
    """Return the user's resolved active tenant (highest-level UserPermission)."""
    perm = (
        UserPermission.objects
        .filter(user=user, is_active=True)
        .select_related('tenant')
        .order_by('-level')
        .first()
    )
    return perm.tenant if perm else None


def require_sceptre_participant(view_func):
    """Gate: 0b (seeker, placed in induction) or higher."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not _is_seeker_or_above(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def require_sceptre_steward(view_func):
    """Gate: Level 3+ OR an active steward-role UserPermission.

    When the user's resolved tenant is the Induction tenant, also accepts
    stewards from Prime, Formation & Teaching, and Community Life & Care —
    the agencies constitutionally responsible for Induction.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        level_ok = user.competence_level in STEWARD_LEVELS
        role_ok = UserPermission.objects.filter(
            user=user,
            role__in=UserPermission.STEWARD_ROLES,
            is_active=True,
        ).exists()
        if level_ok or role_ok:
            return view_func(request, *args, **kwargs)
        # Extended check: agency stewards responsible for Induction
        tenant = _get_user_tenant(user)
        if tenant and tenant.tier == 'induction' and _is_induction_steward(user):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper


def is_steward(user):
    """Helper — returns True if user has steward access on their resolved tenant.

    For Induction tenant users, also accepts Prime, Formation & Teaching,
    and Community Life & Care stewards.
    """
    if user.competence_level in STEWARD_LEVELS:
        return True
    if UserPermission.objects.filter(
        user=user, role__in=UserPermission.STEWARD_ROLES, is_active=True
    ).exists():
        return True
    # Extended: check induction-specific oversight
    tenant = _get_user_tenant(user)
    if tenant and tenant.tier == 'induction':
        return _is_induction_steward(user)
    return False
