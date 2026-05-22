from django.contrib import admin
from .models import HandbookRecord, HandbookAccess


@admin.register(HandbookRecord)
class HandbookRecordAdmin(admin.ModelAdmin):
    list_display = ['title', 'tenant', 'status', 'version_number', 'created_by', 'updated_at']
    list_filter = ['status', 'tenant', 'category']
    search_fields = ['title', 'content', 'slug']
    readonly_fields = ['id', 'created_at', 'updated_at', 'locked_at', 'published_at']


@admin.register(HandbookAccess)
class HandbookAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'role', 'granted_by', 'granted_at']
    list_filter = ['role', 'tenant']
