import uuid
import secrets
from django.db import models
from django.conf import settings
from django.utils import timezone
from core.managers import SoftDeleteMixin


class Tenant(SoftDeleteMixin, models.Model):
    TIER_CHOICES = [
        ('handbook', 'Handbook'),
        ('induction', 'Induction'),
        ('church_node', 'Church Node'),
        ('church_collective', 'Church Collective'),
        ('district', 'District'),
        ('provincial', 'Provincial'),
        ('national', 'National'),
        ('regional', 'Regional'),
        ('continental', 'Continental'),
        ('global', 'Global'),
    ]
    AFFILIATION_CHOICES = [
        ('ichebo', 'Ichebo'),
        ('independent', 'Independent'),
        ('affiliate', 'Affiliate'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('suspended', 'Suspended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.PROTECT, related_name='children'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_tenants'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    # Materialized path — e.g. /global/africa/southafrica/gauteng/pretoria/
    path = models.CharField(max_length=500, db_index=True)

    tier = models.CharField(max_length=30, choices=TIER_CHOICES)
    affiliation = models.CharField(max_length=20, choices=AFFILIATION_CHOICES, default='independent')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_collective = models.BooleanField(default=False)

    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)

    is_agency = models.BooleanField(default=False)
    coordinator_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='coordinating_tenants'
    )
    community_theme = models.CharField(max_length=100, blank=True)
    area_of_operation = models.TextField(blank=True)

    # Location (JSON field — PostgreSQL)
    location = models.JSONField(default=dict, blank=True)
    settings_data = models.JSONField(default=dict, blank=True)
    # deleted_at — provided by SoftDeleteMixin

    class Meta:
        db_table = 'tenants_tenant'
        indexes = [
            models.Index(fields=['path']),
            models.Index(fields=['tier']),
            models.Index(fields=['status']),
        ]

    def get_descendants(self):
        return Tenant.objects.filter(
            path__startswith=self.path
        ).exclude(pk=self.pk)

    def get_ancestors(self):
        parts = self.path.strip('/').split('/')
        ancestor_paths = [
            '/' + '/'.join(parts[:i+1]) + '/'
            for i in range(len(parts) - 1)
        ]
        return Tenant.objects.filter(path__in=ancestor_paths)

    @property
    def logo_url(self):
        return self.logo.url if self.logo else None

    def __str__(self):
        return f"{self.name} ({self.path})"


class UserPermission(SoftDeleteMixin, models.Model):
    ROLE_CHOICES = [
        ('seeker', 'Seeker'),
        ('beginner', 'Beginner'),
        ('disciple', 'Disciple'),
        ('branch-steward', 'Branch Steward'),
        ('district-steward', 'District Steward'),
        ('provincial-steward', 'Provincial Steward'),
        ('national-steward', 'National Steward'),
        ('regional-steward', 'Regional Steward'),
        ('continental-steward', 'Continental Steward'),
        ('global-steward', 'Global Steward'),
        ('admin', 'Admin'),
    ]

    # Roles that imply hierarchical oversight of descendant tenants, not
    # just the one tenant the role is granted on — e.g. a global-steward on
    # Prime Tenancy oversees every tenant under it, not only Prime itself.
    # Derived from ROLE_CHOICES (minus the three non-steward member roles)
    # so the two can't drift apart; was previously copy-pasted as a literal
    # set in four separate places (tenants/views.py's DRF API and three
    # spots in template_views.py) with no shared source of truth — see
    # get_oversight_tenant_ids in tenants/service.py, added 2026-06-24 after
    # a global-steward's own community went invisible to them: the API view
    # already walked this hierarchy correctly, the template-rendered pages
    # never did.
    STEWARD_ROLES = frozenset(
        role for role, _ in ROLE_CHOICES
        if role not in ('seeker', 'beginner', 'disciple')
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='permissions')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='tenant_permissions'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='granted_permissions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    tenant_path = models.CharField(max_length=500, db_index=True)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    level = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    granted_at = models.DateTimeField(auto_now_add=True)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='permissions_granted', null=True
    )

    # Metadata for Community and Governance features (v8 amendment)
    # shepherd_id: UUID of pastoral supervisor (Community feature)
    # service_order: KGS Service Order label (Community feature)
    metadata = models.JSONField(default=dict, blank=True)
    # deleted_at — provided by SoftDeleteMixin

    class Meta:
        db_table = 'tenants_userpermission'
        unique_together = [['tenant', 'user', 'role']]


class TenantInvitation(SoftDeleteMixin, models.Model):
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired',  'Expired'),
    ]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant     = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='invitations')
    email      = models.EmailField()
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='sent_invitations'
    )
    token      = models.CharField(max_length=64, unique=True)
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    accepted_at = models.DateTimeField(null=True, blank=True)
    expires_at  = models.DateTimeField()
    created_at  = models.DateTimeField(auto_now_add=True)
    # deleted_at — provided by SoftDeleteMixin

    class Meta:
        db_table = 'tenants_tenantinvitation'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(48)
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return self.status == 'pending' and timezone.now() > self.expires_at

    def __str__(self):
        return f"Invitation({self.email} → {self.tenant.name}, {self.status})"


class DesktopLicence(SoftDeleteMixin, models.Model):
    """
    One row per issued Desktop licence key.
    Staff issues keys via Django admin; stewards enter them in the activation wizard.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.PROTECT, related_name='desktop_licences'
    )
    licence_key = models.CharField(max_length=39, unique=True)  # XXXX-XXXX-XXXX-XXXX
    issued_at = models.DateTimeField(auto_now_add=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='issued_licences'
    )
    revoked_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tenants_desktoplicence'
        ordering = ['-issued_at']

    @property
    def is_active(self):
        if self.revoked_at:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def __str__(self):
        status = 'active' if self.is_active else ('revoked' if self.revoked_at else 'expired')
        return f"{self.licence_key} → {self.tenant.name} ({status})"


class ServiceOrder(SoftDeleteMixin, models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug         = models.CharField(max_length=80, unique=True)
    name         = models.CharField(max_length=120)
    domain       = models.CharField(max_length=120)
    office       = models.CharField(max_length=120)
    order_number = models.PositiveSmallIntegerField(unique=True)
    is_active    = models.BooleanField(default=True)
    # deleted_at — provided by SoftDeleteMixin

    class Meta:
        db_table = 'tenants_serviceorder'
        ordering = ['order_number']

    def __str__(self):
        return f"{self.order_number}. {self.name}"
