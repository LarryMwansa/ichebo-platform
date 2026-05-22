import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_email(self, recipient_email, subject, message):
    """Send a Brevo SMTP email asynchronously. Retries up to 3 times on failure."""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@ichebo.com'),
            recipient_list=[recipient_email],
            fail_silently=False,
        )
    except Exception as exc:
        logger.exception('Email task failed for %s', recipient_email)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_fcm_push(self, user_id, title, body, data=None):
    """Send FCM push notification to a single user asynchronously. Retries up to 3 times."""
    from accounts.models import User
    from notifications.fcm import send_push_notification
    try:
        user = User.objects.get(id=user_id)
        send_push_notification(user, title, body, data or {})
    except User.DoesNotExist:
        logger.info('FCM push skipped — user %s not found', user_id)
    except Exception as exc:
        logger.exception('FCM task failed for user %s', user_id)
        raise self.retry(exc=exc)
