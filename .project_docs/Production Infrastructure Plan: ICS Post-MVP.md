# Production Infrastructure Plan: ICS Post-MVP

## Context
MVP is complete. Next phase requires preparing the VPS (8GB RAM / 80GB HDD) for:
- Mobile app traffic (DRF API as primary consumer)
- Redis + Celery for background tasks (Paraclete AI, notifications)
- Django Channels for real-time notifications
- Docker Compose for portability and easier scaling later
- **MinIO** local S3-compatible object storage (profile avatars, tenant logos, future video files)
- **Offline capabilities** — service worker PWA for desktop web; SQLite + sync for mobile
- **Device file manager** — save/open ICS content on phone, laptop, or desktop
- **Records linking improvements** — fix Activity→Record loose metadata links; add aggregated related-records API; wire Community to Record
- **Video player** — simple URL-based embed (YouTube, Vimeo, direct `.mp4`); no self-hosting infrastructure required
- Mobile app serves **ALL levels (0–5 + prime tenant)** with role-adaptive UI — operators get full tools on mobile, not a lite member-only view
- Desktop HTMX remains the primary surface for complex operator workflows; mobile exposes the same capability in a touch-optimised form

---

## Firebase FCM (Push Notifications)
**Free. No credit card required.**
Firebase Spark (free) plan includes:
- Unlimited FCM push notification messages
- Covers both Android and iOS
- Only pay if you use Firestore, Functions, or Hosting — none of which are needed here
- Cost to start: $0

---

## VPS Upgrade Requirement

### Current assumed spec (based on 3 Gunicorn workers)
- ~1 CPU core, ~2GB RAM
- Footprint: ~1.2GB RAM (Gunicorn + PostgreSQL + Nginx + OS)

### Minimum for production with Redis + Celery + Docker
| Service | RAM needed |
|---------|-----------|
| OS + Nginx | ~350MB |
| PostgreSQL | ~400MB |
| Gunicorn/Uvicorn (ASGI) | ~450MB |
| Redis | ~150MB |
| Celery workers (3) | ~400MB |
| Docker daemon + overhead | ~400MB |
| Buffer | ~850MB |
| **Total** | **~3GB** |

**Minimum recommended: 4GB RAM, 2 vCPU, 60GB SSD**
**Comfortable for a few hundred concurrent users: 8GB RAM, 4 vCPU, 80GB SSD**
**User confirmed: 8GB RAM / 80GB HDD — already at the comfortable tier.**

Most VPS providers (Hetzner, DigitalOcean, Linode): 4GB/2vCPU costs ~$12–20/month.

---

## Production Stack (What Gets Added)

```
Current:                          New:
Nginx                             Nginx (+ MinIO proxy pass on /media/)
Gunicorn (sync WSGI)         →    Uvicorn/Daphne (async ASGI)
PostgreSQL                        PostgreSQL
File-based cache             →    Redis (cache + broker + WebSocket)
-                            →    Celery worker (background tasks)
-                            →    Celery beat (scheduled tasks)
-                            →    Django Channels (WebSocket/real-time)
URLField for avatars/logos   →    MinIO (S3-compatible local object store)
systemd (manual)             →    Docker Compose (service orchestration)
```

---

## MinIO — Local S3-Compatible Object Storage

**Why MinIO instead of AWS S3?**
- Runs locally on the VPS — zero egress costs, no cloud dependency
- S3-compatible API: same boto3/django-storages code, swap to AWS S3 later with one env var change
- ~256MB RAM footprint
- Stores: profile avatars, tenant logos, attachments, future video files
- Web console at port 9001 for easy bucket management

**Storage buckets:**
| Bucket | Contents | Access |
|--------|----------|--------|
| `ics-avatars` | User profile pictures | Public read |
| `ics-logos` | Tenant/community logos | Public read |
| `ics-private` | Protected member docs, attachments | Private (presigned URLs) |
| `ics-documents` | Record attachments uploaded from device | Private (presigned URLs, 1hr expiry) |
| `ics-videos` | Self-hosted video files (future phase only) | Private (presigned URLs) |

**HDD headroom on 80GB:**
| Use | Estimate |
|-----|----------|
| OS + Docker + app | ~15GB |
| PostgreSQL data | ~5GB |
| MinIO media files | ~30GB |
| Self-hosted video (future) | ~25GB |
| **Total** | **~75GB / 80GB** |

