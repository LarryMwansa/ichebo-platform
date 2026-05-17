# learn/api_views.py — DRF endpoints for the Learn App
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from records.models import Record, Relationship
from activity.models import Activity
from .models import CertificationConfirmation
from .serializers import (
    CertificationConfirmSerializer,
    ProgrammeListSerializer,
    ProgrammeDetailSerializer,
    CourseSerializer,
    LessonSerializer,
    EnrolmentSerializer,
    LessonProgressSerializer,
)
from .services import (
    confirm_certification_record,
    enrol_in_programme,
    complete_lesson,
    check_prerequisites,
    CertificationError,
    EnrolmentError,
)

User = get_user_model()


def _is_level(user, min_level):
    return getattr(user, 'competence_level', 0) >= min_level


# ── Health ────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok", "app": "learn"})


# ── Programme catalogue ───────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def programme_list(request):
    """
    List all active qualification programmes.
    Annotates each with whether the requesting user is enrolled and whether
    they meet the prerequisite level.
    """
    programmes = Record.objects.filter(
        record_family='learning',
        record_type='programme',
        status__in=['active', 'locked'],
        deleted_at__isnull=True,
    ).order_by('permissions_data__required_level', 'created_at')

    user_level = getattr(request.user, 'competence_level', 0)
    enrolled_programme_ids = set(
        Activity.objects.filter(
            activity_type='programme',
            assigned_to=request.user,
            status__in=['pending', 'in_progress'],
            deleted_at__isnull=True,
        ).values_list('linked_record_id', flat=True)
    )

    data = []
    for programme in programmes:
        serialized = ProgrammeListSerializer(programme).data
        required_level = (programme.permissions_data or {}).get('required_level', 1)
        serialized['enrolled'] = programme.id in enrolled_programme_ids
        serialized['accessible'] = user_level >= required_level
        data.append(serialized)

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def programme_detail(request, programme_id):
    """Programme detail with full course + lesson tree."""
    programme = get_object_or_404(
        Record,
        id=programme_id,
        record_family='learning',
        record_type='programme',
        status__in=['active', 'locked'],
        deleted_at__isnull=True,
    )
    data = ProgrammeDetailSerializer(programme).data

    ok, reason = check_prerequisites(request.user, programme)
    data['accessible'] = ok
    data['prerequisite_message'] = reason if not ok else ''

    enrolment = Activity.objects.filter(
        activity_type='programme',
        assigned_to=request.user,
        linked_record=programme,
        deleted_at__isnull=True,
    ).first()
    data['enrolment'] = EnrolmentSerializer(enrolment).data if enrolment else None

    return Response(data)


# ── Curriculum (course + lesson tree) ─────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def programme_curriculum(request, programme_id):
    """
    Returns ordered list of courses (and their lessons) for a programme.
    Traverses part_of Relationships: course → part_of → programme.
    """
    programme = get_object_or_404(
        Record,
        id=programme_id,
        record_family='learning',
        record_type='programme',
        status__in=['active', 'locked'],
    )

    required_level = (programme.permissions_data or {}).get('required_level', 1)
    if not _is_level(request.user, required_level):
        return Response(
            {"detail": "Insufficient competence level to access this programme."},
            status=status.HTTP_403_FORBIDDEN,
        )

    course_ids = Relationship.objects.filter(
        to_record_id=programme_id,
        relationship_type='part_of',
        deleted_at__isnull=True,
    ).values_list('from_record_id', flat=True)

    courses = Record.objects.filter(
        id__in=course_ids,
        record_type='course',
        status__in=['active', 'locked'],
    ).order_by('created_at')

    curriculum = []
    for course in courses:
        lesson_ids = Relationship.objects.filter(
            to_record_id=course.id,
            relationship_type='part_of',
            deleted_at__isnull=True,
        ).values_list('from_record_id', flat=True)
        lessons = Record.objects.filter(
            id__in=lesson_ids,
            record_type__in=['lesson', 'assignment', 'quiz'],
            status__in=['active', 'locked'],
        ).order_by('created_at')
        curriculum.append({
            'course': CourseSerializer(course).data,
            'lessons': LessonSerializer(lessons, many=True).data,
        })

    return Response({
        'programme': ProgrammeListSerializer(programme).data,
        'curriculum': curriculum,
    })


