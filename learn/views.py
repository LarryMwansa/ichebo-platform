# learn/views.py — Django template views + HTMX partial views
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from records.models import Record, Relationship
from activity.models import Activity


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
        active_pathway = (first.metadata or {}).get('kgs_pathway', first.kgs_pathway)
        prog_id = (first.metadata or {}).get('programme_record_id')
        if prog_id:
            try:
                prog = Record.objects.get(id=prog_id)
                active_qualification = (prog.metadata or {}).get('qualification', prog.title)
            except Record.DoesNotExist:
                pass

    return render(request, 'learn/my_learning.html', {
        'enrolments': enrolments,
        'certifications': certifications,
        'pending_certifications': pending_certifications,
        'active_pathway': active_pathway,
        'active_qualification': active_qualification,
        'user_level': level,
    })


# ── Programme Catalogue ───────────────────────────────────────────────────────

@login_required
def catalogue(request):
    user_level = _user_level(request.user)
    programmes = Record.objects.filter(
        record_family='learning',
        record_type='programme',
        status='active',
        deleted_at__isnull=True,
    ).order_by('created_at')

    for p in programmes:
        p.is_locked = user_level < (p.permissions_data.get('required_level', 1))

    return render(request, 'learn/catalogue.html', {
        'programmes': programmes,
        'user_level': user_level,
    })


# ── Programme Detail ──────────────────────────────────────────────────────────

