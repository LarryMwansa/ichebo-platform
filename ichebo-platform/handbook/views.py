import json
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.utils.html import escape
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie

from governance.services import create_new_version
from records.models import Record, Relationship
from activity.models import Activity
from . import access as rules
from .models import HandbookAccess
from .registry import (
    ANALYSIS_LINK_TYPES, GOVERNANCE_TYPES, KEY_TYPES, LIBRARY_KEYS, LIBRARY_LABELS,
    LIBRARY_MANDATE, LIBRARY_REFERENCE, LIBRARY_TYPES, LINK_TYPES, LINK_TYPE_VALUES,
    MANDATE_TYPES, REFERENCE_TYPES, TYPE_LABELS, TYPE_SINGULAR_LABELS, library_of,
)


def _keys_qs(user):
    return Record.objects.filter(
        record_family='reference',
        record_type__in=KEY_TYPES,
        created_by=user,
        deleted_at__isnull=True,
    )


def _link_types_for(record):
    """Record links offered for this record; the HRS analysis links only on a narrative."""
    if record.record_type == 'narrative':
        return LINK_TYPES
    return [(value, label) for value, label in LINK_TYPES if value not in ANALYSIS_LINK_TYPES]


def _requested_library(request):
    """The Library named in the URL. `branch` is the pre-v2.0 name, kept as an alias."""
    library = request.GET.get('library') or request.GET.get('branch') or LIBRARY_REFERENCE
    return library if library in LIBRARY_TYPES else LIBRARY_REFERENCE


# ── Handbook Home ─────────────────────────────────────────────────────────────

@login_required
def handbook_home(request):
    access = rules.get_access(request.user)
    is_superuser = request.user.is_staff or request.user.is_superuser
    is_author = is_superuser or rules.can_write(access)

    if rules.level(request.user) < rules.REFERENCE_ACCESS_LEVEL and not is_author:
        return HttpResponseForbidden('The Handbook requires Level 3 or above.')

    library = _requested_library(request)

    if library == LIBRARY_MANDATE and rules.level(request.user) < rules.MANDATE_ACCESS_LEVEL and not is_author:
        return HttpResponseForbidden('The Mandate Library requires Level 4 or above.')

    status_filter = request.GET.get('status', '')

    if library == LIBRARY_KEYS:
        qs = _keys_qs(request.user)
        if status_filter:
            qs = qs.filter(status=status_filter)
    else:
        qs = rules.governance_qs(request.user, access, include_drafts=is_author)
        if status_filter and (access or is_superuser):
            qs = qs.filter(status=status_filter)

    records_by_type = {}
    for rtype in LIBRARY_TYPES[library]:
        records = list(qs.filter(record_type=rtype).order_by('-updated_at')[:30])
        if records:
            records_by_type[rtype] = records

    return render(request, 'workspace/handbook/home.html', {
        'active_app':      'handbook',
        'ws_page_title':   'Handbook',
        'access':          access,
        'can_write':       library == LIBRARY_KEYS or is_author,
        'is_editor':       is_superuser or rules.is_editor(access),
        'active_library':  library,
        'library_label':   LIBRARY_LABELS[library],
        'type_labels':     TYPE_LABELS,
        'records_by_type': records_by_type,
        'status_filter':   status_filter,
        'has_access':      access is not None or is_superuser,
    })


# ── Handbook Record Detail ────────────────────────────────────────────────────

