import secrets
import string
from django.contrib import admin
from django.utils import timezone
from .models import DesktopLicence, ServiceOrder, Tenant, TenantInvitation, UserPermission


# ── DesktopLicence ────────────────────────────────────────────────────────────

def _generate_key():
    alphabet = string.ascii_uppercase + string.digits
    parts = [''.join(secrets.choice(alphabet) for _ in range(8)) for _ in range(4)]
    return '-'.join(parts)


@admin.action(description='Revoke selected licences')
def revoke_licences(modeladmin, request, queryset):
    queryset.filter(revoked_at__isnull=True).update(revoked_at=timezone.now())


@admin.register(DesktopLicence)
class DesktopLicenceAdmin(admin.ModelAdmin):
    list_display  = ('licence_key', 'tenant', 'issued_at', 'issued_by',
                     'revoked_at', 'expires_at', 'status_badge')
    list_filter   = ('tenant', 'revoked_at')
    search_fields = ('licence_key', 'tenant__name', 'notes')
    readonly_fields = ('id', 'issued_at', 'licence_key')
    actions       = [revoke_licences]
    ordering      = ('-issued_at',)

    fieldsets = (
        (None, {
            'fields': ('id', 'licence_key', 'tenant', 'issued_by'),
        }),
        ('Validity', {
            'fields': ('issued_at', 'expires_at', 'revoked_at'),
        }),
        ('Notes', {
            'fields': ('notes',),
        }),
    )

    def status_badge(self, obj):
        if obj.revoked_at:
            return '🔴 Revoked'
        if obj.expires_at and timezone.now() > obj.expires_at:
            return '🟡 Expired'
        return '🟢 Active'
    status_badge.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        if not change:
            # Auto-generate key on first save if blank
            if not obj.licence_key:
                obj.licence_key = _generate_key()
            if not obj.issued_by_id:
                obj.issued_by = request.user
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields
        # On add, licence_key is auto-generated — keep it readonly on create too
        return ('id', 'issued_at')


# ── Supporting models ─────────────────────────────────────────────────────────

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display  = ('name', 'tier', 'status', 'affiliation', 'path')
    list_filter   = ('tier', 'status', 'affiliation')
    search_fields = ('name', 'slug', 'path')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('path',)


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    list_display  = ('user', 'tenant', 'role', 'level', 'is_active', 'granted_at')
    list_filter   = ('role', 'is_active')
    search_fields = ('user__email', 'tenant__name')
    readonly_fields = ('id', 'granted_at')


@admin.register(TenantInvitation)
class TenantInvitationAdmin(admin.ModelAdmin):
    list_display  = ('email', 'tenant', 'status', 'expires_at', 'created_at')
    list_filter   = ('status',)
    search_fields = ('email', 'tenant__name')
    readonly_fields = ('id', 'token', 'created_at')


@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display  = ('order_number', 'name', 'domain', 'office', 'is_active')
    list_filter   = ('is_active',)
    search_fields = ('name', 'slug')
    ordering      = ('order_number',)
