"""
notifications/service.py

Utility functions for creating Notification records.
Called by signal handlers — never by views directly.
All functions are fire-and-forget; errors are logged, never raised.
"""
import logging

logger = logging.getLogger(__name__)


def create_notification(user, notification_type, title, body='', data=None):
    """
    Create a Notification for `user`.

    Args:
        user: accounts.User instance
        notification_type: str — must match Notification.NOTIFICATION_TYPES choices
        title: str — short summary shown in notification list
        body: str — optional longer description
        data: dict — optional extra metadata (record_id, url, tenant_name, etc.)

    Returns:
        Notification instance, or None on error.
    """
    from .models import Notification

    try:
        n = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            body=body,
            data=data or {},
        )
        return n
    except Exception:
        logger.exception(
            'Failed to create notification type=%s for user=%s',
            notification_type,
            user.pk,
        )
        return None


def notify_membership_approved(membership_request):
    """Called when a steward approves a MembershipRequest."""
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
    """Called when a steward denies a MembershipRequest."""
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
    """Called from learn signal when a user earns a certification."""
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
    """Called when an activity is assigned to a user by someone else."""
    if not activity.assigned_to:
        return
    if activity.assigned_to == activity.created_by:
        return  # self-assigned — no notification needed
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