---

## Video — Simple URL Player (No Self-Hosting Required)

**Approach: embed videos from YouTube, Vimeo, or any direct `.mp4` URL. No upload, no transcoding, no HLS.**

- Users (operators) paste a video URL when creating a lesson or gathering
- Backend normalises it to an embed URL (YouTube `watch?v=ID` → `embed/ID`)
- HTMX template renders `<iframe>` for YouTube/Vimeo or `<video>` tag for direct `.mp4` links
- Mobile Flutter uses `youtube_player_flutter` (YouTube) + `video_player` (direct URLs)
- The existing `stream_url = URLField` on Gatherings already supports this — no new model needed for gatherings
- For lesson Records: store video URL in `custom_fields['video_url']` (JSONField already exists) or add a single `video_url = URLField(blank=True)` to the Record model

**What is NOT needed (removed from plan):**
- MinIO `ics-videos` bucket — not required for URL-based playback
- ffmpeg / `ffmpeg-python` — not required
- `transcode_video` Celery task — not required
- HLS segments / `.m3u8` playlists — not required
- `hls.js` — not required
- Separate `video/` Django app — not required

**Self-hosted video (deferred):** If the ministry later needs to upload and host its own video files (e.g. confidential content not suitable for YouTube), the Celery + MinIO infrastructure from other phases is already in place as a foundation. That is a separate future phase.

---

## Records Linking & Relationships (Build Now)

### What already exists (do not rebuild)
- `Relationship` model: 16 typed relationship types, directed/bidirectional, strength, notes, soft-delete — fully built
- REST CRUD at `GET/POST /api/relationships/` + `GET/PUT/DELETE /api/relationships/{id}/`
- `governance/services.py`: `get_linked_records(record_id)` — already traverses both outgoing and incoming relationships
- `learn/views.py`: `part_of` relationships already navigate lesson → course → programme hierarchy
- `records/tests.py`: relationship creation and soft-delete tests already exist

### Gaps to fix now

**1. Activity → Record linking (fix loose metadata coupling)**

Current: `Activity.metadata['programme_record_id']` and `metadata['lesson_record_id']` — loose string keys, no FK, no query support.

Fix: Add explicit FK fields to the Activity model:
```python
# activity/models.py
linked_record = models.ForeignKey(
    'records.Record', on_delete=models.SET_NULL,
    null=True, blank=True, related_name='linked_activities'
)
```
- New migration for `activity` app
- Update `activity/serializers.py` to expose `linked_record_id`
- Keep metadata fields for backward compat; new code uses FK

**2. Aggregated Related Records API**

Current: Clients must make two calls — `?from_record_id=X` and `?to_record_id=X` — and merge results themselves.

Fix: Add a new action on `RecordViewSet`:
```
GET /api/records/{id}/related/
```
Returns all outgoing + incoming relationships for a record, grouped by `relationship_type`. Reuses `get_linked_records()` from `governance/services.py` — no new logic, just expose it.

**File to change:** `records/views.py` — add `@action(detail=True, methods=['get'])` named `related`
**File to change:** `records/urls.py` — router already handles custom actions via ModelViewSet; no URL change needed

**3. Community → Record linking**

Current: Community models (`MembershipRequest` stub only) have zero links to Record. Announcements and gatherings are stored as Records directly, but there's no way to link community content to governance records.

Fix: Use the existing Relationship model — no new model needed. Add a community-scoped relationship type `community_ref` to RELATIONSHIP_TYPES choices. Expose via the existing `/api/relationships/` CRUD.

**4. Django Admin registration**

Fix: Register `Relationship` in `records/admin.py` so operators can inspect and manually manage links.

---

## Video Player — Simple Implementation

### Desktop Web (HTMX)
**New template partial:** `templates/video/player.html`
```html
{% if video_url %}
  {% if 'youtube.com' in video_url or 'youtu.be' in video_url %}
    <iframe src="{{ embed_url }}" frameborder="0" allowfullscreen
            class="w-full aspect-video rounded-lg"></iframe>
  {% elif 'vimeo.com' in video_url %}
    <iframe src="{{ embed_url }}" frameborder="0" allowfullscreen
            class="w-full aspect-video rounded-lg"></iframe>
  {% else %}
    <video src="{{ video_url }}" controls class="w-full rounded-lg"></video>
  {% endif %}
{% endif %}
```

