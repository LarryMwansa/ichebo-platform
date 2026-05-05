from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from records.models import Record
from activity.models import Activity

@login_required
def universal_desk(request, record_id=None):
    """The Universal Desk — A single entry point for all ICS drafting."""
    record = None
    if record_id:
        record = Record.objects.filter(id=record_id, created_by=request.user).first()
    
    # Context-aware initialization
    initial_family = request.GET.get('family', 'journal')
    initial_type = request.GET.get('type', 'note')
    
    if record:
        initial_family = record.record_family
        initial_type = record.record_type

    # Fetch Explorer Data
    recent_records = Record.objects.filter(created_by=request.user).order_by('-updated_at')[:10]
    journal_drafts = Record.objects.filter(created_by=request.user, record_family='journal').order_by('-updated_at')[:5]
    gov_drafts = Record.objects.filter(created_by=request.user, record_family='governance').order_by('-updated_at')[:5]
    active_missions = Activity.objects.filter(created_by=request.user, status='pending').order_by('-created_at')[:5]

    # Fetch Relationships
    current_relationships = []
    if record:
        current_relationships = record.outgoing_relationships.select_related('to_record', 'bible_verse').all()

    context = {
        'active_app': 'desk',
        'ws_page_title': 'The Desk',
        'record': record,
        'active_family': initial_family,
        'active_type': initial_type,
        'save_url': '/governance/desk/save/',
        'is_desk': True,
        # Explorer context
        'recent_records': recent_records,
        'journal_drafts': journal_drafts,
        'gov_drafts': gov_drafts,
        'active_missions': active_missions,
        # Relationships context
        'current_relationships': current_relationships,
    }
    return render(request, 'workspace/editorial/desk_view.html', context)

@login_required
def desk_relationships_partial(request, record_id):
    """Return desk-style relationship cards for the options bar Relations tab."""
    record = get_object_or_404(Record, id=record_id, created_by=request.user)
    relationships = record.outgoing_relationships.select_related('to_record').all()
    return render(request, 'workspace/editorial/partials/_desk_rel_cards.html', {
        'relationships': relationships,
        'record': record,
    })


@login_required
def universal_save(request):
    """The Central Traffic Controller for all Desk saves"""
    if request.method != 'POST':
        return HttpResponse("Method not allowed", status=405)

    family = request.POST.get('record_family', 'journal')
    rtype = request.POST.get('record_type', 'note')
    title = request.POST.get('title', 'Untitled').strip()
    content = request.POST.get('content', '').strip()

    # 1. Handle Activity Family
    if family == 'activity':
        activity = Activity.objects.create(
            created_by=request.user,
            activity_type=rtype,
            title=title,
            description=content,
            due_at=request.POST.get('due_at') or None,
            recurrence=request.POST.get('recurrence', 'none'),
            kgs_pathway=request.POST.get('kgs_pathway', ''),
            status='pending'
        )
        return HttpResponse(f'<div class="ws-alert ws-alert--success">Activity "{title}" Saved to Registry</div>')

    # 2. Handle Governance Family
    elif family == 'governance':
        rclass = request.POST.get('record_class', 'governance')
        version = request.POST.get('version', 1)
        record = Record.objects.create(
            created_by=request.user,
            record_class=rclass,
            record_family='governance',
            record_type=rtype,
            title=title,
            content=content,
            version=version,
            status='draft'
        )
        return HttpResponse(f'''
            <div class="ws-alert ws-alert--success">
                <span class="material-symbols-outlined">gavel</span>
                Governance {rtype.title()} Saved as Draft (v{version})
            </div>
        ''')

    # 3. Handle Journal Family (Default)
    else:
        record = Record.objects.create(
            created_by=request.user,
            record_class='personal',
            record_family='journal',
            record_type=rtype,
            title=title,
            content=content,
            status='active'
        )
        return HttpResponse(f'<div class="ws-alert ws-alert--success">Journal entry saved to Registry</div>')
