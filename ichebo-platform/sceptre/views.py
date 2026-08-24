"""
sceptre.ichebo.org — participant and steward views.
"""
from django.http import Http404
from django.shortcuts import render, redirect

from sceptre.auth import require_sceptre_participant, require_sceptre_steward, is_steward


def _get_tenant_for_user(user, request=None):
    """Resolve the user's active community tenant.

    Prime stewards can switch context: if the session holds a
    'sceptre_tenant_slug' set by switch_tenant_view, and the user
    genuinely has oversight of that tenant (via get_oversight_tenant_ids),
    that tenant is used instead of their highest-level UserPermission."""
    from tenants.models import Tenant, UserPermission
    from tenants.service import get_oversight_tenant_ids

    if request is not None:
        slug = request.session.get('sceptre_tenant_slug')
        if slug:
            try:
                candidate = Tenant.objects.get(slug=slug, status='active')
                oversight_ids = get_oversight_tenant_ids(user)
                if candidate.id in oversight_ids:
                    return candidate
            except Tenant.DoesNotExist:
                pass
            # Clear stale / unauthorised slug
            request.session.pop('sceptre_tenant_slug', None)

    perm = (
        UserPermission.objects.filter(user=user, is_active=True)
        .select_related('tenant')
        .order_by('-level')
        .first()
    )
    return perm.tenant if perm else None


@require_sceptre_participant
def participant_home(request):
    """
    Participant home — channel video first, schedule sidebar, VOD grid,
    series/programmes grid, notification CTA.
    """
    from django.db.models import Q
    from records.models import Record

    tenant = _get_tenant_for_user(request.user, request)
    user_is_steward = is_steward(request.user)

    # Recent broadcasts — last 6 records with video content for this tenant.
    recent_broadcasts = []
    if tenant:
        from media.models import VideoRecord
        raw_recs = list(
            Record.objects.filter(
                record_family__in=['media', 'broadcast'],
                deleted_at__isnull=True,
            ).filter(
                Q(tenant_id=tenant.id) | Q(tenant__name__icontains='Global') | Q(tenant__name__icontains='Default') | Q(tenant_id__isnull=True)
            ).order_by('-created_at')[:6]
        )
        recent_broadcasts = [VideoRecord(r) for r in raw_recs]

    # Programmes / Active Enrolments — user's active Learn courses or tenant's teaching programmes.
    programmes = []
    try:
        from activity.models import Activity
        if request.user and request.user.is_authenticated:
            active_activities = Activity.objects.filter(
                assigned_to=request.user,
                activity_type__in=['programme', 'project'],
                status__in=['pending', 'in_progress'],
                deleted_at__isnull=True,
            ).order_by('-updated_at')[:8]

            for act in active_activities:
                programmes.append({
                    'name': act.title,
                    'progress': getattr(act, 'progress', 0),
                    'is_enrolled': True,
                    'url': f'https://learn.ichebo.org/course/{act.linked_record_id}/' if act.linked_record_id else 'https://learn.ichebo.org/',
                })

        if not programmes and tenant:
            learn_records = Record.objects.filter(
                record_family='learn',
                record_type__in=['programme', 'course'],
                deleted_at__isnull=True,
            ).filter(
                Q(tenant_id=tenant.id) | Q(tenant__name__icontains='Global') | Q(tenant__name__icontains='Default') | Q(tenant_id__isnull=True)
            ).order_by('-created_at')[:8]

            for r in learn_records:
                programmes.append({
                    'name': r.title,
                    'progress': None,
                    'is_enrolled': False,
                    'url': f'https://learn.ichebo.org/course/{r.id}/',
                })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Teaching series query error: %s", e)

    # Schedule — upcoming ChannelSlots for this tenant.
    schedule = []
    try:
        from broadcast.models import ChannelSlot
        from django.utils import timezone
        if tenant:
            now = timezone.now()
            raw_slots = list(
                ChannelSlot.objects.filter(
                    tenant=tenant,
                    deleted_at__isnull=True,
                    scheduled_end__gte=now,
                ).order_by('scheduled_start')[:6]
            )
            for slot in raw_slots:
                is_currently_active = (slot.scheduled_start <= now <= slot.scheduled_end)
                schedule.append({
                    'id': str(slot.id),
                    'title': slot.title,
                    'day_abbr': slot.scheduled_start.strftime("%a").upper(),
                    'time_str': f"{slot.scheduled_start.strftime('%H:%M')} - {slot.scheduled_end.strftime('%H:%M')}",
                    'description': 'Live Broadcast' if slot.content_type == 'live' else 'Video on Demand',
                    'is_live': is_currently_active,
                })
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Schedule query error: %s", e)

    return render(request, 'sceptre/home/home.html', {
        'tenant': tenant,
        'tenant_id': str(tenant.id) if tenant else '',
        'is_steward': user_is_steward,
        'recent_broadcasts': recent_broadcasts,
        'programmes': programmes,
        'schedule': schedule,
    })


