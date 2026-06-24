# learn/views.py — Django template views + HTMX partial views
import json

from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from records.models import Record, Relationship
from activity.models import Activity
from governance.services import get_linked_records


def _user_level(user):
    return getattr(user, 'competence_level', 0)


# ── My Learning home ─────────────────────────────────────────────────────────

@login_required
def my_learning(request):
    user = request.user
    level = _user_level(user)

    enrolments = Activity.objects.filter(
        activity_type='programme',
        assigned_to=user,
        status__in=['pending', 'in_progress'],
    ).order_by('-created_at')

    certifications = Record.objects.filter(
        record_type='certification',
        created_by=user,
        status='active',
        deleted_at__isnull=True,
    ).order_by('-updated_at')

    pending_certifications = Record.objects.filter(
        record_type='certification',
        created_by=user,
        status='draft',
        deleted_at__isnull=True,
    ).order_by('-created_at')

    # Pathway banner: derive from first active enrolment
    active_pathway = None
    active_qualification = None
    if enrolments.exists():
        first = enrolments.first()
        prog_id = (first.metadata or {}).get('programme_record_id')
        if prog_id:
            try:
                prog = Record.objects.get(id=prog_id)
                pathways = (prog.custom_fields or {}).get('kgs_pathways', [])
                active_pathway = pathways[0] if pathways else None
                active_qualification = (prog.custom_fields or {}).get('kgs_qualification', prog.title)
            except Record.DoesNotExist:
                pass

    return render(request, 'learn/my_learning.html', {
        'enrolments': enrolments,
        'certifications': certifications,
        'pending_certifications': pending_certifications,
        'active_pathway': active_pathway,
        'active_qualification': active_qualification,
        'user_level': level,
        'active_app': 'formation',
        'ws_page_title': 'Learn',
    })


# ── Programme Catalogue ───────────────────────────────────────────────────────

@login_required
def catalogue(request):
    user_level = _user_level(request.user)
    programmes = sorted(
        Record.objects.filter(
            record_family='learning',
            record_type__in=['programme', 'induction'],
            status='active',
            deleted_at__isnull=True,
        ),
        key=lambda p: p.permissions_data.get('required_level', 1)
    )

    for p in programmes:
        p.is_locked = user_level < (p.permissions_data.get('required_level', 1))

    return render(request, 'learn/catalogue.html', {
        'programmes': programmes,
        'user_level': user_level,
        'active_app': 'formation',
        'ws_page_title': 'Learn',
    })


# ── Programme Detail ──────────────────────────────────────────────────────────

@login_required
def programme_detail(request, programme_id):
    user = request.user
    user_level = _user_level(user)

    programme = get_object_or_404(
        Record, id=programme_id,
        record_family='learning', record_type__in=['programme', 'induction'],
        status__in=['active', 'locked']
    )

    required_level = programme.permissions_data.get('required_level', 1)
    if user_level < required_level:
        return render(request, 'learn/locked.html', {'programme': programme})

    course_ids = Relationship.objects.filter(
        to_record_id=programme_id,
        relationship_type='part_of'
    ).values_list('from_record_id', flat=True)

    is_author = _user_level(user) >= 4
    visible_statuses = ['active', 'locked', 'draft', 'submitted'] if is_author else ['active', 'locked']

    courses = Record.objects.filter(
        id__in=course_ids, record_type='course',
        status__in=visible_statuses
    ).order_by('created_at')

    curriculum = []
    for course in courses:
        lesson_ids = Relationship.objects.filter(
            to_record_id=course.id, relationship_type='part_of'
        ).values_list('from_record_id', flat=True)
        lessons = Record.objects.filter(
            id__in=lesson_ids,
            record_type__in=['lesson', 'assignment', 'quiz'],
            status__in=visible_statuses
        ).order_by('created_at')
        curriculum.append({'course': course, 'lessons': list(lessons)})

    already_enrolled = Activity.objects.filter(
        activity_type='programme',
        assigned_to=user,
        metadata__programme_record_id=str(programme_id)
    ).exists()

    is_author = user_level >= 4
    is_owner = is_author and programme.created_by_id == user.id
    can_delete = (user_level >= 5) or (is_owner and programme.status in ('draft', 'submitted'))

    return render(request, 'learn/programme_detail.html', {
        'programme': programme,
        'curriculum': curriculum,
        'already_enrolled': already_enrolled,
        'is_author': is_author,
        'is_owner': is_owner,
        'can_delete': can_delete,
    })


# ── Course Detail ─────────────────────────────────────────────────────────────

@login_required
def course_detail(request, course_id):
    is_author = _user_level(request.user) >= 4
    visible_statuses = ['active', 'locked', 'draft', 'submitted'] if is_author else ['active', 'locked']

    course = get_object_or_404(
        Record, id=course_id,
        record_type='course',
        status__in=visible_statuses
    )

    lesson_ids = Relationship.objects.filter(
        to_record_id=course_id, relationship_type='part_of'
    ).values_list('from_record_id', flat=True)

    lessons = Record.objects.filter(
        id__in=lesson_ids,
        record_type__in=['lesson', 'assignment', 'quiz'],
        status__in=visible_statuses
    ).order_by('created_at')

    # Resolve parent programme via relationship
    programme_rel = Relationship.objects.filter(
        from_record_id=course_id, relationship_type='part_of',
    ).select_related('to_record').first()
    programme = programme_rel.to_record if programme_rel else None

    user_level = _user_level(request.user)
    is_author = user_level >= 4
    is_owner = is_author and course.created_by_id == request.user.id
    can_delete = (user_level >= 5) or (is_owner and course.status in ('draft', 'submitted'))

    return render(request, 'learn/course_detail.html', {
        'course': course,
        'lessons': lessons,
        'programme': programme,
        'is_author': is_author,
        'is_owner': is_owner,
        'can_delete': can_delete,
        'ws_page_title': 'Learn',
    })


