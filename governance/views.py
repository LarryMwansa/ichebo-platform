# governance/views.py — all views: CBV with HTMX partial detection + permission gates
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from records.models import Record, Relationship
from .services import (
    LIBRARY_TYPES, MANDATE_TYPES, LIBRARY_TYPE_LABELS, MANDATE_TYPE_LABELS,
    HRS_COMPLEXITY_CHOICES, HRS_POLARITY_CHOICES, HRS_POSITION_CHOICES,
    HRS_DIRECTION_CHOICES, HRS_SPEED_CHOICES, RELATIONSHIP_TYPES,
    get_handbook_records, get_key_records, get_version_chain,
    get_linked_records, create_new_version,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _level(user):
    return getattr(user, 'competence_level', 0)


def _htmx(request):
    return bool(request.headers.get('HX-Request'))


def _shell_or_partial(request, partial_template, context, shell_template='governance/governance.html'):
    """Return partial HTML for HTMX requests, full shell for browser navigation."""
    if _htmx(request):
        return render(request, partial_template, context)
    context['_partial'] = partial_template
    return render(request, shell_template, context)


# ── Health ─────────────────────────────────────────────────────────────────────

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([AllowAny])
def governance_health(request):
    return Response({'status': 'ok', 'app': 'governance'})


# ── Governance home ────────────────────────────────────────────────────────────

@login_required
def governance_home(request):
    if _level(request.user) < 3:
        raise PermissionDenied
    return _shell_or_partial(request, 'governance/_home.html', {
        'library_types': LIBRARY_TYPE_LABELS,
        'mandate_types': MANDATE_TYPE_LABELS,
    })


# ── Reference Library ──────────────────────────────────────────────────────────

@login_required
def library_home(request):
    if _level(request.user) < 3:
        raise PermissionDenied
    return _shell_or_partial(request, 'governance/_home.html', {
        'library_types': LIBRARY_TYPE_LABELS,
        'mandate_types': MANDATE_TYPE_LABELS,
        'active_branch': 'library',
    })


@login_required
def library_list(request, record_type):
    if _level(request.user) < 3:
        raise PermissionDenied
    if record_type not in LIBRARY_TYPES:
        raise PermissionDenied

    search = request.GET.get('q', '').strip()
    tag_filter = request.GET.get('tag', '').strip()

    records = get_handbook_records(record_type, search=search)
    if tag_filter:
        records = [r for r in records if tag_filter in (r.tags or [])]

    return _shell_or_partial(request, 'governance/_library_list.html', {
        'records':       records,
        'record_type':   record_type,
        'type_label':    LIBRARY_TYPE_LABELS.get(record_type, record_type.title()),
        'search':        search,
        'tag_filter':    tag_filter,
        'library_types': LIBRARY_TYPE_LABELS,
        'is_level5':     _level(request.user) >= 5,
    })


@login_required
def library_detail(request, record_id):
    if _level(request.user) < 3:
        raise PermissionDenied

    record = get_object_or_404(
        Record, id=record_id, record_family='governance',
        record_type__in=LIBRARY_TYPES, deleted_at__isnull=True
    )
    return _shell_or_partial(request, 'governance/_library_detail.html', {
        'record':      record,
        'library_types': LIBRARY_TYPE_LABELS,
        'is_level5':   _level(request.user) >= 5,
    })


# ── Mandate branch ─────────────────────────────────────────────────────────────

@login_required
def mandate_home(request):
    if _level(request.user) < 4:
        raise PermissionDenied
    return _shell_or_partial(request, 'governance/_home.html', {
        'library_types': LIBRARY_TYPE_LABELS,
        'mandate_types': MANDATE_TYPE_LABELS,
        'active_branch': 'mandate',
    })


@login_required
def mandate_list(request, record_type):
    if _level(request.user) < 4:
        raise PermissionDenied
    if record_type not in MANDATE_TYPES:
        raise PermissionDenied

    search = request.GET.get('q', '').strip()
    records = get_handbook_records(record_type, search=search)

    return _shell_or_partial(request, 'governance/_mandate_list.html', {
        'records':       records,
        'record_type':   record_type,
        'type_label':    MANDATE_TYPE_LABELS.get(record_type, record_type.title()),
        'search':        search,
        'mandate_types': MANDATE_TYPE_LABELS,
        'is_level5':     _level(request.user) >= 5,
    })


@login_required
def mandate_detail(request, record_id):
    if _level(request.user) < 4:
        raise PermissionDenied

    record = get_object_or_404(
        Record, id=record_id, record_family='governance',
        record_type__in=MANDATE_TYPES, deleted_at__isnull=True
    )
    return _shell_or_partial(request, 'governance/_mandate_detail.html', {
        'record':        record,
        'mandate_types': MANDATE_TYPE_LABELS,
        'is_level5':     _level(request.user) >= 5,
    })


# ── My Keys ────────────────────────────────────────────────────────────────────

@login_required
def keys_list(request):
    if _level(request.user) < 3:
        raise PermissionDenied

    search = request.GET.get('q', '').strip()
    keys = get_key_records(request.user, search=search)

    return _shell_or_partial(request, 'governance/_keys_list.html', {
        'keys':   keys,
        'search': search,
    })


@login_required
def keys_detail(request, record_id):
    if _level(request.user) < 3:
        raise PermissionDenied

    record = get_object_or_404(
        Record, id=record_id, record_family='reference',
        record_type='key', created_by=request.user, deleted_at__isnull=True
    )
    linked = get_linked_records(record_id)
    return _shell_or_partial(request, 'governance/_keys_detail.html', {
        'record': record,
        'linked': linked,
    })


# ── HTMX partials ──────────────────────────────────────────────────────────────

@login_required
def htmx_linked_records(request, record_id):
    if _level(request.user) < 3:
        return HttpResponse('')

    record = get_object_or_404(Record, id=record_id, deleted_at__isnull=True)
    grouped = get_linked_records(record_id)

    return render(request, 'governance/_linked_records.html', {
        'record':             record,
        'grouped':            grouped,
        'relationship_types': RELATIONSHIP_TYPES,
        'is_level5':          _level(request.user) >= 5,
    })


@login_required
def htmx_version_history(request, record_id):
    if _level(request.user) < 4:
        return HttpResponse('')

    record = get_object_or_404(Record, id=record_id, deleted_at__isnull=True)
    chain = get_version_chain(record)

    return render(request, 'governance/_version_history.html', {
        'record': record,
        'chain':  chain,
    })


# ── Record create / edit (Level 3+ for Keys; Level 5 for Handbook) ────────────

@login_required
def htmx_record_create(request):
    level = _level(request.user)
    if level < 3:
        return HttpResponse('', status=403)

    # Determine which families this level can write
    allowed_families = ['reference']  # keys
    if level >= 5:
        allowed_families.append('governance')

    if request.method == 'POST':
        record_family = request.POST.get('record_family', 'reference')
        record_type   = request.POST.get('record_type', 'key')

        if record_family == 'governance' and level < 5:
            return HttpResponse('<p class="gov-error">Level 5 required to create Handbook records.</p>', status=403)
        if record_family == 'reference' and record_type != 'key':
            return HttpResponse('<p class="gov-error">Only Key records allowed.</p>', status=403)

        # HRS custom_fields (only for Handbook records)
        custom_fields = {}
        if record_family == 'governance':
            for field in ['complexity', 'polarity', 'position', 'direction', 'speed', 'emotional_tone']:
                val = request.POST.get(field, '').strip()
                if val:
                    custom_fields[field] = val
            if record_type == 'key':
                custom_fields['symbol'] = request.POST.get('symbol', '').strip()
        else:
            custom_fields['symbol']         = request.POST.get('symbol', '').strip()
            custom_fields['source_context'] = request.POST.get('source_context', '').strip()

        tags       = [t.strip() for t in request.POST.get('tags', '').split(',') if t.strip()]
        categories = [c.strip() for c in request.POST.get('categories', '').split(',') if c.strip()]

        record = Record.objects.create(
            created_by=request.user,
            record_class='governance' if record_family == 'governance' else 'personal',
            record_family=record_family,
            record_type=record_type,
            origin='user',
            title=request.POST.get('title', '').strip(),
            content=request.POST.get('content', '').strip() or None,
            summary=request.POST.get('summary', '').strip() or None,
            status=request.POST.get('status', 'draft'),
            version=1,
            tags=tags,
            categories=categories,
            custom_fields=custom_fields,
            metadata={'source_app': 'governance'},
            permissions_data={
                'visibility': 'global' if record_family == 'governance' else 'personal',
                'required_level': 3,
                'roles_allowed': [],
                'can_edit': [],
            },
        )

        if record_family == 'reference':
            return redirect('governance:keys-detail', record_id=record.id)

        rtype = record.record_type
        if rtype in LIBRARY_TYPES:
            return redirect('governance:library-detail', record_id=record.id)
        return redirect('governance:mandate-detail', record_id=record.id)

    # GET — return the create form
    record_type   = request.GET.get('record_type', 'key')
    record_family = request.GET.get('record_family', 'reference')

    return render(request, 'governance/_record_form.html', {
        'record':           None,
        'record_type':      record_type,
        'record_family':    record_family,
        'library_types':    LIBRARY_TYPE_LABELS,
        'mandate_types':    MANDATE_TYPE_LABELS,
        'complexity_opts':  HRS_COMPLEXITY_CHOICES,
        'polarity_opts':    HRS_POLARITY_CHOICES,
        'position_opts':    HRS_POSITION_CHOICES,
        'direction_opts':   HRS_DIRECTION_CHOICES,
        'speed_opts':       HRS_SPEED_CHOICES,
        'is_level5':        level >= 5,
        'allowed_families': allowed_families,
    })


@login_required
def htmx_record_edit(request, record_id):
    if _level(request.user) < 5:
        return HttpResponse('', status=403)

    record = get_object_or_404(Record, id=record_id, deleted_at__isnull=True)

    if record.status == 'locked':
        return HttpResponse('<p class="gov-error">This record is locked and cannot be edited.</p>')

    if request.method == 'POST':
        tags       = [t.strip() for t in request.POST.get('tags', '').split(',') if t.strip()]
        categories = [c.strip() for c in request.POST.get('categories', '').split(',') if c.strip()]

        custom_fields = dict(record.custom_fields or {})
        for field in ['complexity', 'polarity', 'position', 'direction', 'speed', 'emotional_tone', 'symbol']:
            val = request.POST.get(field, '').strip()
            if val:
                custom_fields[field] = val

        record.title      = request.POST.get('title', record.title).strip()
        record.content    = request.POST.get('content', record.content or '').strip() or None
        record.summary    = request.POST.get('summary', record.summary or '').strip() or None
        record.status     = request.POST.get('status', record.status)
        record.tags       = tags
        record.categories = categories
        record.custom_fields = custom_fields
        record.save()

        return redirect('governance:library-detail', record_id=record.id) \
            if record.record_type in LIBRARY_TYPES \
            else redirect('governance:mandate-detail', record_id=record.id)

    return render(request, 'governance/_record_form.html', {
        'record':          record,
        'record_type':     record.record_type,
        'record_family':   record.record_family,
        'library_types':   LIBRARY_TYPE_LABELS,
        'mandate_types':   MANDATE_TYPE_LABELS,
        'complexity_opts': HRS_COMPLEXITY_CHOICES,
        'polarity_opts':   HRS_POLARITY_CHOICES,
        'position_opts':   HRS_POSITION_CHOICES,
        'direction_opts':  HRS_DIRECTION_CHOICES,
        'speed_opts':      HRS_SPEED_CHOICES,
        'is_level5':       True,
    })


# ── Lock record ────────────────────────────────────────────────────────────────

@login_required
def htmx_record_lock(request, record_id):
    if _level(request.user) < 5 or request.method != 'POST':
        return HttpResponse('', status=403)

    record = get_object_or_404(Record, id=record_id, deleted_at__isnull=True)

    if record.status == 'locked':
        return HttpResponse(
            '<div id="record-status-area" class="gov-status-badge gov-locked">Locked</div>'
        )

    record.status    = 'locked'
    record.locked_by = request.user
    record.locked_at = timezone.now()
    record.save(update_fields=['status', 'locked_by', 'locked_at', 'updated_at'])

    return HttpResponse(
        f'<div id="record-status-area" class="gov-status-badge gov-locked">'
        f'🔒 Locked by {request.user.display_name or request.user.email} '
        f'on {record.locked_at.strftime("%d %b %Y")}</div>'
    )


# ── Supersede record ───────────────────────────────────────────────────────────

@login_required
def htmx_record_supersede(request, record_id):
    if _level(request.user) < 5 or request.method != 'POST':
        return HttpResponse('', status=403)

    record = get_object_or_404(Record, id=record_id, deleted_at__isnull=True)

    if record.status not in ('locked', 'active'):
        return HttpResponse(
            '<p class="gov-error">Only locked or active records can be superseded.</p>'
        )

    try:
        new_record = create_new_version(record, request.user)
    except Exception as exc:
        return HttpResponse(
            f'<p class="gov-error">Supersede failed: {exc}</p>'
        )

    # Redirect to new draft
    if new_record.record_type in LIBRARY_TYPES:
        redirect_url = f'/governance/library/record/{new_record.id}/'
    else:
        redirect_url = f'/governance/mandate/record/{new_record.id}/'

    return HttpResponse(
        status=204,
        headers={'HX-Redirect': redirect_url}
    )


# ── Create Relationship (Level 5) ──────────────────────────────────────────────

@login_required
def htmx_relationship_create(request):
    if _level(request.user) < 5 or request.method != 'POST':
        return HttpResponse('', status=403)

    from_record_id   = request.POST.get('from_record_id', '').strip()
    to_record_id     = request.POST.get('to_record_id', '').strip()
    bible_verse_id   = request.POST.get('bible_verse_id', '').strip() or None
    rel_type         = request.POST.get('relationship_type', '')
    notes            = request.POST.get('notes', '').strip() or None

    from_record = get_object_or_404(Record, id=from_record_id)
    to_record   = None
    bible_verse = None

    if bible_verse_id:
        from bible.models import BibleVerse
        bible_verse = get_object_or_404(BibleVerse, id=bible_verse_id)
    elif to_record_id:
        to_record = get_object_or_404(Record, id=to_record_id)

    Relationship.objects.create(
        created_by=request.user,
        from_record=from_record,
        to_record=to_record,
        bible_verse=bible_verse,
        relationship_type=rel_type,
        direction='directed',
        notes=notes,
    )

    # Return refreshed linked records panel
    grouped = get_linked_records(from_record_id)
    return render(request, 'governance/_linked_records.html', {
        'record':             from_record,
        'grouped':            grouped,
        'relationship_types': RELATIONSHIP_TYPES,
        'is_level5':          True,
    })
