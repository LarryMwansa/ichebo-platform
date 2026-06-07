"""
notifications/signals.py

Signal receivers that trigger Notification creation.
Connected in NotificationsConfig.ready() via notifications/apps.py.
All receivers import lazily to avoid circular imports.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver, Signal

# Custom signal fired by tenants/service.py after invitation created
invitation_sent = Signal()  # kwargs: tenant, email, invited_by, token

# Custom signal fired by tenants/service.py after member removed
member_removed_signal = Signal()  # kwargs: user, tenant

# Custom signal fired by learn/views.py htmx_approve_content
content_approved = Signal()  # kwargs: record, approved_by

# Custom signal fired by learn/views.py htmx_publish_content
content_published = Signal()  # kwargs: record, published_by


# ---------------------------------------------------------------------------
# MembershipRequest — approval / denial
# ---------------------------------------------------------------------------

@receiver(post_save, sender='community.MembershipRequest')
def on_membership_request_reviewed(sender, instance, created, **kwargs):
    if created:
        return
    from notifications.service import notify_membership_approved, notify_membership_denied
    if instance.status == 'approved':
        notify_membership_approved(instance)
    elif instance.status == 'denied':
        notify_membership_denied(instance)


# ---------------------------------------------------------------------------
# Activity — new assignment
# ---------------------------------------------------------------------------

@receiver(post_save, sender='activity.Activity')
def on_activity_assigned(sender, instance, created, **kwargs):
    if not created:
        return
    from notifications.service import notify_activity_assigned
    notify_activity_assigned(instance)


# ---------------------------------------------------------------------------
# Learn — certification earned / level advanced
# ---------------------------------------------------------------------------

@receiver(post_save, sender='learn.CertificationConfirmation')
def on_certification_confirmed(sender, instance, created, **kwargs):
    if not created:
        return

    from accounts.models import User
    from notifications.service import notify_certification_earned, notify_level_advanced, notify_induction_completed

    try:
        learner = User.objects.get(id=instance.learner_id)
    except User.DoesNotExist:
        return

    # Resolve the cert Record for title and metadata
    programme_title = 'Programme'
    cert_record = None
    try:
        from records.models import Record
        cert_record = Record.objects.get(id=instance.certification_record_id)
        programme_title = cert_record.title or programme_title
    except Exception:
        pass

    notify_certification_earned(
        user=learner,
        programme_title=programme_title,
        cert_record_id=instance.certification_record_id,
    )

    if (instance.new_competence_level or 0) > (instance.previous_competence_level or 0):
        notify_level_advanced(
            user=learner,
            previous_level=instance.previous_competence_level,
            new_level=instance.new_competence_level,
            confirmed_by=instance.confirmed_by,
        )

    if cert_record:
        rec_meta = cert_record.metadata or {}
        if rec_meta.get('context') == 'induction_completion':
            placement_tenant = rec_meta.get('placement_tenant_name', 'your community')
            notify_induction_completed(user=learner, placement_tenant_name=placement_tenant)


# ---------------------------------------------------------------------------
# Tenants — invitation sent
# ---------------------------------------------------------------------------

@receiver(invitation_sent)
def on_invitation_sent(sender, tenant, email, invited_by, token, **kwargs):
    from notifications.service import notify_tenant_invitation
    notify_tenant_invitation(email=email, tenant=tenant, invited_by=invited_by, token=token)


# ---------------------------------------------------------------------------
# Tenants — UserPermission created (member added via invitation accept)
# ---------------------------------------------------------------------------

@receiver(post_save, sender='tenants.TenantInvitation')
def on_invitation_accepted(sender, instance, created, **kwargs):
    if created:
        return
    if instance.status != 'accepted':
        return
    from accounts.models import User
    from notifications.service import notify_member_added
    try:
        user = User.objects.get(email__iexact=instance.email)
        notify_member_added(user=user, tenant=instance.tenant)
    except User.DoesNotExist:
        pass


# ---------------------------------------------------------------------------
# Tenants — member removed
# ---------------------------------------------------------------------------

@receiver(member_removed_signal)
def on_member_removed(sender, user, tenant, **kwargs):
    from notifications.service import notify_member_removed
    notify_member_removed(user=user, tenant=tenant)


# ---------------------------------------------------------------------------
# Learn — content approved by reviewer
# ---------------------------------------------------------------------------

@receiver(content_approved)
def on_content_approved(sender, record, approved_by, **kwargs):
    from notifications.service import notify_content_approved
    notify_content_approved(record=record, approved_by=approved_by)


# Learn — content published (made live)
# ---------------------------------------------------------------------------

@receiver(content_published)
def on_content_published(sender, record, published_by, **kwargs):
    from notifications.service import notify_content_published
    notify_content_published(record=record, published_by=published_by)
