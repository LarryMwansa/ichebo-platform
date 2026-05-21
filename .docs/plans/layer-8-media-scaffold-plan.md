# Layer 8 — Ichebo Media Scaffold Plan

**Version:** 1.0 — 2026-05-21  
**Status:** Approved for implementation  
**Reference documents:** DOC G (ichebo-media-spec), ADR-021, master-roadmap Layer 8  
**Author:** Claude (technical) — reviewed by Chizola

---

## What This Document Is

A precise build plan for scaffolding Ichebo Media across three codebases simultaneously. Every file to create is named. Every decision that could be made two ways is made here so no time is lost during implementation.

---

## The Two-Level Reality

This scaffold splits cleanly across two environments:

| Level | Environment | What gets built |
|---|---|---|
| **Local** | This machine, right now | All Go source, Django app, Flutter widget — compiles and tests pass |
| **Production** | Hetzner CX42 server (new) | FFmpeg binary, `mediad` systemd service, Nginx proxy, Object Storage credentials, CDN rules |

**Everything in this plan is buildable locally.** When Chizola provisions the Video Engine server, the code is already waiting. The only gap between local and production is the `.env` file and the `ffmpeg` binary.

---

## Repository Structure After Scaffold

```
ichebo-platform/
├── ichebo-media/              ← NEW — Go Video Engine (currently empty dir)
│   ├── go.mod
│   ├── go.sum
│   ├── cmd/
│   │   └── mediad/
│   │       └── main.go        ← HTTP server entry point
│   ├── pkg/
│   │   ├── config/
│   │   │   └── config.go      ← env-based config
│   │   ├── health/
│   │   │   └── health.go      ← GET /health
│   │   ├── storage/
│   │   │   ├── storage.go     ← S3 client (upload + delivery buckets)
│   │   │   └── storage_test.go
│   │   ├── upload/
│   │   │   ├── session.go     ← upload session registry
│   │   │   ├── handler.go     ← init / chunk / complete HTTP handlers
│   │   │   └── upload_test.go
│   │   ├── transcode/
│   │   │   ├── profiles.go    ← quality profile definitions
│   │   │   ├── queue.go       ← buffered channel job queue + worker pool
│   │   │   ├── worker.go      ← FFmpeg execution + segment writes
│   │   │   ├── handler.go     ← POST /engine/transcode, GET status
│   │   │   └── transcode_test.go
│   │   ├── hls/
│   │   │   ├── manifest.go    ← master + per-quality .m3u8 generation
│   │   │   └── manifest_test.go
│   │   └── webhook/
│   │       ├── webhook.go     ← POST to Django /api/media/transcode-complete/
│   │       └── webhook_test.go
│   └── deploy/
│       ├── mediad.service     ← systemd unit file
│       └── nginx-media.conf   ← Nginx proxy config for /engine/
│
├── ichebo-platform/           ← Django backend (existing)
│   ├── media/                 ← NEW Django app
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py          ← VideoRecord helper + TranscodeJob
│   │   ├── serializers.py
│   │   ├── views.py           ← DRF API views
│   │   ├── urls.py
│   │   └── migrations/
│   │       └── 0001_initial.py
│   ├── records/
│   │   └── models.py          ← MODIFIED: add "media" to record_family choices
│   ├── ics_project/
│   │   ├── settings/base.py   ← MODIFIED: add 'media' to INSTALLED_APPS
│   │   └── urls.py            ← MODIFIED: add media API URLs
│   └── video_live/
│       ├── models.py          ← MODIFIED: add Broadcast + StreamKey models
│       ├── views.py           ← MODIFIED: add video library page
│       └── templates/
│           └── video_live/
│               └── library.html ← NEW: video library management UI
│
└── ichebo-mobile/             ← Flutter app (existing)
    ├── pubspec.yaml           ← MODIFIED: add video_player, chewie
    └── lib/
        ├── shared/
        │   └── widgets/
        │       ├── ichebo_video_player.dart  ← NEW: HLS + URL player
        │       ├── video_progress_tracker.dart ← NEW: milestone events
        │       └── chapter_navigator.dart    ← NEW: chapter chip row
        └── features/
            └── learn/
                └── lesson_screen.dart       ← MODIFIED: use IcheboVideoPlayer
```

