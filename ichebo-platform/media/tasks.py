"""
media/tasks.py — recovers media Records stuck in status='draft' when the Go
Video Engine's webhook delivery to Django failed.

The engine retries its webhook 3x with backoff (pkg/webhook/webhook.go), then
gives up silently if all attempts fail — the transcode job completes on the
engine side but the Record never finds out, staying status='draft' forever.
This task closes that gap by polling the engine's existing job-status
endpoint for any stuck job, rather than introducing new persisted state on
either side.

Note: the engine's job queue is in-memory only (pkg/transcode/queue.go). If
mediad itself restarts between job completion and this task's next run, the
job is gone and a 404 is the best this can do — this recovers from transient
network/webhook failures, not from the engine process restarting.
"""
import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

import requests

from .models import TranscodeJob

logger = logging.getLogger(__name__)

STUCK_THRESHOLD_MINUTES = 5


@shared_task
def reconcile_stuck_transcode_jobs():
    """Scheduled periodically — finds draft media Records whose transcode job
    is older than STUCK_THRESHOLD_MINUTES and polls the engine directly."""
    from records.models import Record

    cutoff = timezone.now() - timezone.timedelta(minutes=STUCK_THRESHOLD_MINUTES)
    stuck_jobs = TranscodeJob.objects.filter(
        status__in=['queued', 'processing'],
        created_at__lt=cutoff,
        record__status='draft',
        record__record_family='media',
    ).select_related('record')

    for job in stuck_jobs:
        reconcile_transcode_job.delay(str(job.id))


@shared_task
def reconcile_transcode_job(transcode_job_id):
    """Polls the engine for a single job's true status and applies it,
    exactly as TranscodeCompleteWebhookView would have done."""
    try:
        job = TranscodeJob.objects.select_related('record').get(id=transcode_job_id)
    except TranscodeJob.DoesNotExist:
        return

    engine_url = getattr(settings, 'MEDIA_ENGINE_URL', 'http://localhost:8090')
    try:
        resp = requests.get(
            f'{engine_url}/engine/transcode/{job.job_id}/status',
            timeout=10,
        )
        if resp.status_code == 404:
            # Job is gone from the engine's in-memory queue — most likely the
            # engine restarted. Nothing to reconcile against; leave as-is for
            # manual investigation rather than guessing at a status.
            logger.warning(
                'Transcode job %s not found on engine — likely lost to an engine restart',
                job.job_id,
            )
            return
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        logger.exception('Failed to poll engine for transcode job %s', job.job_id)
        return

    engine_status = data.get('status', '')
    if engine_status not in ('complete', 'failed'):
        return  # still genuinely in progress — nothing to reconcile yet

    record = job.record
    job.status = engine_status
    job.progress_pct = data.get('progress_pct', 0)
    job.error = data.get('error', '')
    job.completed_at = timezone.now()
    job.save(update_fields=['status', 'progress_pct', 'error', 'completed_at'])

    record.custom_fields.update({
        'transcoding_status': engine_status,
        'video_url': data.get('video_url', ''),
        'thumbnail_url': data.get('thumbnail_url', ''),
        'duration_seconds': data.get('duration_seconds', 0),
    })
    if engine_status == 'complete':
        record.status = 'active'
    record.save(update_fields=['custom_fields', 'status'])

    logger.info(
        'Reconciled transcode job %s for record %s — status=%s (webhook delivery had been lost)',
        job.job_id, record.id, engine_status,
    )
