# accounts/permissions.py
from rest_framework.permissions import BasePermission
from tenants.models import UserPermission

class IsLevel1OrAbove(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.competence_level >= 1

class IsLevel2OrAbove(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.competence_level >= 2

class IsLevel4OrAbove(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.competence_level >= 4

class IsLevel5OrAbove(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.competence_level >= 5

def check_record_permission(user, record):
    """
    Full permission check per data contract Part 7.
    Returns True if user may read this record, False otherwise.
    """
    if not user or not user.is_authenticated:
        return record.visibility == 'public'

    if user.status == 'seeker':
        return (record.created_by == user) or record.visibility == 'public'

    # Handbook short-circuit
    if record.tenant and record.tenant.path.startswith('/global/handbook/'):
        return user.competence_level >= 5

    visibility = record.permissions_data.get('visibility', 'private')
    required_level = record.permissions_data.get('required_level', 1)
    roles_allowed = record.permissions_data.get('roles_allowed', [])

    if visibility == 'private':
        return record.created_by == user

    if user.competence_level < required_level:
        return False

    if visibility == 'public':
        return True

    user_permissions = UserPermission.objects.filter(
        user=user, is_active=True
    ).values_list('tenant_path', 'role')

    tenant_path = record.tenant.path if record.tenant else ''

    if visibility == 'tenant':
        has_access = any(tp == tenant_path for tp, _ in user_permissions)
    elif visibility == 'collective':
        has_access = any(
            tenant_path.startswith(tp) or tp.startswith(tenant_path)
            for tp, _ in user_permissions
        )
    else:
        has_access = False

    if not has_access:
        return False

    if roles_allowed:
        return any(role in roles_allowed for _, role in user_permissions)

    return True