---

## Phase M.1 — Video Engine (Go)

### M.1.1 — Module scaffold + config

**`ichebo-media/go.mod`**
```
module github.com/ichebo/media
go 1.23

require (
    github.com/aws/aws-sdk-go-v2 v1.32.x
    github.com/aws/aws-sdk-go-v2/config v1.27.x
    github.com/aws/aws-sdk-go-v2/service/s3 v1.61.x
    github.com/aws/aws-sdk-go-v2/credentials v1.17.x
    github.com/google/uuid v1.6.0
)
```

**`pkg/config/config.go`** — All configuration from environment variables. Zero hard-coded values.

| Env var | Purpose | Required |
|---|---|---|
| `MEDIA_PORT` | HTTP server port | No (default: 8090) |
| `MEDIA_UPLOAD_BUCKET` | S3 upload bucket name | Yes (prod only) |
| `MEDIA_DELIVERY_BUCKET` | S3 delivery bucket name | Yes (prod only) |
| `MEDIA_S3_ENDPOINT` | S3 endpoint URL (Hetzner) | Yes (prod only) |
| `MEDIA_S3_REGION` | S3 region | Yes (prod only) |
| `MEDIA_S3_ACCESS_KEY` | S3 access key | Yes (prod only) |
| `MEDIA_S3_SECRET_KEY` | S3 secret key | Yes (prod only) |
| `MEDIA_CDN_BASE_URL` | CDN base URL for delivery | Yes (prod only) |
| `MEDIA_FFMPEG_PATH` | Path to ffmpeg binary | No (default: `ffmpeg`) |
| `MEDIA_WORKER_COUNT` | Transcode worker pool size | No (default: CPU-1) |
| `MEDIA_DJANGO_WEBHOOK_URL` | Django transcode-complete endpoint | Yes (prod only) |
| `MEDIA_DJANGO_API_KEY` | Shared secret for webhook auth | Yes (prod only) |
| `MEDIA_TEMP_DIR` | Temp dir for chunk assembly | No (default: `/tmp/ichebo-media`) |

**Local dev mode:** When `MEDIA_S3_ENDPOINT` is empty, the storage client falls back to local disk (`/tmp/ichebo-media/storage/`). This means the entire engine runs locally without any cloud credentials.

---

### M.1.2 — Storage client

**`pkg/storage/storage.go`** — Two interfaces:

```go
type UploadStore interface {
    PutObject(ctx, key, reader, size) error
    DeleteObject(ctx, key) error
    GetPresignedURL(ctx, key, expiry) (string, error)
}

type DeliveryStore interface {
    PutObject(ctx, key, reader, size) error
    GetPublicURL(key) string  // CDN_BASE_URL + "/" + key
}
```

Two implementations:
- `S3Store` — wraps aws-sdk-go-v2, points to Hetzner Object Storage
- `LocalStore` — writes to local disk, `GetPublicURL` returns `file://` path

**`pkg/storage/storage_test.go`** — Tests against `LocalStore` only (no S3 credentials needed in CI).

---

### M.1.3 — Chunked upload handler

**`pkg/upload/session.go`** — Upload session registry:

```go
type Session struct {
    ID          string
    RecordID    string
    TenantID    string
    Filename    string
    FileSizBytes int64
    TotalChunks int
    TempDir     string
    Received    map[int]string  // chunk_n → sha256 checksum
    mu          sync.Mutex
}

type Registry struct {
    sessions map[string]*Session
    mu       sync.RWMutex
}
```

Sessions are in-memory. On server restart, incomplete uploads are abandoned (clients must re-init). This is acceptable for Phase M.1 — sessions survive normal operation. Persistence can be added in Phase M.2.

**`pkg/upload/handler.go`** — Three HTTP handlers:

**`POST /engine/upload/init`**
- Body: `{ filename, file_size_bytes, content_type, tenant_id, record_id, chunk_size_bytes? }`
- Creates session, calculates `total_chunks = ceil(file_size / chunk_size)` (default chunk size: 5MB)
- Returns: `{ upload_id, total_chunks, chunk_size_bytes }`

