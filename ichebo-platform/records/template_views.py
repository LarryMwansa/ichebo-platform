# records/template_views.py — Django template views + HTMX partial views
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Record, Relationship
from governance.services import get_linked_records

JOURNAL_RECORD_TYPES = [
    ('prayer', 'Prayer'),
    ('spirit', 'Spirit'),
    ('dream', 'Dream'),
    ('dar', 'Activity Report'),
    ('note', 'General'),
]


# ── My Records home ───────────────────────────────────────────────────────────

@login_required
def my_records(request):
    record_type = request.GET.get('type')
    records = Record.objects.filter(
        created_by=request.user,
        deleted_at__isnull=True,
        record_family='journal',
    )
    if record_type:
        records = records.filter(record_type=record_type)
    
    records = records.order_by('-updated_at')

    context = {
        'records': records,
        'record_types': JOURNAL_RECORD_TYPES,
        'active_type': record_type,
        'active_app': 'records',
        'ws_page_title': 'Records',
        'is_desk': True,  # Flag to render the desk by default
    }

    if request.headers.get('HX-Request') and not request.GET.get('full'):
        return render(request, 'records/partials/record_list.html', context)

    return render(request, 'workspace/records/my_records.html', context)


# ── Record detail ─────────────────────────────────────────────────────────────

@login_required
def record_detail(request, record_id):
    record = get_object_or_404(Record, id=record_id, deleted_at__isnull=True)

    # Personal records are private; non-personal records are readable by any authenticated user
    if record.record_class == 'personal' and record.created_by != request.user:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    # Breadcrumb: find where we came from
    via_record = None
    via_id = request.GET.get('via')
    if via_id:
        via_record = Record.objects.filter(id=via_id).first()

    if request.headers.get('HX-Request'):
        from django.template.loader import render_to_string
        ctx = {'record': record, 'via_record': via_record}
        stage_html = render_to_string(
            'workspace/records/partials/record_detail_stage.html', ctx, request=request
        )
        options_html = render_to_string(
            'workspace/records/partials/_options_detail.html', ctx, request=request
        )
        return HttpResponse(f'<div>{stage_html}{options_html}</div>', content_type='text/html')

    return render(request, 'workspace/records/record_detail.html', {
        'record': record,
        'via_record': via_record,
        'active_app': 'records',
        'ws_page_title': record.title,
        'record_types': JOURNAL_RECORD_TYPES,
    })


# ── HTMX: recent drafts sidebar widget ───────────────────────────────────────

@login_required
def htmx_recent_drafts(request):
    drafts = Record.objects.filter(
        created_by=request.user,
        record_family='journal',
        status__in=['draft', 'active'],
        deleted_at__isnull=True,
    ).order_by('-updated_at')[:5]

    if not drafts.exists():
        return HttpResponse(
            '<div style="padding: var(--space-s); font-size: 12px; color: var(--muted);">'
            'No recent entries.</div>'
        )

    items = ''.join(
        f'<a href="/records/{r.id}/" class="ctx-btn" style="height: auto; padding: 6px 8px; '
        f'flex-direction: column; align-items: flex-start; gap: 2px; text-decoration: none;">'
        f'<span style="font-size: 12px; font-weight: 600; color: var(--text); white-space: nowrap; '
        f'overflow: hidden; text-overflow: ellipsis; max-width: 180px;">{r.title[:36]}</span>'
        f'<span style="font-size: 10px; color: var(--muted); text-transform: uppercase; '
        f'letter-spacing: 0.06em;">{r.get_record_type_display() if hasattr(r, "get_record_type_display") else r.record_type}</span>'
        f'</a>'
        for r in drafts
    )
    return HttpResponse(items)


# ── HTMX: create record ───────────────────────────────────────────────────────

