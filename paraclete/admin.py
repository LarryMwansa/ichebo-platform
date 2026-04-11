from django.contrib import admin
from .models import ParacletePrompt


@admin.register(ParacletePrompt)
class ParacletePromptAdmin(admin.ModelAdmin):
    list_display = ['pathway', 'min_level', 'is_active', 'text_preview', 'created_at']
    list_filter = ['pathway', 'min_level', 'is_active']
    search_fields = ['text']
    list_editable = ['is_active']

    def text_preview(self, obj):
        return obj.text[:80]
    text_preview.short_description = 'Text'
