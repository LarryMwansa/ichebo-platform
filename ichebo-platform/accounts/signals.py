import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

logger = logging.getLogger(__name__)


@receiver(post_save, sender='accounts.User')
def auto_place_new_user_in_induction_tenant(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        from tenants.models import Tenant, UserPermission
        induction_tenant = Tenant.objects.filter(
            tier='induction', slug='induction'
        ).first()
        if not induction_tenant:
            logger.warning(
                'Induction tenant not found — user %s placed with no community. '
                'Run: python manage.py seed_induction_tenant',
                instance.pk,
            )
            return
        UserPermission.objects.get_or_create(
            user=instance,
            tenant=induction_tenant,
            role='seeker',
            defaults={
                'created_by': instance,
                'granted_by': instance,
                'tenant_path': induction_tenant.path,
                'level': 0,
                'is_active': True,
            },
        )
        if not instance.induction_enrolled_at:
            instance.induction_enrolled_at = timezone.now()
            instance.save(update_fields=['induction_enrolled_at'])
    except Exception:
        logger.exception(
            'Failed to auto-place user %s in induction tenant', instance.pk
        )
