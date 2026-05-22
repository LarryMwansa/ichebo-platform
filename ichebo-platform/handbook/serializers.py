from rest_framework import serializers
from .models import (
    HandbookRecord, HandbookRelationship, HandbookAccess,
    BRANCH_CHOICES, RECORD_TYPE_CHOICES, HRS_RELATIONSHIP_TYPES,
)


class HandbookRecordListSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.display_name', read_only=True, default='')
    branch_label = serializers.CharField(read_only=True)

    class Meta:
        model = HandbookRecord
        fields = [
            'id', 'title', 'slug', 'summary', 'branch', 'branch_label',
            'record_type', 'tags', 'status', 'version_number',
            'created_by_name', 'published_at', 'updated_at',
        ]


class HandbookRelationshipSerializer(serializers.ModelSerializer):
    to_record_title = serializers.CharField(source='to_record.title', read_only=True, default='')
    bible_verse_ref = serializers.SerializerMethodField()

    class Meta:
        model = HandbookRelationship
        fields = [
            'id', 'relationship_type', 'direction', 'notes',
            'to_record', 'to_record_title',
            'bible_verse', 'bible_verse_ref',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_bible_verse_ref(self, obj):
        if obj.bible_verse:
            v = obj.bible_verse
            return f'{v.book.code} {v.chapter}:{v.verse}'
        return None


class HandbookRecordDetailSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.display_name', read_only=True, default='')
    locked_by_name = serializers.CharField(source='locked_by.display_name', read_only=True, default='')
    previous_version_id = serializers.UUIDField(source='previous_version.id', read_only=True, default=None)
    superseded_by_id = serializers.UUIDField(source='superseded_by.id', read_only=True, default=None)
    branch_label = serializers.CharField(read_only=True)
    outgoing_relationships = HandbookRelationshipSerializer(many=True, read_only=True)

    class Meta:
        model = HandbookRecord
        fields = [
            'id', 'title', 'slug', 'content', 'summary',
            'branch', 'branch_label', 'record_type', 'tags',
            'hrs_complexity', 'hrs_relationship_position', 'hrs_position',
            'hrs_direction', 'hrs_speed', 'hrs_emotional_tone',
            'status', 'version_number',
            'previous_version_id', 'superseded_by_id',
            'created_by_name', 'locked_by_name',
            'locked_at', 'published_at', 'created_at', 'updated_at',
            'outgoing_relationships',
        ]
        read_only_fields = [
            'id', 'status', 'version_number', 'locked_at', 'published_at',
            'created_at', 'updated_at',
        ]


class HandbookRecordWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = HandbookRecord
        fields = [
            'title', 'slug', 'content', 'summary',
            'branch', 'record_type', 'tags',
            'hrs_complexity', 'hrs_relationship_position', 'hrs_position',
            'hrs_direction', 'hrs_speed', 'hrs_emotional_tone',
        ]

    def validate(self, data):
        from .models import RECORD_TYPES_BY_BRANCH
        branch = data.get('branch', getattr(self.instance, 'branch', None))
        record_type = data.get('record_type', getattr(self.instance, 'record_type', None))
        if branch and record_type:
            allowed = RECORD_TYPES_BY_BRANCH.get(branch, [])
            if record_type not in allowed:
                raise serializers.ValidationError(
                    {'record_type': f'"{record_type}" is not valid for branch "{branch}".'}
                )
        return data


class HandbookAccessSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.display_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = HandbookAccess
        fields = ['id', 'user', 'user_name', 'user_email', 'role', 'granted_at']
        read_only_fields = ['id', 'granted_at']
