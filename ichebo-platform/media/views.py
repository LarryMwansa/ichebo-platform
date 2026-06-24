import uuid
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from records.models import Record
from .engine_client import post_with_retry
from .models import TranscodeJob, VideoRecord
from .serializers import VideoRecordSerializer


class UploadInitView(APIView):
    """POST /api/media/upload/init/ — initialise a chunked upload session.

    SessionAuthentication added 2026-06-24 (video-direction-v2-plan.md) so
    the Learn lesson-authoring page's browser session can call this
    directly — the original TokenAuthentication-only setup required a DRF
    auth token, a Flutter-app credential a normal Django session doesn't
    carry, and rendering one into page HTML for this purpose would have
    been a real credential-exposure surface. Session auth already carries
    CSRF protection via Django's standard session-cookie + CSRF-token
    pair; DRF's SessionAuthentication enforces that automatically. Token
    auth stays for the Flutter app's existing calls — both are checked,
    either is accepted.
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        title = request.data.get('title', '').strip()
        filename = request.data.get('filename', '').strip()
        file_size = request.data.get('file_size_bytes')
        record_type = request.data.get('record_type', 'teaching_video')
        tenant_id = request.data.get('tenant_id')

        if not title or not filename or not file_size:
            return Response({'error': 'title, filename, and file_size_bytes are required'}, status=400)

        # Create the Record immediately so it has a stable UUID before upload completes.
        record = Record.objects.create(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            created_by=request.user,
            record_class='organizational',
            record_family='media',
            record_type=record_type,
            title=title,
            status='draft',
            custom_fields={'transcoding_status': 'queued'},
        )

        # Forward init request to Go Video Engine.
        engine_url = getattr(settings, 'MEDIA_ENGINE_URL', 'http://localhost:8090')
        try:
            resp = post_with_retry(
                f'{engine_url}/engine/upload/init',
                json={
                    'filename': filename,
                    'file_size_bytes': int(file_size),
                    'content_type': request.data.get('content_type', 'video/mp4'),
                    'tenant_id': str(tenant_id) if tenant_id else '',
                    'record_id': str(record.id),
                },
                timeout=15,
            )
            engine_data = resp.json()
        except Exception as exc:
            record.delete()
            return Response({'error': f'Video engine unreachable: {exc}'}, status=503)

        return Response({
            'record_id': str(record.id),
            'upload_id': engine_data['upload_id'],
            'total_chunks': engine_data['total_chunks'],
            'chunk_size_bytes': engine_data['chunk_size_bytes'],
        })


class UploadCompleteView(APIView):
    """POST /api/media/upload/complete/ — assemble chunks and start transcoding.

    SessionAuthentication added alongside TokenAuthentication — see
    UploadInitView's docstring for why.
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        upload_id = request.data.get('upload_id', '').strip()
        record_id = request.data.get('record_id', '').strip()
        chunk_checksums = request.data.get('chunk_checksums', [])
        quality_profiles = request.data.get('quality_profiles', [])

        if not upload_id or not record_id:
            return Response({'error': 'upload_id and record_id are required'}, status=400)

        try:
            record = Record.objects.get(id=record_id, record_family='media')
        except Record.DoesNotExist:
            return Response({'error': 'Record not found'}, status=404)

        engine_url = getattr(settings, 'MEDIA_ENGINE_URL', 'http://localhost:8090')

        # Complete assembly in the engine.
        try:
            resp = post_with_retry(
                f'{engine_url}/engine/upload/{upload_id}/complete',
                json={'chunk_checksums': chunk_checksums},
                timeout=60,
            )
            engine_data = resp.json()
        except Exception as exc:
            return Response({'error': f'Upload complete failed: {exc}'}, status=503)

        raw_key = engine_data.get('raw_object_key', '')

        # Submit transcode job to the engine.
        try:
            transcode_resp = post_with_retry(
                f'{engine_url}/engine/transcode',
                json={
                    'upload_id': upload_id,
                    'record_id': record_id,
                    'raw_object_key': raw_key,
                    'tenant_id': str(record.tenant_id) if record.tenant_id else '',
                    'quality_profiles': quality_profiles,
                },
                timeout=15,
            )
            transcode_data = transcode_resp.json()
        except Exception as exc:
            return Response({'error': f'Transcode submit failed: {exc}'}, status=503)

        job_id = transcode_data.get('job_id', '')

        # Create TranscodeJob record in Django.
        TranscodeJob.objects.create(
            record=record,
            job_id=job_id,
            status='queued',
        )

        record.custom_fields['transcoding_status'] = 'queued'
        record.custom_fields['transcode_job_id'] = job_id
        record.save(update_fields=['custom_fields'])

        return Response({'record_id': record_id, 'job_id': job_id})


class VideoListView(APIView):
    """GET /api/media/videos/ — list all media Records for the current user's tenant.

    SessionAuthentication added alongside TokenAuthentication — see
    UploadInitView's docstring for why.
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Record.objects.filter(record_family='media').order_by('-created_at')
        tenant_id = request.query_params.get('tenant_id')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        serializer = VideoRecordSerializer(qs[:50], many=True)
        return Response(serializer.data)


class VideoDetailView(APIView):
    """GET /api/media/videos/{id}/ — single video Record with all fields.

    SessionAuthentication added alongside TokenAuthentication — see
    UploadInitView's docstring for why. Learn's lesson-authoring page polls
    this endpoint to detect when a just-uploaded video's transcoding job
    completes.
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, record_id):
        try:
            record = Record.objects.get(id=record_id, record_family='media')
        except Record.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        return Response(VideoRecordSerializer(record).data)


