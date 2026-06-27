"""
View decorators for sceptre.ichebo.org access control.
Participant gate: competence_level >= 1, OR an active UserPermission on
an induction-tier tenant (0b/seeker — placed in induction but not yet in
a real Sceptre Community). A 0a/visitor with no induction placement at
all is correctly excluded — their front door is join.ichebo.org, not
this surface. Mirrors community/views.py:my_community's existing
Level-0 branch; not a new rule.
Steward gate: Level 3+ OR a role in UserPermission.STEWARD_ROLES.
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from tenants.models import UserPermission

STEWARD_LEVELS = (3, 4, 5)


def _is_seeker_or_above(user):
    """0b+ — see this file's module docstring."""
    if user.competence_level >= 1:
        return True
    return UserPermission.objects.filter(
        user=user, tenant__tier='induction', is_active=True,
    ).exists()


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
    """Gate: Level 3+ OR an active steward-role UserPermission."""
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
        if not (level_ok or role_ok):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def is_steward(user):
    """Helper — returns True if user has steward access."""
    if user.competence_level in STEWARD_LEVELS:
        return True
    return UserPermission.objects.filter(
        user=user, role__in=UserPermission.STEWARD_ROLES, is_active=True
    ).exists()
