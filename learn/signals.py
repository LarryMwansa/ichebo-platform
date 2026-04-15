"""
learn/signals.py

Auto-certification signal: when a programme Activity reaches 100% progress,
create a draft certification Record awaiting steward confirmation.

The draft is idempotent — a second completion event won't create a duplicate
if a draft or active certification already exists for this learner + programme.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from activity.models import Activity
from records.models import Record


@receiver(post_save, sender=Activity)
def auto_create_draft_certification(sender, instance, **kwargs):
    """
    Fires after every Activity save. Only acts when:
      - activity_type == 'programme'
      - progress >= 100
      - assigned_to is set
      - programme_record_id is in metadata
    """
    if instance.activity_type != 'programme':
        return

    if instance.progress < 100:
        return

    learner = instance.assigned_to
    if learner is None:
        return

    programme_record_id = (instance.metadata or {}).get('programme_record_id')
    if not programme_record_id:
        return

    # Idempotency: skip if a certification already exists for this learner + programme
    if Record.objects.filter(
        record_type='certification',
        created_by=learner,
        metadata__programme_record_id=programme_record_id,
        status__in=['draft', 'active'],
        deleted_at__isnull=True,
    ).exists():
        return

    # Fetch programme for its title and required level
    try:
        programme = Record.objects.get(id=programme_record_id, record_type='programme')
    except Record.DoesNotExist:
        return

    target_level = (programme.permissions_data or {}).get('required_level', 1)

    Record.objects.create(
        created_by=learner,
        tenant=instance.tenant,
        record_class='organizational',
        record_family='learning',
        record_type='certification',
        origin='system',
        title=f'Certification — {programme.title}',
        status='draft',
        metadata={
            'source_app': 'learn',
            'programme_record_id': str(programme_record_id),
            'learner_id': str(learner.id),
            'target_level': target_level,
        },
        permissions_data={
            'visibility': 'tenant',
            'required_level': 3,
            'roles_allowed': [],
            'can_edit': [],
        },
    )
