from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from records.models import Record

@login_required
def universal_desk(request, record_id=None):
    """
    The Universal Desk — A single entry point for all ICS drafting.
    """
    record = None
    if record_id:
        record = Record.objects.filter(id=record_id, created_by=request.user).first()
    
    context = {
        'active_app': 'desk',
        'ws_page_title': 'The Desk',
        'record': record,
        'active_type': record.record_type if record else 'note',
        'save_url': '/records/htmx/create/' if not record else f'/records/htmx/record/{record.id}/edit/',
        'is_desk': True,
    }
    
    return render(request, 'workspace/editorial/desk_view.html', context)