@login_required
def handbook_record(request, record_id):
    access = rules.get_access(request.user)
    is_superuser = request.user.is_staff or request.user.is_superuser

    # Keys — personal records stored under record_family='reference'
    key_record = Record.objects.filter(
        pk=record_id,
        record_family='reference',
        record_type__in=KEY_TYPES,
        created_by=request.user,
        deleted_at__isnull=True,
    ).first()

    if key_record:
        if rules.level(request.user) < rules.KEYS_ACCESS_LEVEL and not is_superuser:
            return HttpResponseForbidden('The Keys Library requires Level 3 or above.')
        record = key_record
        can_write = True
    else:
        # Grant holders see drafts; everyone else sees published, level-gated
        qs = rules.governance_qs(request.user, access, include_drafts=bool(access) or is_superuser)
        record = get_object_or_404(qs, pk=record_id)
        can_write = is_superuser or rules.can_write(access)

    # Version chain
    history = []
    cursor = record
    while cursor is not None:
        history.append(cursor)
        try:
            cursor = Record.objects.get(pk=cursor.previous_version_id) if cursor.previous_version_id else None
        except Record.DoesNotExist:
            break

    outgoing = [
        rel for rel in record.outgoing_relationships.select_related('to_record', 'bible_verse', 'bible_verse__book')
        if rel.to_record is None or rules.can_see_record(request.user, access, rel.to_record)
    ]
    library = library_of(record.record_type)

    from django.urls import reverse
    recent_records = Record.objects.filter(
        created_by=request.user,
        record_family='governance',
        deleted_at__isnull=True,
    ).order_by('-updated_at')[:8]
    gov_drafts = Record.objects.filter(
        created_by=request.user,
        record_family='governance',
        status='draft',
        deleted_at__isnull=True,
    ).order_by('-updated_at')[:5]

    return render(request, 'workspace/handbook/record.html', {
        'active_app':           'handbook',
        'ws_page_title':        record.title,
        'access':               access,
        'record':               record,
        'history':              history,
        'outgoing':             outgoing,
        'can_write':            can_write,
        'is_editor':            rules.is_editor(access),
        'active_library':       library,
        'is_reference':         library == LIBRARY_REFERENCE,
        'is_mandate':           library == LIBRARY_MANDATE,
        'is_key':               library == LIBRARY_KEYS,
        'is_narrative':         record.record_type == 'narrative',
        'type_labels':          TYPE_SINGULAR_LABELS,
        'link_types':           _link_types_for(record),
        'record_types_reference': REFERENCE_TYPES,
        'record_types_mandate':   MANDATE_TYPES,
        # Editor canvas context
        'save_url':             reverse('handbook:save'),
        'handbook_save_url':    reverse('handbook:save'),
        'active_family':        'governance',
        'active_type':          record.record_type,
        'is_desk':              True,
        'recent_records':       recent_records,
        'gov_drafts':           gov_drafts,
        'journal_drafts':       [],
        'active_missions':      [],
    })


# ── New Record (The Desk embedded) ────────────────────────────────────────────

@login_required
def handbook_new(request):
    if rules.level(request.user) < rules.REFERENCE_ACCESS_LEVEL:
        return HttpResponseForbidden()

    access = rules.get_access(request.user)
    is_superuser = request.user.is_staff or request.user.is_superuser
    library = _requested_library(request)

    if library != LIBRARY_KEYS and not rules.can_write(access) and not is_superuser:
        return HttpResponseForbidden()

    from django.urls import reverse
    recent_records = Record.objects.filter(
        created_by=request.user,
        record_family='governance',
        deleted_at__isnull=True,
    ).order_by('-updated_at')[:8]
    gov_drafts = Record.objects.filter(
        created_by=request.user,
        record_family='governance',
        status='draft',
        deleted_at__isnull=True,
    ).order_by('-updated_at')[:5]

    # A Key is personal: it must default to the 'reference' family, never 'governance',
    # or the editor saves it as a Handbook record every author can read.
    default_type = LIBRARY_TYPES[library][0]
    default_family = 'reference' if library == LIBRARY_KEYS else 'governance'

    return render(request, 'workspace/handbook/record.html', {
        'active_app':             'handbook',
        'ws_page_title':          'New Record',
        'access':                 access,
        'record':                 None,
        'history':                [],
        'outgoing':               [],
        'can_write':              True,
        'is_editor':              rules.is_editor(access),
        'active_library':         library,
        'is_key':                 library == LIBRARY_KEYS,
        'is_reference':           library == LIBRARY_REFERENCE,
        'is_mandate':             library == LIBRARY_MANDATE,
        'is_narrative':           False,
        'type_labels':            TYPE_SINGULAR_LABELS,
        'link_types':             [],
        'record_types_reference': REFERENCE_TYPES,
        'record_types_mandate':   MANDATE_TYPES,
        # Editor canvas context
        'save_url':               reverse('handbook:save'),
        'handbook_save_url':      reverse('handbook:save'),
        'active_family':          default_family,
        'active_type':            default_type,
        'is_desk':                True,
        'recent_records':         recent_records,
        'gov_drafts':             gov_drafts,
        'journal_drafts':         [],
        'active_missions':        [],
    })


