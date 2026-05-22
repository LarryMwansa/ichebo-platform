from django.contrib import admin
from .models import HandbookRecord, HandbookRelationship, HandbookAccess


@admin.register(HandbookRecord)
class HandbookRecordAdmin(admin.ModelAdmin):
    list_display = ['title', 'branch', 'record_type', 'status', 'version_number', 'created_by', 'updated_at']
    list_filter = ['branch', 'record_type', 'status']
    search_fields = ['title', 'content', 'slug']
    readonly_fields = ['id', 'created_at', 'updated_at', 'locked_at', 'published_at']


@admin.register(HandbookRelationship)
class HandbookRelationshipAdmin(admin.ModelAdmin):
    list_display = ['from_record', 'relationship_type', 'to_record', 'bible_verse', 'direction']
    list_filter = ['relationship_type', 'direction']


@admin.register(HandbookAccess)
class HandbookAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'granted_by', 'granted_at']
    list_filter = ['role']
