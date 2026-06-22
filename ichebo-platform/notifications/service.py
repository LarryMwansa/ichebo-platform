"""
notifications/service.py

Utility functions for creating Notification records and dispatching async
email and FCM push tasks. Called by signal handlers — never by views directly.
All functions are fire-and-forget; errors are logged, never raised.
"""
import logging

logger = logging.getLogger(__name__)

# Types that also trigger a Brevo email
EMAIL_TYPES = {'level_advanced', 'certification_earned', 'tenant_invitation', 'induction_completed'}


def create_notification(user, notification_type, title, body='', data=None):
    from .models import Notification
    from .tasks import send_fcm_push
    try:
        n = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            body=body,
            data=data or {},
        )
        if notification_type in EMAIL_TYPES:
            _send_email(user, title, body, data or {})
        if getattr(user, 'fcm_token', None):
            send_fcm_push.delay(str(user.pk), title, body, data or {})
        return n
    except Exception:
        logger.exception(
            'Failed to create notification type=%s for user=%s',
            notification_type, user.pk,
        )
        return None


def _send_email(user, title, body, data):
    from .tasks import send_notification_email
    recipient = user.email if hasattr(user, 'email') else str(user)
    if not recipient:
        return
    action_url = data.get('url', '') if isinstance(data, dict) else ''
    message = body
    if action_url:
        message += f'\n\n{action_url}'
    send_notification_email.delay(recipient, title, message)


# ---------------------------------------------------------------------------
# Existing handlers
# ---------------------------------------------------------------------------

def notify_membership_approved(membership_request):
    create_notification(
        user=membership_request.user,
        notification_type='membership_approved',
        title=f'Welcome to {membership_request.tenant.name}!',
        body='Your membership request has been approved. You now have access to this community.',
        data={
            'tenant_id': str(membership_request.tenant.id),
            'tenant_name': membership_request.tenant.name,
            'url': '/community/',
        },
    )


def notify_membership_denied(membership_request):
    create_notification(
        user=membership_request.user,
        notification_type='membership_denied',
        title=f'Membership request for {membership_request.tenant.name} was not approved.',
        body='A steward has reviewed your request. You may contact them directly for more information.',
        data={
            'tenant_id': str(membership_request.tenant.id),
            'tenant_name': membership_request.tenant.name,
        },
    )


def notify_certification_earned(user, programme_title, cert_record_id=None):
    create_notification(
        user=user,
        notification_type='certification_earned',
        title=f'Certification earned: {programme_title}',
        body='Congratulations! You have completed all lessons in this programme.',
        data={
            'cert_record_id': str(cert_record_id) if cert_record_id else None,
            'programme_title': programme_title,
            'url': '/learn/',
        },
    )


def notify_activity_assigned(activity):
    if not activity.assigned_to:
        return
    if activity.assigned_to == activity.created_by:
        return
    create_notification(
        user=activity.assigned_to,
        notification_type='activity_assigned',
        title=f'New task assigned: {activity.title}',
        body=f'You have been assigned a new {activity.activity_type}.',
        data={
            'activity_id': str(activity.id),
            'activity_type': activity.activity_type,
            'due_at': activity.due_at.isoformat() if activity.due_at else None,
        },
    )


# ---------------------------------------------------------------------------
# V2.5 — Level advancement & induction
# ---------------------------------------------------------------------------

def notify_level_advanced(user, previous_level, new_level, confirmed_by=None):
    from accounts.context_processors import LEVEL_NAMES
    new_name = LEVEL_NAMES.get(new_level, f'Level {new_level}')
    confirmer = confirmed_by.display_name if confirmed_by and hasattr(confirmed_by, 'display_name') else 'a steward'
    create_notification(
        user=user,
        notification_type='level_advanced',
        title=f'You have advanced to {new_name} — Level {new_level}',
        body=f'Confirmed by {confirmer}. Your formation journey continues — keep going.',
        data={
            'previous_level': previous_level,
            'new_level': new_level,
            'url': '/accounts/formation/',
        },
    )


def notify_induction_completed(user, placement_tenant_name):
    create_notification(
        user=user,
        notification_type='induction_completed',
        title='Induction complete — welcome to the community!',
        body=f'You have been placed in {placement_tenant_name}. Your journey as a Foundational Disciple begins now.',
        data={
            'placement_tenant': placement_tenant_name,
            'url': '/accounts/formation/',
        },
    )