**New utility:** `core/utils/video.py` — `get_embed_url(url)` converts watch URLs to embed URLs:
- `youtube.com/watch?v=ID` → `youtube.com/embed/ID`
- `youtu.be/ID` → `youtube.com/embed/ID`
- `vimeo.com/ID` → `player.vimeo.com/video/ID`
- Direct `.mp4` URL → returned as-is (rendered with `<video>` tag)

**Model change:** `records/models.py` — add `video_url = models.URLField(blank=True)` to Record model for lesson videos. Gatherings already have `stream_url`.

**New migration:** `records` app

### Mobile (Flutter — added at mobile build phase)
- `youtube_player_flutter`: renders YouTube player natively for YouTube URLs
- `video_player` + `chewie`: plays direct `.mp4` URLs with controls
- URL type detected from `video_url` field in the Record/Gathering API response

### No new infrastructure needed
No MinIO video bucket, no ffmpeg, no Celery task, no hls.js. Zero additional dependencies beyond what is already planned.

---

## Offline Capabilities & Device File Manager

### Strategy per platform

| Platform | Users | Offline Storage | File Manager |
|----------|-------|----------------|--------------|
| Desktop Web (HTMX) | All levels (primary operator surface) | Service Worker + IndexedDB | File System Access API (Chrome/Edge) |
| Mobile App (Flutter) | **All levels 0–5 + prime tenant** | SQLite (`sqflite`) | `path_provider` + `file_picker` |

**Mobile app is not a lite member-only companion — it is a full-capability client for every role.** The API already enforces permissions per level; the Flutter app simply adapts its navigation shell and screen set based on the authenticated user's level.

---

### Role-Adaptive Mobile App Architecture

One Flutter app, one codebase. Navigation shell and available screens are driven by `user.level` returned in the auth token response. The DRF backend already enforces permissions — the app simply renders what the user is allowed to see.

**Navigation shells by level:**

| Level | Role | Bottom Nav / Drawer |
|-------|------|---------------------|
| 0 | Guest/Seeker | Bible, Learn, Explore, Profile |
| 1 | Member | + Activities, Community |
| 2 | Disciple | + Governance (read), Certifications |
| 3 | Leader | + My Group dashboard, Member management (group-scoped) |
| 4 | Elder | + Programme oversight, Reports, Governance (write) |
| 5 | Apostle | + Full operator console, Announcements, All reports |
| Prime | Tenant admin | + Tenant switcher, Multi-community oversight, Billing/settings |

**Adaptive UI rules:**
- Auth response includes `{ level: 4, permissions: [...] }` — Flutter router applies `GoRouter` redirect guards per route
- Each screen checks `AuthProvider.level` for conditional widget rendering (e.g. Edit buttons only appear for Levels 3+)
- Operator screens (governance management, programme builder, member roster) are full-featured — same data as HTMX desktop, different layout optimised for touch
- Prime tenant sees a **community switcher** in the app bar — can switch context between communities they oversee
- Deep links and push notifications route to the correct screen regardless of level

**DRF API contract for mobile:**
- `GET /api/auth/me/` — returns `{ id, name, level, permissions[], tenant_id, tenant_name, avatar_url }`
- All existing DRF endpoints already use `level`-based `IsAuthenticated` + `HasPermission` guards
- No new permission logic needed — the app just consumes what the API already exposes

**Robustness requirements:**
- App must function fully offline for read operations (SQLite cache)
- Write operations queue locally when offline, sync on reconnect (Background Sync via `workmanager`)
- FCM push notifications wake the app and refresh the relevant screen
- Session token refresh handled silently (refresh token flow, no forced logout on expiry)
- All operator tools available 24/7 — no "desktop only" restrictions

---

### Desktop Web — PWA + Service Worker (HTMX)

**What gets cached offline:**
- Handbook pages, governance docs, lesson content (read-only)
- Last-viewed dashboard state
- User preferences and form drafts (IndexedDB)