# ── Lesson Viewer ─────────────────────────────────────────────────────────────

@login_required
def lesson_viewer(request, lesson_id):
    lesson = get_object_or_404(
        Record, id=lesson_id,
        record_type__in=['lesson', 'assignment', 'quiz'],
        status__in=['active', 'locked']
    )

    parent_rel = Relationship.objects.filter(
        from_record_id=lesson_id, relationship_type='part_of'
    ).first()
    course = None
    programme = None
    siblings = []
    if parent_rel:
        course = Record.objects.filter(id=parent_rel.to_record_id).first()
        if course:
            sibling_ids = Relationship.objects.filter(
                to_record_id=course.id, relationship_type='part_of'
            ).values_list('from_record_id', flat=True)
            siblings = list(Record.objects.filter(
                id__in=sibling_ids,
                status__in=['active', 'locked']
            ).order_by('created_at'))
            # Resolve the parent programme for the back link
            prog_rel = Relationship.objects.filter(
                from_record_id=course.id, relationship_type='part_of'
            ).first()
            if prog_rel:
                programme = Record.objects.filter(
                    id=prog_rel.to_record_id, record_type='programme'
                ).first()

    current_index = next((i for i, s in enumerate(siblings) if s.id == lesson.id), 0)
    prev_lesson = siblings[current_index - 1] if current_index > 0 else None
    next_lesson = siblings[current_index + 1] if current_index < len(siblings) - 1 else None

    # Check if already completed via the task Activity tree
    is_completed = Activity.objects.filter(
        assigned_to=request.user,
        activity_type='task',
        status='completed',
        linked_record_id=lesson_id,
    ).exists()

    from core.utils.video import get_embed_url, get_video_type
    raw_video_url = (lesson.custom_fields or {}).get('video_url', '')
    embed_url = get_embed_url(raw_video_url) if raw_video_url else None
    video_type = get_video_type(raw_video_url) if raw_video_url else None

    user_level = _user_level(request.user)
    is_author = user_level >= 4
    is_owner = is_author and lesson.created_by_id == request.user.id
    can_delete = (user_level >= 5) or (is_owner and lesson.status in ('draft', 'submitted'))

    return render(request, 'learn/lesson_viewer.html', {
        'lesson': lesson,
        'course': course,
        'programme': programme,
        'siblings': siblings,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'is_completed': is_completed,
        'video_url': raw_video_url,
        'embed_url': embed_url,
        'video_type': video_type,
        'is_author': is_author,
        'is_owner': is_owner,
        'can_delete': can_delete,
    })


# ── Certification Queue (steward view) ────────────────────────────────────────

@login_required
def certification_queue_view(request):
    if _user_level(request.user) < 3:
        return redirect('learn:learn-home')

    certifications = Record.objects.filter(
        record_type='certification',
        status='draft',
        deleted_at__isnull=True,
    ).order_by('created_at')

    return render(request, 'learn/certification_queue.html', {
        'certifications': certifications,
        'active_app': 'formation',
        'ws_page_title': 'Learn',
    })


# ── Authorship (Level 4+) ─────────────────────────────────────────────────────

@login_required
def authorship(request):
    if _user_level(request.user) < 4:
        return redirect('learn:learn-home')

    # Get user's in-progress and approved records
    user_records = Record.objects.filter(
        created_by=request.user,
        record_family='learning',
        status__in=['draft', 'submitted', 'approved'],
        deleted_at__isnull=True,
    ).order_by('-updated_at')

    # Organize by type
    by_type = {}
    for record in user_records:
        rtype = record.record_type
        if rtype not in by_type:
            by_type[rtype] = {'draft': [], 'submitted': [], 'approved': []}
        by_type[rtype][record.status].append(record)

    return render(request, 'learn/authorship.html', {
        'user_records': user_records,
        'by_type': by_type,
        'active_app': 'formation',
        'ws_page_title': 'Learn',
    })


@login_required
def programme_manage(request, record_id):
    user = request.user
    user_level = _user_level(user)
    if user_level < 4:
        return redirect('learn:learn-home')

    record = get_object_or_404(
        Record, id=record_id,
        record_family='learning', record_type__in=['programme', 'induction'],
        deleted_at__isnull=True,
    )
    is_owner = record.created_by_id == user.id
    if user_level < 5 and not is_owner:
        return redirect('learn:learn-home')

    can_delete = (user_level >= 5) or (is_owner and record.status in ('draft', 'submitted', 'approved'))

    # Build course+lesson tree
    course_ids = Relationship.objects.filter(
        to_record_id=record_id, relationship_type='part_of'
    ).values_list('from_record_id', flat=True)
    courses = Record.objects.filter(
        id__in=course_ids, record_type='course', deleted_at__isnull=True
    ).order_by('created_at')
    curriculum = []
    for course in courses:
        lesson_ids = Relationship.objects.filter(
            to_record_id=course.id, relationship_type='part_of'
        ).values_list('from_record_id', flat=True)
        lessons = Record.objects.filter(
            id__in=lesson_ids,
            record_type__in=['lesson', 'assignment', 'quiz'],
            deleted_at__isnull=True,
        ).order_by('created_at')
        curriculum.append({'course': course, 'lessons': list(lessons)})

    return render(request, 'learn/programme_manage.html', {
        'record': record,
        'curriculum': curriculum,
        'can_delete': can_delete,
        'is_owner': is_owner,
        'user_level': user_level,
    })


