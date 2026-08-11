from rest_framework import serializers
from records.models import Record
from activity.models import Activity
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


class LessonSerializer(serializers.ModelSerializer):
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = [
            'id', 'title', 'summary', 'content', 'status',
            'record_type', 'custom_fields', 'video_url',
            'created_at', 'updated_at',
        ]

    def get_video_url(self, obj):
        return (obj.custom_fields or {}).get('video_url')


class CourseSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = [
            'id', 'title', 'summary', 'status', 'record_type',
            'custom_fields', 'lessons', 'created_at', 'updated_at',
        ]

    def get_lessons(self, obj):
        from learn.engine import STEP_TYPES, ordered_children
        lessons = ordered_children(obj, STEP_TYPES, ['active', 'locked'])
        return LessonSerializer(lessons, many=True).data


class ProgrammeListSerializer(serializers.ModelSerializer):
    kgs_qualification = serializers.SerializerMethodField()
    kgs_pathways = serializers.SerializerMethodField()
    required_level = serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = [
            'id', 'title', 'summary', 'status',
            'kgs_qualification', 'kgs_pathways', 'required_level',
            'created_at', 'updated_at',
        ]

    def get_kgs_qualification(self, obj):
        return (obj.custom_fields or {}).get('kgs_qualification', '')

    def get_kgs_pathways(self, obj):
        return (obj.custom_fields or {}).get('kgs_pathways', [])

    def get_required_level(self, obj):
        return (obj.permissions_data or {}).get('required_level', 1)


class ProgrammeDetailSerializer(ProgrammeListSerializer):
    courses = serializers.SerializerMethodField()

    class Meta(ProgrammeListSerializer.Meta):
        fields = ProgrammeListSerializer.Meta.fields + ['courses', 'content']

    def get_courses(self, obj):
        from learn.engine import ordered_children
        courses = ordered_children(obj, ['course'], ['active', 'locked'])
        return CourseSerializer(courses, many=True).data


class EnrolmentSerializer(serializers.ModelSerializer):
    programme_id = serializers.UUIDField(source='linked_record_id')
    programme_title = serializers.CharField(source='linked_record.title', read_only=True)

    class Meta:
        model = Activity
        fields = [
            'id', 'programme_id', 'programme_title',
            'status', 'progress', 'created_at', 'updated_at',
        ]
        read_only_fields = fields


class LessonProgressSerializer(serializers.ModelSerializer):
    lesson_id = serializers.UUIDField(source='linked_record_id')
    lesson_title = serializers.CharField(source='linked_record.title', read_only=True)

    class Meta:
        model = Activity
        fields = [
            'id', 'lesson_id', 'lesson_title',
            'status', 'progress', 'updated_at',
        ]
        read_only_fields = fields
