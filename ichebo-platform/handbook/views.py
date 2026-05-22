import json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render

from .models import (
    HandbookAccess, HandbookRecord,
    BRANCH_CHOICES, BRANCH_REFERENCE, BRANCH_MANDATE, BRANCH_KEYS,
    RECORD_TYPES_BY_BRANCH, HRS_RELATIONSHIP_TYPES,
)

HRS_ATTRS = [
    ('complexity',            'Complexity'),
    ('relationship_position', 'Relationship Position'),
    ('position',              'Position'),
    ('direction',             'Direction'),
    ('speed',                 'Speed'),
    ('emotional_tone',        'Emotional Tone'),
]


def _get_access(user):
    return HandbookAccess.objects.filter(user=user).first()


def _can_write(access):
    return access and access.role in (HandbookAccess.ROLE_AUTHOR, HandbookAccess.ROLE_EDITOR)


def _shared_readable_qs(access):
    """Queryset for Reference Library + Mandate Branch records, respecting access role."""
    if not access:
        return HandbookRecord.objects.none()
    if _can_write(access):
        return HandbookRecord.objects.exclude(branch=BRANCH_KEYS)
    return HandbookRecord.objects.filter(
        status__in=[HandbookRecord.STATUS_ACTIVE, HandbookRecord.STATUS_LOCKED],
    ).exclude(branch=BRANCH_KEYS)


def _keys_qs(user):
    """Queryset for the Keys Library — always scoped to the requesting user only."""
    return HandbookRecord.objects.filter(branch=BRANCH_KEYS, created_by=user)


@login_required
def handbook_home(request):
    access = _get_access(request.user)
    active_branch = request.GET.get('branch', BRANCH_REFERENCE)
    if active_branch not in dict(BRANCH_CHOICES):
        active_branch = BRANCH_REFERENCE

    status_filter = request.GET.get('status', '')

    records_by_type = {}
    if active_branch == BRANCH_KEYS:
        # Keys branch — any authenticated user, owner-only records
        qs = _keys_qs(request.user)
        if status_filter:
            qs = qs.filter(status=status_filter)
        for rtype in RECORD_TYPES_BY_BRANCH[BRANCH_KEYS]:
            type_qs = qs.filter(record_type=rtype).order_by('-updated_at')[:20]
            if type_qs.exists():
                records_by_type[rtype] = list(type_qs)
        can_write_branch = True  # any user can write their own keys
    else:
        # Reference Library or Mandate Branch — requires HandbookAccess
        qs = _shared_readable_qs(access)
        if status_filter:
            qs = qs.filter(status=status_filter)
        for rtype in RECORD_TYPES_BY_BRANCH.get(active_branch, []):
            type_qs = qs.filter(branch=active_branch, record_type=rtype).order_by('-updated_at')[:20]
            if type_qs.exists():
                records_by_type[rtype] = list(type_qs)
        can_write_branch = _can_write(access)

    context = {
        'active_app': 'handbook',
        'ws_page_title': 'Handbook',
        'access': access,
        'can_write': can_write_branch,
        'is_editor': access and access.role == HandbookAccess.ROLE_EDITOR,
        'active_branch': active_branch,
        'branches': BRANCH_CHOICES,
        'record_types_by_branch': RECORD_TYPES_BY_BRANCH,
        'records_by_type': records_by_type,
        'status_filter': status_filter,
        'has_shared_access': access is not None,
    }
    return render(request, 'workspace/handbook/home.html', context)


@login_required
def handbook_record(request, pk):
    access = _get_access(request.user)

    # Try keys first (no HandbookAccess required, but must be owner)
    key_record = HandbookRecord.objects.filter(pk=pk, branch=BRANCH_KEYS, created_by=request.user).first()
    if key_record:
        record = key_record
        can_write = True
        is_editor = access and access.role == HandbookAccess.ROLE_EDITOR
    else:
        # Shared branches — require HandbookAccess
        if not access:
            return HttpResponseForbidden()
        record = get_object_or_404(_shared_readable_qs(access), pk=pk)
        can_write = _can_write(access)
        is_editor = access.role == HandbookAccess.ROLE_EDITOR

    history = []
    cursor = record
    while cursor is not None:
        history.append(cursor)
        cursor = cursor.previous_version

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
        'can_write': can_write,
        'is_editor': is_editor,
        'hrs_relationship_types': HRS_RELATIONSHIP_TYPES,
        'hrs_attrs': HRS_ATTRS,
        'record_types_by_branch': json.dumps(RECORD_TYPES_BY_BRANCH),
        'is_reference': record.branch == BRANCH_REFERENCE,
        'is_key': record.branch == BRANCH_KEYS,
    }
    return render(request, 'workspace/handbook/record.html', context)


@login_required
def handbook_new(request):
    access = _get_access(request.user)
    active_branch = request.GET.get('branch', BRANCH_REFERENCE)
    if active_branch not in dict(BRANCH_CHOICES):
        active_branch = BRANCH_REFERENCE

    # Keys branch: any authenticated user can create their own key records
    if active_branch == BRANCH_KEYS:
        can_write = True
        is_editor = access and access.role == HandbookAccess.ROLE_EDITOR
    else:
        if not _can_write(access):
            return HttpResponseForbidden()
        can_write = True
        is_editor = access.role == HandbookAccess.ROLE_EDITOR

    context = {
        'active_app': 'handbook',
        'ws_page_title': 'New Record',
        'access': access,
        'record': None,
        'can_write': can_write,
        'is_editor': is_editor,
        'is_key': active_branch == BRANCH_KEYS,
        'is_reference': active_branch == BRANCH_REFERENCE,
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
