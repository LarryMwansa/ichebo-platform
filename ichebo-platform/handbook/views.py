from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render

import json
from .models import (
    HandbookAccess, HandbookRecord,
    BRANCH_CHOICES, BRANCH_REFERENCE, BRANCH_MANDATE, BRANCH_KEYS,
    RECORD_TYPES_BY_BRANCH, HRS_RELATIONSHIP_TYPES,
)

HRS_ATTRS = [
    ('complexity',             'Complexity'),
    ('relationship_position',  'Relationship Position'),
    ('position',               'Position'),
    ('direction',              'Direction'),
    ('speed',                  'Speed'),
    ('emotional_tone',         'Emotional Tone'),
]


def _get_access(user):
    return HandbookAccess.objects.filter(user=user).first()


def _can_write(access):
    return access and access.role in (HandbookAccess.ROLE_AUTHOR, HandbookAccess.ROLE_EDITOR)


def _readable_qs(access):
    if not access:
        return HandbookRecord.objects.none()
    if _can_write(access):
        return HandbookRecord.objects.all()
    return HandbookRecord.objects.filter(
        status__in=[HandbookRecord.STATUS_ACTIVE, HandbookRecord.STATUS_LOCKED]
    )


@login_required
def handbook_home(request):
    access = _get_access(request.user)
    qs = _readable_qs(access)

    active_branch = request.GET.get('branch', BRANCH_REFERENCE)
    if active_branch not in dict(BRANCH_CHOICES):
        active_branch = BRANCH_REFERENCE

    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    records_by_type = {}
    for rtype in RECORD_TYPES_BY_BRANCH.get(active_branch, []):
        type_qs = qs.filter(branch=active_branch, record_type=rtype).order_by('-updated_at')[:20]
        if type_qs.exists():
            records_by_type[rtype] = list(type_qs)

    context = {
        'active_app': 'handbook',
        'ws_page_title': 'Handbook',
        'access': access,
        'can_write': _can_write(access),
        'is_editor': access and access.role == HandbookAccess.ROLE_EDITOR,
        'active_branch': active_branch,
        'branches': BRANCH_CHOICES,
        'record_types_by_branch': RECORD_TYPES_BY_BRANCH,
        'records_by_type': records_by_type,
        'status_filter': status_filter,
    }
    return render(request, 'workspace/handbook/home.html', context)


@login_required
def handbook_record(request, pk):
    access = _get_access(request.user)
    if not access:
        return HttpResponseForbidden()
    record = get_object_or_404(_readable_qs(access), pk=pk)
    # Version history chain
    history = []
    cursor = record
    while cursor is not None:
        history.append(cursor)
        cursor = cursor.previous_version
    # Relationships
    outgoing = record.outgoing_relationships.select_related(
        'to_record', 'bible_verse', 'bible_verse__book'
    )
    context = {
        'active_app': 'handbook',
        'ws_page_title': record.title,
        'access': access,
        'record': record,
        'history': history,
        'outgoing': outgoing,
        'can_write': _can_write(access),
        'is_editor': access.role == HandbookAccess.ROLE_EDITOR,
        'hrs_relationship_types': HRS_RELATIONSHIP_TYPES,
        'hrs_attrs': HRS_ATTRS,
        'record_types_by_branch': json.dumps(RECORD_TYPES_BY_BRANCH),
        'is_reference': record.branch == BRANCH_REFERENCE,
    }
    return render(request, 'workspace/handbook/record.html', context)


@login_required
def handbook_new(request):
    access = _get_access(request.user)
    if not _can_write(access):
        return HttpResponseForbidden()
    active_branch = request.GET.get('branch', BRANCH_REFERENCE)
    context = {
        'active_app': 'handbook',
        'ws_page_title': 'New Record',
        'access': access,
        'record': None,
        'can_write': True,
        'is_editor': access.role == HandbookAccess.ROLE_EDITOR,
        'active_branch': active_branch,
        'branches': BRANCH_CHOICES,
        'record_types_by_branch': json.dumps(RECORD_TYPES_BY_BRANCH),
        'hrs_relationship_types': HRS_RELATIONSHIP_TYPES,
        'hrs_attrs': HRS_ATTRS,
    }
    return render(request, 'workspace/handbook/record.html', context)


@login_required
def handbook_access(request):
    access = _get_access(request.user)
    if not access or access.role != HandbookAccess.ROLE_EDITOR:
        return HttpResponseForbidden()
    context = {
        'active_app': 'handbook',
        'ws_page_title': 'Manage Access',
        'access': access,
    }
    return render(request, 'workspace/handbook/access.html', context)
