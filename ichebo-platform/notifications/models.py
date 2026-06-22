"""
notifications/models.py

Notification model — delivered in-app to individual users.
Created via signals from community, learn, activity, and governance apps.
"""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from core.managers import SoftDeleteMixin


class Notification(SoftDeleteMixin, models.Model):
    NOTIFICATION_TYPES = [
        ('membership_approved',  'Membership Approved'),
        ('membership_denied',    'Membership Denied'),
        ('activity_assigned',    'Activity Assigned'),
        ('activity_completed',   'Activity Completed'),
        ('lesson_completed',     'Lesson Completed'),
        ('certification_earned', 'Certification Earned'),
        ('level_advanced',       'Level Advanced'),
        ('induction_completed',  'Induction Completed'),
        ('announcement',         'Community Announcement'),
        ('mandate_published',    'Mandate Published'),
        ('tenant_invitation',    'Community Invitation'),
        ('member_added',         'Added to Community'),
        ('member_removed',       'Removed from Community'),
        ('support_request_created',      'Support Request Created'),
        ('support_request_acknowledged', 'Support Request Acknowledged'),
        ('live_request_raised',          'Live Request Raised'),
        ('system',               'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
        default='system',
    )
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    # Extra metadata: record_id, tenant_id, activity_id, url, etc.
    data = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    # deleted_at — provided by SoftDeleteMixin

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'read_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['user', 'updated_at']),
        ]

    def __str__(self):
        return f'[{self.notification_type}] {self.title} → {self.user_id}'

    @property
    def is_read(self):
        return self.read_at is not None

    def mark_read(self):
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])
