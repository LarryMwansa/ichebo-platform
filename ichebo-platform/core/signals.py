"""
core/signals.py

Post-save signals that append a SyncChangelog entry for every write to a
syncable entity. The entry and the entity write are in the same DB transaction
because Django's post_save fires before the transaction commits when called
inside atomic().

Entity type mapping:
  records.Record            → 'record'
  records.Relationship      → 'relationship'
  activity.Activity         → 'activity'
  accounts.User             → 'member'
  tenants.UserPermission    → 'member'
  notifications.Notification → 'notification'
  learn.CertificationConfirmation → 'certification'
  community.MembershipRequest     → 'membership'
  tenants.Tenant            → 'tenant'
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import OP_CREATE, OP_UPDATE, OP_DELETE, SyncChangelog


def _append(entity_type, entity_id, operation, instance):
    from django.core.serializers import serialize
    import json

    # Build a minimal payload dict for hashing — use model fields as dict
    try:
        from django.forms.models import model_to_dict
        payload = model_to_dict(instance)
    except Exception:
        payload = {'id': str(entity_id)}

    payload['id'] = str(entity_id)
    payload_hash = SyncChangelog.compute_hash(payload)

    actor_id = None
    for attr in ('created_by_id', 'user_id', 'actor_id'):
        val = getattr(instance, attr, None)
        if val:
            actor_id = val
            break

    SyncChangelog.objects.create(
        entity_type=entity_type,
        entity_id=entity_id,
        operation=operation,
        changed_at=timezone.now(),
        actor_id=actor_id,
        payload_hash=payload_hash,
    )


# ── records ──────────────────────────────────────────────────────────────────

@receiver(post_save, sender='records.Record')
def changelog_record(sender, instance, created, **kwargs):
    _append('record', instance.pk, OP_CREATE if created else OP_UPDATE, instance)


@receiver(post_save, sender='records.Relationship')
def changelog_relationship(sender, instance, created, **kwargs):
    _append('relationship', instance.pk, OP_CREATE if created else OP_UPDATE, instance)


# ── activity ──────────────────────────────────────────────────────────────────

@receiver(post_save, sender='activity.Activity')
def changelog_activity(sender, instance, created, **kwargs):
    _append('activity', instance.pk, OP_CREATE if created else OP_UPDATE, instance)


# ── accounts ──────────────────────────────────────────────────────────────────

@receiver(post_save, sender='accounts.User')
def changelog_user(sender, instance, created, **kwargs):
    _append('member', instance.pk, OP_CREATE if created else OP_UPDATE, instance)


# ── tenants ───────────────────────────────────────────────────────────────────

@receiver(post_save, sender='tenants.UserPermission')
def changelog_user_permission(sender, instance, created, **kwargs):
    _append('member', instance.pk, OP_CREATE if created else OP_UPDATE, instance)


@receiver(post_save, sender='tenants.Tenant')
def changelog_tenant(sender, instance, created, **kwargs):
    _append('tenant', instance.pk, OP_CREATE if created else OP_UPDATE, instance)


# ── notifications ─────────────────────────────────────────────────────────────

@receiver(post_save, sender='notifications.Notification')
def changelog_notification(sender, instance, created, **kwargs):
    _append('notification', instance.pk, OP_CREATE if created else OP_UPDATE, instance)


# ── learn ─────────────────────────────────────────────────────────────────────

@receiver(post_save, sender='learn.CertificationConfirmation')
def changelog_certification(sender, instance, created, **kwargs):
    _append('certification', instance.pk, OP_CREATE if created else OP_UPDATE, instance)


# ── community ─────────────────────────────────────────────────────────────────

@receiver(post_save, sender='community.MembershipRequest')
def changelog_membership(sender, instance, created, **kwargs):
    _append('membership', instance.pk, OP_CREATE if created else OP_UPDATE, instance)
