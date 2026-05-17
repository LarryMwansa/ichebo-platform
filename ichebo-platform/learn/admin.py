from django.contrib import admin
from .models import CertificationConfirmation


@admin.register(CertificationConfirmation)
class CertificationConfirmationAdmin(admin.ModelAdmin):
    list_display = [
        'certification_record_id', 'learner_id', 'confirmed_by',
        'previous_competence_level', 'new_competence_level', 'confirmed_at',
    ]
    list_filter = ['new_competence_level', 'previous_competence_level']
    search_fields = ['learner_id', 'confirmed_by__email', 'notes']
    readonly_fields = [
        'id', 'certification_record_id', 'learner_id', 'confirmed_by',
        'previous_competence_level', 'new_competence_level', 'confirmed_at',
    ]
    ordering = ['-confirmed_at']
