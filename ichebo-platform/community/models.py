import uuid
from django.conf import settings
from django.db import models


class MembershipRequest(models.Model):
    """
    Deferred — Phase 2 of Community App.
    Stubbed here so migration exists and Phase 2 requires no schema change.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='membership_requests_made'
    )
    tenant      = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='membership_requests_created'
    )
    status      = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('denied', 'Denied')],
        default='pending'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='membership_requests_reviewed'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    note        = models.TextField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    deleted_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'community_membership_request'
        ordering = ['-created_at']

    def __str__(self):
        return f"MembershipRequest({self.user_id} → {self.tenant_id}, {self.status})"
