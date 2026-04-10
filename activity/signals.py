from django.db.models.signals import post_save
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
            new_value=instance.title
        )
