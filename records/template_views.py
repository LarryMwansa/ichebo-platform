# records/template_views.py — Django template views + HTMX partial views
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Record

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
    }

    if request.headers.get('HX-Request') and not request.GET.get('full'):
        return render(request, 'records/partials/record_list.html', context)

    return render(request, 'records/my_records.html', context)


# ── Record detail ─────────────────────────────────────────────────────────────

@login_required
def record_detail(request, record_id):
    record = get_object_or_404(Record, id=record_id, deleted_at__isnull=True)

    # Personal records are private; non-personal records are readable by any authenticated user
    if record.record_class == 'personal' and record.created_by != request.user:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    return render(request, 'records/record_detail.html', {'record': record})


# ── HTMX: create record ───────────────────────────────────────────────────────

@login_required
def htmx_create_record(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            return HttpResponse('<p class="record-error">Title is required.</p>', status=400)

        record = Record.objects.create(
            created_by=request.user,
            record_class='personal',
            record_family='journal',
            record_type=request.POST.get('record_type', 'note'),
            origin='user',
            status='active',
            title=title,
            content=request.POST.get('content', '').strip(),
        )
        return render(request, 'records/partials/record_card.html', {'record': record})

    # GET — return the create form
    return render(request, 'records/partials/create_form.html', {
        'record_types': JOURNAL_RECORD_TYPES,
        'active_type': request.GET.get('record_type', 'note'),
    })


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
        record.save(update_fields=['title', 'content', 'updated_at'])
        return render(request, 'records/partials/record_card.html', {'record': record})

    # GET — return edit form pre-populated
    return render(request, 'records/partials/edit_form.html', {
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