@login_required
def course_manage(request, record_id):
    user = request.user
    user_level = _user_level(user)
    if user_level < 4:
        return redirect('learn:learn-home')

    record = get_object_or_404(
        Record, id=record_id, record_type='course', deleted_at__isnull=True
    )
    is_owner = record.created_by_id == user.id
    if user_level < 5 and not is_owner:
        return redirect('learn:learn-home')

    can_delete = (user_level >= 5) or (is_owner and record.status in ('draft', 'submitted', 'approved'))

    lesson_ids = Relationship.objects.filter(
        to_record_id=record_id, relationship_type='part_of'
    ).values_list('from_record_id', flat=True)
    lessons = Record.objects.filter(
        id__in=lesson_ids,
        record_type__in=['lesson', 'assignment', 'quiz'],
        deleted_at__isnull=True,
    ).order_by('created_at')

    programme_rel = Relationship.objects.filter(
        from_record_id=record_id, relationship_type='part_of'
    ).select_related('to_record').first()
    programme = programme_rel.to_record if programme_rel else None

    return render(request, 'learn/course_manage.html', {
        'record': record,
        'lessons': list(lessons),
        'programme': programme,
        'can_delete': can_delete,
        'is_owner': is_owner,
        'user_level': user_level,
    })


@login_required
def author_programme_form(request, record_id=None):
    if _user_level(request.user) < 4:
        return redirect('learn:learn-home')

    record = None
    if record_id:
        record = get_object_or_404(
            Record, id=record_id, created_by=request.user, deleted_at__isnull=True
        )

    if request.method == 'POST':
        # Check if this is a submit action (not just save)
        is_submit = request.POST.get('action') == 'submit'

        # 'induction' type is only available to Level 5 (Architect)
        raw_type = request.POST.get('programme_type', 'programme')
        if raw_type == 'induction' and _user_level(request.user) < 5:
            raw_type = 'programme'
        programme_type = raw_type if raw_type in ('programme', 'induction') else 'programme'

        if record:
            record.title = request.POST.get('title', '').strip()
            record.content = request.POST.get('description', '').strip()
            record.record_type = programme_type
            meta = record.metadata or {}
            meta.update({
                'qualification': request.POST.get('qualification', ''),
                'duration_years': request.POST.get('duration_years', ''),
                'pathways': request.POST.get('pathways', ''),
            })
            record.metadata = meta
            cf = record.custom_fields or {}
            cf['start_date'] = request.POST.get('start_date', '').strip()
            cf['end_date'] = request.POST.get('end_date', '').strip()
            record.custom_fields = cf
            if is_submit:
                record.status = 'submitted'
                # Associate with Handbook when submitted
                from tenants.models import Tenant
                try:
                    handbook = Tenant.objects.get(path='/global/handbook/', tier='handbook')
                    record.tenant = handbook
                except Tenant.DoesNotExist:
                    pass
            record.save(update_fields=['title', 'content', 'record_type', 'metadata', 'custom_fields', 'updated_at', 'status', 'tenant'])
        else:
            status = 'submitted' if is_submit else 'draft'
            tenant_id = None
            if is_submit:
                from tenants.models import Tenant
                try:
                    handbook = Tenant.objects.get(path='/global/handbook/', tier='handbook')
                    tenant_id = handbook.id
                except Tenant.DoesNotExist:
                    pass

            Record.objects.create(
                created_by=request.user,
                tenant_id=tenant_id,
                record_class='organizational',
                record_family='learning',
                record_type=programme_type,
                origin='user',
                title=request.POST.get('title', '').strip(),
                content=request.POST.get('description', '').strip(),
                status=status,
                metadata={
                    'source_app': 'learn',
                    'qualification': request.POST.get('qualification', ''),
                    'duration_years': request.POST.get('duration_years', ''),
                    'pathways': request.POST.get('pathways', ''),
                },
                custom_fields={
                    'start_date': request.POST.get('start_date', '').strip(),
                    'end_date': request.POST.get('end_date', '').strip(),
                },
                permissions_data={
                    'visibility': 'tenant',
                    'required_level': int(request.POST.get('required_level', 1)),
                    'roles_allowed': [],
                    'can_edit': [],
                }
            )
        return redirect('learn:learn-author')

    return render(request, 'learn/author_programme_form.html', {
        'record': record,
        'can_create_induction': _user_level(request.user) >= 5,
    })


