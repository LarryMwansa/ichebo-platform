# learn/services.py — shared business logic for the Learn App
#
# SOLE WRITE PATH for competence_level:
#   confirm_certification_record() is the one function allowed to write
#   user.competence_level. No view, signal, or other service may write
#   this field directly — they must call this function.
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404

from activity.models import Activity
from records.models import Record, Relationship
from .models import CertificationConfirmation

User = get_user_model()


class CertificationError(Exception):
    pass


class EnrolmentError(Exception):
    pass


# ── Prerequisite check ────────────────────────────────────────────────────────

def check_prerequisites(user, programme):
    """
    Returns (ok: bool, reason: str). A programme passes if the user has an
    active CertificationConfirmation whose target_level matches the programme's
    required_level - 1, or if required_level <= 1 (no prior certification needed
    beyond completing induction).
    """
    required_level = (programme.permissions_data or {}).get('required_level', 1)
    user_level = getattr(user, 'competence_level', 0)
    if user_level >= required_level:
        return True, ''
    return False, (
        f'This programme requires competence level {required_level}. '
        f'You are currently level {user_level}.'
    )


# ── Enrolment ─────────────────────────────────────────────────────────────────

@transaction.atomic
def enrol_in_programme(user, programme, tenant=None):
    """
    Enrol a user in a qualification programme.

    Creates:
      - One 'programme' Activity (the enrolment container, progress 0–100)
      - One 'project' Activity per course (course progress tracker)
      - One 'task' Activity per lesson/assignment/quiz in each course

    Returns the top-level programme Activity.

    Raises EnrolmentError if:
      - User is already enrolled (active programme Activity exists)
      - Prerequisite check fails
    """
    ok, reason = check_prerequisites(user, programme)
    if not ok:
        raise EnrolmentError(reason)

    # Idempotency: one active enrolment per programme per user
    existing = Activity.objects.filter(
        activity_type='programme',
        assigned_to=user,
        linked_record=programme,
        status__in=['pending', 'in_progress'],
        deleted_at__isnull=True,
    ).first()
    if existing:
        raise EnrolmentError('You are already enrolled in this programme.')

    programme_activity = Activity.objects.create(
        tenant=tenant,
        created_by=user,
        assigned_to=user,
        activity_type='programme',
        title=programme.title,
        status='in_progress',
        progress=0,
        linked_record=programme,
        metadata={
            'source_app': 'learn',
            'programme_record_id': str(programme.id),
        },
    )

    # Traverse part_of graph: course → programme
    course_ids = Relationship.objects.filter(
        to_record=programme,
        relationship_type='part_of',
        deleted_at__isnull=True,
    ).values_list('from_record_id', flat=True)

    courses = Record.objects.filter(
        id__in=course_ids,
        record_type='course',
        status__in=['active', 'locked'],
    ).order_by('created_at')

    for course in courses:
        course_activity = Activity.objects.create(
            tenant=tenant,
            created_by=user,
            assigned_to=user,
            activity_type='project',
            title=course.title,
            status='in_progress',
            progress=0,
            parent_activity=programme_activity,
            linked_record=course,
            metadata={
                'source_app': 'learn',
                'course_record_id': str(course.id),
                'programme_record_id': str(programme.id),
            },
        )

        lesson_ids = Relationship.objects.filter(
            to_record=course,
            relationship_type='part_of',
            deleted_at__isnull=True,
        ).values_list('from_record_id', flat=True)

        lessons = Record.objects.filter(
            id__in=lesson_ids,
            record_type__in=['lesson', 'assignment', 'quiz'],
            status__in=['active', 'locked'],
        ).order_by('created_at')

        for lesson in lessons:
            Activity.objects.create(
                tenant=tenant,
                created_by=user,
                assigned_to=user,
                activity_type='task',
                title=lesson.title,
                status='pending',
                progress=0,
                parent_activity=course_activity,
                linked_record=lesson,
                metadata={
                    'source_app': 'learn',
                    'lesson_record_id': str(lesson.id),
                    'course_record_id': str(course.id),
                    'programme_record_id': str(programme.id),
                },
            )

    return programme_activity


# ── Progress recalculation ─────────────────────────────────────────────────────

@transaction.atomic
def complete_lesson(user, lesson_activity):
    """
    Mark a lesson task Activity as completed, then recalculate progress up the
    tree: course Activity → programme Activity.

    Returns the updated programme Activity (or None if no programme found).
    """
    if lesson_activity.activity_type != 'task':
        raise EnrolmentError('Only task activities can be completed via this function.')
    if lesson_activity.assigned_to_id != user.id:
        raise EnrolmentError('You can only complete your own lesson activities.')

    lesson_activity.status = 'completed'
    lesson_activity.progress = 100
    lesson_activity.save(update_fields=['status', 'progress', 'updated_at'])

    course_activity = lesson_activity.parent_activity
    if course_activity is None:
        return None

    _recalculate_progress(course_activity)

    programme_activity = course_activity.parent_activity
    if programme_activity is None:
        return None

    _recalculate_progress(programme_activity)
    return programme_activity


