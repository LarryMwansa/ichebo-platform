import uuid
from django.db import models
from django.conf import settings


class CertificationConfirmation(models.Model):
    """
    Audit record of a steward confirming a learner's certification.
    The certification itself is a records.Record with record_type='certification'.
    This model records WHO confirmed it and WHEN, separately from the Record.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    certification_record_id = models.UUIDField(db_index=True)   # FK → records.Record
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='certifications_confirmed'
    )
    learner_id = models.UUIDField(db_index=True)                # FK → User (the learner)
    previous_competence_level = models.IntegerField()
    new_competence_level = models.IntegerField()
    confirmed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-confirmed_at']
        indexes = [
            models.Index(fields=['certification_record_id']),
            models.Index(fields=['learner_id']),
            models.Index(fields=['confirmed_by']),
        ]

    def __str__(self):
        return f"Certification {self.certification_record_id} confirmed by {self.confirmed_by}"
