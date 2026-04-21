from django.contrib import admin
from .models import Record, Relationship

@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    list_display = ['title', 'record_type', 'record_family', 'record_class', 'status', 'created_by', 'created_at']
    list_filter = ['record_family', 'record_type', 'record_class', 'status', 'created_at']
    search_fields = ['title', 'content']
    raw_id_fields = ['created_by', 'tenant', 'locked_by', 'previous_version', 'superseded_by']
    date_hierarchy = 'created_at'

@admin.register(Relationship)
class RelationshipAdmin(admin.ModelAdmin):
    list_display = ['relationship_type', 'from_record', 'to_record', 'bible_verse', 'direction', 'strength', 'created_at']
    list_filter = ['relationship_type', 'direction', 'strength', 'created_at']
    raw_id_fields = ['from_record', 'to_record', 'bible_verse', 'created_by', 'tenant']
