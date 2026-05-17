import uuid
import secrets
from django.db import models
from django.conf import settings
from django.utils import timezone

class Tenant(models.Model):
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


class UserPermission(models.Model):
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

    class Meta:
        db_table = 'tenants_userpermission'
        unique_together = [['tenant', 'user', 'role']]


class TenantInvitation(models.Model):
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


class ServiceOrder(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug         = models.CharField(max_length=80, unique=True)
    name         = models.CharField(max_length=120)
    domain       = models.CharField(max_length=120)
    office       = models.CharField(max_length=120)
    order_number = models.PositiveSmallIntegerField(unique=True)
    is_active    = models.BooleanField(default=True)

    class Meta:
        db_table = 'tenants_serviceorder'
        ordering = ['order_number']

    def __str__(self):
        return f"{self.order_number}. {self.name}"
