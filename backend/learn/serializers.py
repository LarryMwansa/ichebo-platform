from rest_framework import serializers
from .models import CertificationConfirmation


class CertificationConfirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificationConfirmation
        fields = [
            'id', 'certification_record_id', 'confirmed_by',
            'learner_id', 'previous_competence_level',
            'new_competence_level', 'confirmed_at', 'notes'
        ]
        read_only_fields = [
            'id', 'confirmed_by', 'previous_competence_level',
            'new_competence_level', 'confirmed_at'
        ]
