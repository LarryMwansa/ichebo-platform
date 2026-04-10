import uuid
from django.db import models
from django.conf import settings


class Activity(models.Model):
    ACTIVITY_TYPE_CHOICES = [
        ('task', 'Task'),
        ('habit', 'Habit'),
        ('goal', 'Goal'),
        ('event', 'Event'),
        ('campaign', 'Campaign'),
        ('project', 'Project'),
        ('programme', 'Programme'),
        ('reminder', 'Reminder'),
        ('skill', 'Skill'),
    ]
    RECURRENCE_CHOICES = [
        ('none', 'None'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('deferred', 'Deferred'),
    ]
    KGS_PILLAR_CHOICES = [
        ('apostolic', 'Apostolic'),
        ('strategy', 'Strategy'),
        ('formation', 'Formation'),
        ('programmes', 'Programmes'),
        ('mission', 'Mission'),
        ('communities', 'Communities'),
        ('stewardship', 'Stewardship'),
    ]
    KGS_PATHWAY_CHOICES = [
        ('new_life', 'New Life'),
        ('spiritual_formation', 'Spiritual Formation'),
        ('community_life', 'Community Life'),
        ('service', 'Service'),
        ('leadership', 'Leadership'),
        ('learning', 'Learning'),
        ('mission', 'Mission'),
        ('apostolic_stewardship', 'Apostolic Stewardship'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant', null=True, blank=True,
        on_delete=models.PROTECT, related_name='activities'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_activities'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Classification
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES)

    # Identity
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)

    # Timing
    scheduled_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    recurrence = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, default='none')
    recurrence_rule = models.TextField(blank=True, null=True)  # RRULE format for custom

    # Hierarchy (activities can nest: programme → project → campaign → task)
    parent_activity = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.PROTECT, related_name='child_activities'
    )

    # Progress
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField(default=0)  # 0-100

    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='assigned_activities'
    )

    # Activity ↔ Record linking via Relationship engine (NOT a local array)
    # No linked_record_ids field — all links go through records.Relationship

    # KGS alignment
    kgs_pillar = models.CharField(
        max_length=30, choices=KGS_PILLAR_CHOICES,
        null=True, blank=True
    )
    kgs_pathway = models.CharField(
        max_length=30, choices=KGS_PATHWAY_CHOICES,
        null=True, blank=True
    )

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    # {source_app, icon, color, is_template}

    class Meta:
        db_table = 'activity_activity'
        indexes = [
            models.Index(fields=['tenant']),
            models.Index(fields=['activity_type']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['due_at']),
            models.Index(fields=['created_by']),
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'activity_type']),
        ]

    def __str__(self):
        return f"{self.activity_type}: {self.title}"


class ActivityLog(models.Model):
    EVENT_TYPE_CHOICES = [
        ('created', 'Created'),
        ('status_changed', 'Status Changed'),
        ('progress_updated', 'Progress Updated'),
        ('assigned', 'Assigned'),
        ('linked', 'Linked'),
        ('commented', 'Commented'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant', null=True, blank=True,
        on_delete=models.PROTECT, related_name='activity_logs'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_activity_logs'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name='logs'
    )
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES)
    previous_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'activity_activitylog'
        indexes = [
            models.Index(fields=['activity']),
            models.Index(fields=['tenant']),
            models.Index(fields=['event_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.activity.title}: {self.event_type} on {self.created_at}"
