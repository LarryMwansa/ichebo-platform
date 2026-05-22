import uuid
from django.db import models
from django.conf import settings
from core.managers import SoftDeleteMixin


class Record(SoftDeleteMixin, models.Model):
    RECORD_CLASS_CHOICES = [
        ('personal', 'Personal'),
        ('organizational', 'Organizational'),
        ('governance', 'Governance'),
    ]
    RECORD_FAMILY_CHOICES = [
        ('journal', 'Journal'),
        ('governance', 'Governance'),
        ('activity', 'Activity'),
        ('learning', 'Learning'),
        ('reference', 'Reference'),
        ('bible', 'Bible'),
        ('community', 'Community'),
        ('media', 'Media'),
    ]
    ORIGIN_CHOICES = [
        ('user', 'User'),
        ('system', 'System'),
        ('paraclete', 'Paraclete'),
        ('import', 'Import'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
        ('locked', 'Locked'),
        ('superseded', 'Superseded'),
        ('submitted', 'Submitted'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant', null=True, blank=True,
        on_delete=models.PROTECT, related_name='records'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='records'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # deleted_at — provided by SoftDeleteMixin

    record_class = models.CharField(max_length=20, choices=RECORD_CLASS_CHOICES)
    record_family = models.CharField(max_length=20, choices=RECORD_FAMILY_CHOICES)
    record_type = models.CharField(max_length=50)
    origin = models.CharField(max_length=20, choices=ORIGIN_CHOICES, default='user')

    title = models.CharField(max_length=500)
    content = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='locked_records'
    )
    locked_at = models.DateTimeField(null=True, blank=True)

    # Governance versioning
    version = models.IntegerField(null=True, blank=True)
    previous_version = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='next_versions'
    )
    superseded_by = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='supersedes'
    )

    tags = models.JSONField(default=list, blank=True)
    categories = models.JSONField(default=list, blank=True)
    custom_fields = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    permissions_data = models.JSONField(default=dict, blank=True)
    # permissions_data structure: {visibility, required_level, roles_allowed, can_edit}

    class Meta:
        db_table = 'records_record'
        indexes = [
            models.Index(fields=['tenant']),
            models.Index(fields=['record_family']),
            models.Index(fields=['record_type']),
            models.Index(fields=['record_class']),
            models.Index(fields=['created_by']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['tenant', 'record_family']),
            models.Index(fields=['tenant', 'record_class']),
        ]

    def __str__(self):
        return f"{self.record_type}: {self.title}"


class Relationship(SoftDeleteMixin, models.Model):
    DIRECTION_CHOICES = [
        ('directed', 'Directed'),
        ('bidirectional', 'Bidirectional'),
    ]
    RELATIONSHIP_TYPE_CHOICES = [
        ('relates_to', 'Relates To'),
        ('derived_from', 'Derived From'),
        ('references', 'References'),
        ('answers', 'Answers'),
        ('fulfills', 'Fulfills'),
        ('requests', 'Requests'),
        ('has_symbol', 'Has Symbol'),
        ('matches_pattern', 'Matches Pattern'),
        ('assigned_to', 'Assigned To'),
        ('tracks', 'Tracks'),
        ('completes', 'Completes'),
        ('part_of', 'Part Of'),
        ('aligns_with', 'Aligns With'),
        ('authorised_by', 'Authorised By'),
        ('has_subject', 'Has Subject'),
        ('has_entity', 'Has Entity'),
        ('tagged_in', 'Tagged In'),
        ('community_ref', 'Community Reference'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant', null=True, blank=True,
        on_delete=models.PROTECT
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    # deleted_at — provided by SoftDeleteMixin

    from_record = models.ForeignKey(
        Record, on_delete=models.CASCADE, related_name='outgoing_relationships'
    )
    to_record = models.ForeignKey(
        Record, on_delete=models.CASCADE, related_name='incoming_relationships',
        null=True, blank=True
    )
    bible_verse = models.ForeignKey(
        'bible.BibleVerse',
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='governance_references'
    )

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.to_record is None and self.bible_verse is None:
            raise ValidationError("A Relationship must target either a Record or a BibleVerse.")
        if self.to_record is not None and self.bible_verse is not None:
            raise ValidationError("A Relationship cannot target both a Record and a BibleVerse.")

    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    relationship_type = models.CharField(max_length=30, choices=RELATIONSHIP_TYPE_CHOICES)
    notes = models.TextField(blank=True, null=True)
    # Extra context stored by the creating app (e.g. linked_activity_id for gathering dual-write)
    metadata = models.JSONField(default=dict, blank=True)
    strength = models.CharField(
        max_length=10,
        choices=[('weak','Weak'),('medium','Medium'),('strong','Strong')],
        null=True, blank=True
    )

    class Meta:
        db_table = 'records_relationship'
        indexes = [
            models.Index(fields=['from_record']),
            models.Index(fields=['to_record']),
            models.Index(fields=['bible_verse']),
            models.Index(fields=['relationship_type']),
        ]
