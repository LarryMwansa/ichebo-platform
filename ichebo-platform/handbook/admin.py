from django.contrib import admin
from .models import HandbookAccess


@admin.register(HandbookAccess)
class HandbookAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'granted_by', 'granted_at']
    list_filter = ['role']