**`PUT /engine/upload/{upload_id}/chunk/{n}`**
- Body: raw binary chunk
- Validates: session exists, chunk number valid, not already received
- Writes chunk to `temp_dir/{upload_id}/chunk_{n}`
- Computes SHA-256 of received bytes
- Returns: `{ received: true, checksum: "sha256:..." }`

**`POST /engine/upload/{upload_id}/complete`**
- Body: `{ chunk_checksums: [{ n: 0, checksum: "sha256:..." }, ...] }`
- Validates all chunks received and checksums match
- Assembles chunks into final file using `io.Copy` from each chunk in order
- Uploads assembled file to upload bucket: `uploads/{record_id}/original{ext}`
- Cleans up temp dir
- Returns: `{ raw_object_key: "uploads/{record_id}/original.mp4" }`

**`pkg/upload/upload_test.go`** — Tests:
- `TestSession_ChunkAccounting` — all chunks received, none missed
- `TestUpload_ChecksumMismatch` — chunk with wrong checksum is rejected
- `TestUpload_DuplicateChunk` — duplicate chunk number is idempotent
- `TestUpload_AssemblyOrder` — chunks assembled in correct order regardless of arrival order

---

### M.1.4 — Quality profiles

**`pkg/transcode/profiles.go`** — Locked quality definitions matching spec §2.2:

```go
type QualityProfile struct {
    Name       string   // "1080p", "720p", "480p", "360p", "audio"
    Width      int
    Height     int
    VideoBitrate string  // "-b:v 4M"
    AudioBitrate string  // "-b:a 128k"
    FFmpegArgs  []string // extra args for this profile
}

var DefaultProfiles = []QualityProfile{
    {Name: "1080p", Width: 1920, Height: 1080, VideoBitrate: "4M", AudioBitrate: "192k"},
    {Name: "720p",  Width: 1280, Height: 720,  VideoBitrate: "2M", AudioBitrate: "128k"},
    {Name: "480p",  Width: 854,  Height: 480,  VideoBitrate: "1M", AudioBitrate: "96k"},
    {Name: "360p",  Width: 640,  Height: 360,  VideoBitrate: "600k", AudioBitrate: "64k"},
    {Name: "audio", Width: 0,    Height: 0,    VideoBitrate: "", AudioBitrate: "128k"},
}
```

---

### M.1.5 — Transcoding queue + worker

**`pkg/transcode/queue.go`** — Job queue:

```go
type Job struct {
    ID           string
    UploadID     string
    RecordID     string
    TenantID     string
    RawObjectKey string
    Profiles     []string  // ["1080p","720p","480p","360p"]
    Status       string    // queued | processing | complete | failed
    ProgressPct  int
    Error        string
    CreatedAt    time.Time
    CompletedAt  *time.Time
}

type Queue struct {
    jobs    map[string]*Job
    ch      chan *Job
    mu      sync.RWMutex
}
```

Worker pool: `min(runtime.NumCPU()-1, 4)` goroutines. Each worker blocks on `ch`. One job at a time per worker.

**Local dev behaviour:** With `MEDIA_FFMPEG_PATH` unset and FFmpeg not installed, worker logs `[transcode] ffmpeg not available — skipping` and marks job `complete` with a stub `video_url`. This lets the entire API run locally without FFmpeg.

**`pkg/transcode/worker.go`** — For each job:

1. Download raw file from upload bucket to local temp path
2. For each quality profile:
   - Run FFmpeg: `ffmpeg -i {input} {profile_args} -hls_time 6 -hls_segment_filename {out_dir}/{profile}/segment_%03d.ts {out_dir}/{profile}/index.m3u8`
   - On progress: parse FFmpeg stderr (`frame=... fps=... time=...`) → update `ProgressPct`
3. Extract thumbnail: `ffmpeg -i {input} -ss 10 -frames:v 1 {out_dir}/thumbnail.jpg`
4. Upload all segments, manifests, thumbnail to delivery bucket at `videos/{record_id}/`
5. Build master HLS manifest (see M.1.6)
6. Upload master manifest to `videos/{record_id}/index.m3u8`
7. Call webhook to notify Django (see M.1.7)
8. Mark job `complete`