**Implementation:**
1. `manifest.json` — makes the HTMX app installable as a PWA on desktop/laptop
2. `static/js/sw.js` (service worker):
   - **Cache-first** for static assets (CSS, JS, fonts)
   - **Network-first with cache fallback** for handbook/governance pages
   - **Background Sync** for queued write operations (form submits while offline)
3. IndexedDB (via `idb` library): store draft edits, queue failed POSTs, cache Record JSON
4. Nginx: serve `manifest.json` and set correct `Service-Worker-Allowed` headers

**File manager on desktop (Chrome/Edge):**
- [File System Access API](https://developer.chrome.com/docs/capabilities/web-apis/file-system-access) — no library needed, native browser API
- Operator clicks "Save to device" on any Record → `window.showSaveFilePicker()` → saves as `.pdf` or `.html`
- Operator clicks "Open folder" → `window.showDirectoryPicker()` → browser reads/writes files in that local folder
- Falls back to standard `<a download>` link on Firefox/Safari

**New files:**
- `static/js/sw.js` — service worker
- `static/manifest.json` — PWA manifest
- `templates/base.html` — add `<link rel="manifest">` and SW registration script

---

### Mobile App — Offline First (Flutter, All Levels)

**Local database:**
- `sqflite`: SQLite on device — mirrors Records, Bible verses, Activities, Lessons, Governance docs, Programmes
- Scope cached per level: Level 0–2 caches personal + community data; Level 3–5 caches their scoped management data (group roster, programme records, reports)
- Sync strategy: `GET /api/sync/?since=<iso_timestamp>` delta endpoint (all models already have `updated_at`)
- On open: fetch delta, apply to local SQLite; on write: local-first, queue to backend, sync when online

**Device file system:**
- `path_provider`: `getApplicationDocumentsDirectory()` — private to app, persists across updates
- `getExternalStorageDirectory()` (Android) / `getDownloadsDirectory()` — visible in device Files app
- `file_picker`: System file picker — attach any device file (PDF, image, doc) to a Record or message
- `open_file_plus`: Open downloaded ICS files in native viewer apps

**File manager UX (all levels):**
- "My ICS Files" screen — visible to all users
- Base folder structure: `ICS/Lessons/`, `ICS/Handbook/`, `ICS/Downloads/`
- Operators (Level 3+) also see: `ICS/Governance/`, `ICS/Reports/`, `ICS/Programmes/`
- User can create subfolders, rename, delete, share via Android/iOS share sheet
- Downloaded content auto-saves to the relevant folder by type

**New Flutter packages (added when mobile app is built):**
```
sqflite, path_provider, file_picker, open_file_plus, workmanager (background sync), go_router (role-adaptive routing)
```

---

### Backend — Delta Sync API (needed by both platforms)

**New endpoint:** `GET /api/sync/changes/`
- Query param: `?since=2026-04-01T00:00:00Z`
- Returns: all Records, Activities, and Notifications modified after that timestamp
- All models already have `updated_at = auto_now=True` — no model changes needed
- Response format matches existing DRF serializers

**New file:** `core/views/sync.py` — `SyncChangesView(APIView)`
**New URL:** `api/sync/changes/` in `ics_project/urls.py`

---

### MinIO Bucket Addition (for offline/file manager)

Add `ics-documents` bucket:
| Bucket | Contents | Access |
|--------|----------|--------|
| `ics-documents` | User-uploaded attachments on Records | Private (presigned URLs, 1-hour expiry) |

**New model (now, not deferred):**
```python
# records/models.py — new model
class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='attachments')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    file = models.FileField(upload_to='documents/')
    filename = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
```

This is the server-side anchor for files users upload from their device (mobile file picker → DRF upload → MinIO `ics-documents` → presigned URL returned to client).

---

## Implementation Plan

### Phase 1: Dependencies
**Files to change:**
- `requirements.txt` — add: `redis`, `celery`, `django-celery-beat`, `channels`, `channels-redis`, `uvicorn[standard]`, `daphne`, `django-storages[s3]`, `boto3`, `Pillow`

### Phase 2: Django Settings
**Files to change:**
- `ics_project/settings/base.py` — add CHANNEL_LAYERS, CELERY_*, CACHES (Redis), STORAGES, MEDIA_URL
- `ics_project/settings/production.py` — Redis URLs + MinIO credentials from env vars

**New settings:**
```python
CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": env("REDIS_URL")}}
CHANNEL_LAYERS = {"default": {"BACKEND": "channels_redis.core.RedisChannelLayer", "CONFIG": {"hosts": [env("REDIS_URL")]}}}
CELERY_BROKER_URL = env("REDIS_URL")
CELERY_RESULT_BACKEND = env("REDIS_URL")

# MinIO / S3-compatible storage
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    },
}
AWS_S3_ENDPOINT_URL = env("MINIO_ENDPOINT")       # e.g. http://minio:9000
AWS_ACCESS_KEY_ID = env("MINIO_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = env("MINIO_SECRET_KEY")
AWS_STORAGE_BUCKET_NAME = env("MINIO_BUCKET_NAME", default="ics-media")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
MEDIA_URL = env("MEDIA_URL")                       # e.g. http://yourdomain.com/media/
```

### Phase 3: Celery App
**New file:** `ics_project/celery.py`
**Update:** `ics_project/__init__.py` to load Celery on startup

### Phase 4: ASGI Configuration
**File to change:** `ics_project/asgi.py` — wire Django Channels router
**Replace:** Gunicorn WSGI → Daphne or Uvicorn ASGI in systemd service

### Phase 5: Docker Compose
**New file:** `docker-compose.yml` — services: web, redis, celery-worker, celery-beat, minio
**New file:** `Dockerfile` — Python 3.11, deps, staticfiles

MinIO service in compose:
```yaml
minio:
  image: minio/minio:latest
  command: server /data --console-address ":9001"
  environment:
    MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
    MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
  volumes:
    - minio_data:/data
  ports:
    - "9000:9000"   # S3 API (internal only — Nginx proxies /media/)
    - "9001:9001"   # Admin console (firewall to VPN/localhost only)
  healthcheck:
    test: ["CMD", "mc", "ready", "local"]
```

**Nginx config addition:** proxy `/media/` to MinIO at `http://minio:9000/ics-media/`

### Phase 6: Environment Variables
**File to change:** `.env.example` — add:
```
REDIS_URL=redis://redis:6379/0
MINIO_ENDPOINT=http://minio:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_BUCKET_NAME=ics-media
MEDIA_URL=https://yourdomain.com/media/
```

### Phase 7: File Storage — Model Updates
**Files to change:**
- `accounts/models.py` — replace `avatar_url = URLField` with `avatar = ImageField(upload_to='avatars/', blank=True, null=True)`; keep `avatar_url` as a `@property` returning `avatar.url` for serializer backward-compat
- `tenants/models.py` — replace `logo_url = URLField` with `logo = ImageField(upload_to='logos/', blank=True, null=True)`; same `@property` pattern
- `accounts/serializers.py` — add writable `avatar` field; keep `avatar_url` as read-only URL output
- `records/models.py` — add `Attachment` model (linked to Record, FileField → MinIO `ics-documents` bucket)
**New migrations:** `accounts`, `tenants`, and `records` apps

### Phase 8: Records Linking Improvements
**Files to change:**
- `activity/models.py` — add `linked_record = ForeignKey('records.Record', SET_NULL, null=True, blank=True, related_name='linked_activities')`
- `activity/serializers.py` — expose `linked_record_id` as writable field
- `records/models.py` — add `'community_ref'` to RELATIONSHIP_TYPES choices
- `records/views.py` — add `@action(detail=True) def related(self, request, pk)` on RecordViewSet; reuses `get_linked_records()` from `governance/services.py`
- `records/admin.py` — register `Relationship` model with list_filter on relationship_type and created_at
**New migration:** `activity` app

### Phase 9: Video Player (URL-based)
**New file:** `core/utils/video.py` — `get_embed_url(url)` normalises YouTube/Vimeo/direct URLs to embeddable form
**New template:** `templates/video/player.html` — `<iframe>` for YouTube/Vimeo, `<video>` for direct `.mp4`
**File to change:** `records/models.py` — add `video_url = URLField(blank=True)` to Record model
**New migration:** `records` app

### Phase 10: PWA + Service Worker (Desktop Web Offline)

**New files:**
- `static/manifest.json` — app name, icons, theme color, `display: standalone`
- `static/js/sw.js` — service worker: cache-first for assets, network-first for pages, Background Sync for queued POSTs
**File to change:**
- `templates/base.html` — add `<link rel="manifest" href="/static/manifest.json">` and inline SW registration script (2 lines)
- `ics_project/settings/base.py` — add `MANIFEST_JSON_NAME` setting; ensure `Content-Security-Policy` allows service workers
- Nginx config — add `Service-Worker-Allowed: /` header on static assets location block

### Phase 11: Delta Sync API (Mobile Offline Foundation)
**New file:** `core/views/sync.py` — `SyncChangesView` returns delta of Records + Activities + Notifications since `?since=` timestamp; uses existing `updated_at` fields; also expose `GET /api/tenants/` scoped to prime tenant's communities
**File to change:** `ics_project/urls.py` — wire `api/sync/changes/` route

### Phase 12: FCM Integration (for mobile push notifications)
**New file:** `notifications/fcm.py` — send_push_notification() helper
**File to change:** `accounts/models.py` — add `fcm_token = CharField(max_length=255, blank=True)` to User model
**New migration:** add fcm_token to user table

---

## Verification
1. `docker compose up` — all services start (web, redis, celery-worker, celery-beat, minio)
2. `redis-cli ping` → PONG
3. `celery -A ics_project inspect ping` — workers respond
4. Django Channels health check via WebSocket connection
5. Upload a profile avatar via DRF API — confirm it lands in MinIO, `avatar_url` returns correct URL
6. Upload an attachment to a Record via DRF API — confirm in MinIO `ics-documents` bucket; presigned URL returned
7. Access MinIO console at `:9001` — confirm all buckets: `ics-avatars`, `ics-logos`, `ics-private`, `ics-documents`, `ics-videos`
8. **Video player**: Paste a YouTube URL into a lesson Record's `video_url` field → open lesson page → iframe renders and plays
9. Test Vimeo URL and direct `.mp4` URL — each renders correctly (iframe vs `<video>` tag)
10. `GET /api/records/{id}/related/` → returns grouped relationship dict (reuses governance service)
11. Create an Activity with `linked_record_id` set → confirm FK persists, queryable via DRF filter
12. Open HTMX app in Chrome → DevTools Application tab → confirm service worker registered, manifest parsed, app installable
13. Go offline in DevTools → navigate to a handbook page → page loads from cache
14. `GET /api/sync/changes/?since=2020-01-01T00:00:00Z` → returns records list
15. Run existing test suite — no regressions
16. Send a test FCM notification via the helper function

---

## Notes
- PostgreSQL can stay native (outside Docker) or move into Compose — either works; native PostgreSQL has simpler backup workflows
- Start with 3 Celery workers (matching current Gunicorn count); tune after load testing
- Redis persistence (`appendonly yes`) should be enabled so the task queue survives a Redis restart
- The HTMX desktop admin continues unchanged — Daphne/Uvicorn serves both WSGI and ASGI
- MinIO admin console (port 9001) **must be firewalled** — only accessible from trusted IPs or VPN; never public
- MinIO `ics-videos` bucket created now but unused until video app is built; Celery workers + ffmpeg will handle transcoding when that phase begins
- `django-storages` with boto3 means switching from MinIO to AWS S3 in future = change 3 env vars, zero code changes
- 80GB HDD is sufficient: ~15GB OS/app, ~5GB PostgreSQL, ~30GB media, ~25GB video headroom
- Service worker scope must be `/` — register from `base.html`, serve `sw.js` from root static, set `Service-Worker-Allowed: /` header in Nginx
- File System Access API works in Chrome/Edge only — always provide a `<a download>` fallback for Firefox/Safari
- Mobile Flutter file manager (SQLite offline DB, `path_provider`, `file_picker`) is built during the mobile app phase, not now — but the delta sync API endpoint built in Phase 9 is its prerequisite
- `Attachment` model upload → MinIO `ics-documents` → presigned URL with 1-hour expiry; never expose raw MinIO URLs publicly
- Mobile app is a **single adaptive app for all levels** — `GoRouter` guards drive which screens appear based on `user.level` from auth token; no separate operator app needed
- DRF permission classes already enforce level-based access — mobile app simply renders what the API allows; no duplicate permission logic in Flutter
- Prime tenant community switcher requires `GET /api/tenants/` endpoint scoped to the authenticated prime tenant's communities — add this to Phase 9 (Sync API) scope