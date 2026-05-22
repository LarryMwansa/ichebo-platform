import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class HandbookRecord(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_LOCKED = 'locked'
    STATUS_SUPERSEDED = 'superseded'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_LOCKED, 'Locked'),
        (STATUS_SUPERSEDED, 'Superseded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='handbook_records',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='handbook_records_created',
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, blank=True)
    content = models.TextField(blank=True)
    summary = models.TextField(blank=True)

    # Versioning
    version_number = models.PositiveIntegerField(default=1)
    previous_version = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='next_versions',
    )
    superseded_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='supersedes',
    )

    # Categorisation
    category = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)

    # Lifecycle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='handbook_records_locked',
    )
    published_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.title} (v{self.version_number})'

    def publish(self, user):
        self.status = self.STATUS_PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=['status', 'published_at', 'updated_at'])

    def lock(self, user):
        self.status = self.STATUS_LOCKED
        self.locked_at = timezone.now()
        self.locked_by = user
        self.save(update_fields=['status', 'locked_at', 'locked_by', 'updated_at'])

    def new_version(self, user):
        """Fork a new draft from this record."""
        return HandbookRecord.objects.create(
            tenant=self.tenant,
            created_by=user,
            title=self.title,
            content=self.content,
            summary=self.summary,
            category=self.category,
            tags=list(self.tags),
            version_number=self.version_number + 1,
            previous_version=self,
            status=self.STATUS_DRAFT,
        )


class HandbookAccess(models.Model):
    ROLE_READER = 'reader'
    ROLE_AUTHOR = 'author'
    ROLE_EDITOR = 'editor'
    ROLE_CHOICES = [
        (ROLE_READER, 'Reader'),
        (ROLE_AUTHOR, 'Author'),
        (ROLE_EDITOR, 'Editor'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='handbook_access',
    )
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
        unique_together = [('tenant', 'user')]

    def __str__(self):
        return f'{self.user} → {self.tenant} ({self.role})'