@require_sceptre_participant
def now_playing_partial(request):
    """
    HTMX partial — resolves the current channel content and returns the
    now-playing strip. Called by hx-trigger='every 60s' from the home
    template. Calls broadcast.services.resolve_now_playing(tenant)
    directly — no HTTP round-trip to this server's own API.
    """
    from broadcast.services import resolve_now_playing
    from django.http import HttpResponse

    tenant = _get_tenant_for_user(request.user, request)
    now_playing = resolve_now_playing(tenant) if tenant else None

    new_sig = now_playing.get('playing_signature', 'offline') if now_playing else 'offline'
    current_sig = request.GET.get('current_playing_signature')
    
    # If the exact same content is already playing, return 204 No Content.
    # HTMX will completely ignore a 204 response and leave the DOM (and video player) untouched.
    if current_sig == new_sig:
        return HttpResponse(status=204)

    return render(request, 'sceptre/home/_now_playing.html', {
        'now_playing': now_playing,
        'tenant_id': str(tenant.id) if tenant else '',
    })


@require_sceptre_participant
def community_area(request):
    """Community area — announcements, gatherings, community info summary."""
    tenant = _get_tenant_for_user(request.user, request)
    user_is_steward = is_steward(request.user)

    from django.db.models import Q
    from records.models import Record

    # Tenant-wide announcements (tenant_id IS NULL) are included via Q(),
    # matching the established pattern in community/views.py.
    announcements = [] if not tenant else list(
        Record.objects.filter(
            record_family='community',
            record_type='announcement',
            status='active',
            deleted_at__isnull=True,
        ).filter(
            Q(tenant_id=tenant.id) | Q(tenant_id__isnull=True)
        ).order_by('-created_at')[:5]
    )

    return render(request, 'sceptre/community/community.html', {
        'tenant': tenant,
        'announcements': announcements,
        'is_steward': user_is_steward,
    })


@require_sceptre_participant
def learn_summary(request):
    """Learn — Level 0 sees induction track; Level 1+ redirects to learn.ichebo.org."""
    user = request.user
    if user.competence_level == 0:
        return induction_track(request)
    return redirect('https://learn.ichebo.org/')


# ---------------------------------------------------------------------------
# Induction learning surface — Level 0 only
# ---------------------------------------------------------------------------

def _induction_programme():
    """The induction programme Record, or None if it hasn't been set up."""
    from records.models import Record
    return Record.objects.filter(
        record_family='learning',
        record_type='induction',
        status__in=['active', 'locked'],
        deleted_at__isnull=True,
    ).first()


def _induction_chrome(request):
    """Context every induction page needs for the sceptre shell."""
    return {
        'tenant': _get_tenant_for_user(request.user, request),
        'is_steward': is_steward(request.user),
    }


def _resolve_step(request, record_id, record_type):
    """Return (programme, step) for a learner, or (programme, None) if absent.

    Enrolment is topped up here so a learner who enrolled before a step was
    published still sees it. enrol_and_sync only writes when the step count
    and task-Activity count actually disagree, so a normal page load stays
    read-only.
    """
    from learn import engine

    programme = _induction_programme()
    if programme is None:
        return None, None

    engine.enrol_and_sync(request.user, programme)

    step = engine.get_step(request.user, programme, record_id)
    if step is None or step.record.record_type != record_type:
        return programme, None
    return programme, step


