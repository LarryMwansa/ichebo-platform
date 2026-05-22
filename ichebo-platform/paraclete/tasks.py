import logging

from celery import shared_task
from django.core.cache import cache

logger = logging.getLogger(__name__)


@shared_task
def refresh_paraclete_digest(user_id):
    """Pre-compute and cache the Paraclete digest for a single user (10-min TTL)."""
    from accounts.models import User
    from paraclete.service import build_digest
    from paraclete.serializers import ParacleteDigestSerializer
    try:
        user = User.objects.get(id=user_id)
        digest = build_digest(user)
        data = ParacleteDigestSerializer(digest).data
        cache.set(f'paraclete_digest_{user_id}', data, 600)
    except Exception:
        logger.exception('Failed to refresh Paraclete digest for user %s', user_id)


@shared_task
def refresh_all_active_digests():
    """Scheduled every 10 minutes — refreshes digests for all active users."""
    from accounts.models import User
    user_ids = list(
        User.objects.filter(is_active=True, status='active').values_list('id', flat=True)
    )
    for uid in user_ids:
        refresh_paraclete_digest.delay(str(uid))