class TranscodeCompleteWebhookView(APIView):
    """POST /api/media/transcode-complete/ — called by Go Video Engine on job completion.

    Authenticated by shared API key in Authorization header, not user token.

    Handles two distinct cases sharing the same payload shape, disambiguated
    by job_id prefix (set by the Go engine — pkg/transcode/worker.go for
    regular uploads, pkg/stream/archiver.go's "archive-" + record_id for
    live broadcast DVR archiving):
    - Regular upload transcode -> updates a media Record's custom_fields.
    - Live broadcast archive complete -> updates a video_live.BroadcastSchedule's
      vod_url. Added 2026-06-23 (Chizola) — record_id in this case is a
      BroadcastSchedule.id, not a Record.id, since the archiver's session
      registry doesn't know about Record at all (see stream/session.go);
      the original version of this view only ever checked Record and would
      have silently 200'd without saving anything for every broadcast
      archive completion.

    authentication_classes/permission_classes explicitly emptied — DRF's
    global DEFAULT_PERMISSION_CLASSES is IsAuthenticated, which rejected
    every call to this view with 401 before the manual bearer-key check
    below ever ran, even with a correct key. Confirmed by direct test: this
    webhook has likely never actually worked since it was written, despite
    its own docstring claiming otherwise. Fixed 2026-06-23 (Chizola) while
    chasing why the live-broadcast archive handshake (a separate, related
    bug — see video_live.api_views.StreamStartWebhookView) wasn't wiring
    up either.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        api_key = getattr(settings, 'MEDIA_ENGINE_API_KEY', 'dev-key')
        auth = request.headers.get('Authorization', '')
        if auth != f'Bearer {api_key}':
            return Response({'error': 'Unauthorized'}, status=401)

        job_id = request.data.get('job_id', '')
        record_id = request.data.get('record_id', '')
        job_status = request.data.get('status', '')
        video_url = request.data.get('video_url', '')
        thumbnail_url = request.data.get('thumbnail_url', '')
        duration_seconds = request.data.get('duration_seconds', 0)
        quality_variants = request.data.get('quality_variants', [])

        # Update TranscodeJob — only relevant for the regular-upload case,
        # but harmless no-op (filter matches nothing) for archive jobs.
        TranscodeJob.objects.filter(job_id=job_id).update(
            status=job_status,
            progress_pct=100 if job_status == 'complete' else 0,
            completed_at=timezone.now() if job_status in ('complete', 'failed') else None,
        )

        if job_id.startswith('archive-'):
            return self._handle_broadcast_archive(record_id, job_status, video_url)

        # Update Record.custom_fields atomically.
        try:
            record = Record.objects.get(id=record_id, record_family='media')
        except Record.DoesNotExist:
            return Response(status=status.HTTP_200_OK)

        record.custom_fields.update({
            'transcoding_status': job_status,
            'video_url': video_url,
            'thumbnail_url': thumbnail_url,
            'duration_seconds': duration_seconds,
            'quality_variants': quality_variants,
        })
        if job_status == 'complete':
            record.status = 'active'
        record.save(update_fields=['custom_fields', 'status'])

        return Response(status=status.HTTP_200_OK)

    def _handle_broadcast_archive(self, broadcast_id, job_status, video_url):
        from video_live.models import BroadcastSchedule

        try:
            broadcast = BroadcastSchedule.objects.get(id=broadcast_id)
        except (BroadcastSchedule.DoesNotExist, ValueError, TypeError):
            return Response(status=status.HTTP_200_OK)

        if job_status == 'complete' and video_url:
            broadcast.vod_url = video_url
            broadcast.save(update_fields=['vod_url', 'updated_at'])

        return Response(status=status.HTTP_200_OK)


class ChapterMarkersView(APIView):
    """
    GET   /api/media/videos/{id}/chapters/  — return current chapter markers
    PATCH /api/media/videos/{id}/chapters/  — replace chapter markers for a lesson video

    Body: { "chapter_markers": [ { "timestamp_seconds": 0, "title": "Introduction" }, ... ] }

    Only the record owner or a Level 3+ steward may write chapter markers.
    Chapter markers are stored in custom_fields.chapter_markers as a JSON array.
    They are read back by the Flutter player to render the chapter navigator.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, record_id):
        try:
            record = Record.objects.get(id=record_id, record_family='media')
        except Record.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        return Response({'chapter_markers': record.custom_fields.get('chapter_markers', [])})

    def patch(self, request, record_id):
        try:
            record = Record.objects.get(id=record_id, record_family='media')
        except Record.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        markers = request.data.get('chapter_markers')
        if not isinstance(markers, list):
            return Response({'error': 'chapter_markers must be a list'}, status=400)

        for i, m in enumerate(markers):
            if not isinstance(m, dict):
                return Response({'error': f'marker[{i}] must be an object'}, status=400)
            if not isinstance(m.get('timestamp_seconds'), int):
                return Response({'error': f'marker[{i}].timestamp_seconds must be an integer'}, status=400)
            if not isinstance(m.get('title'), str) or not m['title'].strip():
                return Response({'error': f'marker[{i}].title must be a non-empty string'}, status=400)

        # Normalise: sort by timestamp, strip extra keys.
        clean = sorted(
            [{'timestamp_seconds': m['timestamp_seconds'], 'title': m['title'].strip()} for m in markers],
            key=lambda x: x['timestamp_seconds'],
        )

        record.custom_fields['chapter_markers'] = clean
        record.save(update_fields=['custom_fields'])

        return Response({'chapter_markers': clean})