# ---------------------------------------------------------------------------
# V2.5 — Tenant invitation & membership
# ---------------------------------------------------------------------------

def notify_tenant_invitation(email, tenant, invited_by, token):
    from accounts.models import User
    from django.urls import reverse
    accept_url = reverse('tenants:invitation-accept', kwargs={'token': token})

    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        # Not a registered user yet — email only, no in-app notification
        from .tasks import send_notification_email
        body = (
            f"{invited_by.display_name if hasattr(invited_by, 'display_name') else invited_by.email} "
            f"has invited you to join {tenant.name} on the Ichebo platform.\n\n"
            f"Accept your invitation at: {accept_url}"
        )
        send_notification_email.delay(email, f"You've been invited to join {tenant.name}", body)
        return
    create_notification(
        user=user,
        notification_type='tenant_invitation',
        title=f"You've been invited to join {tenant.name}",
        body=(
            f"{invited_by.display_name if hasattr(invited_by, 'display_name') else invited_by.email} "
            f"has invited you to join this community."
        ),
        data={
            'tenant_id': str(tenant.id),
            'tenant_name': tenant.name,
            'token': token,
            'url': accept_url,
        },
    )


def notify_member_added(user, tenant):
    create_notification(
        user=user,
        notification_type='member_added',
        title=f'You are now a member of {tenant.name}',
        body='Your membership has been confirmed. Welcome to the community.',
        data={
            'tenant_id': str(tenant.id),
            'tenant_name': tenant.name,
            'url': '/community/',
        },
    )


def notify_member_removed(user, tenant):
    create_notification(
        user=user,
        notification_type='member_removed',
        title=f'You have been removed from {tenant.name}',
        body='Your membership in this community has ended. Contact the steward for more information.',
        data={
            'tenant_id': str(tenant.id),
            'tenant_name': tenant.name,
        },
    )


# ---------------------------------------------------------------------------
# Community — member-to-steward support requests
# ---------------------------------------------------------------------------

def notify_support_request_created(record):
    steward_id = (record.custom_fields or {}).get('assigned_steward_id')
    if not steward_id:
        return  # needs-routing case — no recipient yet
    from accounts.models import User
    try:
        steward = User.objects.get(id=steward_id)
    except User.DoesNotExist:
        return
    create_notification(
        user=steward,
        notification_type='support_request_created',
        title=f'New support request: {record.title}',
        body=(record.content or '')[:200],
        data={
            'record_id': str(record.id),
            'url': f'/community/support/{record.id}/',
        },
    )


def notify_support_request_acknowledged(record):
    create_notification(
        user=record.created_by,
        notification_type='support_request_acknowledged',
        title='Your support request has been seen',
        body='A steward has acknowledged your request and is working on it.',
        data={
            'record_id': str(record.id),
            'url': f'/community/support/{record.id}/',
        },
    )


# ---------------------------------------------------------------------------
# V2.6 — Content approval
# ---------------------------------------------------------------------------

def notify_content_approved(record, approved_by):
    approver = getattr(approved_by, 'display_name', None) or approved_by.email
    rtype = record.record_type.title()
    create_notification(
        user=record.created_by,
        notification_type='mandate_published',
        title=f'Your {rtype} is approved: {record.title}',
        body=f'Approved by {approver}. Go to your Authorship page to publish it when ready.',
        data={
            'record_id': str(record.id),
            'record_type': record.record_type,
            'url': '/learn/author/',
        },
    )


def notify_content_published(record, published_by):
    publisher = getattr(published_by, 'display_name', None) or published_by.email
    rtype = record.record_type.title()
    detail_url = (
        f'/learn/lesson/{record.id}/' if record.record_type in ('lesson', 'assignment', 'quiz')
        else f'/learn/course/{record.id}/' if record.record_type == 'course'
        else f'/learn/programme/{record.id}/'
    )
    # Notify author only if someone else published on their behalf
    if published_by.id != record.created_by_id:
        create_notification(
            user=record.created_by,
            notification_type='mandate_published',
            title=f'Your {rtype} is now live: {record.title}',
            body=f'Published by {publisher}. Learners can now access it.',
            data={'record_id': str(record.id), 'record_type': record.record_type, 'url': detail_url},
        )
