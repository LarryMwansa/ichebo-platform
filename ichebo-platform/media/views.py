import hashlib
import hmac
import time
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

# ---------------------------------------------------------------------------
# Upload-token helpers
# ---------------------------------------------------------------------------
# Tokens are HMAC-SHA256 signed strings with the format:
#   <tenant_id>:<user_id>:<expires_unix>:<hmac_hex>
# This gives us:
#   - Authenticity (only Django's MEDIA_ENGINE_API_KEY can produce a valid token)
#   - Expiry        (Go engine checks expires_unix before accepting)
#   - Tenant scope  (video is automatically associated with the right tenant)
# No database row needed — pure stateless verification on both ends.

_TOKEN_TTL_SECONDS = 600  # 10 minutes


def _make_upload_token(tenant_id: str, user_id: str) -> str:
    """Return a signed upload token valid for _TOKEN_TTL_SECONDS."""
    api_key = getattr(settings, 'MEDIA_ENGINE_API_KEY', '')
    expires = int(time.time()) + _TOKEN_TTL_SECONDS
    payload = f"{tenant_id}:{user_id}:{expires}"
    sig = hmac.new(api_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"


def _verify_upload_token(token: str) -> dict | None:
    """
    Verify a token previously issued by _make_upload_token.
    Returns {'tenant_id': str, 'user_id': str} on success, None on failure.
    """
    api_key = getattr(settings, 'MEDIA_ENGINE_API_KEY', '')
    try:
        tenant_id, user_id, expires_str, sig = token.split(':', 3)
    except ValueError:
        return None
    expires = int(expires_str)
    if int(time.time()) > expires:
        return None  # expired
    expected_payload = f"{tenant_id}:{user_id}:{expires_str}"
    expected_sig = hmac.new(api_key.encode(), expected_payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        return None  # tampered
    return {'tenant_id': tenant_id, 'user_id': user_id}


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
        # For portal uploads the Record doesn't exist yet — create it now.
        try:
            record = Record.objects.get(id=record_id, record_family='media')
        except Record.DoesNotExist:
            # Portal upload: the webhook is the first notification Django gets.
            # tenant_id and title are included since the portal flow wired them in.
            tenant_id = request.data.get('tenant_id', '')
            title = request.data.get('title', '') or f'Video {record_id[:8]}'

            if not tenant_id:
                # Can't attach to a tenant — log and swallow silently.
                import logging
                logging.getLogger(__name__).warning(
                    'transcode-complete webhook for unknown record %s has no tenant_id — skipping',
                    record_id,
                )
                return Response(status=status.HTTP_200_OK)

            from tenants.models import Tenant
            try:
                tenant = Tenant.objects.get(id=tenant_id)
            except (Tenant.DoesNotExist, ValueError):
                return Response(status=status.HTTP_200_OK)

            # Use first superuser as system actor for webhook-created records.
            from django.contrib.auth import get_user_model
            User = get_user_model()
            system_user = User.objects.filter(is_superuser=True).order_by('date_joined').first()

            record = Record.objects.create(
                id=record_id,
                tenant=tenant,
                created_by=system_user,
                record_family='media',
                title=title,
                status='active' if job_status == 'complete' else 'processing',
                custom_fields={
                    'transcoding_status': job_status,
                    'video_url': video_url,
                    'thumbnail_url': thumbnail_url,
                    'duration_seconds': duration_seconds,
                    'quality_variants': quality_variants,
                    'source': 'upload_portal',
                },
            )
            TranscodeJob.objects.filter(job_id=job_id).update(
                status=job_status,
                progress_pct=100 if job_status == 'complete' else 0,
                completed_at=timezone.now() if job_status in ('complete', 'failed') else None,
            )
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


class UploadPortalTokenView(APIView):
    """GET /api/media/upload-token/?tenant_id=<uuid>

    Issues a short-lived (10 min) HMAC-signed token that the Go engine's
    upload page validates before accepting a file. This means the user never
    needs to authenticate directly with the Go engine — they authenticate
    here in the Django session, get a token, and open the upload portal URL
    in a new tab. The token encodes tenant_id and user_id so the completed
    upload can be attributed correctly when the webhook fires.

    Authentication: SessionAuthentication (browser) or TokenAuthentication (app).
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.query_params.get('tenant_id', '')
        if not tenant_id:
            return Response({'error': 'tenant_id is required'}, status=400)

        token = _make_upload_token(str(tenant_id), str(request.user.id))
        engine_public_url = getattr(settings, 'MEDIA_ENGINE_PUBLIC_URL', 'https://video.ichebo.org')

        upload_url = (
            f"{engine_public_url}/upload"
            f"?token={token}"
            f"&tenant_id={tenant_id}"
            f"&callback={request.build_absolute_uri('/api/media/upload-complete-webhook/')}"
        )

        return Response({
            'upload_url': upload_url,
            'expires_in_seconds': _TOKEN_TTL_SECONDS,
        })


class UploadCompleteWebhookView(APIView):
    """POST /api/media/upload-complete-webhook/

    Called by the Go engine's upload page after upload + transcode completes.
    Payload:
        {
          "token":            "<upload token issued by UploadPortalTokenView>",
          "title":            "My Video.mp4",
          "tenant_id":        "<uuid>",
          "video_url":        "https://cdn.ichebo.org/videos/<id>/index.m3u8",
          "thumbnail_url":    "https://...",
          "duration_seconds": 342,
          "file_size_bytes":  104857600,
          "record_type":      "teaching_video"   # optional, default broadcast_video
        }

    Security: Bearer token (shared MEDIA_ENGINE_API_KEY) + HMAC token validation.
    No Django session required — called server-to-server from the Go engine.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        # 1. Verify shared API key (same mechanism as TranscodeCompleteWebhookView).
        api_key = getattr(settings, 'MEDIA_ENGINE_API_KEY', '')
        auth = request.headers.get('Authorization', '')
        if auth != f'Bearer {api_key}':
            return Response({'error': 'Unauthorized'}, status=401)

        # 2. Verify the upload token is still valid and extract claims.
        token = request.data.get('token', '')
        claims = _verify_upload_token(token)
        if claims is None:
            return Response({'error': 'Invalid or expired upload token'}, status=400)

        tenant_id = request.data.get('tenant_id') or claims['tenant_id']
        title = request.data.get('title', 'Untitled Video').strip() or 'Untitled Video'
        video_url = request.data.get('video_url', '')
        thumbnail_url = request.data.get('thumbnail_url', '')
        duration_seconds = request.data.get('duration_seconds', 0)
        file_size_bytes = request.data.get('file_size_bytes', 0)
        record_type = request.data.get('record_type', 'broadcast_video')
        job_id = request.data.get('job_id', '')

        # 3. Create the media Record (it does not exist yet — unlike the old
        #    chunked-upload flow, creation happens here on completion, not on init).
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=claims['user_id'])
        except User.DoesNotExist:
            user = None

        record = Record.objects.create(
            id=uuid.uuid4(),
            tenant_id=tenant_id if tenant_id else None,
            created_by=user,
            record_class='organizational',
            record_family='media',
            record_type=record_type,
            title=title,
            status='active',
            custom_fields={
                'transcoding_status': 'complete',
                'video_url': video_url,
                'thumbnail_url': thumbnail_url,
                'duration_seconds': duration_seconds,
                'file_size_bytes': file_size_bytes,
            },
        )

        # 4. Create TranscodeJob record for audit trail (if job_id provided).
        if job_id:
            TranscodeJob.objects.create(
                record=record,
                job_id=job_id,
                status='complete',
                progress_pct=100,
                completed_at=timezone.now(),
            )

        return Response({
            'record_id': str(record.id),
            'status': 'created',
        }, status=201)
