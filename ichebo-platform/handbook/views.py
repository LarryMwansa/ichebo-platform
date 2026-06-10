import json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from records.models import Record, Relationship
from activity.models import Activity
from .models import HandbookAccess

# ── Governance record type groupings (mirrors governance/services.py) ─────────

LIBRARY_TYPES = ['class', 'principle', 'concept', 'divine_pattern', 'narrative', 'subject', 'entity']
MANDATE_TYPES = [
    'mandate', 'statement', 'framework', 'protocol', 'procedure', 'programme',
]
KEY_TYPES = ['key', 'subject', 'entity', 'narrative']

LIBRARY_TYPE_LABELS = {
    'class':          'Classes',
    'principle':      'Principles',
    'concept':        'Concepts',
    'divine_pattern': 'Divine Patterns',
    'narrative':      'Narratives',
    'subject':        'Subjects',
    'entity':         'Entities',
}
MANDATE_TYPE_LABELS = {
    'mandate':   'Mandates',
    'statement': 'Statements',
    'framework': 'Frameworks',
    'protocol':  'Protocols',
    'procedure': 'Procedures',
    'programme': 'Programmes',
}

ALL_GOVERNANCE_TYPES = LIBRARY_TYPES + MANDATE_TYPES + KEY_TYPES

HRS_ATTRS = [
    ('complexity',            'Complexity'),
    ('relationship_position', 'Relationship Position'),
    ('position',              'Position'),
    ('direction',             'Direction'),
    ('speed',                 'Speed'),
    ('emotional_tone',        'Emotional Tone'),
]

RECORD_TYPES_BY_BRANCH = {
    'reference': LIBRARY_TYPES,
    'mandate':   MANDATE_TYPES,
    'keys':      KEY_TYPES,
}

STATUS_CHOICES = ['draft', 'active', 'locked', 'superseded', 'submitted']


# ── Access level constants ─────────────────────────────────────────────────────
# Will be moved to PlatformConfig (L10.6) for System Panel configuration.
KEYS_ACCESS_LEVEL      = 4   # Keys Library — entity/narrative are L4-5 content
REFERENCE_ACCESS_LEVEL = 3   # Reference Library
MANDATE_ACCESS_LEVEL   = 3   # Handbook authoring of Mandate records


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_access(user):
    return HandbookAccess.objects.filter(user=user).first()


def _can_write(access):
    return access and access.role in (HandbookAccess.ROLE_AUTHOR, HandbookAccess.ROLE_EDITOR)


def _is_editor(access):
    return access and access.role == HandbookAccess.ROLE_EDITOR


def _governance_qs(user, access, include_drafts=False):
    """Base queryset for governance records, respecting access role."""
    qs = Record.objects.filter(
        record_family='governance',
        deleted_at__isnull=True,
    ).exclude(record_type='key')

    if _can_write(access):
        return qs  # authors/editors see everything including drafts
    if include_drafts:
        return qs
    return qs.filter(status__in=['active', 'locked'])


def _keys_qs(user):
    return Record.objects.filter(
        record_family='reference',
        record_type__in=KEY_TYPES,
        created_by=user,
        deleted_at__isnull=True,
    )


def _level(user):
    return getattr(user, 'competence_level', 0)


# ── Handbook Home ─────────────────────────────────────────────────────────────