def _recalculate_progress(activity):
    """
    Set activity.progress to the percentage of child task/project activities
    that are completed. Saves immediately.
    """
    children = Activity.objects.filter(
        parent_activity=activity,
        deleted_at__isnull=True,
    )
    total = children.count()
    if total == 0:
        return
    completed = children.filter(status='completed').count()
    activity.progress = int((completed / total) * 100)
    if activity.progress >= 100:
        activity.status = 'completed'
    activity.save(update_fields=['progress', 'status', 'updated_at'])


# ── Certification confirmation (sole write path for competence_level) ─────────

def confirm_certification_record(cert_record, confirmed_by, notes='', placement_tenant_id=None):
    """
    Execute the certification confirmation flow for a single certification Record.

    This is the SOLE authorised write path for competence_level on the User model.
    Call this from both the DRF API view and the HTMX view — never write
    competence_level directly in a view.

    When metadata.context == 'induction_completion', also handles placement:
      - Creates UserPermission in the placement tenant at level 1
      - Deactivates the Induction Tenant UserPermission
      - Sets induction_completed_at on User

    Args:
        cert_record: Record instance with record_type='certification', status='draft'
        confirmed_by: User instance — the confirming steward (must be Level 3+)
        notes: optional string from the confirming steward
        placement_tenant_id: required when context == 'induction_completion'

    Returns:
        CertificationConfirmation instance

    Raises:
        CertificationError with a human-readable message on validation failure
    """
    metadata = cert_record.metadata or {}
    learner_id = metadata.get('learner_id') or str(cert_record.created_by_id)
    target_level = metadata.get('target_level', 1)
    context = metadata.get('context', '')

    learner = get_object_or_404(User, id=learner_id)
    previous_level = getattr(learner, 'competence_level', 0)

    if previous_level >= target_level:
        raise CertificationError(
            f'Learner is already at or above the target competence level ({target_level}).'
        )

    new_level = min(previous_level + 1, target_level)

    with transaction.atomic():
        cert_record.status = 'active'
        cert_record.save(update_fields=['status', 'updated_at'])

        learner.competence_level = new_level
        learner.save(update_fields=['competence_level'])

        if context == 'induction_completion':
            _handle_induction_placement(learner, new_level, placement_tenant_id)
            # Store placement tenant name on cert record metadata for signal
            if placement_tenant_id:
                from tenants.models import Tenant as _Tenant
                try:
                    _pt = _Tenant.objects.get(id=placement_tenant_id)
                    metadata['placement_tenant_name'] = _pt.name
                    cert_record.metadata = metadata
                    cert_record.save(update_fields=['metadata', 'updated_at'])
                except _Tenant.DoesNotExist:
                    pass

        return CertificationConfirmation.objects.create(
            certification_record_id=cert_record.id,
            confirmed_by=confirmed_by,
            learner_id=learner.id,
            previous_competence_level=previous_level,
            new_competence_level=new_level,
            notes=notes,
        )


def _handle_induction_placement(learner, new_level, placement_tenant_id):
    """
    Called when confirming an induction completion certification.
    Deactivates the Induction Tenant permission and creates a Level 1
    permission in the placement tenant. Sets induction_completed_at.
    Imported inline to avoid circular imports with tenants/accounts apps.
    """
    from django.utils import timezone
    from tenants.models import UserPermission

    # Deactivate induction tenant permission
    UserPermission.objects.filter(
        user=learner,
        tenant__tier='induction',
        is_active=True,
    ).update(is_active=False)

    # Create home tenant permission if placement specified
    if placement_tenant_id:
        from tenants.models import Tenant
        try:
            placement_tenant = Tenant.objects.get(id=placement_tenant_id)
        except Tenant.DoesNotExist:
            raise CertificationError(f'Placement tenant {placement_tenant_id} does not exist.')

        UserPermission.objects.get_or_create(
            user=learner,
            tenant=placement_tenant,
            defaults={
                'level': new_level,
                'role': 'member',
                'is_active': True,
            },
        )

    # Set induction_completed_at if the field exists
    if hasattr(learner, 'induction_completed_at'):
        learner.induction_completed_at = timezone.now()
        learner.save(update_fields=['induction_completed_at'])
