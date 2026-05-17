from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Activity, ActivityLog


@receiver(post_save, sender=Activity)
def log_activity_creation(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            activity=instance,
            tenant=instance.tenant,
            created_by=instance.created_by,
            event_type='created',
            new_value=instance.title,
        )


@receiver(pre_save, sender=Activity)
def capture_previous_status(sender, instance, **kwargs):
    """Store previous status on the instance so post_save can compare."""
    if instance.pk:
        try:
            instance._previous_status = Activity.objects.filter(
                pk=instance.pk
            ).values_list('status', flat=True).get()
        except Activity.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Activity)
def log_status_transition(sender, instance, created, **kwargs):
    if created:
        return
    previous = getattr(instance, '_previous_status', None)
    if previous is not None and previous != instance.status:
        ActivityLog.objects.create(
            activity=instance,
            tenant=instance.tenant,
            created_by=instance.created_by,
            event_type='status_changed',
            previous_value=previous,
            new_value=instance.status,
        )