@require_sceptre_participant
def induction_track(request):
    """The induction programme track — step list for Level 0 users."""
    from learn import engine

    programme = _induction_programme()
    if programme is None:
        return render(request, 'sceptre/induction/track.html', {
            'modules': [], 'total': 0, 'passed': 0, 'pct': 0,
            'current_step': None, 'awaiting_cert': None,
            **_induction_chrome(request),
        })

    engine.enrol_and_sync(request.user, programme)

    steps = engine.get_steps(request.user, programme)
    passed, total, pct = engine.progress_summary(steps)

    return render(request, 'sceptre/induction/track.html', {
        'programme': programme,
        'modules': engine.group_by_course(steps),
        'current_step': engine.get_current_step(steps),
        'awaiting_cert': engine.awaiting_confirmation(request.user, programme),
        'total': total,
        'passed': passed,
        'pct': pct,
        **_induction_chrome(request),
    })


@require_sceptre_participant
def induction_lesson(request, step_id):
    """Read a single lesson. Marks it complete on POST."""
    from core.utils.video import get_embed_url, get_video_type
    from learn import engine

    programme, step = _resolve_step(request, step_id, 'lesson')
    if step is None:
        raise Http404('Lesson not found in the induction curriculum.')

    if not step.unlocked:
        return render(request, 'sceptre/induction/locked.html', {
            'step': step, **_induction_chrome(request),
        })

    if request.method == 'POST':
        try:
            engine.mark_lesson_complete(request.user, step)
        except engine.EngineError:
            pass
        return redirect('induction_track')

    video_url = step.video_url
    return render(request, 'sceptre/induction/lesson.html', {
        'step': step,
        'prog': step,                       # template shim: .status, .score
        'attachments': step.record.learning_attachments.all(),
        'video_url': video_url,
        'embed_url': get_embed_url(video_url) if video_url else None,
        'video_type': get_video_type(video_url) if video_url else None,
        **_induction_chrome(request),
    })


@require_sceptre_participant
def induction_quiz(request, step_id):
    """Display and submit a quiz, module test, or the final test."""
    from learn import engine
    from learn.models import AssessmentQuestion

    programme, step = _resolve_step(request, step_id, 'quiz')
    if step is None:
        raise Http404('Assessment not found in the induction curriculum.')

    if not step.unlocked:
        return render(request, 'sceptre/induction/locked.html', {
            'step': step, **_induction_chrome(request),
        })

    if request.method == 'POST':
        try:
            result = engine.score_assessment(
                request.user, step, request.POST.getlist('answer')
            )
        except engine.EngineError as exc:
            return render(request, 'sceptre/induction/locked.html', {
                'step': step, 'message': str(exc), **_induction_chrome(request),
            })

        # Re-resolve so the template sees post-submission state — in
        # particular awaiting_steward once the final test is passed.
        refreshed = engine.get_step(request.user, programme, step_id) or step
        return render(request, 'sceptre/induction/quiz_result.html', {
            'step': refreshed,
            'result': result,
            'prog': refreshed,
            **_induction_chrome(request),
        })

    questions = list(
        AssessmentQuestion.objects
        .filter(record=step.record)
        .prefetch_related('options')
        .order_by('order')
    )

    return render(request, 'sceptre/induction/quiz.html', {
        'step': step,
        'prog': step,
        'questions': questions,
        **_induction_chrome(request),
    })


def bible_redirect(request):
    """Bible — open redirect to bible.ichebo.org."""
    return redirect('https://bible.ichebo.org/')


@require_sceptre_participant
def support_area(request):
    """Support — native sceptre support request list."""
    from django.utils import timezone
    from records.models import Record
    
    tenant = _get_tenant_for_user(request.user, request)
    user_is_steward = is_steward(request.user)

    now = timezone.now()
    requests = Record.objects.filter(
        record_family='community',
        record_type='support_request',
        created_by=request.user,
        deleted_at__isnull=True,
    ).order_by('-created_at')

    # Annotate overdue state at read-time
    request_items = []
    for req in requests:
        due_at_str = req.custom_fields.get('response_due_at')
        is_overdue = False
        if due_at_str and req.status != 'completed':
            from django.utils.dateparse import parse_datetime
            due_at = parse_datetime(due_at_str)
            if due_at and now > due_at:
                is_overdue = True
        request_items.append({
            'record': req,
            'is_overdue': is_overdue,
        })

    return render(request, 'sceptre/support/support.html', {
        'request_items': request_items,
        'now': now,
        'tenant': tenant,
        'is_steward': user_is_steward,
    })


@require_sceptre_participant
def profile_summary(request):
    """Profile summary — interim until identity.ichebo.org ships."""
    user_is_steward = is_steward(request.user)
    tenant = _get_tenant_for_user(request.user, request)
    return render(request, 'sceptre/profile/profile.html', {
        'is_steward': user_is_steward,
        'tenant': tenant,
    })