@login_required
def author_course_form(request, record_id=None):
    if _user_level(request.user) < 4:
        return redirect('learn:learn-home')

    record = None
    if record_id:
        record = get_object_or_404(
            Record, id=record_id, created_by=request.user, deleted_at__isnull=True
        )

    programmes = Record.objects.filter(
        record_family='learning', record_type='programme',
        status__in=['active', 'draft', 'submitted']
    )

    if request.method == 'POST':
        is_submit = request.POST.get('action') == 'submit'

        if record:
            record.title = request.POST.get('title', '').strip()
            record.content = request.POST.get('description', '').strip()
            cf = record.custom_fields or {}
            cf['start_date'] = request.POST.get('start_date', '').strip()
            cf['end_date'] = request.POST.get('end_date', '').strip()
            record.custom_fields = cf
            if is_submit:
                record.status = 'submitted'
                from tenants.models import Tenant
                try:
                    handbook = Tenant.objects.get(path='/global/handbook/', tier='handbook')
                    record.tenant = handbook
                except Tenant.DoesNotExist:
                    pass
            record.save(update_fields=['title', 'content', 'custom_fields', 'updated_at', 'status', 'tenant'])
        else:
            status = 'submitted' if is_submit else 'draft'
            tenant_id = None
            if is_submit:
                from tenants.models import Tenant
                try:
                    handbook = Tenant.objects.get(path='/global/handbook/', tier='handbook')
                    tenant_id = handbook.id
                except Tenant.DoesNotExist:
                    pass

            course = Record.objects.create(
                created_by=request.user,
                tenant_id=tenant_id,
                record_class='organizational',
                record_family='learning',
                record_type='course',
                origin='user',
                title=request.POST.get('title', '').strip(),
                content=request.POST.get('description', '').strip(),
                status=status,
                metadata={'source_app': 'learn'},
                custom_fields={
                    'start_date': request.POST.get('start_date', '').strip(),
                    'end_date': request.POST.get('end_date', '').strip(),
                },
                permissions_data={'visibility': 'tenant', 'required_level': 1,
                                  'roles_allowed': [], 'can_edit': []},
            )
            prog_id = request.POST.get('programme_id')
            if prog_id:
                Relationship.objects.create(
                    created_by=request.user,
                    from_record=course,
                    to_record_id=prog_id,
                    relationship_type='part_of',
                    direction='directed',
                )
        return redirect('learn:learn-author')

    return render(request, 'learn/author_course_form.html', {
        'programmes': programmes,
        'record': record,
    })


@login_required
def author_lesson_form(request, record_id=None):
    if _user_level(request.user) < 4:
        return redirect('learn:learn-home')

    record = None
    if record_id:
        record = get_object_or_404(
            Record, id=record_id, created_by=request.user, deleted_at__isnull=True
        )

    courses = Record.objects.filter(
        record_family='learning', record_type='course',
        status__in=['active', 'draft']
    )

    if request.method == 'POST':
        video_url = request.POST.get('video_url', '').strip()
        is_submit = request.POST.get('action') == 'submit'

        if record:
            record.title = request.POST.get('title', '').strip()
            record.content = request.POST.get('content', '').strip()
            custom = record.custom_fields or {}
            if video_url:
                custom['video_url'] = video_url
            elif 'video_url' in custom:
                del custom['video_url']
            record.custom_fields = custom
            if is_submit and record.status == 'draft':
                record.status = 'submitted'
            record.save(update_fields=['title', 'content', 'custom_fields', 'status', 'updated_at'])
        else:
            custom_fields = {'video_url': video_url} if video_url else {}
            status = 'submitted' if is_submit else 'draft'
            lesson = Record.objects.create(
                created_by=request.user,
                record_class='organizational',
                record_family='learning',
                record_type=request.POST.get('record_type', 'lesson'),
                origin='user',
                title=request.POST.get('title', '').strip(),
                content=request.POST.get('content', '').strip(),
                status=status,
                custom_fields=custom_fields,
                metadata={'source_app': 'learn'},
                permissions_data={'visibility': 'tenant', 'required_level': 1,
                                  'roles_allowed': [], 'can_edit': []},
            )
            course_id = request.POST.get('course_id')
            if course_id:
                Relationship.objects.create(
                    created_by=request.user,
                    from_record=lesson,
                    to_record_id=course_id,
                    relationship_type='part_of',
                    direction='directed',
                )
        return redirect('learn:learn-author')

    return render(request, 'learn/author_lesson_form.html', {
        'courses': courses,
        'record': record,
        'media_engine_public_url': settings.MEDIA_ENGINE_PUBLIC_URL,
    })


# ── Handbook Review Queue (Level 5) ──────────────────────────────────────────

@login_required
def htmx_author_delete(request, record_id):
    if _user_level(request.user) < 4:
        return HttpResponse('', status=403)
    if request.method != 'POST':
        return HttpResponse('', status=405)

    user_level = _user_level(request.user)
    if user_level >= 5:
        # Architects can delete any learning record regardless of owner or status
        record = get_object_or_404(
            Record,
            id=record_id,
            record_family='learning',
            deleted_at__isnull=True,
        )
    else:
        # Level 4 authors can only delete their own draft/submitted records
        record = get_object_or_404(
            Record,
            id=record_id,
            created_by=request.user,
            record_family='learning',
            status__in=['draft', 'submitted'],
            deleted_at__isnull=True,
        )
    record.soft_delete()
    response = HttpResponse('', status=200)
    response['HX-Redirect'] = '/learn/author/'
    return response


