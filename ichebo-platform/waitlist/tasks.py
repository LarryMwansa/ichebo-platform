from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_waitlist_confirmation(self, entry_id):
    from .models import WaitlistEntry
    try:
        entry = WaitlistEntry.objects.get(id=entry_id)
        send_mail(
            subject='You are on the list — Ichebo Christian Services',
            message=(
                f'Dear {entry.name},\n\n'
                'Thank you for registering your interest in the Sceptre Community Programme.\n\n'
                'We are forming the first communities as the Ichebo Platform reaches completion. '
                'We will be in touch with you personally when we are ready to bring the founding '
                'communities on board.\n\n'
                'You do not need to do anything further. We have your details and will reach out directly.\n\n'
                'Ichebo Christian Services\n'
                'ichebo.org'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[entry.email],
            fail_silently=False,
        )
        entry.notified = True
        entry.save(update_fields=['notified'])
    except WaitlistEntry.DoesNotExist:
        pass
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_waitlist_notification(self, entry_id):
    from .models import WaitlistEntry
    try:
        entry = WaitlistEntry.objects.get(id=entry_id)
        send_mail(
            subject=f'New waitlist registration — {entry.get_path_display()}',
            message=(
                f'New waitlist registration received.\n\n'
                f'Name: {entry.name}\n'
                f'Email: {entry.email}\n'
                f'Path: {entry.get_path_display()}\n'
                f'Registered: {entry.created_at.strftime("%Y-%m-%d %H:%M UTC")}\n'
                f'IP: {entry.ip_address or "not captured"}\n\n'
                f'View all entries: https://app.ichebo.org/admin/waitlist/waitlistentry/'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['info@ichebo.org'],
            fail_silently=False,
        )
    except WaitlistEntry.DoesNotExist:
        pass
    except Exception as exc:
        raise self.retry(exc=exc)
