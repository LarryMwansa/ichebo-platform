from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'email', 'display_name', 'password']

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            display_name=validated_data.get('display_name', ''),
            password=validated_data['password'],
            status='seeker',
            competence_level=0
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Invalid credentials')
        if user.status == 'suspended':
            raise serializers.ValidationError('Account suspended')
        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    preferred_bible_translation_code = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'display_name', 'avatar_url',
            'competence_level', 'status', 'created_at',
            'preferences', 'preferred_bible_translation',
            'preferred_bible_translation_code',
        ]
        read_only_fields = ['id', 'created_at', 'competence_level']

    def get_preferred_bible_translation_code(self, obj):
        if obj.preferred_bible_translation:
            return obj.preferred_bible_translation.code
        return None

    def update(self, instance, validated_data):
        # Merge preferences JSONField rather than replacing it wholesale
        incoming_prefs = validated_data.pop('preferences', None)
        if incoming_prefs is not None:
            current = instance.preferences or {}
            current.update(incoming_prefs)
            instance.preferences = current
        return super().update(instance, validated_data)