@login_required
def handbook_home(request):
    if _level(request.user) < 3:
        return HttpResponseForbidden()

    access = _get_access(request.user)
    active_branch = request.GET.get('branch', 'reference')
    if active_branch not in RECORD_TYPES_BY_BRANCH:
        active_branch = 'reference'
    status_filter = request.GET.get('status', '')

    records_by_type = {}

    is_superuser = request.user.is_staff or request.user.is_superuser

    if active_branch == 'keys':
        if _level(request.user) < KEYS_ACCESS_LEVEL and not request.user.is_superuser:
            return HttpResponseForbidden('Keys Library requires Level 4 or above.')
        qs = _keys_qs(request.user)
        if status_filter:
            qs = qs.filter(status=status_filter)
        for rtype in KEY_TYPES:
            type_qs = qs.filter(record_type=rtype).order_by('-updated_at')[:30]
            if type_qs.exists():
                records_by_type[rtype] = list(type_qs)
        can_write_branch = True
    else:
        if not access and not is_superuser:
            can_write_branch = False
            qs = Record.objects.none()
        else:
            qs = _governance_qs(request.user, access, include_drafts=is_superuser or _can_write(access))
            if status_filter:
                qs = qs.filter(status=status_filter)
            for rtype in RECORD_TYPES_BY_BRANCH.get(active_branch, []):
                type_qs = qs.filter(record_type=rtype).order_by('-updated_at')[:20]
                if type_qs.exists():
                    records_by_type[rtype] = list(type_qs)
            can_write_branch = is_superuser or _can_write(access)

    return render(request, 'workspace/handbook/home.html', {
        'active_app':            'handbook',
        'ws_page_title':         'Handbook',
        'access':                access,
        'can_write':             can_write_branch,
        'is_editor':             is_superuser or _is_editor(access),
        'active_branch':         active_branch,
        'record_types_by_branch': RECORD_TYPES_BY_BRANCH,
        'library_type_labels':   LIBRARY_TYPE_LABELS,
        'mandate_type_labels':   MANDATE_TYPE_LABELS,
        'records_by_type':       records_by_type,
        'status_filter':         status_filter,
        'has_access':            access is not None or is_superuser,
    })


# ── Handbook Record Detail ────────────────────────────────────────────────────