# ── Access Management ─────────────────────────────────────────────────────────

@login_required
def handbook_access(request):
    access = rules.get_access(request.user)
    is_superuser = request.user.is_staff or request.user.is_superuser
    if not rules.is_editor(access) and not is_superuser:
        return HttpResponseForbidden()

    if request.method == 'POST':
        from accounts.models import User
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', HandbookAccess.ROLE_READER)
        if email and role in dict(HandbookAccess.ROLE_CHOICES):
            try:
                target_user = User.objects.get(email=email)
                HandbookAccess.objects.update_or_create(
                    user=target_user,
                    defaults={'role': role, 'granted_by': request.user},
                )
            except User.DoesNotExist:
                pass
        return redirect('handbook:access')

    all_access = HandbookAccess.objects.select_related('user', 'granted_by').order_by('role', 'user__email')

    return render(request, 'workspace/handbook/access.html', {
        'active_app':   'handbook',
        'ws_page_title': 'Manage Access',
        'access':        access,
        'all_access':    all_access,
    })


# ── HTMX: Save governance record (The Desk save — moved from governance) ──────

@login_required
def handbook_save(request):
    """Save a governance record from the Handbook editor."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    access = rules.get_access(request.user)
    is_superuser = request.user.is_staff or request.user.is_superuser
    record_id = request.POST.get('record_id', '').strip()
    title = request.POST.get('title', 'Untitled').strip()
    content = request.POST.get('content', '').strip()
    record_type = request.POST.get('record_type', 'principle').strip()

    # record_family posted by the editor dial; fall back to 'governance'
    record_family = request.POST.get('record_family', 'governance').strip()
    if record_family not in ('governance', 'reference'):
        record_family = 'governance'

    is_key = record_type in KEY_TYPES and record_family == 'reference'
    if not is_key and record_type not in GOVERNANCE_TYPES:
        return HttpResponse('Unknown record type.', status=400)

    if is_key:
        if rules.level(request.user) < rules.KEYS_ACCESS_LEVEL and not is_superuser:
            return HttpResponseForbidden()
    elif not rules.can_write(access) and not is_superuser:
        return HttpResponseForbidden()

    # The retired HRS attributes (DOC F 3.7) are no longer written; stored values are left untouched.
    symbol = request.POST.get('symbol', '')
    custom_fields = {'symbol': symbol} if symbol else {}

    if record_id:
        try:
            lookup_family = 'reference' if is_key else 'governance'
            record = Record.objects.get(
                pk=record_id,
                record_family=lookup_family,
                deleted_at__isnull=True,
            )
            if is_key and record.created_by != request.user:
                return HttpResponseForbidden()
            record.title = title
            record.content = content
            record.record_type = record_type
            if custom_fields:
                record.custom_fields = {**record.custom_fields, **custom_fields}
            record.save(update_fields=['title', 'content', 'record_type', 'custom_fields', 'updated_at'])
        except Record.DoesNotExist:
            return HttpResponse(status=404)
    else:
        record = Record.objects.create(
            created_by=request.user,
            record_class='personal' if is_key else 'governance',
            record_family='reference' if is_key else 'governance',
            record_type=record_type,
            title=title,
            content=content,
            status='draft',
            custom_fields=custom_fields or {},
        )

    from django.urls import reverse
    response = HttpResponse(status=204)
    response['HX-Redirect'] = reverse('handbook:record', kwargs={'record_id': record.pk})
    return response


# ── HTMX: Lock a record ───────────────────────────────────────────────────────

@login_required
def handbook_lock(request, record_id):
    if request.method != 'POST':
        return HttpResponse(status=405)
    access = rules.get_access(request.user)
    if not rules.can_write(access):
        return HttpResponseForbidden()
    record = get_object_or_404(Record, pk=record_id, record_family='governance', deleted_at__isnull=True)
    record.status = 'locked'
    record.save(update_fields=['status', 'updated_at'])
    return HttpResponse('<span style="color:var(--primary);font-size:12px;font-weight:700;">Locked</span>')


# ── HTMX: Publish (draft → active) ───────────────────────────────────────────

@login_required
def handbook_publish(request, record_id):
    if request.method != 'POST':
        return HttpResponse(status=405)
    access = rules.get_access(request.user)
    if not rules.can_write(access):
        return HttpResponseForbidden()
    record = get_object_or_404(Record, pk=record_id, record_family='governance', deleted_at__isnull=True)
    if rules.has_journal_link(record):
        return HttpResponse(JOURNAL_LINK_BLOCK, status=422)
    record.status = 'active'
    record.save(update_fields=['status', 'updated_at'])
    return HttpResponse('<span style="color:#00b894;font-size:12px;font-weight:700;">Published</span>')


# ── HTMX: New version ─────────────────────────────────────────────────────────

@login_required
def handbook_new_version(request, record_id):
    if request.method != 'POST':
        return HttpResponse(status=405)
    access = rules.get_access(request.user)
    if not rules.can_write(access):
        return HttpResponseForbidden()
    old = get_object_or_404(Record, pk=record_id, record_family='governance', deleted_at__isnull=True)
    new_record = create_new_version(old, request.user)

    from django.urls import reverse
    response = HttpResponse(status=204)
    response['HX-Redirect'] = reverse('handbook:record', kwargs={'record_id': new_record.pk})
    return response


# ── HTMX: Delete ──────────────────────────────────────────────────────────────
# Added 2026-06-24 — Handbook had no delete action at all (Lock/Publish/New
# Version existed, Delete never did). Reported as a real privacy concern
# alongside the handbook_new miscategorization bug above: Keys are
# personal records (created_by-scoped, see handbook_record's key_record
# branch above), and with no delete action there was no way to remove a
# Key that had been miscategorized or was otherwise wrong. Soft-delete via
# deleted_at, mirroring the established pattern in
# records/template_views.py:htmx_delete_record.
#
# Permission mirrors handbook_record's own branch exactly: a Key can only
# be deleted by the user who created it (personal data — _can_write's
# HandbookAccess role is for institutional Handbook content, not personal
# Keys, and was never the right check here); a governance record follows
# the same rules.can_write(access) rule as Lock/Publish/New Version above.
@login_required
def handbook_delete(request, record_id):
    if request.method != 'POST':
        return HttpResponse(status=405)

    key_record = Record.objects.filter(
        pk=record_id, record_family='reference', record_type__in=KEY_TYPES,
        created_by=request.user, deleted_at__isnull=True,
    ).first()

    if key_record:
        record = key_record
    else:
        access = rules.get_access(request.user)
        is_superuser = request.user.is_staff or request.user.is_superuser
        if not (is_superuser or rules.can_write(access)):
            return HttpResponseForbidden()
        record = get_object_or_404(
            Record, pk=record_id, record_family='governance', deleted_at__isnull=True
        )
        if record.status == 'locked':
            return HttpResponse(
                '<p class="gov-error">This record is locked and cannot be deleted.</p>',
                status=403,
            )

    library = LIBRARY_KEYS if key_record else (library_of(record.record_type) or LIBRARY_REFERENCE)

    record.deleted_at = timezone.now()
    record.save(update_fields=['deleted_at'])

    from django.urls import reverse
    response = HttpResponse(status=204)
    response['HX-Redirect'] = f"{reverse('handbook:home')}?library={library}"
    return response


# ── HTMX: Set status ─────────────────────────────────────────────────────────

JOURNAL_LINK_BLOCK = (
    '<span style="color:#e17055;font-size:12px;">This record is linked to a journal entry. '
    'Journals are private, so remove the link before publishing.</span>'
)

VALID_STATUS_TRANSITIONS = {
    'draft':      ['active', 'archived'],
    'active':     ['locked', 'draft', 'archived'],
    'locked':     ['archived'],
    'archived':   ['draft'],
    'superseded': [],
    'submitted':  ['approved', 'draft'],
    'approved':   ['active', 'draft'],
}

@login_required
def handbook_set_status(request, record_id):
    if request.method != 'POST':
        return HttpResponse(status=405)

    access = rules.get_access(request.user)
    is_superuser = request.user.is_staff or request.user.is_superuser

    # Try personal (keys) record first, then governance
    record = Record.objects.filter(
        pk=record_id, record_family='reference',
        record_type__in=KEY_TYPES, created_by=request.user,
        deleted_at__isnull=True,
    ).first()
    if not record:
        if not rules.can_write(access) and not is_superuser:
            return HttpResponseForbidden()
        record = get_object_or_404(Record, pk=record_id, record_family='governance', deleted_at__isnull=True)

    new_status = request.POST.get('status', '').strip()
    allowed = VALID_STATUS_TRANSITIONS.get(record.status, [])
    if new_status not in allowed:
        return HttpResponse(
            f'<span style="color:#e17055;font-size:12px;">Cannot move {record.status} → {escape(new_status)}</span>',
            status=422,
        )

    if (record.record_family == 'governance' and new_status in rules.PUBLISHED_STATUSES
            and rules.has_journal_link(record)):
        return HttpResponse(JOURNAL_LINK_BLOCK, status=422)

    record.status = new_status
    record.save(update_fields=['status', 'updated_at'])

    # Build options for the refreshed dropdown
    transitions = VALID_STATUS_TRANSITIONS.get(new_status, [])
    options = f'<option value="{new_status}" selected>{new_status.title()}</option>'
    for s in transitions:
        options += f'<option value="{s}">{s.title()}</option>'

    return HttpResponse(f'''
        <div class="dopt-section" id="hb-status-panel">
            <div class="ws-label-tag" style="margin-bottom:8px;">Status</div>
            <select class="editorial-type-picker" style="width:100%;"
                    hx-post="/handbook/htmx/{record.pk}/set-status/"
                    hx-target="#hb-status-panel"
                    hx-swap="outerHTML"
                    hx-trigger="change"
                    name="status">
                {options}
            </select>
        </div>
    ''')


# ── HTMX: Linked records panel ────────────────────────────────────────────────

@login_required
def handbook_linked_records(request, record_id):
    access = rules.get_access(request.user)
    record = get_object_or_404(Record, pk=record_id, record_family='governance', deleted_at__isnull=True)
    if not rules.can_see_record(request.user, access, record):
        raise Http404
    outgoing = [
        rel for rel in record.outgoing_relationships.select_related('to_record', 'bible_verse', 'bible_verse__book')
        if rel.to_record is None or rules.can_see_record(request.user, access, rel.to_record)
    ]
    incoming = [
        rel for rel in record.incoming_relationships.select_related('from_record')
        if rules.can_see_record(request.user, access, rel.from_record)
    ]
    return render(request, 'workspace/handbook/partials/_linked_records.html', {
        'record':   record,
        'outgoing': outgoing,
        'incoming': incoming,
        'can_write': rules.can_write(access),
    })


# ── HTMX: Create relationship ────────────────────────────────────────────────

@login_required
def handbook_relationship_create(request):
    if request.method != 'POST':
        return HttpResponse(status=405)

    access = rules.get_access(request.user)
    is_superuser = request.user.is_staff or request.user.is_superuser
    if not rules.can_write(access) and not is_superuser:
        return HttpResponseForbidden()

    from_id  = request.POST.get('from_record_id', '').strip()
    to_id    = request.POST.get('to_record_id', '').strip()
    rel_type = request.POST.get('relationship_type', 'references').strip()
    notes    = request.POST.get('notes', '').strip()

    if not from_id or not to_id:
        return HttpResponse('Missing record IDs', status=400)

    from_record = get_object_or_404(Record, pk=from_id, deleted_at__isnull=True)
    to_record   = get_object_or_404(Record, pk=to_id,   deleted_at__isnull=True)
    if not (rules.can_see_record(request.user, access, from_record)
            and rules.can_see_record(request.user, access, to_record)):
        raise Http404
    if rel_type not in LINK_TYPE_VALUES:
        return HttpResponse('Unknown link type.', status=400)
    if rel_type in ANALYSIS_LINK_TYPES and from_record.record_type != 'narrative':
        return HttpResponse('Subjects and entities can only be linked from a narrative.', status=400)
    for end, other in ((from_record, to_record), (to_record, from_record)):
        if (end.record_family == 'journal' and other.record_family == 'governance'
                and other.status in rules.PUBLISHED_STATUSES):
            return HttpResponse('A published record cannot be linked to a journal entry.', status=400)

    Relationship.objects.get_or_create(
        from_record=from_record,
        to_record=to_record,
        relationship_type=rel_type,
        defaults={'notes': notes, 'created_by': request.user},
    )
    return HttpResponse(status=204)


# ── HTMX: List relationships for a record ────────────────────────────────────

@login_required
def handbook_relationship_list(request, record_id):
    record = get_object_or_404(Record, pk=record_id, deleted_at__isnull=True)
    access = rules.get_access(request.user)
    if not rules.can_see_record(request.user, access, record):
        raise Http404
    outgoing = [
        rel for rel in record.outgoing_relationships.select_related('to_record').order_by('relationship_type')
        if rel.to_record is not None and rules.can_see_record(request.user, access, rel.to_record)
    ]
    incoming = [
        rel for rel in record.incoming_relationships.select_related('from_record').order_by('relationship_type')
        if rules.can_see_record(request.user, access, rel.from_record)
    ]

    rows = ''
    for rel in outgoing:
        rows += f'''
        <div class="dopt-rel-card">
            <div style="font-size:10px;color:var(--muted);text-transform:uppercase;
                        letter-spacing:0.06em;margin-bottom:2px;">{escape(rel.relationship_type.replace("_"," "))}</div>
            <a href="/handbook/records/{rel.to_record.pk}/"
               style="font-size:13px;font-weight:600;color:var(--text);text-decoration:none;">
               {escape(rel.to_record.title[:60])}
            </a>
        </div>'''
    for rel in incoming:
        rows += f'''
        <div class="dopt-rel-card">
            <div style="font-size:10px;color:var(--muted);text-transform:uppercase;
                        letter-spacing:0.06em;margin-bottom:2px;">← {escape(rel.relationship_type.replace("_"," "))}</div>
            <a href="/handbook/records/{rel.from_record.pk}/"
               style="font-size:13px;font-weight:600;color:var(--text);text-decoration:none;">
               {escape(rel.from_record.title[:60])}
            </a>
        </div>'''

    if not rows:
        rows = '''<div style="padding:24px 0;text-align:center;">
            <span class="material-symbols-outlined" style="font-size:36px;opacity:0.12;display:block;">link_off</span>
            <p style="font-size:12px;color:var(--muted);margin-top:8px;">No established links yet.</p>
        </div>'''

    return HttpResponse(rows)


# ── HTMX: Narrative analysis (subjects and entities) ─────────────────────────

@login_required
def handbook_analysis(request, record_id):
    access = rules.get_access(request.user)
    is_superuser = request.user.is_staff or request.user.is_superuser
    qs = rules.governance_qs(request.user, access, include_drafts=bool(access) or is_superuser)
    narrative = get_object_or_404(qs, pk=record_id, record_type='narrative')
    links = [
        rel for rel in narrative.outgoing_relationships
        .filter(relationship_type__in=ANALYSIS_LINK_TYPES, deleted_at__isnull=True)
        .select_related('to_record')
        if rel.to_record is not None and rules.can_see_record(request.user, access, rel.to_record)
    ]
    return render(request, 'workspace/handbook/partials/_analysis.html', {
        'subjects':  [rel for rel in links if rel.relationship_type == 'has_subject'],
        'entities':  [rel for rel in links if rel.relationship_type == 'has_entity'],
        'can_write': is_superuser or rules.can_write(access),
    })


# ── Knowledge Graph ──────────────────────────────────────────────────────────

# Offline: it served every user's records, journals and keys included, to anonymous visitors.
# Must be rescoped to what the viewer may see before it returns (DOC F v2.2, Part 7.5).
@login_required
def handbook_graph(request):
    return render(request, 'workspace/handbook/graph.html', {
        'active_app':    'handbook',
        'ws_page_title': 'Apostolic Web',
        'graph_offline': True,
    })


@login_required
def handbook_graph_data(request):
    from django.http import JsonResponse
    return JsonResponse({'nodes': [], 'links': []})


# ── HTMX: Recent governance records for context bar ──────────────────────────

@login_required
def handbook_recent(request):
    access = rules.get_access(request.user)
    if not access:
        return HttpResponse('')
    qs = rules.governance_qs(request.user, access).order_by('-updated_at')[:6]
    items = ''.join(
        f'<a href="/handbook/records/{r.pk}/" class="ctx-btn" style="font-size:12px;">'
        f'<span class="material-symbols-outlined" style="font-size:14px;">article</span>'
        f'{escape(r.title[:40])}</a>'
        for r in qs
    )
    return HttpResponse(items or '<div style="padding:var(--space-s);font-size:12px;color:var(--muted);">No records yet.</div>')
