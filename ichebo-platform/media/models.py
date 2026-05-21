import uuid
from django.db import models
from records.models import Record


class TranscodeJob(models.Model):
    """Tracks a video transcoding job submitted to the Ichebo Media Go engine."""
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    record       = models.ForeignKey(Record, on_delete=models.PROTECT, related_name='transcode_jobs')
    job_id       = models.CharField(max_length=100)  # UUID from the Go Video Engine
    status       = models.CharField(max_length=20, default='queued')
    # Choices: queued | processing | complete | failed
    progress_pct = models.IntegerField(default=0)
    error        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"TranscodeJob({self.job_id[:8]}… {self.status})"


class VideoRecord:
    """Typed accessor wrapper for a Record with record_family='media'.

    Not a database model — wraps an existing Record instance and provides
    typed property accessors for custom_fields keys. No migration needed.
    """
    def __init__(self, record: Record):
        self._r = record

    @property
    def record(self) -> Record:
        return self._r

    @property
    def video_url(self) -> str | None:
        return self._r.custom_fields.get('video_url')

    @property
    def thumbnail_url(self) -> str | None:
        return self._r.custom_fields.get('thumbnail_url')

    @property
    def duration_seconds(self) -> int | None:
        return self._r.custom_fields.get('duration_seconds')

    @property
    def transcoding_status(self) -> str:
        return self._r.custom_fields.get('transcoding_status', 'queued')

    @property
    def quality_variants(self) -> list:
        return self._r.custom_fields.get('quality_variants', [])

    @property
    def chapter_markers(self) -> list:
        return self._r.custom_fields.get('chapter_markers', [])

    @property
    def presenter(self) -> str | None:
        return self._r.custom_fields.get('presenter')

    @classmethod
    def from_record(cls, record: Record) -> 'VideoRecord':
        return cls(record)