@login_required
def review_queue(request):
    if _user_level(request.user) < 5:
        return redirect('learn:learn-home')

    items = Record.objects.filter(
        record_family='learning',
        status='submitted',
        deleted_at__isnull=True,
    ).order_by('-updated_at')  # Most recent first

    # Enrich items with author info and parent programme (for courses/lessons)
    for item in items:
        item.author_display = item.created_by.display_name or item.created_by.email

        # For courses, get parent programme
        if item.record_type == 'course':
            parent_rel = Relationship.objects.filter(
                from_record_id=item.id, relationship_type='part_of'
            ).first()
            if parent_rel:
                item.parent_programme = Record.objects.filter(id=parent_rel.to_record_id).first()

    return render(request, 'learn/review_queue.html', {
        'items': items,
        'active_app': 'formation',
        'ws_page_title': 'Learn',
    })


# ── G4 — Induction Review Queue (Level 5) ────────────────────────────────────

@login_required
def induction_review_queue(request):
    if _user_level(request.user) < 5:
        return redirect('learn:learn-home')

    from django.contrib.auth import get_user_model
    from tenants.models import UserPermission, Tenant
    User = get_user_model()

    # All users currently in the Induction Tenant
    induction_perm_ids = UserPermission.objects.filter(
        tenant__tier='induction',
        is_active=True,
    ).values_list('user_id', flat=True)

    inductees = User.objects.filter(id__in=induction_perm_ids).order_by('induction_enrolled_at')

    # Attach progress data to each inductee
    induction_programme = Record.objects.filter(
        record_family='learning',
        record_type='induction',
        status='active',
        origin='system',
        deleted_at__isnull=True,
    ).first()

    for inductee in inductees:
        enrolment = Activity.objects.filter(
            activity_type='programme',
            assigned_to=inductee,
            linked_record=induction_programme,
            deleted_at__isnull=True,
        ).first() if induction_programme else None

        inductee.enrolment = enrolment
        inductee.progress = enrolment.progress if enrolment else 0
        inductee.enrolment_status = enrolment.status if enrolment else 'not_enrolled'

        # Count completed lessons
        if enrolment:
            total = Activity.objects.filter(
                activity_type='task',
                assigned_to=inductee,
                parent_activity__parent_activity=enrolment,
                deleted_at__isnull=True,
            ).count()
            done = Activity.objects.filter(
                activity_type='task',
                assigned_to=inductee,
                parent_activity__parent_activity=enrolment,
                status='completed',
                deleted_at__isnull=True,
            ).count()
            inductee.lessons_done = done
            inductee.lessons_total = total
        else:
            inductee.lessons_done = 0
            inductee.lessons_total = 0

        # Check if already has a pending induction cert
        inductee.cert_pending = Record.objects.filter(
            record_type='certification',
            status='draft',
            metadata__context='induction_completion',
            metadata__learner_id=str(inductee.id),
            deleted_at__isnull=True,
        ).first()

    placement_tenants = Tenant.objects.filter(
        status='active',
    ).exclude(tier__in=['induction', 'handbook']).order_by('name')

    return render(request, 'learn/induction_review_queue.html', {
        'inductees': inductees,
        'placement_tenants': placement_tenants,
        'induction_programme': induction_programme,
        'active_app': 'formation',
        'ws_page_title': 'Learn',
    })


@login_required
def htmx_induction_confirm_prompt(request, user_id):
    """HTMX GET: return inline confirmation prompt partial for induction."""
    import json
    from django.contrib.auth import get_user_model
    from tenants.models import Tenant
    User = get_user_model()

    if _user_level(request.user) < 5:
        return HttpResponse(status=403)

    learner = get_object_or_404(User, id=user_id)
    profile = getattr(learner, 'profile', None)
    name = (profile.full_name if profile else None) or getattr(learner, 'display_name', None) or learner.email

    placement_tenant_id = request.GET.get('placement_tenant_id', '').strip() or None
    placement_tenant = None
    if placement_tenant_id:
        placement_tenant = Tenant.objects.filter(id=placement_tenant_id).first()

    class _Obj:
        pass
    inductee = _Obj()
    inductee.id = user_id

    return render(request, 'learn/partials/induction_confirm_prompt.html', {
        'inductee': inductee,
        'name': name,
        'placement_tenant': placement_tenant,
    })


