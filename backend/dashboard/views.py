from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from paraclete.service import build_digest


@login_required
def index(request):
    digest = build_digest(request.user)
    return render(request, 'dashboard/index.html', {
        'digest': digest,
        'active_app': 'dashboard',
        'ws_page_title': 'Dashboard',
    })


@login_required
def htmx_governance_tab(request):
    from records.models import Record
    user = request.user
    level = user.competence_level

    if level < 3:
        return render(request, 'dashboard/_governance_panel.html', {
            'level': level,
            'locked': True,
        })

    tenant_ids = list(
        user.tenant_permissions.filter(is_active=True).values_list('tenant_id', flat=True)
    )
    recent_qs = Record.objects.filter(
        deleted_at__isnull=True,
        record_family='governance',
    ).filter(
        Q(created_by=user) | Q(tenant_id__in=tenant_ids)
    ).order_by('-updated_at')[:5]

    recent_docs = []
    for rec in recent_qs:
        if rec.record_type in ('edict', 'decree', 'principle', 'ordinance'):
            url = f'/governance/mandate/{rec.id}/'
        else:
            url = f'/governance/reference/{rec.id}/'
        recent_docs.append({'record': rec, 'url': url})

    return render(request, 'dashboard/_governance_panel.html', {
        'level': level,
        'locked': False,
        'recent_docs': recent_docs,
    })


@login_required
def htmx_records_tab(request):
    from records.models import Record
    user = request.user
    records = Record.objects.filter(
        deleted_at__isnull=True,
        created_by=user,
        record_family='journal',
    ).order_by('-updated_at')[:10]
    return render(request, 'dashboard/_records_panel.html', {
        'records': records,
    })


@login_required
def htmx_launcher(request):
    """Returns the App Launcher grid component."""
    return render(request, 'components/_app_launcher.html')


@login_required
def explore(request):
    """Explore hub — unified reference browser."""
    return render(request, 'dashboard/explore.html')


@login_required
def you(request):
    """You hub — personal dashboard with stats and quick links."""
    from activity.models import Activity
    from records.models import Record
    user = request.user

    activity_count = Activity.objects.filter(
        created_by=user, deleted_at__isnull=True
    ).count()

    record_count = Record.objects.filter(
        created_by=user, deleted_at__isnull=True
    ).count()

    digest = build_digest(user)

    return render(request, 'dashboard/you.html', {
        'activity_count': activity_count,
        'record_count': record_count,
        'digest': digest,
    })
def htmx_explore_create_menu(request):
    """Returns the creation selection menu for the Explore context."""
    return render(request, 'dashboard/partials/_explore_create_menu.html')

