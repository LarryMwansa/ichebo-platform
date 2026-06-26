import uuid

from django.conf import settings
from django.db import models

from core.managers import SoftDeleteMixin

CONTENT_TYPE_CHOICES = [
    ('vod', 'Video on Demand'),
    ('live', 'Live Broadcast'),
]


class ChannelConfig(SoftDeleteMixin, models.Model):
    """Per-tenant channel configuration — one row per Sceptre Community
    tenant. Holds the fallback hierarchy for the Ichebo Channel: a loop
    default and a rotating fallback playlist, used when nothing is
    scheduled and no live broadcast is active (ADR-024)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='channel_config',
    )
    # The id of a records.Record with record_family='media' — resolved at
    # read time via media.models.VideoRecord(record), a typed wrapper
    # around Record, not a separate model with its own primary key.
    loop_default_video_id = models.UUIDField(null=True, blank=True)
    # Ordered list of media-family Record UUIDs (strings)
    fallback_playlist = models.JSONField(default=list, blank=True)
    # Current index in fallback_playlist — advances on each resolution call
    fallback_position = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='channel_configs_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Channel Configuration'
        verbose_name_plural = 'Channel Configurations'

    def __str__(self):
        return f'ChannelConfig for {self.tenant}'


class ChannelSlot(SoftDeleteMixin, models.Model):
    """A scheduled programme-grid entry on the Ichebo Channel — either a
    VOD playback window or a live broadcast window, resolved ahead of the
    fallback playlist/loop default (ADR-024)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='channel_slots',
    )
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)
    # id of a records.Record with record_family='media', for content_type='vod'
    video_record_id = models.UUIDField(null=True, blank=True)
    # id of a video_live.BroadcastSchedule, for content_type='live'
    broadcast_schedule_id = models.UUIDField(null=True, blank=True)
    # Denormalised — avoids a join on every now-playing resolution call
    title = models.CharField(max_length=255)
    is_recurring = models.BooleanField(default=False)
    # RRULE string — deferred, nullable in v1
    recurrence_rule = models.CharField(max_length=255, null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='channel_slots_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_start']
        indexes = [
            models.Index(fields=['tenant', 'scheduled_start', 'scheduled_end']),
        ]

    def __str__(self):
        return f'{self.title} ({self.scheduled_start:%Y-%m-%d %H:%M})'
