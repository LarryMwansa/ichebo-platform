import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone

# ── Branch constants ──────────────────────────────────────────────────────────
BRANCH_REFERENCE = 'reference'
BRANCH_MANDATE = 'mandate'
BRANCH_KEYS = 'keys'

BRANCH_CHOICES = [
    (BRANCH_REFERENCE, 'Reference Library'),
    (BRANCH_MANDATE, 'Mandate Branch'),
    (BRANCH_KEYS, 'Keys Library'),
]

# Record types per branch — used for validation and UI grouping
RECORD_TYPES_BY_BRANCH = {
    BRANCH_REFERENCE: ['class', 'principle', 'concept', 'divine_pattern'],
    BRANCH_MANDATE: [
        'mandate', 'statement', 'framework', 'narrative',
        'subject', 'entity', 'protocol', 'procedure', 'programme',
    ],
    BRANCH_KEYS: ['key'],
}

ALL_RECORD_TYPES = [rt for rts in RECORD_TYPES_BY_BRANCH.values() for rt in rts]

RECORD_TYPE_CHOICES = [(rt, rt.replace('_', ' ').title()) for rt in ALL_RECORD_TYPES]

# HRS relationship types used within the Handbook
HRS_RELATIONSHIP_TYPES = [
    ('part_of',        'Part Of'),
    ('derived_from',   'Derived From'),
    ('aligns_with',    'Aligns With'),
    ('authorised_by',  'Authorised By'),
    ('references',     'References'),
    ('has_symbol',     'Has Symbol'),
    ('matches_pattern','Matches Pattern'),
]


class HandbookRecord(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_ACTIVE = 'active'
    STATUS_LOCKED = 'locked'
    STATUS_SUPERSEDED = 'superseded'
    STATUS_CHOICES = [
        (STATUS_DRAFT,      'Draft'),
        (STATUS_ACTIVE,     'Active'),
        (STATUS_LOCKED,     'Locked'),
        (STATUS_SUPERSEDED, 'Superseded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='handbook_records_created',
    )

    # Core fields
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, blank=True)
    content = models.TextField(blank=True)
    summary = models.TextField(blank=True)

    # Branch + record type
    branch = models.CharField(max_length=20, choices=BRANCH_CHOICES, default=BRANCH_REFERENCE)
    record_type = models.CharField(max_length=30, choices=RECORD_TYPE_CHOICES, default='principle')

    # HRS attributes — Reference Library records only. Free-text, no enum constraint.
    hrs_complexity = models.CharField(max_length=100, blank=True)
    hrs_relationship_position = models.CharField(max_length=100, blank=True)
    hrs_position = models.CharField(max_length=100, blank=True)
    hrs_direction = models.CharField(max_length=100, blank=True)
    hrs_speed = models.CharField(max_length=100, blank=True)
    hrs_emotional_tone = models.CharField(max_length=100, blank=True)

    # Tags
    tags = models.JSONField(default=list, blank=True)

    # Versioning chain
    version_number = models.PositiveIntegerField(default=1)
    previous_version = models.ForeignKey(
        'self',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='next_versions',
    )
    superseded_by = models.ForeignKey(
        'self',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='supersedes',
    )

    # Lifecycle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='handbook_records_locked',
    )
    published_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['branch', 'record_type', '-updated_at']

    def __str__(self):
        return f'{self.title} (v{self.version_number})'

    @property
    def is_reference_library(self):
        return self.branch == BRANCH_REFERENCE

    @property
    def branch_label(self):
        return dict(BRANCH_CHOICES).get(self.branch, self.branch)

    def publish(self, user):
        self.status = self.STATUS_ACTIVE
        self.published_at = timezone.now()
        self.save(update_fields=['status', 'published_at', 'updated_at'])

    def lock(self, user):
        self.status = self.STATUS_LOCKED
        self.locked_at = timezone.now()
        self.locked_by = user
        self.save(update_fields=['status', 'locked_at', 'locked_by', 'updated_at'])

    def new_version(self, user):
        new = HandbookRecord.objects.create(
            created_by=user,
            title=self.title,
            content=self.content,
            summary=self.summary,
            branch=self.branch,
            record_type=self.record_type,
            hrs_complexity=self.hrs_complexity,
            hrs_relationship_position=self.hrs_relationship_position,
            hrs_position=self.hrs_position,
            hrs_direction=self.hrs_direction,
            hrs_speed=self.hrs_speed,
            hrs_emotional_tone=self.hrs_emotional_tone,
            tags=list(self.tags),
            version_number=self.version_number + 1,
            previous_version=self,
            status=self.STATUS_DRAFT,
        )
        # Mark this record as superseded
        self.superseded_by = new
        self.status = self.STATUS_SUPERSEDED
        self.save(update_fields=['superseded_by', 'status', 'updated_at'])
        return new


class HandbookRelationship(models.Model):
    """HRS relationship between two HandbookRecords, or from a HandbookRecord to a BibleVerse."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True,
        related_name='handbook_relationships_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    from_record = models.ForeignKey(
        HandbookRecord,
        on_delete=models.CASCADE,
        related_name='outgoing_relationships',
    )
    to_record = models.ForeignKey(
        HandbookRecord,
        on_delete=models.CASCADE,
        related_name='incoming_relationships',
        null=True, blank=True,
    )
    bible_verse = models.ForeignKey(
        'bible.BibleVerse',
        on_delete=models.CASCADE,
        related_name='handbook_references',
        null=True, blank=True,
    )

    relationship_type = models.CharField(
        max_length=30,
        choices=HRS_RELATIONSHIP_TYPES,
        default='references',
    )
    direction = models.CharField(
        max_length=20,
        choices=[('directed', 'Directed'), ('bidirectional', 'Bidirectional')],
        default='directed',
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['relationship_type']

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.to_record is None and self.bible_verse is None:
            raise ValidationError('Must target either a HandbookRecord or a BibleVerse.')
        if self.to_record is not None and self.bible_verse is not None:
            raise ValidationError('Cannot target both a HandbookRecord and a BibleVerse.')

    def __str__(self):
        target = self.to_record or self.bible_verse
        return f'{self.from_record.title} —[{self.relationship_type}]→ {target}'


class HandbookAccess(models.Model):
    ROLE_READER = 'reader'   # Level 3-4 read access
    ROLE_AUTHOR = 'author'   # Level 5 write access
    ROLE_EDITOR = 'editor'   # Level 5 + admin (access management)
    ROLE_CHOICES = [
        (ROLE_READER, 'Reader'),
        (ROLE_AUTHOR, 'Author'),
        (ROLE_EDITOR, 'Editor'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='handbook_access',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_READER)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='handbook_access_granted',
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # One access record per user — no tenant scoping, Handbook is global
        unique_together = [('user',)]

    def __str__(self):
        return f'{self.user} ({self.role})'
