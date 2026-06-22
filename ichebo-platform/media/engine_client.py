"""
media/engine_client.py — resilient HTTP client for calls to the Go Video Engine.

The Go engine retries its outbound webhook to Django 3x with backoff before
giving up (pkg/webhook/webhook.go). The Django -> Go direction previously had
no retries at all - a single transient blip (e.g. the engine mid-restart
during a deploy) failed the request immediately. This mirrors the same
retry/backoff shape on this side so a few seconds of unavailability doesn't
surface as a hard failure to the end user.
"""
import logging
import time

import requests

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
BACKOFF_SECONDS = (1, 2)  # delay before attempt 2, before attempt 3


def post_with_retry(url, json=None, timeout=15):
    """POST with up to MAX_ATTEMPTS attempts and short backoff between tries.

    Raises the last exception if all attempts fail - callers keep their
    existing try/except handling unchanged, they just see fewer transient
    failures in practice.
    """
    last_exc = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = requests.post(url, json=json, timeout=timeout)
            resp.raise_for_status()
            return resp
        except Exception as exc:
            last_exc = exc
            if attempt < MAX_ATTEMPTS:
                delay = BACKOFF_SECONDS[attempt - 1]
                logger.warning(
                    'Video engine call failed (attempt %d/%d): %s — retrying in %ds',
                    attempt, MAX_ATTEMPTS, exc, delay,
                )
                time.sleep(delay)
            else:
                logger.error(
                    'Video engine call failed after %d attempts: %s', MAX_ATTEMPTS, exc,
                )
    raise last_exc