@login_required
def programme_detail(request, programme_id):
    user = request.user
    user_level = _user_level(user)

    programme = get_object_or_404(
        Record, id=programme_id,
        record_family='learning', record_type='programme',
        status__in=['active', 'locked']
    )

    required_level = programme.permissions_data.get('required_level', 1)
    if user_level < required_level:
        return render(request, 'learn/locked.html', {'programme': programme})

    course_ids = Relationship.objects.filter(
        to_record_id=programme_id,
        relationship_type='part_of'
    ).values_list('from_record_id', flat=True)

    courses = Record.objects.filter(
        id__in=course_ids, record_type='course',
        status__in=['active', 'locked']
    ).order_by('created_at')

    curriculum = []
    for course in courses:
        lesson_ids = Relationship.objects.filter(
            to_record_id=course.id, relationship_type='part_of'
        ).values_list('from_record_id', flat=True)
        lessons = Record.objects.filter(
            id__in=lesson_ids,
            record_type__in=['lesson', 'assignment', 'quiz'],
            status__in=['active', 'locked']
        ).order_by('created_at')
        curriculum.append({'course': course, 'lessons': list(lessons)})

    already_enrolled = Activity.objects.filter(
        activity_type='programme',
        assigned_to=user,
        metadata__programme_record_id=str(programme_id)
    ).exists()

    return render(request, 'learn/programme_detail.html', {
        'programme': programme,
        'curriculum': curriculum,
        'already_enrolled': already_enrolled,
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

    current_index = next((i for i, s in enumerate(siblings) if s.id == lesson.id), 0)
    prev_lesson = siblings[current_index - 1] if current_index > 0 else None
    next_lesson = siblings[current_index + 1] if current_index < len(siblings) - 1 else None

    # Check if already completed
    is_completed = Activity.objects.filter(
        assigned_to=request.user,
        status='completed',
        metadata__lesson_record_id=str(lesson_id)
    ).exists()

    return render(request, 'learn/lesson_viewer.html', {
        'lesson': lesson,
        'course': course,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'is_completed': is_completed,
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
    })


# ── Authorship (Level 4+) ─────────────────────────────────────────────────────

@login_required
def authorship(request):
    if _user_level(request.user) < 4:
        return redirect('learn:learn-home')
    return render(request, 'learn/authorship.html', {})


@login_required
def author_programme_form(request):
    if _user_level(request.user) < 4:
        return redirect('learn:learn-home')

    if request.method == 'POST':
        Record.objects.create(
            created_by=request.user,
            record_class='organizational',
            record_family='learning',
            record_type='programme',
            origin='user',
            title=request.POST.get('title', '').strip(),
            content=request.POST.get('description', '').strip(),
            status='draft',
            metadata={
                'source_app': 'learn',
                'qualification': request.POST.get('qualification', ''),
                'duration_years': request.POST.get('duration_years', ''),
                'pathways': request.POST.get('pathways', ''),
            },
            permissions_data={
                'visibility': 'tenant',
                'required_level': int(request.POST.get('required_level', 1)),
                'roles_allowed': [],
                'can_edit': [],
            }
        )
        return redirect('learn:learn-author')

    return render(request, 'learn/author_programme_form.html', {})


@login_required
def author_course_form(request):
    if _user_level(request.user) < 4:
        return redirect('learn:learn-home')

    programmes = Record.objects.filter(
        record_family='learning', record_type='programme',
        status__in=['active', 'draft']
    )

    if request.method == 'POST':
        course = Record.objects.create(
            created_by=request.user,
            record_class='organizational',
            record_family='learning',
            record_type='course',
            origin='user',
            title=request.POST.get('title', '').strip(),
            content=request.POST.get('description', '').strip(),
            status='draft',
            metadata={'source_app': 'learn'},
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

    return render(request, 'learn/author_course_form.html', {'programmes': programmes})


@login_required
def author_lesson_form(request):
    if _user_level(request.user) < 4:
        return redirect('learn:learn-home')

    courses = Record.objects.filter(
        record_family='learning', record_type='course',
        status__in=['active', 'draft']
    )

    if request.method == 'POST':
        lesson = Record.objects.create(
            created_by=request.user,
            record_class='organizational',
            record_family='learning',
            record_type=request.POST.get('record_type', 'lesson'),
            origin='user',
            title=request.POST.get('title', '').strip(),
            content=request.POST.get('content', '').strip(),
            status='draft',
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

    return render(request, 'learn/author_lesson_form.html', {'courses': courses})


# ── Handbook Review Queue (Level 5) ──────────────────────────────────────────

@login_required
def review_queue(request):
    if _user_level(request.user) < 5:
        return redirect('learn:learn-home')

    items = Record.objects.filter(
        record_family='learning',
        status='submitted',
        deleted_at__isnull=True,
    ).order_by('updated_at')

    return render(request, 'learn/review_queue.html', {'items': items})


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
    """HTMX POST: creates enrolment Activity, returns confirmation fragment."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    user = request.user
    if _user_level(user) < 1:
        return HttpResponse(
            '<span class="lock-indicator">Enrolment requires Level 1 or above.</span>',
            status=403
        )

    programme = get_object_or_404(Record, id=programme_id, record_type='programme')

    # Prevent duplicate enrolment
    if Activity.objects.filter(
        activity_type='programme', assigned_to=user,
        metadata__programme_record_id=str(programme_id)
    ).exists():
        return HttpResponse('<span class="enrolled-badge">Already Enrolled</span>')

    Activity.objects.create(
        activity_type='programme',
        title=f'Enrolment — {programme.title}',
        assigned_to=user,
        created_by=user,
        status='in_progress',
        progress=0,
        kgs_pathway='learning',
        metadata={
            'source_app': 'learn',
            'programme_record_id': str(programme_id),
        }
    )
    return HttpResponse('<span class="enrolled-badge">Enrolled ✓</span>')


@login_required
def htmx_complete_lesson(request, lesson_id):
    """HTMX POST: marks lesson Activity complete (creates if absent), recalculates programme progress."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    lesson = get_object_or_404(
        Record, id=lesson_id,
        record_type__in=['lesson', 'assignment', 'quiz'],
    )

    existing = Activity.objects.filter(
        metadata__lesson_record_id=str(lesson_id),
        assigned_to=request.user,
    ).first()

    if existing:
        existing.status = 'completed'
        existing.progress = 100
        existing.save(update_fields=['status', 'progress'])
    else:
        Activity.objects.create(
            activity_type='lesson',
            title=f'Lesson — {lesson.title}',
            assigned_to=request.user,
            created_by=request.user,
            status='completed',
            progress=100,
            kgs_pathway='learning',
            metadata={'source_app': 'learn', 'lesson_record_id': str(lesson_id)},
        )

    _recalculate_programme_progress(request.user, lesson_id)

    return HttpResponse(
        '<button class="btn-primary complete-btn" disabled>✓ Completed</button>'
    )


@login_required
def htmx_confirm_cert(request, cert_id):
    """HTMX POST: steward confirms certification, advances competence_level."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    from django.contrib.auth import get_user_model
    from .models import CertificationConfirmation
    from django.utils import timezone

    if _user_level(request.user) < 3:
        return HttpResponse('<div class="cert-card">Permission denied.</div>', status=403)

    cert = get_object_or_404(Record, id=cert_id, record_type='certification', status='draft')
    metadata = cert.metadata or {}
    learner_id = metadata.get('learner_id') or str(cert.created_by_id)
    target_level = metadata.get('target_level', 1)

    User = get_user_model()
    learner = get_object_or_404(User, id=learner_id)
    previous_level = getattr(learner, 'competence_level', 0)
    new_level = min(previous_level + 1, target_level)

    cert.status = 'active'
    cert.save(update_fields=['status', 'updated_at'])

    learner.competence_level = new_level
    learner.save(update_fields=['competence_level'])

    CertificationConfirmation.objects.create(
        certification_record_id=cert.id,
        confirmed_by=request.user,
        learner_id=learner.id,
        previous_competence_level=previous_level,
        new_competence_level=new_level,
        notes=request.POST.get('notes', '')
    )

    return HttpResponse(
        f'<div class="cert-card confirmed">'
        f'<span class="enrolled-badge">✓ Confirmed — Level {previous_level} → {new_level}</span>'
        f'</div>'
    )


@login_required
def htmx_approve_content(request, record_id):
    """HTMX POST: Level 5 approves submitted learning content."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    if _user_level(request.user) < 5:
        return HttpResponse('<div class="review-card">Permission denied.</div>', status=403)

    record = get_object_or_404(Record, id=record_id, status='submitted')
    record.status = 'active'
    record.save(update_fields=['status', 'updated_at'])

    return HttpResponse(
        f'<div class="review-card confirmed">'
        f'<span class="lesson-type-tag">{record.record_type}</span>'
        f'<h4>{record.title}</h4>'
        f'<span class="enrolled-badge">✓ Approved</span>'
        f'</div>'
    )


@login_required
def htmx_return_content(request, record_id):
    """HTMX POST: Level 5 returns submitted content to draft."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    if _user_level(request.user) < 5:
        return HttpResponse(status=403)

    record = get_object_or_404(Record, id=record_id, status='submitted')
    record.status = 'draft'
    record.save(update_fields=['status', 'updated_at'])

    return HttpResponse(
        f'<div class="review-card">'
        f'<span class="lesson-type-tag">{record.record_type}</span>'
        f'<h4>{record.title}</h4>'
        f'<span class="cert-pending-badge">Returned to Draft</span>'
        f'</div>'
    )


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
