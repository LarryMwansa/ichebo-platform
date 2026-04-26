"""
notifications/signals.py

Signal receivers that trigger Notification creation.
Connected in NotificationsConfig.ready() via notifications/apps.py.

All receivers import lazily to avoid circular imports.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver


# ---------------------------------------------------------------------------
# MembershipRequest — approval / denial
# ---------------------------------------------------------------------------

@receiver(post_save, sender='community.MembershipRequest')
def on_membership_request_reviewed(sender, instance, created, **kwargs):
    """Fire a notification when a pending request is approved or denied."""
    if created:
        return  # Submission itself doesn't trigger a notification

    from notifications.service import notify_membership_approved, notify_membership_denied

    if instance.status == 'approved':
        notify_membership_approved(instance)
    elif instance.status == 'denied':
        notify_membership_denied(instance)


# ---------------------------------------------------------------------------
# Activity — new assignment (assigned_to differs from created_by)
# ---------------------------------------------------------------------------

@receiver(post_save, sender='activity.Activity')
def on_activity_assigned(sender, instance, created, **kwargs):
    """Notify the assignee when a new activity is created for them by someone else."""
    if not created:
        return

    from notifications.service import notify_activity_assigned
    notify_activity_assigned(instance)


# ---------------------------------------------------------------------------
# Learn — certification earned
# (The Learn app's post_save signal on Enrolment already creates Certification;
#  we hook into Certification's post_save here.)
# ---------------------------------------------------------------------------

@receiver(post_save, sender='learn.CertificationConfirmation')
def on_certification_created(sender, instance, created, **kwargs):
    """Notify the learner when a new CertificationConfirmation record is created."""
    if not created:
        return

    from notifications.service import notify_certification_earned

    programme_title = ''
    cert_record_id = None

    # CertificationConfirmation links to a Record (the programme) via record FK
    if hasattr(instance, 'record') and instance.record:
        programme_title = instance.record.title
        cert_record_id = instance.record.id

    notify_certification_earned(
        user=instance.user,
        programme_title=programme_title or 'Programme',
        cert_record_id=cert_record_id,
    )
