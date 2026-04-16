from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from .models import Tenant, UserPermission

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


def _user_level(user):
    return getattr(user, 'competence_level', 0)


def _make_unique_slug(base_slug):
    slug = base_slug
    counter = 1
    while Tenant.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


@login_required
def my_tenants(request):
    """List tenants the user stewards or has any permission in."""
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
    })


@login_required
def create_tenant(request):
    """Tenant creation wizard — Level 4+ only."""
    if _user_level(request.user) < 3:
        return redirect('tenants:my-tenants')

    errors = {}
    form_data = {}

    # Active tenants the user already stewards — valid parent candidates
    steward_roles = {
        'branch-steward', 'district-steward', 'provincial-steward',
        'national-steward', 'regional-steward', 'continental-steward', 'global-steward',
    }
    steward_perms = (
        UserPermission.objects
        .filter(user=request.user, is_active=True, role__in=steward_roles)
        .select_related('tenant')
    )
    parent_candidates = [p.tenant for p in steward_perms]

    # Also include all active tenants for the parent picker (non-stewards can still place under a parent)
    all_active_tenants = list(Tenant.objects.filter(status='active').order_by('name'))

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        tier = request.POST.get('tier', '').strip()
        affiliation = request.POST.get('affiliation', '').strip()
        description = request.POST.get('description', '').strip()
        parent_id = request.POST.get('parent_id', '').strip()

        form_data = {
            'name': name,
            'tier': tier,
            'affiliation': affiliation,
            'description': description,
            'parent_id': parent_id,
        }

        valid_tiers = [t[0] for t in Tenant.TIER_CHOICES]
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
                parent = Tenant.objects.get(id=parent_id, status='active')
            except Tenant.DoesNotExist:
                errors['parent_id'] = 'Selected parent does not exist.'

        if not errors:
            base_slug = slugify(name)[:190]
            slug = _make_unique_slug(base_slug)
            path = f"{parent.path}{slug}/" if parent else f"/{slug}/"

            role = TIER_STEWARD_ROLE.get(tier, 'branch-steward')
            tenant = Tenant.objects.create(
                created_by=request.user,
                name=name,
                slug=slug,
                path=path,
                tier=tier,
                affiliation=affiliation,
                status='active',
                description=description or None,
                parent=parent,
            )
            UserPermission.objects.create(
                tenant=tenant,
                user=request.user,
                created_by=request.user,
                granted_by=request.user,
                tenant_path=path,
                role=role,
                level=_user_level(request.user),
                is_active=True,
            )
            return redirect('tenants:tenant-created', tenant_id=tenant.id)

    return render(request, 'tenants/create_tenant.html', {
        'form_data': form_data,
        'errors': errors,
        'tier_choices': Tenant.TIER_CHOICES,
        'affiliation_choices': Tenant.AFFILIATION_CHOICES,
        'all_active_tenants': all_active_tenants,
    })


@login_required
def tenant_created(request, tenant_id):
    """Success page shown after creating a tenant."""
    tenant = get_object_or_404(
        Tenant, id=tenant_id,
        permissions__user=request.user, permissions__is_active=True
    )
    return render(request, 'tenants/tenant_created.html', {'tenant': tenant})