# ── Public views (no auth required) ───────────────────────────────────────

def community_directory(request):
    """
    Public community directory — no login required.
    Adapted from v1 find-a-church.html; serves dynamic Tenant data.
    GET params: ?q=  ?theme=  ?format=  ?status=
    """
    from tenants.models import Tenant

    qs = Tenant.objects.filter(
        status='active',
        deleted_at__isnull=True,
        is_agency=False,
        tier='church_node',
    ).order_by('name')

    q = request.GET.get('q', '').strip()
    theme = request.GET.get('theme', '').strip()
    fmt = request.GET.get('format', '').strip()
    status_filter = request.GET.get('status', '').strip()

    if q:
        from django.db.models import Q as DQ
        qs = qs.filter(
            DQ(name__icontains=q) |
            DQ(community_theme__icontains=q) |
            DQ(area_of_operation__icontains=q)
        )
    if theme:
        qs = qs.filter(community_theme__icontains=theme)

    communities = list(qs[:60])

    # Distinct theme list for filter chips
    themes = list(
        Tenant.objects.filter(
            status='active', deleted_at__isnull=True,
            is_agency=False, tier='church_node',
        ).exclude(community_theme='')
        .values_list('community_theme', flat=True)
        .distinct()
        .order_by('community_theme')[:20]
    )

    return render(request, 'sceptre/community/directory.html', {
        'communities': communities,
        'themes': themes,
        'total_count': len(communities),
        'q': q,
        'theme': theme,
    })


def community_profile(request, slug):
    """
    Public community profile page — no login required.
    Resolves Tenant by slug; 404 if not found or not active.
    """
    from django.shortcuts import get_object_or_404
    from tenants.models import Tenant, UserPermission

    community = get_object_or_404(
        Tenant,
        slug=slug,
        deleted_at__isnull=True,
    )

    # Member count
    member_count = UserPermission.objects.filter(
        tenant=community,
        is_active=True,
        deleted_at__isnull=True,
    ).count()

    # Public steward names
    stewards = list(
        UserPermission.objects.filter(
            tenant=community,
            role__in=UserPermission.STEWARD_ROLES,
            is_active=True,
            deleted_at__isnull=True,
        ).select_related('user').values_list('user__first_name', 'user__last_name')[:5]
    )
    steward_names = [f"{fn} {ln}".strip() for fn, ln in stewards]

    # Recent broadcasts for this community
    recent_broadcasts = []
    try:
        from records.models import Record
        recent_broadcasts = list(
            Record.objects.filter(
                record_family='broadcast',
                tenant=community,
                deleted_at__isnull=True,
            ).order_by('-created_at')[:3]
        )
    except Exception:
        pass

    return render(request, 'sceptre/community/profile.html', {
        'community': community,
        'member_count': member_count,
        'steward_names': steward_names,
        'recent_broadcasts': recent_broadcasts,
    })


# ── Steward views ──────────────────────────────────────────────────────────

@require_sceptre_steward
def steward_members(request):
    """Native Sceptre member roster."""
    from tenants.models import UserPermission
    tenant = _get_tenant_for_user(request.user, request)
    members = UserPermission.objects.filter(
        tenant=tenant, is_active=True
    ).select_related('user').order_by('-level', 'user__first_name')
    return render(request, 'sceptre/steward/members.html', {'members': members})


@require_sceptre_steward
def steward_gatherings(request):
    """Native Sceptre gatherings list."""
    from records.models import Record
    from django.utils import timezone
    tenant = _get_tenant_for_user(request.user, request)
    now = timezone.now()
    gatherings = Record.objects.filter(
        record_family='community', record_type='gathering', tenant=tenant
    ).order_by('custom_fields__scheduled_at')
    
    upcoming = gatherings.filter(custom_fields__scheduled_at__gte=now.isoformat())
    past = gatherings.filter(custom_fields__scheduled_at__lt=now.isoformat()).order_by('-custom_fields__scheduled_at')[:10]
    return render(request, 'sceptre/steward/gatherings.html', {
        'upcoming': upcoming, 'past': past
    })