# ── Enrolment ─────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enrol(request, programme_id):
    """
    Enrol the requesting user in a programme.
    Creates the programme Activity tree (programme → courses → lesson tasks).
    """
    programme = get_object_or_404(
        Record,
        id=programme_id,
        record_family='learning',
        record_type='programme',
        status__in=['active', 'locked'],
        deleted_at__isnull=True,
    )

    tenant = getattr(request.user, 'current_tenant', None)

    try:
        programme_activity = enrol_in_programme(request.user, programme, tenant=tenant)
    except EnrolmentError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        EnrolmentSerializer(programme_activity).data,
        status=status.HTTP_201_CREATED,
    )


# ── My enrolments ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_enrolments(request):
    """List all programme enrolments for the requesting user."""
    enrolments = Activity.objects.filter(
        activity_type='programme',
        assigned_to=request.user,
        deleted_at__isnull=True,
    ).select_related('linked_record').order_by('-created_at')
    return Response(EnrolmentSerializer(enrolments, many=True).data)


# ── Lesson completion ─────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_lesson_view(request, lesson_activity_id):
    """
    Mark a lesson task Activity as completed.
    Recalculates course and programme progress automatically.
    If programme reaches 100%, the signal in signals.py creates a draft certification.
    """
    lesson_activity = get_object_or_404(
        Activity,
        id=lesson_activity_id,
        activity_type='task',
        assigned_to=request.user,
        deleted_at__isnull=True,
    )

    try:
        programme_activity = complete_lesson(request.user, lesson_activity)
    except EnrolmentError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    response_data = {
        'lesson': LessonProgressSerializer(lesson_activity).data,
        'programme': EnrolmentSerializer(programme_activity).data if programme_activity else None,
    }
    return Response(response_data)


# ── My lesson tasks for a programme ──────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_lesson_tasks(request, programme_id):
    """
    Return all lesson task Activities for the user's enrolment in a programme,
    grouped by course. Used by the lesson viewer to show completion state.
    """
    programme_activity = Activity.objects.filter(
        activity_type='programme',
        assigned_to=request.user,
        linked_record_id=programme_id,
        deleted_at__isnull=True,
    ).first()

    if not programme_activity:
        return Response(
            {"detail": "You are not enrolled in this programme."},
            status=status.HTTP_404_NOT_FOUND,
        )

    course_activities = Activity.objects.filter(
        parent_activity=programme_activity,
        activity_type='project',
        deleted_at__isnull=True,
    ).select_related('linked_record').order_by('created_at')

    result = []
    for course_act in course_activities:
        lesson_tasks = Activity.objects.filter(
            parent_activity=course_act,
            activity_type='task',
            deleted_at__isnull=True,
        ).select_related('linked_record').order_by('created_at')
        result.append({
            'course_activity_id': str(course_act.id),
            'course_title': course_act.title,
            'progress': course_act.progress,
            'lessons': LessonProgressSerializer(lesson_tasks, many=True).data,
        })

    return Response({
        'programme_activity_id': str(programme_activity.id),
        'programme_title': programme_activity.title,
        'progress': programme_activity.progress,
        'courses': result,
    })


# ── Certification Queue (steward) ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def certification_queue(request):
    """Draft certifications visible to the requesting steward (Level 3+)."""
    if not _is_level(request.user, 3):
        return Response(
            {"detail": "Certification queue requires Level 3 or above."},
            status=status.HTTP_403_FORBIDDEN,
        )

    certifications = Record.objects.filter(
        record_type='certification',
        status='draft',
        deleted_at__isnull=True,
    ).order_by('created_at')

    from records.serializers import RecordSerializer
    return Response(RecordSerializer(certifications, many=True).data)


# ── Confirm Certification (sole writer of competence_level) ───────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_certification(request, certification_id):
    """
    Steward confirms a learner's certification.
    This endpoint is the SOLE authorised writer of competence_level.
    Gated to competence_level >= 3.

    Body (optional):
        notes: str
        placement_tenant_id: UUID — required for induction_completion context
    """
    if not _is_level(request.user, 3):
        return Response(
            {"detail": "Certification confirmation requires Level 3 or above."},
            status=status.HTTP_403_FORBIDDEN,
        )

    certification_record = get_object_or_404(
        Record,
        id=certification_id,
        record_type='certification',
        status='draft',
        deleted_at__isnull=True,
    )

    try:
        confirmation = confirm_certification_record(
            cert_record=certification_record,
            confirmed_by=request.user,
            notes=request.data.get('notes', ''),
            placement_tenant_id=request.data.get('placement_tenant_id'),
        )
    except CertificationError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        CertificationConfirmSerializer(confirmation).data,
        status=status.HTTP_200_OK,
    )
