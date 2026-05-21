from rest_framework import serializers
from records.models import Record
from .models import TranscodeJob


class VideoRecordSerializer(serializers.ModelSerializer):
    video_url        = serializers.SerializerMethodField()
    thumbnail_url    = serializers.SerializerMethodField()
    duration_seconds = serializers.SerializerMethodField()
    transcoding_status = serializers.SerializerMethodField()
    quality_variants = serializers.SerializerMethodField()
    chapter_markers  = serializers.SerializerMethodField()
    presenter        = serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = [
            'id', 'title', 'summary', 'status', 'created_at', 'updated_at',
            'video_url', 'thumbnail_url', 'duration_seconds',
            'transcoding_status', 'quality_variants', 'chapter_markers', 'presenter',
        ]

    def get_video_url(self, obj):
        return obj.custom_fields.get('video_url')

    def get_thumbnail_url(self, obj):
        return obj.custom_fields.get('thumbnail_url')

    def get_duration_seconds(self, obj):
        return obj.custom_fields.get('duration_seconds')

    def get_transcoding_status(self, obj):
        return obj.custom_fields.get('transcoding_status', 'queued')

    def get_quality_variants(self, obj):
        return obj.custom_fields.get('quality_variants', [])

    def get_chapter_markers(self, obj):
        return obj.custom_fields.get('chapter_markers', [])

    def get_presenter(self, obj):
        return obj.custom_fields.get('presenter')


class TranscodeJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranscodeJob
        fields = ['id', 'job_id', 'status', 'progress_pct', 'error', 'created_at', 'completed_at']
