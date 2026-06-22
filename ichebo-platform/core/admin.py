from django.contrib import admin

from .models import PlatformConfig


@admin.register(PlatformConfig)
class PlatformConfigAdmin(admin.ModelAdmin):
    list_display = ['bootstrapped_at', 'bootstrapped_by', 'bootstrap_version', 'require_email_verification']

    def has_add_permission(self, request):
        # Singleton — only allow editing the existing row, never adding more.
        return not PlatformConfig.objects.exists()
