import secrets
import uuid

from django.conf import settings
from django.db import models


class BroadcastSchedule(models.Model):
    """
    A scheduled live broadcast session.
    Created by a Level 3+ steward via the Studio UI.
    One stream key is generated per broadcast and issued to the broadcaster.
    The Go Video Engine validates the key on RTMP ingest.
    """
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('live',      'Live'),
        ('ended',     'Ended'),
        ('cancelled', 'Cancelled'),
    ]

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant         = models.ForeignKey(
        'tenants.Tenant', on_delete=models.PROTECT, related_name='broadcasts',
    )
    created_by     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='broadcasts_created',
    )
    title          = models.CharField(max_length=255)
    description    = models.TextField(blank=True)
    scheduled_at   = models.DateTimeField(db_index=True)
    duration_minutes = models.IntegerField(default=60)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', db_index=True)

    # Stream key — generated once, never regenerated after issue.
    stream_key     = models.CharField(max_length=64, unique=True, editable=False)

    # Filled in when the stream goes live (from the Go engine start webhook).
    rtmp_url       = models.CharField(max_length=500, blank=True)
    hls_url        = models.CharField(max_length=500, blank=True)

    # Filled in after archive is complete.
    vod_url        = models.CharField(max_length=500, blank=True)

    # Optional link to a Gathering Record for this broadcast.
    gathering_record = models.ForeignKey(
        'records.Record', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='broadcasts',
    )

    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_at']

    def save(self, *args, **kwargs):
        if not self.stream_key:
            self.stream_key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    @property
    def rtmp_ingest_url(self):
        base = getattr(settings, 'MEDIAMTX_RTMP_URL', 'rtmp://media.ichebo.org/live')
        return f'{base}/{self.stream_key}'

    @property
    def viewer_hls_url(self):
        if self.hls_url:
            return self.hls_url
        base = getattr(settings, 'MEDIAMTX_HLS_BASE_URL', 'https://cdn.ichebo.org/live')
        return f'{base}/{self.stream_key}/index.m3u8'

    def __str__(self):
        return f'Broadcast({self.title}, {self.status})'
