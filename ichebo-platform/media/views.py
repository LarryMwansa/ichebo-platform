import uuid
import requests
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from records.models import Record
from .models import TranscodeJob, VideoRecord
from .serializers import VideoRecordSerializer


class UploadInitView(APIView):
    """POST /api/media/upload/init/ — initialise a chunked upload session."""
    authentication_classes = [TokenAuthentication]
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
            resp = requests.post(
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
            resp.raise_for_status()
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
    """POST /api/media/upload/complete/ — assemble chunks and start transcoding."""
    authentication_classes = [TokenAuthentication]
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
            resp = requests.post(
                f'{engine_url}/engine/upload/{upload_id}/complete',
                json={'chunk_checksums': chunk_checksums},
                timeout=60,
            )
            resp.raise_for_status()
            engine_data = resp.json()
        except Exception as exc:
            return Response({'error': f'Upload complete failed: {exc}'}, status=503)

        raw_key = engine_data.get('raw_object_key', '')

        # Submit transcode job to the engine.
        try:
            transcode_resp = requests.post(
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
            transcode_resp.raise_for_status()
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
    """GET /api/media/videos/ — list all media Records for the current user's tenant."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Record.objects.filter(record_family='media').order_by('-created_at')
        tenant_id = request.query_params.get('tenant_id')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        serializer = VideoRecordSerializer(qs[:50], many=True)
        return Response(serializer.data)


class VideoDetailView(APIView):
    """GET /api/media/videos/{id}/ — single video Record with all fields."""
    authentication_classes = [TokenAuthentication]
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
    """

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

        # Update TranscodeJob.
        TranscodeJob.objects.filter(job_id=job_id).update(
            status=job_status,
            progress_pct=100 if job_status == 'complete' else 0,
            completed_at=timezone.now() if job_status in ('complete', 'failed') else None,
        )

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
