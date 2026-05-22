from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import HandbookAccess, HandbookRecord


def _user_access(user, tenant_id=None):
    qs = HandbookAccess.objects.filter(user=user).select_related('tenant')
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)
    return qs.first()


@login_required
def handbook_home(request):
    access = _user_access(request.user)
    records = []
    if access:
        qs = HandbookRecord.objects.filter(tenant=access.tenant).order_by('-updated_at')
        if access.role == HandbookAccess.ROLE_READER:
            qs = qs.filter(status__in=[HandbookRecord.STATUS_PUBLISHED, HandbookRecord.STATUS_LOCKED])
        records = qs[:30]
    context = {
        'active_app': 'handbook',
        'ws_page_title': 'Handbook',
        'access': access,
        'records': records,
    }
    return render(request, 'workspace/handbook/home.html', context)


@login_required
def handbook_record(request, pk):
    access = _user_access(request.user)
    if not access:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()
    qs = HandbookRecord.objects.filter(tenant=access.tenant)
    if access.role == HandbookAccess.ROLE_READER:
        qs = qs.filter(status__in=[HandbookRecord.STATUS_PUBLISHED, HandbookRecord.STATUS_LOCKED])
    record = get_object_or_404(qs, pk=pk)
    # Version history chain
    history = []
    cursor = record
    while cursor is not None:
        history.append(cursor)
        cursor = cursor.previous_version
    context = {
        'active_app': 'handbook',
        'ws_page_title': record.title,
        'access': access,
        'record': record,
        'history': history,
        'can_write': access.role in (HandbookAccess.ROLE_AUTHOR, HandbookAccess.ROLE_EDITOR),
        'is_editor': access.role == HandbookAccess.ROLE_EDITOR,
    }
    return render(request, 'workspace/handbook/record.html', context)


@login_required
def handbook_access(request):
    access = _user_access(request.user)
    if not access or access.role != HandbookAccess.ROLE_EDITOR:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()
    context = {
        'active_app': 'handbook',
        'ws_page_title': 'Manage Access',
        'access': access,
    }
    return render(request, 'workspace/handbook/access.html', context)


@login_required
def handbook_new(request):
    access = _user_access(request.user)
    if not access or access.role not in (HandbookAccess.ROLE_AUTHOR, HandbookAccess.ROLE_EDITOR):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()
    context = {
        'active_app': 'handbook',
        'ws_page_title': 'New Record',
        'access': access,
        'record': None,
    }
    return render(request, 'workspace/handbook/record.html', context)