**`pkg/transcode/handler.go`** — Two HTTP handlers:

**`POST /engine/transcode`**
- Body: `{ upload_id, record_id, raw_object_key, quality_profiles?, tenant_id }`
- Creates job, pushes to queue channel
- Returns: `{ job_id }`

**`GET /engine/transcode/{job_id}/status`**
- Returns: `{ job_id, status, progress_pct, error? }`

**`pkg/transcode/transcode_test.go`** — Tests:
- `TestQueue_EnqueueAndDequeue`
- `TestJob_StatusTransitions`
- `TestProfile_FFmpegArgs` — validates generated FFmpeg command string for each profile
- `TestWorker_StubMode` — worker completes gracefully when FFmpeg unavailable

---

### M.1.6 — HLS manifest generation

**`pkg/hls/manifest.go`** — Builds master `.m3u8` per spec §5.3:

```
#EXTM3U
#EXT-X-VERSION:3

#EXT-X-STREAM-INF:BANDWIDTH=4000000,RESOLUTION=1920x1080
1080p/index.m3u8

#EXT-X-STREAM-INF:BANDWIDTH=2000000,RESOLUTION=1280x720
720p/index.m3u8

#EXT-X-STREAM-INF:BANDWIDTH=1000000,RESOLUTION=854x480
480p/index.m3u8

#EXT-X-STREAM-INF:BANDWIDTH=600000,RESOLUTION=640x360
360p/index.m3u8

#EXT-X-STREAM-INF:BANDWIDTH=128000
audio/index.m3u8
```

`BuildMasterManifest(profiles []QualityProfile) string` — pure function, no I/O.

**`pkg/hls/manifest_test.go`** — `TestManifest_ContainsAllProfiles`, `TestManifest_BandwidthOrder` (highest first)

---

### M.1.7 — Django webhook client

**`pkg/webhook/webhook.go`** — Called by worker on job completion:

```
POST {MEDIA_DJANGO_WEBHOOK_URL}/api/media/transcode-complete/
Authorization: Bearer {MEDIA_DJANGO_API_KEY}
Content-Type: application/json

{
  "job_id": "uuid",
  "record_id": "uuid",
  "status": "complete",
  "video_url": "https://cdn.ichebo.org/videos/{record_id}/index.m3u8",
  "thumbnail_url": "https://cdn.ichebo.org/videos/{record_id}/thumbnail.jpg",
  "duration_seconds": 3720,
  "quality_variants": [
    {"name": "1080p", "url": "https://cdn.ichebo.org/videos/{record_id}/1080p/index.m3u8"},
    ...
  ],
  "file_size_bytes": 2147483648
}
```

Retry policy: 3 attempts, exponential backoff (2s, 4s, 8s). On all retries exhausted: logs error, does not crash.

**`pkg/webhook/webhook_test.go`** — `TestWebhook_SuccessOnFirstAttempt`, `TestWebhook_RetryOnFailure`, `TestWebhook_ExhaustedRetries`

---

### M.1.8 — HTTP server entry point

**`cmd/mediad/main.go`**:
- Loads config
- Initialises storage clients (S3 or local based on env)
- Initialises upload registry
- Initialises transcode queue + starts worker pool
- Registers all HTTP handlers on `net/http` ServeMux
- `GET /health` → `{"status":"ok","version":"0.1.0"}`
- `GET /engine/status` → worker pool stats (queue depth, active workers)
- `POST /engine/upload/init`
- `PUT /engine/upload/{id}/chunk/{n}`
- `POST /engine/upload/{id}/complete`
- `POST /engine/transcode`
- `GET /engine/transcode/{id}/status`
- Listens on `MEDIA_PORT` (default 8090)
- Graceful shutdown on SIGTERM (drains in-flight transcodes up to 10 minutes)

---

### M.1.9 — Deploy files

