from django.contrib import admin
from .models import WaitlistEntry


@admin.register(WaitlistEntry)
class WaitlistEntryAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'path', 'created_at', 'notified']
    list_filter = ['path', 'notified', 'created_at']
    search_fields = ['name', 'email']
    readonly_fields = [
        'id', 'consent_timestamp', 'ip_address',
        'created_at', 'notified'
    ]
    ordering = ['-created_at']
