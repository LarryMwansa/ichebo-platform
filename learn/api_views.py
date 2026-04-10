# learn/api_views.py — DRF endpoints for the Learn App
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from records.models import Record, Relationship
from .models import CertificationConfirmation
from .serializers import CertificationConfirmSerializer

User = get_user_model()


def _is_level(user, min_level):
    return getattr(user, 'competence_level', 0) >= min_level


# ── Health ────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok", "app": "learn"})


# ── Curriculum (course + lesson tree for a programme) ────────────────────────

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
        status__in=['active', 'locked']
    )

    required_level = programme.permissions_data.get('required_level', 1)
    user_level = getattr(request.user, 'competence_level', 0)
    if user_level < required_level:
        return Response(
            {"detail": "Insufficient competence level to access this programme."},
            status=status.HTTP_403_FORBIDDEN
        )

    course_ids = Relationship.objects.filter(
        to_record_id=programme_id,
        relationship_type='part_of'
    ).values_list('from_record_id', flat=True)

    courses = Record.objects.filter(
        id__in=course_ids,
        record_type='course',
        status__in=['active', 'locked']
    ).order_by('created_at')

    from records.serializers import RecordSerializer

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
        curriculum.append({
            'course': RecordSerializer(course).data,
            'lessons': RecordSerializer(lessons, many=True).data,
        })

    from records.serializers import RecordSerializer as RS
    return Response({
        'programme': RS(programme).data,
        'curriculum': curriculum,
    })


# ── Certification Queue (steward) ─────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def certification_queue(request):
    """Draft certifications visible to the requesting steward (Level 3+)."""
    if not _is_level(request.user, 3):
        return Response(
            {"detail": "Certification queue requires Level 3 or above."},
            status=status.HTTP_403_FORBIDDEN
        )

    certifications = Record.objects.filter(
        record_type='certification',
        status='draft',
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
    """
    if not _is_level(request.user, 3):
        return Response(
            {"detail": "Certification confirmation requires Level 3 or above."},
            status=status.HTTP_403_FORBIDDEN
        )

    certification_record = get_object_or_404(
        Record,
        id=certification_id,
        record_type='certification',
        status='draft'
    )

    metadata = certification_record.metadata or {}
    learner_id = metadata.get('learner_id') or str(certification_record.created_by_id)
    target_level = metadata.get('target_level', 1)

    learner = get_object_or_404(User, id=learner_id)
    previous_level = getattr(learner, 'competence_level', 0)

    if previous_level >= target_level:
        return Response(
            {"detail": "Learner is already at or above the target competence level."},
            status=status.HTTP_400_BAD_REQUEST
        )

    new_level = min(previous_level + 1, target_level)

    # Advance certification status
    certification_record.status = 'active'
    certification_record.save(update_fields=['status', 'updated_at'])

    # Advance learner competence level — ONLY write path in the system
    learner.competence_level = new_level
    learner.save(update_fields=['competence_level'])

    # Audit record
    confirmation = CertificationConfirmation.objects.create(
        certification_record_id=certification_record.id,
        confirmed_by=request.user,
        learner_id=learner.id,
        previous_competence_level=previous_level,
        new_competence_level=new_level,
        notes=request.data.get('notes', '')
    )

    serializer = CertificationConfirmSerializer(confirmation)
    return Response(serializer.data, status=status.HTTP_200_OK)
