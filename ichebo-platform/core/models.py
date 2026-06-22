import hashlib
import json
import uuid

from django.conf import settings
from django.db import models


SYNCABLE_ENTITY_TYPES = (
    'record',
    'relationship',
    'activity',
    'member',          # User + UserPermission
    'notification',
    'certification',   # CertificationConfirmation
    'membership',      # MembershipRequest
    'tenant',
)

OP_CREATE = 'CREATE'
OP_UPDATE = 'UPDATE'
OP_DELETE = 'DELETE'


class SyncChangelog(models.Model):
    """
    Append-only journal of every write to a syncable entity on the cloud.

    Mirrors the Go pkg/changelog.Entry struct (DOC C §3.2).
    The Sync Engine's push endpoint reads this to detect conflicts.
    The pull endpoint uses updated_at on source models — this table is for
    push conflict detection and the desktop's pending-sync audit trail.

    Invariants (enforced at write sites, not DB constraints):
    - Rows are never updated or deleted.
    - payload_hash is SHA-256 of the serialised entity JSON at write time.
    - Every entity write and its changelog entry are committed atomically.
    """

    OPERATION_CHOICES = [
        (OP_CREATE, 'Create'),
        (OP_UPDATE, 'Update'),
        (OP_DELETE, 'Delete'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entity_type = models.CharField(max_length=30)
    entity_id = models.UUIDField(db_index=True)
    operation = models.CharField(max_length=10, choices=OPERATION_CHOICES)
    changed_at = models.DateTimeField(db_index=True)
    device_id = models.UUIDField(null=True, blank=True)  # null = cloud-originated write
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='changelog_entries',
    )
    payload_hash = models.CharField(max_length=64)  # SHA-256 hex digest
    synced_at = models.DateTimeField(null=True, blank=True)  # null = not yet ack'd by desktop

    class Meta:
        db_table = 'core_sync_changelog'
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['changed_at']),
            models.Index(fields=['synced_at']),
        ]
        ordering = ['changed_at']

    def __str__(self):
        return f'{self.operation} {self.entity_type}:{self.entity_id} @ {self.changed_at}'

    @staticmethod
    def compute_hash(payload: dict) -> str:
        canonical = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()


class PlatformConfig(models.Model):
    """
    Singleton row tracking platform bootstrap state and a handful of
    settings a Level 5 steward should be able to change without a code
    deploy. See .docs/plans/platform-bootstrap-plan.md.

    Uses a fixed, well-known UUID as its primary key (not an auto-incrementing
    integer) per the platform-wide UUID PK rule (core/apps.py:check_uuid_primary_keys)
    — every model must carry a permanent identity for Sync Engine compatibility,
    even a singleton with no sync requirement of its own.

    Always fetch via PlatformConfig.get_solo() — never .objects.create()
    or .objects.get(pk=...) directly.
    """
    SINGLETON_ID = uuid.UUID('00000000-0000-0000-0000-000000000001')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bootstrapped_at = models.DateTimeField(null=True, blank=True)
    bootstrapped_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
    )
    bootstrap_version = models.CharField(max_length=20, default='', blank=True)

    # ── Email verification toggle ───────────────────────────────────────────
    # When True: new users start status='pending_verification' and must verify
    # before login. When False: new users start status='seeker' immediately.
    require_email_verification = models.BooleanField(default=True)

    # ── Library access gates ────────────────────────────────────────────────
    # Minimum competence_level required to access each library. Defaults
    # match the constants these replace in governance/views.py and
    # handbook/views.py (not yet wired to read from here — see plan §
    # "Access Gating Configuration", deferred to the /platform/ UI phase).
    mandate_access_level = models.IntegerField(default=4)
    keys_access_level = models.IntegerField(default=4)
    reference_access_level = models.IntegerField(default=3)

    class Meta:
        db_table = 'core_platform_config'

    def save(self, *args, **kwargs):
        self.pk = self.SINGLETON_ID
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # singleton — never actually deleted

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=cls.SINGLETON_ID)
        return obj

    def __str__(self):
        return f'PlatformConfig(bootstrapped={bool(self.bootstrapped_at)})'
