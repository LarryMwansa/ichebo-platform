import uuid
from django.db import models
from django.conf import settings

class Activity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenants.Tenant', null=True, blank=True,
                               on_delete=models.SET_NULL, related_name='activities')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.PROTECT,
                                   related_name='created_activities')
    created_at = models.DateTimeField(auto_now_add=True)

    ACTIVITY_TYPES = [
        ('task', 'Task'), ('habit', 'Habit'), ('goal', 'Goal'),
        ('event', 'Event'), ('campaign', 'Campaign'), ('project', 'Project'),
        ('programme', 'Programme'), ('reminder', 'Reminder'), ('skill', 'Skill'),
    ]
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    scheduled_at = models.DateTimeField(null=True, blank=True, db_index=True)
    due_at = models.DateTimeField(null=True, blank=True, db_index=True)
    recurrence = models.CharField(
        max_length=10,
        choices=[('none','None'),('daily','Daily'),('weekly','Weekly'),
                 ('monthly','Monthly'),('custom','Custom')],
        default='none'
    )
    recurrence_rule = models.CharField(max_length=500, blank=True, null=True)

    parent_activity = models.ForeignKey('self', null=True, blank=True,
                                        on_delete=models.SET_NULL,
                                        related_name='child_activities',
                                        db_index=True)

    STATUS_CHOICES = [
        ('pending','Pending'), ('in_progress','In Progress'),
        ('completed','Completed'), ('cancelled','Cancelled'), ('deferred','Deferred'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField(default=0)

    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name='assigned_activities',
                                    db_index=True)

    KGS_PILLARS = [
        ('apostolic','Apostolic'), ('strategy','Strategy'),
        ('formation','Formation'), ('programmes','Programmes'),
        ('mission','Mission'), ('communities','Communities'),
        ('stewardship','Stewardship'),
    ]
    KGS_PATHWAYS = [
        ('new_life','New Life'), ('spiritual_formation','Spiritual Formation'),
        ('community_life','Community Life'), ('service','Service'),
        ('leadership','Leadership'), ('learning','Learning'),
        ('mission','Mission'), ('apostolic_stewardship','Apostolic Stewardship'),
    ]
    kgs_pillar = models.CharField(max_length=30, choices=KGS_PILLARS,
                                  blank=True, null=True)
    kgs_pathway = models.CharField(max_length=30, choices=KGS_PATHWAYS,
                                   blank=True, null=True)

    metadata = models.JSONField(default=dict, blank=True)
    # metadata keys: source_app, icon, color, is_template, template_id, service_order

    linked_record = models.ForeignKey(
        'records.Record', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='linked_activities'
    )

    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant']),
            models.Index(fields=['activity_type']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['status']),
            models.Index(fields=['due_at']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['parent_activity']),
            models.Index(fields=['created_by']),
            models.Index(fields=['tenant', 'activity_type']),
            models.Index(fields=['tenant', 'assigned_to']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['assigned_to', 'due_at']),
        ]

    def __str__(self):
        return f"{self.activity_type}: {self.title}"


class ActivityLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='logs')
    tenant = models.ForeignKey('tenants.Tenant', null=True, blank=True, on_delete=models.SET_NULL)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    event_type = models.CharField(max_length=50)
    previous_value = models.CharField(max_length=255, blank=True, null=True)
    new_value = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['activity']),
            models.Index(fields=['event_type']),
        ]