**`deploy/mediad.service`** — systemd unit for production:
```ini
[Unit]
Description=Ichebo Media Video Engine
After=network.target

[Service]
Type=simple
User=ichebo
WorkingDirectory=/opt/ichebo-media
EnvironmentFile=/etc/ichebo/media.env
ExecStart=/usr/local/bin/mediad
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**`deploy/nginx-media.conf`** — Nginx location block to proxy `/engine/` to Go service on port 8090.

---

## Phase M.2 — Django `media` app

### M.2.1 — Records model change

**`records/models.py`** — Add `"media"` to `RECORD_FAMILY_CHOICES`:
```python
('media', 'Media'),
```

Migration: `records/migrations/0004_record_family_media.py` (AlterField only — no data change).

---

### M.2.2 — `media` app models

**`media/models.py`** — Two models:

**`VideoRecord`** — not a database model. A Python helper class that wraps a `Record` instance and provides typed property accessors for `custom_fields` keys. No migration needed.

```python
class VideoRecord:
    """Typed accessors for a Record with record_family='media'."""
    def __init__(self, record: Record): self._r = record
    
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
```

**`TranscodeJob`** — database model:
```python
class TranscodeJob(models.Model):
    id         = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    record     = ForeignKey(Record, on_delete=PROTECT, related_name='transcode_jobs')
    job_id     = CharField(max_length=100)         # UUID from Video Engine
    status     = CharField(max_length=20)          # queued|processing|complete|failed
    progress_pct = IntegerField(default=0)
    error      = TextField(blank=True)
    created_at = DateTimeField(auto_now_add=True)
    completed_at = DateTimeField(null=True, blank=True)
```

---

### M.2.3 — DRF API

**`media/views.py`** — Five views:

| Endpoint | Method | Auth | Action |
|---|---|---|---|
| `/api/media/upload/init/` | POST | Token | Validates, calls Video Engine `/engine/upload/init`, returns session |
| `/api/media/upload/complete/` | POST | Token | Calls Video Engine `/engine/upload/{id}/complete`, creates Record + TranscodeJob, calls `/engine/transcode` |
| `/api/media/videos/` | GET | Token | List Records with `record_family=media`, paginated, ordered by `created_at` desc |
| `/api/media/videos/{id}/` | GET | Token | Single video Record with all custom_fields |
| `/api/media/transcode-complete/` | POST | API key | Webhook: update TranscodeJob + Record custom_fields |

**`POST /api/media/upload/init/`** — body:
```json
{ "title": "...", "filename": "...", "file_size_bytes": 1234, "record_type": "teaching_video" }
```
Creates the Record immediately (`transcoding_status: "queued"`). Forwards to Video Engine. Returns `{ record_id, upload_id, total_chunks, chunk_size_bytes }`.

**`POST /api/media/transcode-complete/`** — webhook body:
```json
{ "job_id": "...", "record_id": "...", "status": "complete", "video_url": "...", "thumbnail_url": "...", "duration_seconds": 3720, "quality_variants": [...] }
```
Updates `Record.custom_fields` atomically. Updates `TranscodeJob.status`. No response body needed (returns 200).

---

### M.2.4 — Video library management UI

**`video_live/templates/video_live/library.html`** — Extends the base Apostolic Command Shell template. Lists all media Records as cards with:
- Thumbnail (or placeholder if still transcoding)
- Title, presenter, duration
- Transcoding status badge (queued / processing N% / complete / failed)
- Copy HLS URL button (for pasting into lesson records)

This is a read-browse UI only in Phase M.1. Upload is via the DRF API (mobile or dedicated upload form in Phase M.3).

---

### M.2.5 — Django settings + URL wiring

**`ics_project/settings/base.py`** — Add to `INSTALLED_APPS`:
```python
'media',
```

Add to settings:
```python
MEDIA_ENGINE_URL = env('MEDIA_ENGINE_URL', default='http://localhost:8090')
MEDIA_ENGINE_API_KEY = env('MEDIA_ENGINE_API_KEY', default='dev-key')
```

**`ics_project/urls.py`** — Add:
```python
path('api/media/', include('media.urls')),
```

---

## Phase M.3 — Flutter HLS Player

### M.3.1 — pubspec additions

```yaml
video_player: ^2.9.2
chewie: ^1.8.5
```

**Why `chewie` over `better_player`:** Chewie is the official Flutter team's UI layer over `video_player`. Actively maintained. `better_player` is community-maintained with a history of stale PRs. Spec §6.1 names both — chewie is the right choice.

---

### M.3.2 — `IcheboVideoPlayer` widget

**`lib/shared/widgets/ichebo_video_player.dart`**

Signature:
```dart
class IcheboVideoPlayer extends StatefulWidget {
  final String videoUrl;           // HLS .m3u8 URL or YouTube/Vimeo URL
  final double? aspectRatio;       // default 16/9
  final String? activityId;        // if set, progress tracking is active
  final String? videoRecordId;     // paired with activityId
  final List<ChapterMarker>? chapters;
  final VoidCallback? onComplete;  // fired at 100% milestone
}
```

**URL routing logic** (mirrors spec §7.3):
- Contains `.m3u8` OR starts with `https://cdn.ichebo.org` → HLS player (video_player + chewie)
- Contains `youtube.com`, `youtu.be`, `vimeo.com` → `url_launcher` (existing behaviour)
- Anything else → `url_launcher` fallback