@login_required
def htmx_create_record(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            return HttpResponse('<p class="record-error">Title is required.</p>', status=400)

        rtype = request.POST.get('record_type', 'note')
        metadata = {'source_app': 'records'}
        if rtype == 'dar':
            metadata['dar'] = True

        record = Record.objects.create(
            created_by=request.user,
            record_class='personal',
            record_family='journal',
            record_type=rtype,
            origin='user',
            status='active',
            title=title,
            content=request.POST.get('content', '').strip(),
            metadata=metadata,
        )
        from django.urls import reverse
        detail_url = reverse('records:records-detail', kwargs={'record_id': record.pk})
        # Drawer submit
        if request.headers.get('HX-Target') == 'drawerInner':
            response = HttpResponse(status=204)
            response['HX-Trigger'] = 'recordCreated'
            response['HX-Redirect'] = reverse('records:records-home')
            return response
        # Any HTMX call (e.g. compose form) → redirect browser to detail
        if request.headers.get('HX-Request'):
            response = HttpResponse(status=204)
            response['HX-Redirect'] = detail_url
            return response
        return render(request, 'workspace/records/record_detail.html', {
            'record': record,
            'is_desk': False,
            'active_app': 'records',
            'ws_page_title': record.title,
            'record_types': JOURNAL_RECORD_TYPES,
        })

    # GET — partial for HTMX, full shell for direct navigation
    ctx = {
        'record_types': JOURNAL_RECORD_TYPES,
        'active_type': request.GET.get('record_type', 'prayer'),
        'active_app': 'records',
    }
    if request.headers.get('HX-Request'):
        hx_target = request.headers.get('HX-Target', '')
        if hx_target in ('drawerInner', 'record-create-pane'):
            return render(request, 'records/partials/create_form.html', ctx)
        return render(request, 'workspace/records/partials/editorial_form.html', ctx)
    return render(request, 'workspace/records/create.html', ctx)


# ── HTMX: edit record ─────────────────────────────────────────────────────────

@login_required
def htmx_edit_record(request, record_id):
    record = get_object_or_404(
        Record, id=record_id, created_by=request.user, deleted_at__isnull=True
    )

    if request.GET.get('show') == '1':
        return render(request, 'records/partials/record_card.html', {'record': record})

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if title:
            record.title = title
        record.content = request.POST.get('content', '').strip()
        rtype = request.POST.get('record_type', record.record_type)
        if rtype:
            record.record_type = rtype
        record.save(update_fields=['title', 'content', 'record_type', 'updated_at'])
        from django.urls import reverse
        from django.template.loader import render_to_string
        import json
        refresh_target = request.POST.get('refresh_target', '')
        hx_target = request.headers.get('HX-Target', '')
        # Desktop options bar save — OOB swap the detail into #ics-canvas
        if hx_target == 'record-edit-pane' or refresh_target == 'record-edit-pane':
            stage_html = render_to_string(
                'workspace/records/partials/record_detail_stage.html',
                {'record': record, 'record_types': JOURNAL_RECORD_TYPES},
                request=request,
            )
            oob_html = f'<div><div id="ics-canvas" hx-swap-oob="innerHTML">{stage_html}</div></div>'
            resp = HttpResponse(oob_html, content_type='text/html')
            resp['X-WS-Toast'] = json.dumps([{'level': 'success', 'message': 'Entry saved.'}])
            return resp
        # Mobile drawer save — redirect to detail page
        response = HttpResponse(status=204)
        response['HX-Trigger'] = 'recordCreated'
        response['HX-Redirect'] = reverse('records:records-detail', kwargs={'record_id': record.id})
        return response

    # GET — drawer and options bar pane both get the compact form
    hx_target = request.headers.get('HX-Target', '')
    if hx_target in ('drawerInner', 'record-edit-pane'):
        return render(request, 'records/partials/edit_form.html', {
            'record': record,
            'record_types': JOURNAL_RECORD_TYPES,
            'refresh_target': 'record-edit-pane' if hx_target == 'record-edit-pane' else '',
        })
    return render(request, 'workspace/records/partials/editorial_form.html', {
        'record': record,
        'record_types': JOURNAL_RECORD_TYPES,
    })


# ── HTMX: delete record ───────────────────────────────────────────────────────

@login_required
def htmx_delete_record(request, record_id):
    if request.method != 'POST':
        return HttpResponse(status=405)

    record = get_object_or_404(
        Record, id=record_id, created_by=request.user, deleted_at__isnull=True
    )
    record.deleted_at = timezone.now()
    record.save(update_fields=['deleted_at'])
    return HttpResponse('')


# ── HTMX: linked records panel ────────────────────────────────────────────────

RELATIONSHIP_CONTEXTS = {
    'learning': ['part_of', 'answers', 'fulfills', 'references', 'relates_to'],
    'governance': ['derived_from', 'aligns_with', 'authorised_by', 'has_symbol', 'matches_pattern', 'has_subject', 'has_entity', 'references'],
    'activity': ['assigned_to', 'tracks', 'completes', 'aligns_with', 'relates_to'],
    'community': ['community_ref', 'tagged_in', 'relates_to'],
    'personal': ['relates_to', 'references', 'tracks'],
}

@login_required
def htmx_linked_records(request, record_id):
    record = get_object_or_404(Record, id=record_id, deleted_at__isnull=True)
    grouped = get_linked_records(record_id)

    context_slug = request.GET.get('context', record.record_family)
    allowed_types = RELATIONSHIP_CONTEXTS.get(context_slug, [])

    if allowed_types:
        relationship_types = [
            (val, label) for val, label in Relationship.RELATIONSHIP_TYPE_CHOICES
            if val in allowed_types
        ]
    else:
        relationship_types = Relationship.RELATIONSHIP_TYPE_CHOICES

    ctx = {
        'record': record,
        'grouped': grouped,
        'relationship_types': relationship_types,
        'can_add_link': True,
        'context': context_slug,
    }

    # Mobile drawer: wrap in the relations drawer shell
    if request.headers.get('HX-Target') == 'drawerInner':
        return render(request, 'workspace/records/partials/_m_relations.html', ctx)

    return render(request, '_linked_records_section.html', ctx)


# ── HTMX: create relationship ─────────────────────────────────────────────────

@login_required
def htmx_relationship_create(request):
    if request.method != 'POST':
        return HttpResponse('', status=405)

    from_record_id = request.POST.get('from_record_id', '').strip()
    to_record_id = request.POST.get('to_record_id', '').strip()
    rel_type = request.POST.get('relationship_type', '')
    notes = request.POST.get('notes', '').strip() or None

    try:
        from_record = get_object_or_404(Record, id=from_record_id, deleted_at__isnull=True)
        to_record = get_object_or_404(Record, id=to_record_id, deleted_at__isnull=True) if to_record_id else None

        if not to_record:
            return HttpResponse('<p style="color:var(--error)">Target record not found.</p>', status=400)

        Relationship.objects.create(
            created_by=request.user,
            from_record=from_record,
            to_record=to_record,
            relationship_type=rel_type,
            direction='directed',
            notes=notes,
        )

        # Return refreshed linked records panel
        grouped = get_linked_records(from_record_id)
        return render(request, '_linked_records_section.html', {
            'record': from_record,
            'grouped': grouped,
            'relationship_types': Relationship.RELATIONSHIP_TYPE_CHOICES,
            'can_add_link': True,
        })
    except Exception as e:
        return HttpResponse(f'<p style="color:var(--error)">Error: {str(e)}</p>', status=400)


# ── HTMX: search records ──────────────────────────────────────────────────

@login_required
def htmx_record_search(request):
    query = request.GET.get('q', '').strip()
    family = request.GET.get('family', '').strip()
    record_type = request.GET.get('type', '').strip()

    qs = Record.objects.filter(deleted_at__isnull=True).order_by('-created_at')

    if query:
        qs = qs.filter(title__icontains=query)
    if family:
        qs = qs.filter(record_family=family)
    if record_type:
        qs = qs.filter(record_type=record_type)

    results = qs[:50]

    return render(request, 'records/partials/_search_results.html', {
        'results': results,
        'query': query,
        'has_results': results.exists(),
    })


# ── Knowledge Graph (Apostolic Web) ──────────────────────────────────────────

@login_required
def graph_view(request):
    """Full-page graph visualization shell."""
    qs = Record.objects.filter(deleted_at__isnull=True)
    total = qs.count()
    governance_count = qs.filter(record_class='governance').count()
    personal_count   = qs.filter(record_family='journal').count()
    relationship_count = Relationship.objects.filter(deleted_at__isnull=True, to_record__isnull=False).count()

    return render(request, 'workspace/records/graph.html', {
        'active_app': 'records',
        'ws_page_title': 'Knowledge Graph',
        'total_nodes': total,
        'governance_count': governance_count,
        'personal_count': personal_count,
        'relationship_count': relationship_count,
    })


@login_required
def htmx_graph_data(request):
    """Returns JSON nodes and links for the D3 graph."""
    import json
    from django.http import JsonResponse

    # Fetch all active records (nodes)
    records = Record.objects.filter(deleted_at__isnull=True)
    
    nodes = []
    for r in records:
        nodes.append({
            'id': str(r.id),
            'title': r.title,
            'family': r.record_family,
            'type': r.record_type,
            'level': r.permissions_data.get('required_level', 1) if r.permissions_data else 1,
        })

    # Fetch all active relationships (links)
    relationships = Relationship.objects.filter(deleted_at__isnull=True, to_record__isnull=False)
    
    links = []
    for rel in relationships:
        links.append({
            'source': str(rel.from_record_id),
            'target': str(rel.to_record_id),
            'type': rel.relationship_type,
        })

    return JsonResponse({
        'nodes': nodes,
        'links': links,
    })


# ── HTMX: FAB action sheet ────────────────────────────────────────────────────

@login_required
def htmx_fab_sheet(request):
    return render(request, 'records/partials/_fab_sheet.html')