@login_required
def htmx_induction_confirm(request, user_id):
    """HTMX POST: steward confirms induction completion → advances learner to Level 1."""
    import json
    if request.method != 'POST':
        return HttpResponse(status=405)

    if _user_level(request.user) < 5:
        return HttpResponse('<p class="form-error">Permission denied.</p>', status=403)

    from django.contrib.auth import get_user_model
    from tenants.models import Tenant
    from .services import confirm_certification_record, CertificationError
    User = get_user_model()

    learner = get_object_or_404(User, id=user_id)
    notes = request.POST.get('notes', '').strip()
    placement_tenant_id = request.POST.get('placement_tenant_id', '').strip() or None

    # Find or create the induction certification record for this learner
    cert = Record.objects.filter(
        record_type='certification',
        status='draft',
        metadata__context='induction_completion',
        metadata__learner_id=str(learner.id),
        deleted_at__isnull=True,
    ).first()

    if not cert:
        cert = Record.objects.create(
            created_by=request.user,
            tenant=None,
            record_class='organizational',
            record_family='learning',
            record_type='certification',
            origin='system',
            title=f'Induction Completion — {learner.display_name or learner.email}',
            summary=f'Induction programme completed by {learner.email}. Confirmed by steward.',
            status='draft',
            metadata={
                'context': 'induction_completion',
                'learner_id': str(learner.id),
                'target_level': 1,
                'source_app': 'learn',
            },
            permissions_data={
                'required_level': 5,
                'visibility': 'steward',
            },
        )

    try:
        confirmation = confirm_certification_record(
            cert_record=cert,
            confirmed_by=request.user,
            notes=notes,
            placement_tenant_id=placement_tenant_id,
        )
    except CertificationError as exc:
        resp = HttpResponse(
            f'<div id="inductee-{user_id}"'
            f' style="background:var(--card);border:1px solid var(--border);border-radius:12px;'
            f'padding:22px 24px;display:flex;align-items:center;gap:12px;">'
            f'<span class="material-symbols-outlined" style="color:#e53e3e;font-size:20px;">error</span>'
            f'<div style="font-size:13px;color:var(--text);">{exc}</div>'
            f'</div>',
            status=400,
        )
        resp['X-WS-Toast'] = json.dumps([{'level': 'error', 'message': str(exc)}])
        return resp

    profile = getattr(learner, 'profile', None)
    name = (profile.full_name if profile else None) or getattr(learner, 'display_name', None) or learner.email
    resp = HttpResponse(
        f'<div id="inductee-{user_id}"'
        f' style="background:var(--card);border:1px solid var(--border);border-radius:12px;'
        f'padding:22px 24px;display:flex;align-items:center;gap:14px;">'
        f'<span class="material-symbols-outlined" style="color:var(--primary);font-size:28px;">verified</span>'
        f'<div>'
        f'<div style="font-size:14px;font-weight:700;color:var(--text);margin-bottom:4px;">{name}</div>'
        f'<div style="font-size:12px;color:var(--muted);">'
        f'Confirmed · Level {confirmation.previous_competence_level} → Level {confirmation.new_competence_level}'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    resp['X-WS-Toast'] = json.dumps([{
        'level': 'success',
        'message': f'{name} advanced to Level {confirmation.new_competence_level}.',
    }])
    return resp


# ── HTMX Partial Views ────────────────────────────────────────────────────────

def _recalculate_programme_progress(user, lesson_id):
    """Recalculate and persist a programme Activity's progress after a lesson is completed."""
    # lesson → course
    course_rel = Relationship.objects.filter(
        from_record_id=lesson_id, relationship_type='part_of'
    ).first()
    if not course_rel:
        return

    # course → programme
    prog_rel = Relationship.objects.filter(
        from_record_id=course_rel.to_record_id, relationship_type='part_of'
    ).first()
    if not prog_rel:
        return

    programme_id = prog_rel.to_record_id

    # all courses in this programme
    course_ids = list(Relationship.objects.filter(
        to_record_id=programme_id, relationship_type='part_of'
    ).values_list('from_record_id', flat=True))
    if not course_ids:
        return

    # all lesson records across those courses
    lesson_ids = {
        str(lid) for lid in Relationship.objects.filter(
            to_record_id__in=course_ids, relationship_type='part_of'
        ).values_list('from_record_id', flat=True)
    }
    if not lesson_ids:
        return

    # completed lesson Activities for this user in this programme
    completed_ids = set(
        Activity.objects.filter(
            assigned_to=user,
            activity_type='lesson',
            status='completed',
        ).values_list('metadata__lesson_record_id', flat=True)
    )
    completed_count = len(lesson_ids & completed_ids)
    progress = int((completed_count / len(lesson_ids)) * 100)

    # Use .save() (not .update()) so post_save signals fire — the
    # auto-certification signal depends on seeing the updated progress value.
    programme_activity = Activity.objects.filter(
        activity_type='programme',
        assigned_to=user,
        metadata__programme_record_id=str(programme_id),
    ).first()
    if programme_activity:
        programme_activity.progress = progress
        if progress >= 100:
            programme_activity.status = 'completed'
        programme_activity.save(update_fields=['progress', 'status'])


@login_required
def htmx_enrol(request, programme_id):
    """HTMX POST: creates enrolment Activity tree, returns confirmation fragment."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    from .services import enrol_in_programme, EnrolmentError

    programme = get_object_or_404(Record, id=programme_id, record_type='programme')

    try:
        enrol_in_programme(request.user, programme)
    except EnrolmentError as exc:
        already = 'already enrolled' in str(exc).lower()
        if already:
            return HttpResponse(
                '<div style="display:inline-flex;align-items:center;gap:8px;padding:10px 20px;'
                'background:#e8f5e9;border:1px solid #a5d6a7;border-radius:8px;'
                'font-size:13px;font-weight:700;color:#2e7d32;">'
                '<span class="material-symbols-outlined" style="font-size:18px;">check_circle</span>'
                'Active Enrolment'
                '</div>'
            )
        resp = HttpResponse(status=400)
        resp['X-WS-Toast'] = json.dumps([{'level': 'error', 'message': str(exc)}])
        return resp

    return HttpResponse(
        '<div class="status-badge status-badge--active" style="display:inline-flex;align-items:center;gap:8px;padding:10px 20px;">'
        '<span class="material-symbols-outlined" style="font-size:18px;">check_circle</span>'
        'Enrolled ✓'
        '</div>'
    )


@login_required
def htmx_complete_lesson(request, lesson_id):
    """HTMX POST: marks lesson task Activity complete, recalculates programme progress."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    from .services import complete_lesson, EnrolmentError

    task_activity = Activity.objects.filter(
        activity_type='task',
        assigned_to=request.user,
        linked_record_id=lesson_id,
        deleted_at__isnull=True,
    ).first()

    if not task_activity:
        resp = HttpResponse(status=204)
        resp['X-WS-Toast'] = json.dumps([{
            'level': 'warning',
            'message': 'Enrol in this programme first to track your progress.',
        }])
        return resp

    try:
        complete_lesson(request.user, task_activity)
    except EnrolmentError as exc:
        resp = HttpResponse(status=400)
        resp['X-WS-Toast'] = json.dumps([{'level': 'error', 'message': str(exc)}])
        return resp

    resp = HttpResponse(
        '<div style="display:inline-flex;align-items:center;gap:8px;padding:10px 20px;'
        'background:#e8f5e9;border:1px solid #a5d6a7;border-radius:8px;'
        'font-size:13px;font-weight:700;color:#2e7d32;">'
        '<span class="material-symbols-outlined" style="font-size:18px;">check_circle</span>'
        'Completed'
        '</div>'
    )
    resp['X-WS-Toast'] = json.dumps([{'level': 'success', 'message': 'Lesson marked complete!'}])
    return resp


@login_required
def htmx_submit_assessment(request, lesson_id):
    """HTMX POST: saves quiz/assignment submission, then marks lesson complete."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    from .services import complete_lesson, EnrolmentError

    task_activity = Activity.objects.filter(
        activity_type='task',
        assigned_to=request.user,
        linked_record_id=lesson_id,
        deleted_at__isnull=True,
    ).first()

    if not task_activity:
        resp = HttpResponse(status=204)
        resp['X-WS-Toast'] = json.dumps([{
            'level': 'warning',
            'message': 'Enrol in this programme first to submit.',
        }])
        return resp

    # Collect submission: single textarea (assignment) or multiple q_* fields (quiz)
    submission_data = {}
    for key, value in request.POST.items():
        if key.startswith('q_') or key == 'submission':
            submission_data[key] = value

    # Persist to task Activity metadata
    meta = task_activity.metadata or {}
    meta['submission'] = submission_data
    task_activity.metadata = meta
    task_activity.save(update_fields=['metadata'])

    try:
        complete_lesson(request.user, task_activity)
    except EnrolmentError as exc:
        resp = HttpResponse(status=400)
        resp['X-WS-Toast'] = json.dumps([{'level': 'error', 'message': str(exc)}])
        return resp

    resp = HttpResponse(
        '<div style="display:inline-flex;align-items:center;gap:8px;padding:10px 20px;'
        'background:#e8f5e9;border:1px solid #a5d6a7;border-radius:8px;'
        'font-size:13px;font-weight:700;color:#2e7d32;">'
        '<span class="material-symbols-outlined" style="font-size:18px;">check_circle</span>'
        'Submitted &amp; Completed'
        '</div>'
    )
    resp['X-WS-Toast'] = json.dumps([{'level': 'success', 'message': 'Submission received and lesson complete!'}])
    return resp


@login_required
def htmx_confirm_cert(request, cert_id):
    """HTMX POST: steward confirms certification, advances competence_level."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    from .services import confirm_certification_record, CertificationError

    if _user_level(request.user) < 3:
        return HttpResponse('<div class="cert-card">Permission denied.</div>', status=403)

    cert = get_object_or_404(Record, id=cert_id, record_type='certification', status='draft')

    try:
        confirmation = confirm_certification_record(
            cert_record=cert,
            confirmed_by=request.user,
            notes=request.POST.get('notes', ''),
        )
    except CertificationError as exc:
        return HttpResponse(
            f'<div class="cert-card"><p class="form-error">{exc}</p></div>',
            status=400,
        )

    prev = confirmation.previous_competence_level
    new = confirmation.new_competence_level
    return HttpResponse(
        f'<div class="cert-card confirmed">'
        f'<span class="enrolled-badge">✓ Confirmed — Level {prev} → {new}</span>'
        f'</div>'
    )


@login_required
def htmx_approve_content(request, record_id):
    """HTMX POST: Level 5 approves submitted content → status becomes 'approved', author notified."""
    if request.method != 'POST':
        return HttpResponse(status=405)
    if _user_level(request.user) < 5:
        return HttpResponse('<p class="form-error">Permission denied.</p>', status=403)

    record = get_object_or_404(Record, id=record_id, status='submitted')
    record.status = 'approved'
    record.save(update_fields=['status', 'updated_at'])

    from notifications.signals import content_approved
    content_approved.send(sender=record.__class__, record=record, approved_by=request.user)

    html = f'''
    <div id="ws-review-{record.id}"
         style="background:var(--card);border:1px solid var(--border);border-radius:12px;
                padding:22px 24px;opacity:0.6;">
      <div style="display:flex;align-items:center;gap:12px;">
        <span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;
                     color:#16a34a;background:#dcfce7;padding:3px 8px;border-radius:4px;">
          {record.record_type.title()}
        </span>
        <span style="font-size:14px;font-weight:700;color:var(--text);">{record.title}</span>
      </div>
      <div style="margin-top:12px;display:flex;align-items:center;gap:8px;font-size:12px;
                  font-weight:700;color:#16a34a;">
        <span style="font-size:16px;" class="material-symbols-outlined">check_circle</span>
        Approved — author notified to publish
      </div>
    </div>
    '''
    return HttpResponse(html)


@login_required
def htmx_publish_content(request, record_id):
    """HTMX POST: publish approved content → status becomes 'active'.
    Level 4 owner of an approved record, or Level 5 for any record.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    user_level = _user_level(request.user)
    if user_level >= 5:
        # Level 5 can publish from submitted or approved
        record = get_object_or_404(
            Record, id=record_id,
            record_family='learning', status__in=['submitted', 'approved'],
            deleted_at__isnull=True,
        )
    elif user_level >= 4:
        # Level 4 author can only publish their own approved records
        record = get_object_or_404(
            Record, id=record_id,
            created_by=request.user,
            record_family='learning', status='approved',
            deleted_at__isnull=True,
        )
    else:
        return HttpResponse('', status=403)

    record.status = 'active'
    record.save(update_fields=['status', 'updated_at'])

    from notifications.signals import content_published
    content_published.send(sender=record.__class__, record=record, published_by=request.user)

    response = HttpResponse('', status=200)
    response['HX-Redirect'] = '/learn/author/'
    return response


@login_required
def htmx_return_content(request, record_id):
    """HTMX POST: Level 5 returns submitted content to draft."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    if _user_level(request.user) < 5:
        return HttpResponse(status=403)

    record = get_object_or_404(Record, id=record_id, status='submitted')
    feedback = request.POST.get('feedback', '')

    # Store feedback in metadata if provided
    if feedback:
        meta = record.metadata or {}
        meta['review_feedback'] = feedback
        record.metadata = meta

    record.status = 'draft'
    record.save(update_fields=['status', 'updated_at', 'metadata'])

    # Return HTMX fragment that fades out
    html = f'''
    <div class="review-card" style="opacity: 0.5; background: var(--warning-light); border: 1px solid var(--warning); transition: all 0.3s ease;">
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 12px;">
          <span class="lesson-type-tag" style="padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; background: var(--warning-light); color: var(--warning);">
            {record.record_type.title()}
          </span>
          <h4 style="margin: 0; font-size: 14px; font-weight: 600;">{record.title}</h4>
        </div>
      </div>
      <div style="margin-top: 12px; padding: 8px 12px; background: var(--warning); color: #fff; border-radius: 4px; font-size: 12px; font-weight: 600;">
        ↶ Returned to Draft
      </div>
    </div>
    '''
    return HttpResponse(html)


# ── HTMX Data Partials (embed in other pages / lazy-load) ─────────────────────

@login_required
def htmx_my_learning(request):
    """HTMX GET: returns My Learning content fragment (enrolments + certs)."""
    user = request.user

    enrolments = Activity.objects.filter(
        activity_type='programme',
        assigned_to=user,
        status__in=['pending', 'in_progress'],
    ).order_by('-created_at')

    certifications = Record.objects.filter(
        record_type='certification',
        created_by=user,
        status='active',
        deleted_at__isnull=True,
    ).order_by('-updated_at')

    pending_certifications = Record.objects.filter(
        record_type='certification',
        created_by=user,
        status='draft',
        deleted_at__isnull=True,
    ).order_by('-created_at')

    return render(request, 'learn/partials/my_learning.html', {
        'enrolments': enrolments,
        'certifications': certifications,
        'pending_certifications': pending_certifications,
    })


@login_required
def htmx_catalogue(request):
    """HTMX GET: returns programme catalogue grid fragment."""
    user_level = _user_level(request.user)
    programmes = Record.objects.filter(
        record_family='learning',
        record_type='programme',
        status='active',
        deleted_at__isnull=True,
    ).order_by('created_at')

    for p in programmes:
        p.is_locked = user_level < (p.permissions_data.get('required_level', 1))

    return render(request, 'learn/partials/catalogue.html', {
        'programmes': programmes,
        'user_level': user_level,
    })


@login_required
def htmx_progress(request, programme_id):
    """HTMX GET: returns progress bar fragment for one programme enrolment."""
    activity = Activity.objects.filter(
        activity_type='programme',
        assigned_to=request.user,
        metadata__programme_record_id=str(programme_id),
    ).first()

    return render(request, 'learn/partials/progress.html', {
        'activity': activity,
        'programme_id': programme_id,
    })


@login_required
def htmx_cert_queue(request):
    """HTMX GET: returns certification queue fragment (Level 3+)."""
    if _user_level(request.user) < 3:
        return HttpResponse(
            '<p class="empty-state">Steward access required.</p>',
            status=403,
        )

    certifications = Record.objects.filter(
        record_type='certification',
        status='draft',
        deleted_at__isnull=True,
    ).order_by('created_at')

    return render(request, 'learn/partials/cert_queue.html', {
        'certifications': certifications,
    })


@login_required
def htmx_linked_records(request, record_id):
    """HTMX GET: returns linked records panel for a lesson or programme."""
    record = get_object_or_404(Record, id=record_id, deleted_at__isnull=True)
    grouped = get_linked_records(record_id)

    # Filter for learning context
    allowed_types = ['part_of', 'answers', 'fulfills', 'references', 'relates_to']
    relationship_types = [
        (val, label) for val, label in Relationship.RELATIONSHIP_TYPE_CHOICES 
        if val in allowed_types
    ]

    return render(request, '_linked_records_section.html', {
        'record': record,
        'grouped': grouped,
        'relationship_types': relationship_types,
        'can_add_link': True,
        'context': 'learning',
    })