@require_sceptre_steward
def steward_formation(request):
    """Native Sceptre formation pipeline."""
    from tenants.models import UserPermission
    tenant = _get_tenant_for_user(request.user, request)
    members = UserPermission.objects.filter(tenant=tenant, is_active=True).select_related('user')
    seekers = members.filter(level=0).order_by('user__first_name')
    disciples = members.filter(level__in=[1, 2]).order_by('user__first_name')
    stewards = members.filter(level__gte=3).order_by('-level', 'user__first_name')
    
    return render(request, 'sceptre/steward/formation.html', {
        'seekers': seekers, 'disciples': disciples, 'stewards': stewards
    })


@require_sceptre_steward
def induction_final_test_queue(request):
    """Steward view — learners who passed the Final Test awaiting confirmation."""
    from learn import engine
    from learn.models import AssessmentAttempt
    from tenants.models import Tenant
    from tenants.service import GEOGRAPHIC_SCAFFOLD_TIERS, get_oversight_tenant_ids

    programme = _induction_programme()
    pending = list(engine.pending_confirmations(
        programme=programme, context='induction_completion',
    ))

    # Best final-test score per learner, for the queue rows.
    scores = {}
    if pending:
        learner_ids = [cert.created_by_id for cert in pending]
        for attempt in AssessmentAttempt.objects.filter(
            user_id__in=learner_ids, passed=True,
            record__custom_fields__is_final_assessment=True,
        ).order_by('-created_at'):
            scores.setdefault(attempt.user_id, attempt.score)

    awaiting = [
        {'cert': cert, 'learner': cert.created_by, 'score': scores.get(cert.created_by_id)}
        for cert in pending
    ]

    # Communities this steward may place a learner into. Confirming without one
    # is refused by confirm_certification_record — it would strip the learner's
    # induction membership and leave them with nothing.
    placements = Tenant.objects.filter(
        id__in=get_oversight_tenant_ids(request.user),
        is_agency=False,
        status='active',
    ).exclude(
        tier__in={'handbook', 'induction', *GEOGRAPHIC_SCAFFOLD_TIERS}
    ).order_by('name')

    return render(request, 'sceptre/induction/final_test_queue.html', {
        'awaiting': awaiting,
        'placements': placements,
        'tenant': _get_tenant_for_user(request.user, request),
        'is_steward': True,
    })


@require_sceptre_steward
def htmx_confirm_final_test(request, user_id):
    """POST — steward confirms a learner's Final Test, advancing them to Level 1.

    Routed through services.confirm_certification_record, the sole authorised
    writer of competence_level. The previous implementation called
    induction_service.confirm_final_test, which set competence_level=1 with a
    bare .update() and never touched tenant placement.
    """
    from django.http import HttpResponse
    from accounts.models import User as UserModel
    from learn import engine
    from learn.services import CertificationError, confirm_certification_record

    if request.method != 'POST':
        return HttpResponse('', status=405)

    def _error(message):
        return HttpResponse(
            f'<div id="final-row-{user_id}" style="padding:14px 18px;'
            f'background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);'
            f'border-radius:10px;font-size:13px;color:#f87171;">{message}</div>'
        )

    try:
        learner = UserModel.objects.get(id=user_id)
    except UserModel.DoesNotExist:
        return _error('Learner not found.')

    programme = _induction_programme()
    if programme is None:
        return _error('Induction programme is not set up.')

    cert = engine.awaiting_confirmation(learner, programme)
    if cert is None:
        return _error('No certification is awaiting confirmation for this learner.')

    try:
        confirm_certification_record(
            cert_record=cert,
            confirmed_by=request.user,
            notes=request.POST.get('notes', ''),
            placement_tenant_id=request.POST.get('placement_tenant_id') or None,
        )
    except CertificationError as exc:
        return _error(str(exc))

    learner.refresh_from_db()
    return HttpResponse(
        f'<div id="final-row-{user_id}" style="padding:14px 18px;'
        f'background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.3);'
        f'border-radius:10px;font-size:13px;color:#4ade80;">'
        f'✓ {learner.display_name or learner.email} confirmed — now Level '
        f'{learner.competence_level}.</div>'
    )


@require_sceptre_steward
def steward_announcements(request):
    """Native Sceptre announcements list."""
    from records.models import Record
    tenant = _get_tenant_for_user(request.user, request)
    announcements = Record.objects.filter(
        record_family='community', record_type='announcement', tenant=tenant
    ).order_by('-created_at')
    return render(request, 'sceptre/steward/announcements.html', {'announcements': announcements})


