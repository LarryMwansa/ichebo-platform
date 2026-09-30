# governance/views.py — the read-only governance library (ADR-022).
# Authorship lives in the Handbook; read rules are shared with it via handbook.access.
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from handbook import access as rules
from handbook.registry import MANDATE_TYPES, MANDATE_TYPE_LABELS
from records.models import Record
from .services import get_linked_records, get_version_chain


def _htmx(request):
    return bool(request.headers.get('HX-Request'))


def _shell_or_partial(request, partial_template, context, shell_template='workspace/governance/home.html'):
    """Return partial HTML for HTMX requests, full shell for desktop workspace."""
    if _htmx(request):
        return render(request, partial_template, context)

    context['partial_tpl'] = partial_template
    context.setdefault('active_app', 'governance')
    context.setdefault('ws_page_title', 'Governance')
    return render(request, shell_template, context)


def _require_mandate_level(user):
    if rules.level(user) < rules.MANDATE_ACCESS_LEVEL and not (user.is_staff or user.is_superuser):
        raise PermissionDenied


def _published_mandate_qs():
    return Record.objects.filter(
        record_family='governance',
        record_type__in=MANDATE_TYPES,
        deleted_at__isnull=True,
        status__in=rules.PUBLISHED_STATUSES,
    )


# ── Governance home ────────────────────────────────────────────────────────────

@login_required
def governance_home(request):
    _require_mandate_level(request.user)
    return redirect('governance:mandate-home')


# ── Reference Library — lives in the Handbook (ADR-022) ───────────────────────
# Redirects keep existing bookmarks and HTMX links working.

@login_required
def library_home(request):
    return redirect('/handbook/?library=reference')


@login_required
def library_list(request, record_type):
    return redirect('/handbook/?library=reference')


@login_required
def library_detail(request, record_id):
    return redirect(f'/handbook/records/{record_id}/')


# ── Mandate Library ────────────────────────────────────────────────────────────

@login_required
def mandate_home(request):
    _require_mandate_level(request.user)
    search = request.GET.get('q', '').strip()
    base_qs = _published_mandate_qs()
    type_counts = {slug: base_qs.filter(record_type=slug).count() for slug in MANDATE_TYPES}

    records = base_qs.order_by('-created_at')
    if search:
        records = records.filter(title__icontains=search)

    return _shell_or_partial(request, 'governance/_mandate_home.html', {
        'records':        records,
        'record_type':    None,
        'type_label':     'All',
        'search':         search,
        'mandate_types':  MANDATE_TYPE_LABELS,
        'type_counts':    type_counts,
        'recent_records': base_qs.order_by('-updated_at')[:5],
        'active_branch':  'mandate',
    })


@login_required
def mandate_list(request, record_type):
    _require_mandate_level(request.user)
    if record_type not in MANDATE_TYPES:
        raise Http404

    search = request.GET.get('q', '').strip()
    records = _published_mandate_qs().filter(record_type=record_type).order_by('-created_at')
    if search:
        records = records.filter(title__icontains=search)

    return _shell_or_partial(request, 'governance/_mandate_list.html', {
        'records':       records,
        'record_type':   record_type,
        'type_label':    MANDATE_TYPE_LABELS[record_type],
        'search':        search,
        'mandate_types': MANDATE_TYPE_LABELS,
        'active_branch': 'mandate',
    })


@login_required
def mandate_detail(request, record_id):
    _require_mandate_level(request.user)
    record = get_object_or_404(_published_mandate_qs(), id=record_id)

    via_record = None
    via_id = request.GET.get('via')
    if via_id:
        access = rules.get_access(request.user)
        via_record = rules.governance_qs(request.user, access).filter(id=via_id).first()

    return _shell_or_partial(request, 'governance/_mandate_detail.html', {
        'record':        record,
        'via_record':    via_record,
        'mandate_types': MANDATE_TYPE_LABELS,
        'active_branch': 'mandate',
        'record_type':   record.record_type,
    }, shell_template='workspace/governance/record_detail.html')


# ── Keys Library — personal, lives in the Handbook (ADR-022) ──────────────────

@login_required
def keys_list(request):
    return redirect('/handbook/?library=keys')


@login_required
def keys_detail(request, record_id):
    return redirect(f'/handbook/records/{record_id}/')


# ── HTMX partials ──────────────────────────────────────────────────────────────

def _readable_record_or_404(user, record_id):
    access = rules.get_access(user)
    record = get_object_or_404(Record, id=record_id, deleted_at__isnull=True)
    if not rules.can_see_record(user, access, record):
        raise Http404
    return access, record


@login_required
def htmx_linked_records(request, record_id):
    access, record = _readable_record_or_404(request.user, record_id)
    grouped = {}
    for rel_type, entries in get_linked_records(record_id).items():
        visible = [
            e for e in entries
            if e['record'] is None or rules.can_see_record(request.user, access, e['record'])
        ]
        if visible:
            grouped[rel_type] = visible

    return render(request, 'governance/_linked_records.html', {
        'record':  record,
        'grouped': grouped,
    })


@login_required
def htmx_version_history(request, record_id):
    access, record = _readable_record_or_404(request.user, record_id)
    chain = [r for r in get_version_chain(record) if rules.can_see_record(request.user, access, r)]
    return render(request, 'governance/_version_history.html', {
        'record': record,
        'chain':  chain,
    })


@login_required
def htmx_global_search(request):
    """HTMX GET: global command-center search across multiple registries."""
    if rules.level(request.user) < rules.REFERENCE_ACCESS_LEVEL:
        return HttpResponse('', status=403)

    q = request.GET.get('q', '').strip()

    if not q:
        suggestions = [
            {'title': 'New Journal Entry', 'icon': 'add', 'url': '/records/htmx/create/', 'target': '#ws-detail'},
            {'title': 'Jump to Reference Library', 'icon': 'library_books', 'url': '/handbook/?library=reference', 'target': '_top'},
            {'title': 'Jump to Mandate Library', 'icon': 'gavel', 'url': '/governance/mandate/', 'target': '#ws-content'},
            {'title': 'My Identity Profile', 'icon': 'person', 'url': 'https://identity.ichebo.org/accounts/profile/', 'target': '_top'},
        ]
        return render(request, 'governance/_global_search_results.html', {
            'suggestions': suggestions,
            'is_empty': True,
        })

    access = rules.get_access(request.user)
    gov_results = (
        rules.governance_qs(request.user, access, include_drafts=bool(access))
        .filter(title__icontains=q)
        .order_by('-updated_at')[:5]
    )

    journal_results = Record.objects.filter(
        created_by=request.user,
        record_family='journal',
        deleted_at__isnull=True,
        title__icontains=q,
    ).order_by('-updated_at')[:5]

    from accounts.models import User
    people_results = User.objects.filter(is_active=True, display_name__icontains=q)[:3]

    return render(request, 'governance/_global_search_results.html', {
        'q': q,
        'gov': gov_results,
        'journal': journal_results,
        'people': people_results,
    })