@login_required
def handbook_record(request, record_id):
    if _level(request.user) < 3:
        return HttpResponseForbidden()

    access = _get_access(request.user)

    # Keys — personal records stored under record_family='reference'
    key_record = Record.objects.filter(
        pk=record_id,
        record_family='reference',
        record_type__in=KEY_TYPES,
        created_by=request.user,
        deleted_at__isnull=True,
    ).first()

    is_superuser = request.user.is_staff or request.user.is_superuser

    if key_record:
        if _level(request.user) < KEYS_ACCESS_LEVEL and not is_superuser:
            return HttpResponseForbidden('Keys Library requires Level 4 or above.')
        record = key_record
        can_write = True
    else:
        if not access and not is_superuser:
            return HttpResponseForbidden()
        qs = _governance_qs(request.user, access, include_drafts=True)
        record = get_object_or_404(qs, pk=record_id)
        can_write = is_superuser or _can_write(access)

    # Version chain
    history = []
    cursor = record
    while cursor is not None:
        history.append(cursor)
        try:
            cursor = Record.objects.get(pk=cursor.previous_version_id) if cursor.previous_version_id else None
        except Record.DoesNotExist:
            break

    outgoing = record.outgoing_relationships.select_related(
        'to_record', 'bible_verse', 'bible_verse__book'
    )

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
        'is_editor':            _is_editor(access),
        'is_reference':         record.record_type in LIBRARY_TYPES,
        'is_key':               record.record_type in KEY_TYPES and record.record_family == 'reference',
        'show_hrs':             record.record_type in LIBRARY_TYPES or (record.record_type in KEY_TYPES and record.record_family == 'reference'),
        'hrs_attrs':            HRS_ATTRS,
        'record_types_reference': LIBRARY_TYPES,
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
    if _level(request.user) < 3:
        return HttpResponseForbidden()

    access = _get_access(request.user)
    is_superuser = request.user.is_staff or request.user.is_superuser
    active_branch = request.GET.get('branch', 'reference')
    if active_branch not in RECORD_TYPES_BY_BRANCH:
        active_branch = 'reference'

    if active_branch == 'keys':
        can_write = True
    else:
        if not _can_write(access) and not is_superuser:
            return HttpResponseForbidden()
        can_write = True

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

    default_type = LIBRARY_TYPES[0] if active_branch == 'reference' else MANDATE_TYPES[0]

    return render(request, 'workspace/handbook/record.html', {
        'active_app':             'handbook',
        'ws_page_title':          'New Record',
        'access':                 access,
        'record':                 None,
        'history':                [],
        'outgoing':               [],
        'can_write':              can_write,
        'is_editor':              _is_editor(access),
        'is_key':                 active_branch == 'keys',
        'is_reference':           active_branch == 'reference',
        'show_hrs':               active_branch in ('reference', 'keys'),
        'active_branch':          active_branch,
        'hrs_attrs':              HRS_ATTRS,
        'record_types_reference': LIBRARY_TYPES,
        'record_types_mandate':   MANDATE_TYPES,
        # Editor canvas context
        'save_url':               reverse('handbook:save'),
        'handbook_save_url':      reverse('handbook:save'),
        'active_family':          'governance',
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
    access = _get_access(request.user)
    is_superuser = request.user.is_staff or request.user.is_superuser
    if not _is_editor(access) and not is_superuser:
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

    access = _get_access(request.user)
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

    # Keys: any Level 3+ user can write their own; others need write access
    if not is_key and not _can_write(access) and not is_superuser:
        return HttpResponseForbidden()

    custom_fields = {
        'complexity':            request.POST.get('complexity', ''),
        'polarity':              request.POST.get('polarity', ''),
        'relationship_position': request.POST.get('relationship_position', ''),
        'position':              request.POST.get('position', ''),
        'direction':             request.POST.get('direction', ''),
        'speed':                 request.POST.get('speed', ''),
        'emotional_tone':        request.POST.get('emotional_tone', ''),
        'symbol':                request.POST.get('symbol', ''),
    }
    # Strip empty
    custom_fields = {k: v for k, v in custom_fields.items() if v}

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
    access = _get_access(request.user)
    if not _can_write(access):
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
    access = _get_access(request.user)
    if not _can_write(access):
        return HttpResponseForbidden()
    record = get_object_or_404(Record, pk=record_id, record_family='governance', deleted_at__isnull=True)
    record.status = 'active'
    record.save(update_fields=['status', 'updated_at'])
    return HttpResponse('<span style="color:#00b894;font-size:12px;font-weight:700;">Published</span>')


# ── HTMX: New version ─────────────────────────────────────────────────────────

@login_required
def handbook_new_version(request, record_id):
    if request.method != 'POST':
        return HttpResponse(status=405)
    access = _get_access(request.user)
    if not _can_write(access):
        return HttpResponseForbidden()
    old = get_object_or_404(Record, pk=record_id, record_family='governance', deleted_at__isnull=True)

    new_record = Record.objects.create(
        created_by=request.user,
        record_class=old.record_class,
        record_family='governance',
        record_type=old.record_type,
        title=old.title,
        content=old.content,
        summary=old.summary if hasattr(old, 'summary') else '',
        status='draft',
        previous_version_id=old.pk,
        custom_fields=dict(old.custom_fields),
    )
    # Mark old as superseded
    old.status = 'superseded'
    old.superseded_by_id = new_record.pk
    old.save(update_fields=['status', 'superseded_by_id', 'updated_at'])

    from django.urls import reverse
    response = HttpResponse(status=204)
    response['HX-Redirect'] = reverse('handbook:record', kwargs={'record_id': new_record.pk})
    return response


# ── HTMX: Set status ─────────────────────────────────────────────────────────

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

    access = _get_access(request.user)
    is_superuser = request.user.is_staff or request.user.is_superuser

    # Try personal (keys) record first, then governance
    record = Record.objects.filter(
        pk=record_id, record_family='reference',
        record_type__in=KEY_TYPES, created_by=request.user,
        deleted_at__isnull=True,
    ).first()
    if not record:
        if not _can_write(access) and not is_superuser:
            return HttpResponseForbidden()
        record = get_object_or_404(Record, pk=record_id, record_family='governance', deleted_at__isnull=True)

    new_status = request.POST.get('status', '').strip()
    allowed = VALID_STATUS_TRANSITIONS.get(record.status, [])
    if new_status not in allowed:
        return HttpResponse(
            f'<span style="color:#e17055;font-size:12px;">Cannot move {record.status} → {new_status}</span>',
            status=422,
        )

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
    access = _get_access(request.user)
    record = get_object_or_404(Record, pk=record_id, record_family='governance', deleted_at__isnull=True)
    outgoing = record.outgoing_relationships.select_related('to_record', 'bible_verse', 'bible_verse__book')
    incoming = record.incoming_relationships.select_related('from_record')
    return render(request, 'workspace/handbook/partials/_linked_records.html', {
        'record':   record,
        'outgoing': outgoing,
        'incoming': incoming,
        'can_write': _can_write(access),
    })


# ── HTMX: Create relationship ────────────────────────────────────────────────

@login_required
def handbook_relationship_create(request):
    if request.method != 'POST':
        return HttpResponse(status=405)

    access = _get_access(request.user)
    is_superuser = request.user.is_staff or request.user.is_superuser
    if not _can_write(access) and not is_superuser:
        return HttpResponseForbidden()

    from_id  = request.POST.get('from_record_id', '').strip()
    to_id    = request.POST.get('to_record_id', '').strip()
    rel_type = request.POST.get('relationship_type', 'references').strip()
    notes    = request.POST.get('notes', '').strip()

    if not from_id or not to_id:
        return HttpResponse('Missing record IDs', status=400)

    from_record = get_object_or_404(Record, pk=from_id, deleted_at__isnull=True)
    to_record   = get_object_or_404(Record, pk=to_id,   deleted_at__isnull=True)

    Relationship.objects.get_or_create(
        from_record=from_record,
        to_record=to_record,
        relationship_type=rel_type,
        defaults={'notes': notes},
    )
    return HttpResponse(status=204)


# ── HTMX: List relationships for a record ────────────────────────────────────

@login_required
def handbook_relationship_list(request, record_id):
    record = get_object_or_404(Record, pk=record_id, deleted_at__isnull=True)
    access = _get_access(request.user)
    is_superuser = request.user.is_staff or request.user.is_superuser
    can_write = is_superuser or _can_write(access) or record.record_family == 'reference'
    outgoing = record.outgoing_relationships.select_related('to_record').order_by('relationship_type')
    incoming = record.incoming_relationships.select_related('from_record').order_by('relationship_type')

    rows = ''
    for rel in outgoing:
        rows += f'''
        <div class="dopt-rel-card">
            <div style="font-size:10px;color:var(--muted);text-transform:uppercase;
                        letter-spacing:0.06em;margin-bottom:2px;">{rel.relationship_type.replace("_"," ")}</div>
            <a href="/handbook/records/{rel.to_record.pk}/"
               style="font-size:13px;font-weight:600;color:var(--text);text-decoration:none;">
               {rel.to_record.title[:60]}
            </a>
        </div>'''
    for rel in incoming:
        rows += f'''
        <div class="dopt-rel-card">
            <div style="font-size:10px;color:var(--muted);text-transform:uppercase;
                        letter-spacing:0.06em;margin-bottom:2px;">← {rel.relationship_type.replace("_"," ")}</div>
            <a href="/handbook/records/{rel.from_record.pk}/"
               style="font-size:13px;font-weight:600;color:var(--text);text-decoration:none;">
               {rel.from_record.title[:60]}
            </a>
        </div>'''

    if not rows:
        rows = '''<div style="padding:24px 0;text-align:center;">
            <span class="material-symbols-outlined" style="font-size:36px;opacity:0.12;display:block;">link_off</span>
            <p style="font-size:12px;color:var(--muted);margin-top:8px;">No established links yet.</p>
        </div>'''

    return HttpResponse(rows)


# ── HTMX: Recent governance records for context bar ──────────────────────────

@login_required
def handbook_recent(request):
    access = _get_access(request.user)
    if not access:
        return HttpResponse('')
    qs = _governance_qs(request.user, access).order_by('-updated_at')[:6]
    items = ''.join(
        f'<a href="/handbook/records/{r.pk}/" class="ctx-btn" style="font-size:12px;">'
        f'<span class="material-symbols-outlined" style="font-size:14px;">article</span>'
        f'{r.title[:40]}</a>'
        for r in qs
    )
    return HttpResponse(items or '<div style="padding:var(--space-s);font-size:12px;color:var(--muted);">No records yet.</div>')