@require_sceptre_steward
def steward_support_queue(request):
    """Native Sceptre steward support queue."""
    from django.utils import timezone
    from records.models import Record
    from tenants.models import UserPermission

    user = request.user
    
    # Collect tenant paths this steward oversees
    steward_permissions = UserPermission.objects.filter(
        user=user,
        role__in=UserPermission.STEWARD_ROLES,
        is_active=True,
    ).values_list('tenant__path', flat=True)

    from django.db.models import Q
    tenant_filter = Q()
    for path in steward_permissions:
        if path:
            tenant_filter |= Q(tenant__path__startswith=path)

    # Also include requests assigned directly to this steward
    tenant_filter |= Q(custom_fields__assigned_steward_id=str(user.id))

    now = timezone.now()
    qs = Record.objects.filter(
        record_family='community',
        record_type='support_request',
        deleted_at__isnull=True,
    ).filter(tenant_filter)

    requests_list = list(qs.exclude(status='completed').order_by('created_at')) + \
        list(qs.filter(status='completed').order_by('-created_at')[:20])

    queue_items = []
    for r in requests_list:
        due_at_raw = (r.custom_fields or {}).get('response_due_at')
        due_at = None
        overdue = False
        if due_at_raw:
            from django.utils.dateparse import parse_datetime
            due_at = parse_datetime(due_at_raw)
            if due_at and r.status != 'completed' and now > due_at:
                overdue = True
        queue_items.append({
            'record': r,
            'due_at': due_at,
            'is_overdue': overdue,
        })
        
    # Sort: overdue first, then by due_at ascending, then by created_at
    queue_items.sort(key=lambda x: (
        not x['is_overdue'],
        x['due_at'] or now,
    ))

    return render(request, 'sceptre/steward/support.html', {
        'queue_items': queue_items,
        'now': now,
    })


@require_sceptre_steward
def steward_settings(request):
    return render(request, 'sceptre/steward/settings.html', {
        'tenant': _get_tenant_for_user(request.user, request)
    })

@require_sceptre_steward
def htmx_steward_settings_general(request):
    from django.http import HttpResponse
    if request.method == 'POST':
        tenant = _get_tenant_for_user(request.user, request)
        if not tenant:
            return HttpResponse("Unauthorized", status=403)
        
        tenant.name = request.POST.get('name', tenant.name)
        tenant.slug = request.POST.get('slug', tenant.slug)
        tenant.description = request.POST.get('description', tenant.description)
        tenant.area_of_operation = request.POST.get('area_of_operation', tenant.area_of_operation)
        tenant.save()
        
        return HttpResponse('<div class="sc-toast sc-toast--success">Settings saved successfully</div>')
    return HttpResponse('')

@require_sceptre_steward
def htmx_steward_settings_appearance(request):
    from django.http import HttpResponse
    if request.method == 'POST':
        tenant = _get_tenant_for_user(request.user, request)
        if not tenant:
            return HttpResponse("Unauthorized", status=403)
        
        tenant.community_theme = request.POST.get('community_theme', tenant.community_theme)
        if 'logo' in request.FILES:
            tenant.logo = request.FILES['logo']
        tenant.save()
        return HttpResponse('<div class="sc-toast sc-toast--success">Appearance settings saved</div>')
    return HttpResponse('')

@require_sceptre_steward
def htmx_steward_settings_access(request):
    from django.http import HttpResponse
    if request.method == 'POST':
        tenant = _get_tenant_for_user(request.user, request)
        if not tenant:
            return HttpResponse("Unauthorized", status=403)
        
        privacy = request.POST.get('privacy', 'public')
        tenant.settings_data['privacy'] = privacy
        tenant.save()
        return HttpResponse('<div class="sc-toast sc-toast--success">Access rules saved</div>')
    return HttpResponse('')

@require_sceptre_steward
def htmx_steward_settings_suspend(request):
    from django.http import HttpResponse
    if request.method == 'POST':
        tenant = _get_tenant_for_user(request.user, request)
        if not tenant:
            return HttpResponse("Unauthorized", status=403)
        
        tenant.status = 'suspended'
        tenant.save()
        # Return a message instructing them to contact an admin
        return HttpResponse('<div style="padding: 16px; background: rgba(175,50,54,0.2); border: 1px solid #ff6b6b; border-radius: 8px; color: #ff6b6b; font-family: \'Inter\', sans-serif;">Community suspended. It is now hidden from the directory. Contact a global administrator to undo this.</div>')
    return HttpResponse('')