**HLS player features:**
- `VideoPlayerController.networkUrl(Uri.parse(videoUrl))` with HLS headers
- Chewie controller with: `allowFullScreen: true`, `allowPlaybackSpeedChanging: true`, `playbackSpeeds: [0.75, 1.0, 1.25, 1.5, 2.0]`
- Chapter navigator rendered below the player if `chapters != null && chapters.isNotEmpty`
- Progress tracker wired if `activityId != null`

---

### M.3.3 — `VideoProgressTracker`

**`lib/shared/widgets/video_progress_tracker.dart`**

```dart
class VideoProgressTracker {
  final String activityId;
  final String videoRecordId;
  final int totalSeconds;
  final WidgetRef ref;
  
  final Set<int> _firedMilestones = {};
  
  void onProgress(int watchedSeconds) {
    // Fires PATCH to activities/{activityId}/
    // at 25, 50, 75, 100% — each milestone fires exactly once per session
    // metadata: { source_app: "learn", video_record_id, watched_seconds, total_seconds }
  }
}
```

Progress PATCH body:
```json
{
  "progress": 75,
  "metadata": {
    "source_app": "learn",
    "video_record_id": "uuid",
    "watched_seconds": 1980,
    "total_seconds": 2640
  }
}
```

At `progress: 100` → also calls `onComplete` callback on the player widget.

---

### M.3.4 — `ChapterNavigator`

**`lib/shared/widgets/chapter_navigator.dart`**

```dart
class ChapterMarker {
  final int timestampSeconds;
  final String title;
}

class ChapterNavigator extends StatelessWidget {
  final List<ChapterMarker> chapters;
  final VideoPlayerController controller;
  final int currentPositionSeconds;
}
```

Horizontal scrollable `ListView` of `FilterChip` widgets. Active chapter (current position falls within its range) is highlighted with `IcheboColors.primaryLight`. Tapping seeks `controller.seekTo(Duration(seconds: chapter.timestampSeconds))`.

---

### M.3.5 — Lesson screen wiring

**`lib/features/learn/lesson_screen.dart`** — Replace `_VideoCard`:

```dart
// Before: opens externally
// After:
IcheboVideoPlayer(
  videoUrl: lesson.videoUrl!,
  activityId: lesson.activityId,  // if lesson has linked activity
  videoRecordId: lesson.videoRecordId,  // if lesson has linked video record
  chapters: lesson.chapterMarkers?.map(...).toList(),
  onComplete: () {
    // trigger lesson mark-complete flow
    _markComplete();
  },
)
```

`Lesson` model in `providers.dart` needs two new optional fields: `videoRecordId` and `chapterMarkers`. Add them to `Lesson.fromJson`.

---

## Models Updated — `providers.dart`

