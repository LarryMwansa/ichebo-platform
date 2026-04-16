"""
accounts/authentication.py

Custom DRF token authentication with configurable expiry.
Tokens older than settings.TOKEN_LIFETIME_DAYS (default 90) are automatically
deleted and the request is rejected with 401.

No migration required — uses DRF Token's existing `created` DateTimeField.
"""
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

_DEFAULT_LIFETIME_DAYS = 90


class ExpiringTokenAuthentication(TokenAuthentication):
    """
    DRF TokenAuthentication subclass that enforces a maximum token lifetime.

    Configuration:
        TOKEN_LIFETIME_DAYS = 90  # in settings/base.py or settings/production.py

    On expiry:
        - Token is deleted from the DB (forcing re-login)
        - 401 AuthenticationFailed is raised with code='token_expired'
    """

    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)

        lifetime = timedelta(
            days=getattr(settings, 'TOKEN_LIFETIME_DAYS', _DEFAULT_LIFETIME_DAYS)
        )

        if timezone.now() - token.created > lifetime:
            token.delete()
            raise AuthenticationFailed(
                'Token has expired. Please log in again.',
                code='token_expired',
            )

        return (user, token)