@require_sceptre_participant
def htmx_sceptre_create_support_request(request):
    """
    POST → create a support_request Record, routed to a steward.
    """
    from django.utils import timezone
    from datetime import timedelta
    from django.http import HttpResponse
    from django.urls import reverse
    
    from records.models import Record
    from community.services import resolve_steward_for_tenant
    
    if request.method != 'POST':
        return HttpResponse('')

    user = request.user
    title = request.POST.get('title', '').strip()
    content = request.POST.get('content', '').strip()

    if not title or not content:
        return HttpResponse(
            '<p class="form-error" style="color:#ef4444; margin-bottom: 1rem; font-size: 14px;">Please enter a subject and a description.</p>'
        )

    tenant = _get_tenant_for_user(request.user, request)
    steward = resolve_steward_for_tenant(tenant) if tenant else None
    response_due_at = timezone.now() + timedelta(hours=72)

    record = Record.objects.create(
        tenant=tenant,
        created_by=user,
        record_class='organizational',
        record_family='community',
        record_type='support_request',
        title=title,
        content=content,
        status='submitted',
        custom_fields={
            'response_due_at': response_due_at.isoformat(),
            'assigned_steward_id': str(steward.id) if steward else None,
        },
        permissions_data={'visibility': 'member_and_assigned_steward'}
    )
    
    # Send HX-Redirect back to support area to reload the list
    response = HttpResponse(status=204)
    response['HX-Redirect'] = reverse('support')
    return response

@require_sceptre_steward
def htmx_sceptre_acknowledge_support_request(request, record_id):
    """
    POST → steward acknowledges support request (status submitted -> active)
    """
    from records.models import Record
    from django.utils import timezone
    from django.shortcuts import get_object_or_404
    from django.http import HttpResponse
    from django.urls import reverse

    if request.method != 'POST':
        return HttpResponse('')

    record = get_object_or_404(
        Record,
        id=record_id,
        record_family='community',
        record_type='support_request',
        status='submitted',
        deleted_at__isnull=True,
    )

    custom = dict(record.custom_fields)
    custom['acknowledged_at'] = timezone.now().isoformat()
    custom['assigned_steward_id'] = str(request.user.id)
    record.custom_fields = custom
    record.status = 'active'
    record.save()
    
    response = HttpResponse(status=204)
    response['HX-Redirect'] = reverse('steward_support')
    return response


@require_sceptre_steward
def htmx_sceptre_resolve_support_request(request, record_id):
    """
    POST → steward resolves support request (status active -> completed)
    """
    from records.models import Record
    from django.utils import timezone
    from django.shortcuts import get_object_or_404
    from django.http import HttpResponse
    from django.urls import reverse

    if request.method != 'POST':
        return HttpResponse('')

    record = get_object_or_404(
        Record,
        id=record_id,
        record_family='community',
        record_type='support_request',
        status='active',
        deleted_at__isnull=True,
    )

    custom = dict(record.custom_fields)
    custom['resolved_at'] = timezone.now().isoformat()
    record.custom_fields = custom
    record.status = 'completed'
    record.save()

    response = HttpResponse(status=204)
    response['HX-Redirect'] = reverse('steward_support')
    return response


# ---------------------------------------------------------------------------
# Tenant switcher — Prime Tenancy stewards only
# ---------------------------------------------------------------------------

from django.contrib.auth.decorators import login_required

@login_required
def switch_tenant(request):
    """Accept ?tenant=<slug> from app.ichebo.org community page and store it
    in the session so all sceptre views render in the context of that tenant.
    Only honoured for users who have oversight of the requested tenant.

    GET  ?tenant=<slug>  → set session, redirect to home
    GET  ?tenant=clear   → clear override, redirect to home
    """
    from tenants.models import Tenant
    from tenants.service import get_oversight_tenant_ids

    slug = request.GET.get('tenant', '').strip()

    if slug == 'clear':
        request.session.pop('sceptre_tenant_slug', None)
        return redirect('home')

    if slug:
        try:
            candidate = Tenant.objects.get(slug=slug, status='active')
            oversight_ids = get_oversight_tenant_ids(request.user)
            if candidate.id in oversight_ids:
                request.session['sceptre_tenant_slug'] = slug
        except Tenant.DoesNotExist:
            pass

    return redirect('home')