```dart
class ChapterMarker {
  const ChapterMarker({required this.timestampSeconds, required this.title});
  final int timestampSeconds;
  final String title;
  factory ChapterMarker.fromJson(Map<String, dynamic> j) => ChapterMarker(
    timestampSeconds: j['timestamp_seconds'] as int,
    title: j['title'] as String,
  );
}

// Lesson model — add fields:
final String? videoRecordId;
final List<ChapterMarker> chapterMarkers;

// Lesson.fromJson — add:
videoRecordId: j['video_record_id'] as String?,
chapterMarkers: (j['chapter_markers'] as List? ?? [])
    .map((e) => ChapterMarker.fromJson(e as Map<String, dynamic>)).toList(),
```

---

## Test Coverage

| Package | Tests |
|---|---|
| `pkg/storage` | LocalStore put/get/delete, presigned URL format |
| `pkg/upload` | Chunk accounting, checksum mismatch, duplicate chunk, assembly order |
| `pkg/transcode` | Enqueue/dequeue, status transitions, FFmpeg arg generation, stub mode |
| `pkg/hls` | Master manifest content, bandwidth order |
| `pkg/webhook` | Success, retry, exhausted retries |
| Django `media` | Upload init creates Record, webhook updates custom_fields, list/detail views |

Flutter: no automated tests in this phase (UI widgets are tested manually on device).

---

## What Is Explicitly NOT Built Here

| Item | Why deferred |
|---|---|
| M.2 Live streaming (MediaMTX) | Requires dedicated server — ops work. All code blocked on it is skipped. |
| Broadcast scheduling / stream key UI | Blocked on MediaMTX server |
| Offline video download | Blocked on Layer 6 (Desktop) not built yet |
| Captioning, analytics, multi-language audio | Explicitly deferred — spec §8.5 |
| Video upload form in Django management UI | Phase M.3 learning video phase |
| Picture-in-picture | Desktop phase (Layer 6) |

---

## Build Order

```
M.1.1 go.mod + config              (30 min)
M.1.2 storage client + tests       (45 min)
M.1.3 upload handler + tests       (60 min)
M.1.4 quality profiles             (15 min)
M.1.5 transcode queue + worker     (90 min)   ← longest task
M.1.6 HLS manifest + tests         (30 min)
M.1.7 webhook client + tests       (30 min)
M.1.8 HTTP server entry point      (30 min)
M.1.9 deploy files                 (20 min)

M.2.1 records model + migration    (15 min)
M.2.2 media app models             (20 min)
M.2.3 DRF API views                (60 min)
M.2.4 video library UI             (30 min)
M.2.5 settings + URL wiring        (15 min)

M.3.1 pubspec additions            (5 min)
M.3.2 IcheboVideoPlayer widget     (60 min)
M.3.3 VideoProgressTracker        (30 min)
M.3.4 ChapterNavigator             (30 min)
M.3.5 lesson screen wiring         (20 min)

COMMIT                             (10 min)
```

**Total estimated:** ~9 hours of focused build time.

---

## Commit Message When Done

```
feat(media): Layer 8 scaffold — Video Engine, Django media app, Flutter HLS player

Go Video Engine (ichebo-media):
- Chunked upload handler (init/chunk/complete) with SHA-256 validation
- Transcoding queue + FFmpeg worker pool with quality profiles (1080p/720p/480p/360p/audio)
- HLS master manifest generation per spec §5.3
- Webhook client to Django with retry/backoff
- Local dev mode: runs without S3 or FFmpeg installed
- systemd service + Nginx proxy config in deploy/

Django media app:
- TranscodeJob model + migration
- DRF API: upload init/complete, video list/detail, transcode-complete webhook
- VideoRecord helper with typed custom_fields accessors
- Video library management page in video_live app
- "media" added to record_family choices

Flutter HLS player:
- IcheboVideoPlayer: HLS (video_player+chewie) for .m3u8, url_launcher for YouTube/Vimeo
- VideoProgressTracker: 25/50/75/100% milestones → PATCH activities/
- ChapterNavigator: seekable chip row from chapter_markers custom_fields
- LessonScreen wired to IcheboVideoPlayer

Phase M.2 (live streaming) deferred — requires MediaMTX server infrastructure.
Phase M.3 offline download deferred — requires Layer 6 Desktop.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
