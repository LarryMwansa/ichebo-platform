# learn/services.py — shared business logic for the Learn App
#
# SOLE WRITE PATH for competence_level:
#   confirm_certification_record() is the one function allowed to write
#   user.competence_level. No view, signal, or other service may write
#   this field directly — they must call this function.
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from records.models import Record
from .models import CertificationConfirmation

User = get_user_model()


class CertificationError(Exception):
    pass


def confirm_certification_record(cert_record, confirmed_by, notes=''):
    """
    Execute the certification confirmation flow for a single certification Record.

    This is the SOLE authorised write path for competence_level on the User model.
    Call this from both the DRF API view and the HTMX view — never write
    competence_level directly in a view.

    Args:
        cert_record: Record instance with record_type='certification', status='draft'
        confirmed_by: User instance — the confirming steward (must be Level 3+)
        notes: optional string from the confirming steward

    Returns:
        CertificationConfirmation instance

    Raises:
        CertificationError with a human-readable message on validation failure
    """
    metadata = cert_record.metadata or {}
    learner_id = metadata.get('learner_id') or str(cert_record.created_by_id)
    target_level = metadata.get('target_level', 1)

    learner = get_object_or_404(User, id=learner_id)
    previous_level = getattr(learner, 'competence_level', 0)

    if previous_level >= target_level:
        raise CertificationError(
            f'Learner is already at or above the target competence level ({target_level}).'
        )

    new_level = min(previous_level + 1, target_level)

    cert_record.status = 'active'
    cert_record.save(update_fields=['status', 'updated_at'])

    learner.competence_level = new_level
    learner.save(update_fields=['competence_level'])

    return CertificationConfirmation.objects.create(
        certification_record_id=cert_record.id,
        confirmed_by=confirmed_by,
        learner_id=learner.id,
        previous_competence_level=previous_level,
        new_competence_level=new_level,
        notes=notes,
    )
