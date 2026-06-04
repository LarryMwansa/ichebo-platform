from rest_framework import serializers
from .models import WaitlistEntry


class WaitlistEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = WaitlistEntry
        fields = ['name', 'email', 'path', 'consent']

    def validate_consent(self, value):
        if not value:
            raise serializers.ValidationError(
                'Consent is required to register.'
            )
        return value

    def validate_path(self, value):
        if value not in ('leader', 'individual'):
            raise serializers.ValidationError(
                'Path must be either "leader" or "individual".'
            )
        return value

    def validate_email(self, value):
        return value.lower().strip()
