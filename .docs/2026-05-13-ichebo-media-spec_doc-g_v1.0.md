**ICHEBO MEDIA**

**Product Specification**

_DOC G - Version 1.0 - May 2026_

| **Field**     | **Value**                                                                    |
| ------------- | ---------------------------------------------------------------------------- |
| Document      | DOC G - Ichebo Media Product Specification                                   |
| Version       | 1.0 - May 2026                                                               |
| Status        | Approved - Canonical Reference                                               |
| ADR reference | ADR-021 (Ichebo Media as standalone product)                                 |
| Data contract | data-contract-v11-canonical-2026-05-13.md                                    |
| Roadmap       | Layer 8 - master-roadmap-canonical-2026-05-13.md                             |
| Depends on    | DOC A (Product Vision), DOC D (Technical Architecture), DOC E (Engine Specs) |
| Authors       | Chizola (domain); Claude (technical)                                         |

**The retired phrase**

Self-hosted video if needed is retired from all Ichebo documents. Ichebo Media is planned. It is a first-class product in the Ichebo ecosystem that requires proper engineering.

**-- PRODUCT DEFINITION**

**What Ichebo Media Is**

A full-stack video platform. Three pipelines. One Video Engine. Built for the KGS context.

## **1.1 The Strategic Decision - ADR-021**

The Version 2 roadmap planned video support as URL-based embed only - YouTube, Vimeo, or direct .mp4. Self-hosted video was deferred to "Version 3+ if needed." This characterisation significantly underestimated the scope and architectural significance of video in the KGS context.

Video in the KGS is not an optional feature. It is how:

- Apostolic teaching reaches communities who cannot attend in person
- Formation pathways deliver their content - video lessons are the primary Learn App medium
- The network gathers - live streaming connects distributed communities in real time
- The Seven-Year Programme delivers its teaching phases across the network

**ADR-021 - Locked**

Ichebo Media is a standalone product with its own purpose-built Video Engine. It is not a Django app, not a feature, and not a "if needed" future consideration. It requires proper engineering. It will be built.

## **1.2 What Ichebo Media Serves**

Video in the KGS context serves three distinct purposes with different technical requirements:

| **Pipeline**   | **Purpose**                                                                                        | **Technical character**                                                                                                                   |
| -------------- | -------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Teaching video | Sermon recordings, ministry content, apostolic broadcasts. VOD library. Accessible to all members. | Upload once, serve many. Long-form (20 min-3 hr). Multiple quality outputs. Thumbnail and metadata. Archive forever.                      |
| Learning video | Academy curriculum delivery. Chapter markers, completion tracking, offline download for Desktop.   | Structured content. Chapter segmentation. Progress events to Activity Engine. Offline caching for Desktop. Shorter (5-30 min per lesson). |
| Live streaming | Gathered meetings, network-wide broadcasts. RTMP ingest, HLS delivery, DVR recording.              | Real-time. Low latency. Adaptive bitrate. DVR buffer for late joiners. Auto-archive when stream ends.                                     |

## **1.3 Product Attributes**

| **Attribute**            | **Value**                                                                                                         |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| Product type             | Standalone - own service, own infrastructure, own API                                                             |
| Video Engine language    | Go + FFmpeg                                                                                                       |
| Object storage           | Hetzner Object Storage (S3-compatible) - ics-media bucket                                                         |
| Delivery protocol        | HLS (HTTP Live Streaming) - adaptive bitrate, universally supported                                               |
| Live ingest              | MediaMTX or nginx-rtmp - RTMP ingest server (separate from Django VPS)                                            |
| Playback client          | HLS player in Flutter - quality adaptive, offline download capable                                                |
| Progress tracking        | Activity Engine - lesson completion events from video progress milestones                                         |
| Offline download         | First-class requirement for Ichebo Desktop - not a nice-to-have                                                   |
| Status                   | Version 3+ - planned. Layer 8 of the roadmap.                                                                     |
| Relationship to V2 video | Version 2 Video/Live app (URL embed) remains in production. Ichebo Media supersedes it as infrastructure matures. |

## **1.4 Why Django Cannot Handle This**

Django is a web framework. It handles HTTP requests, serves templates, and talks to PostgreSQL. Video processing is a completely different category of computing:

- Transcoding a 2-hour sermon recording consumes 100% CPU for 30-60 minutes - Django's request workers cannot wait for this
- Live stream ingest requires a dedicated RTMP server process - Django has no RTMP support
- HLS segment generation requires FFmpeg running continuously against an incoming stream - Django cannot orchestrate this
- CDN delivery requires object storage with a CDN layer - Django cannot serve video at scale

The Video Engine is Go + FFmpeg. Django serves the management UI only - browse the video library, schedule a broadcast, view analytics. The actual video work happens in a purpose-built service.

**-- PIPELINE 1**

**Teaching Video**

Upload. Transcode. Store. Serve. Archive forever.

## **2.1 Pipeline Overview**

**Teaching Video - Full Pipeline**

→ Broadcaster uploads video file (web UI or mobile app)

→ Chunked upload handler (Go) receives file in segments - handles large files and poor connections

→ Raw file stored in Hetzner Object Storage (ics-media bucket) - upload bucket

→ Transcoding job queued (Go channel or lightweight queue)

→ FFmpeg transcodes to multiple quality outputs: 1080p, 720p, 480p, 360p

→ Thumbnail extracted at 00:10 mark (or configurable)

→ HLS manifest (.m3u8) generated with quality variants

→ Transcoded segments and manifest stored in Hetzner Object Storage - delivery bucket

→ CDN layer serves HLS segments to Flutter HLS player

→ Video record created in Records Engine (record_family: "learning" or new "media" family)

→ Video is now available in the VOD library

## **2.2 Quality Outputs**

| **Output quality** | **Bitrate target** |
| ------------------ | ------------------ |
| 1080p (Full HD)    | 4-8 Mbps           |
| 720p (HD)          | 2-4 Mbps           |
| 480p (SD)          | 800 Kbps-2 Mbps    |
| 360p (Low)         | 400-800 Kbps       |
| Audio only         | 128 Kbps           |

The HLS player in Flutter automatically selects the appropriate quality based on the viewer's current bandwidth - adaptive bitrate streaming. A viewer on WiFi gets 1080p. A viewer on 3G in rural Zambia gets 360p. The same file serves both.

## **2.3 Chunked Upload Handler**

Large video files - a two-hour Sunday service recording can be 4-8 GB - require chunked upload. The Go upload handler:

- Accepts the file in chunks of configurable size (default 5MB per chunk)
- Resumes interrupted uploads - if the connection drops, the upload continues from the last successful chunk on reconnect
- Validates each chunk (checksum) before accepting
- Assembles chunks into the complete file atomically when all chunks are received
- Handles concurrent uploads - multiple broadcasters can upload simultaneously

## **2.4 Video Metadata Model**

Every video is a Record in the Records Engine. The video-specific metadata lives in custom_fields:

| **custom_field**       | **Value**                                                    |
| ---------------------- | ------------------------------------------------------------ |
| video_url              | HLS manifest URL - points to .m3u8 file on CDN               |
| thumbnail_url          | Thumbnail image URL on CDN                                   |
| duration_seconds       | Total duration in seconds (set after transcoding)            |
| file_size_bytes        | Original upload file size                                    |
| quality_variants       | JSON array of available quality outputs and their URLs       |
| transcoding_status     | queued \| processing \| complete \| failed                   |
| upload_bucket_key      | Object Storage key for the raw uploaded file                 |
| delivery_bucket_prefix | Object Storage prefix for transcoded HLS segments            |
| chapter_markers        | JSON array of chapter timestamps and titles (learning video) |
| presenter              | Display name of the presenter or teacher                     |
| series                 | Series or curriculum this video belongs to                   |

**-- PIPELINE 2**

**Learning Video**

Curriculum delivery. Chapter markers. Progress tracking. Offline download.

## **3.1 What Makes Learning Video Different**

Learning video is teaching video with structure added. The same transcoding pipeline produces the same HLS output - but the video is consumed differently:

- Chapter markers divide the lesson into named segments - the learner can navigate to specific sections
- Progress events are sent to the Activity Engine at configurable milestones (25%, 50%, 75%, 100%)
- Completion at 100% triggers the certification signal if the video is the final lesson in a programme
- Offline download allows the learner to cache the video on Ichebo Desktop for viewing without internet
- The video is embedded within a Learn App lesson record - it is not a standalone video

## **3.2 Chapter Markers**

Chapter markers are stored in the video record's custom_fields.chapter_markers as a JSON array:

// custom_fields.chapter_markers

\[

{ "timestamp_seconds": 0, "title": "Introduction" },

{ "timestamp_seconds": 180, "title": "The Kingdom Mandate - Foundation" },

{ "timestamp_seconds": 720, "title": "Governance Architecture Overview" },

{ "timestamp_seconds": 1440, "title": "The Seven Pillars" },

{ "timestamp_seconds": 2100, "title": "Practical Application" },

{ "timestamp_seconds": 2580, "title": "Questions and Conclusion" }

\]

The Flutter HLS player renders chapter markers as a timeline scrubber with named segments. The learner can tap any chapter to jump directly to it.

## **3.3 Progress Tracking - Activity Engine Integration**

The Flutter video player emits progress events to the Activity Engine at defined milestones. These events are identical to any other Activity status update - they go through the normal write path and append to the ChangeLog.

// Progress event at 100% completion

Activity (programme enrolment) {

status: "completed",

progress: 100,

metadata: {

source_app: "learn",

lesson_record_id: "uuid-of-lesson-record",

video_record_id: "uuid-of-video-record",

watched_seconds: 2640,

total_seconds: 2640,

}

}

// This status transition triggers:

// 1. ActivityLog entry (immutable audit) via Activity Engine

// 2. Certification signal if this is the final lesson in the programme

// 3. Sync Engine pushes the update to cloud on next sync

## **3.4 Offline Download for Desktop**

Ichebo Desktop users can download a learning video for offline viewing. The download is managed by the Sync Engine and stored in the local file system alongside the SQLite database.

- User taps "Download for offline" on a lesson in the Learn section
- Sync Engine fetches the 480p quality variant (balanced quality and file size for offline)
- File stored in the app data directory alongside the SQLite database
- Video record in SQLite updated with local file path: custom_fields.local_file_path
- Flutter player checks local_file_path first - if present, plays locally. If absent, streams from CDN.
- Download progress displayed in the Sync section - same status bar
- Offline video available immediately on next app open, no connection required

**First-class requirement**

Offline video download for Ichebo Desktop is not a nice-to-have. It is a first-class product requirement. A community steward in a rural area must be able to download a formation lesson in town and watch it at home without internet.

**-- PIPELINE 3**

**Live Streaming**

RTMP ingest. HLS delivery. DVR recording. Archive on stream end.

## **4.1 Pipeline Overview**

**Live Streaming - Full Pipeline**

→ Broadcaster opens streaming software (OBS, Streamlabs, or mobile RTMP app)

→ Broadcaster points RTMP output to MediaMTX ingest server: rtmp://media.ichebo.org/live/stream-key

→ MediaMTX receives the RTMP stream and begins transcoding via FFmpeg

→ FFmpeg produces HLS segments in multiple quality levels (1080p, 720p, 480p)

→ HLS segments written to Hetzner Object Storage in real time

→ DVR buffer maintained - viewers can seek back up to 2 hours in the live stream

→ Flutter HLS player loads the live manifest: <https://cdn.ichebo.org/live/{stream-key}/index.m3u8>

→ Viewers receive adaptive bitrate HLS stream

→ When broadcast ends: RTMP stream closes

→ FFmpeg compiles the DVR recording into a complete VOD file

→ VOD automatically published to the Teaching Video library

→ Broadcast Activity record updated: status → completed

## **4.2 The RTMP Ingest Server**

MediaMTX (or nginx-rtmp as an alternative) is the dedicated RTMP ingest server. It runs as a separate process - not on the same VPS as Django. It requires its own server instance because:

- Live streaming is CPU-intensive - FFmpeg transcoding a live stream consumes multiple CPU cores continuously
- Network throughput requirements are different - high inbound (RTMP) and high outbound (HLS to many viewers) simultaneously
- The live server must never be affected by Django application issues or deployments
- Scaling live streaming independently of the web application is essential as the network grows

| **Attribute** | **Value**                                                                      |
| ------------- | ------------------------------------------------------------------------------ |
| Software      | MediaMTX (recommended) - lightweight Go-based RTMP/HLS server                  |
| Alternative   | nginx-rtmp module - well-established, more complex configuration               |
| Server        | Separate Hetzner VPS - CX32 minimum for live transcoding                       |
| Ingest URL    | rtmp://media.ichebo.org/live/{stream-key}                                      |
| Stream key    | Generated by Ichebo Cloud when a broadcast is scheduled - unique per broadcast |
| HLS output    | Written to Hetzner Object Storage in real time                                 |
| Viewer URL    | <https://cdn.ichebo.org/live/{stream-key}/index.m3u8>                          |

## **4.3 Broadcast Scheduling**

A broadcast is scheduled in advance via the Video/Live section of the Apostolic Command Shell (Level 3+). Scheduling creates:

- A Gathering record (Community App) with format: "digital" and stream_url set to the HLS viewer URL
- An event Activity (dual-write pattern) linked to the gathering record
- A unique stream key generated and issued to the broadcaster
- A notification sent to community members with the start time and join link

## **4.4 DVR and Archive**

The DVR buffer allows late-joining viewers to seek back in a live stream - they can watch from the beginning even if the stream has been running for an hour. The buffer is maintained for 2 hours of live content.

When the stream ends, the DVR recording is automatically compiled into a complete VOD and published to the Teaching Video library. The broadcaster does not need to upload again - the archive is created from the live stream itself. The Gathering record is updated with the VOD URL and the event Activity is marked completed.

**-- INFRASTRUCTURE**

**Video Engine Architecture**

Go service. FFmpeg. Hetzner Object Storage. CDN delivery. Separate from Django.

## **5.1 Infrastructure Map**

Ichebo Media requires two additional infrastructure components beyond the existing Django VPS:

| **HETZNER CLOUD - Three servers**                                                                                                                                                                                                                              |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Server 1 - Django VPS (existing)**<br><br>Nginx + Gunicorn + Django + PostgreSQL + MinIO. Manages video metadata. Serves the management UI. Triggers transcoding jobs via API call to Video Engine server.                                                   |
| **Server 2 - Video Engine (new)**<br><br>Go Video Engine service + FFmpeg + MediaMTX (RTMP ingest). Handles upload chunking, transcoding queue, HLS segment generation, live stream ingest. CPU-intensive - dedicated server. CX42 minimum (8 vCPU, 16GB RAM). |
| **Hetzner Object Storage (managed)**<br><br>S3-compatible managed object storage. Two buckets: ics-media-upload (raw files, private) and ics-media-delivery (transcoded HLS, public). CDN layer (Hetzner or Cloudflare) in front of delivery bucket.           |

## **5.2 Video Engine Service - Go**

The Video Engine is a Go service with three responsibilities:

| **Responsibility**      | **Detail**                                                                                                                                                                       |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Upload handler          | Chunked upload API endpoint. Receives file chunks from Django (which receives from the browser/Flutter). Assembles and stores in upload bucket. Returns upload ID.               |
| Transcoding queue       | Job queue (Go channel or lightweight queue like Asynq). Workers pick up transcoding jobs, run FFmpeg, write outputs to delivery bucket, notify Django via webhook when complete. |
| Live stream coordinator | Manages MediaMTX - starts/stops stream sessions, monitors ingest, triggers DVR compilation on stream end, posts archive to delivery bucket.                                      |

// Video Engine API (called by Django)

POST /engine/upload/init

Body: { filename, file_size_bytes, content_type, tenant_id, record_id }

Returns: { upload_id, chunk_urls\[\] } // presigned URLs for each chunk

PUT /engine/upload/{upload_id}/chunk/{chunk_number}

Body: binary chunk data

Returns: { received: true, checksum: "sha256..." }

POST /engine/upload/{upload_id}/complete

Body: { chunk_checksums\[\] }

Returns: { raw_object_key: "uploads/{record_id}/original.mp4" }

POST /engine/transcode

Body: { upload_id, record_id, quality_profiles: \["1080p","720p","480p","360p"\] }

Returns: { job_id } // async - completion notified via webhook

GET /engine/transcode/{job_id}/status

Returns: { status: "queued|processing|complete|failed", progress_pct: 73 }

POST /engine/stream/start

Body: { stream_key, record_id, quality_profiles }

Returns: { rtmp_ingest_url, hls_viewer_url }

POST /engine/stream/end

Body: { stream_key }

Returns: { archive_record_id } // the auto-created VOD record

## **5.3 Object Storage - Two Buckets**

| **Bucket**         | **Access**                  |
| ------------------ | --------------------------- |
| ics-media-upload   | Private - Video Engine only |
| ics-media-delivery | Public read - CDN layer     |

Object path conventions:

// Teaching/learning video (after transcoding)

ics-media-delivery/

videos/{record_id}/

index.m3u8 ← master HLS manifest (all quality variants)

1080p/

index.m3u8 ← quality-specific manifest

segment_000.ts ← HLS transport stream segments

segment_001.ts

...

720p/

index.m3u8

segment_000.ts

...

thumbnail.jpg ← extracted at 00:10 mark

// Live stream (during broadcast)

ics-media-delivery/

live/{stream_key}/

index.m3u8 ← live manifest (updated every 2 seconds)

1080p/

segment_latest.ts ← rolling window of segments

// Live archive (after stream ends)

ics-media-delivery/

videos/{record_id}/ ← same structure as VOD after compilation

## **5.4 CDN Delivery**

The delivery bucket sits behind a CDN layer. The CDN caches HLS segments at edge locations - reducing latency for viewers and reducing egress costs from Hetzner Object Storage.

- Hetzner has its own CDN offering - the natural first choice, integrated with Object Storage
- Cloudflare is an alternative - excellent global coverage, generous free tier
- The CDN URL is configured in the Video Engine - changing CDN providers requires updating one environment variable
- HLS manifests (.m3u8) are not cached - they must always be fresh. Segments (.ts) are cached aggressively (immutable, content-addressed)

**-- PLAYBACK**

**The Flutter HLS Player**

Quality adaptive. Chapter-aware. Offline-capable. Desktop and Mobile.

## **6.1 Flutter Video Player**

The Flutter HLS player is used on both Ichebo Desktop and Ichebo Mobile. It must support:

- HLS adaptive bitrate playback - automatic quality switching based on bandwidth
- Chapter marker navigation - timeline scrubber with named chapters
- Progress reporting - events at 25%, 50%, 75%, 100% milestone thresholds
- Offline playback - check local_file_path before attempting CDN stream
- Picture-in-picture - continue watching while using other parts of the app (Desktop)
- Fullscreen - standard video player fullscreen toggle
- Playback speed control - 0.75x, 1x, 1.25x, 1.5x, 2x

| **Flutter package**             | **Purpose**                                                    |
| ------------------------------- | -------------------------------------------------------------- |
| video_player (flutter official) | Base video playback - supports HLS on all platforms            |
| better_player or media_kit      | Enhanced HLS player with adaptive bitrate and subtitle support |
| chewie                          | UI layer over video_player - controls, fullscreen, pip         |

## **6.2 Player State and Progress Events**

The Flutter player emits progress events to the Activity Engine at milestone thresholds. This is the integration point between Ichebo Media and the domain engines.

// Dart - video progress event emission

class VideoProgressTracker {

final ActivityEngine activityEngine;

final String activityId; // the enrolment Activity ID

final String videoRecordId;

final int totalSeconds;

final Set&lt;int&gt; \_firedMilestones = {};

void onProgress(int watchedSeconds) {

final pct = (watchedSeconds / totalSeconds \* 100).round();

for (final milestone in \[25, 50, 75, 100\]) {

if (pct >= milestone && !\_firedMilestones.contains(milestone)) {

\_firedMilestones.add(milestone);

activityEngine.updateProgress(

activityId: activityId,

progress: milestone,

metadata: {

'source_app': 'learn',

'video_record_id': videoRecordId,

'watched_seconds': watchedSeconds,

'total_seconds': totalSeconds,

}

);

}

}

}

}

## **6.3 Offline Playback Flow**

When a user downloads a video for offline viewing on Ichebo Desktop:

- User taps "Download for offline" - triggers a sync engine download job
- Sync Engine fetches the 480p quality variant from CDN
- File stored at: {app_data_dir}/media/{record_id}/480p.ts (or .mp4 for compatibility)
- Video record in SQLite updated: custom_fields.local_file_path = path
- On next lesson open: Flutter player checks custom_fields.local_file_path first
- If local file exists: plays from local path - no network
- If local file absent: streams from CDN URL as normal
- Download status visible in Sync section alongside data sync status

**-- TRANSITION**

**From Version 2 to Ichebo Media**

URL embed remains. Ichebo Media supersedes it. No forced migration.

## **7.1 Version 2 Video/Live App - Current State**

The Version 2 Video/Live App is in production. It uses URL-based video embedding - YouTube, Vimeo, or direct .mp4 URLs. It works for its intended scope:

- Broadcast scheduling (creates gathering + event Activity)
- Live stream surface (embeds a provided stream URL - typically YouTube Live)
- VOD library (links to external uploaded recordings)
- Programme grid (7-day schedule of broadcasts)

It does not transcode, does not store, does not generate HLS, and does not support offline download. It is the pragmatic starting point.

## **7.2 The Transition Strategy**

**No forced migration**

The Version 2 URL-based approach remains valid for communities that use YouTube or Vimeo for their recordings. Ichebo Media is additive - it gives communities the option of self-hosted video with full control. It does not remove the URL embed option.

The transition path for a community moving to self-hosted:

- Community signs up for Ichebo Media storage (object storage costs are per-GB - pay for what you use)
- Broadcaster uses the Ichebo Media upload tool for new recordings instead of YouTube
- Existing YouTube/Vimeo links continue to work - legacy records are not touched
- New recordings appear in the same Video/Live UI - the difference is transparent to viewers
- Over time, community migrates existing content to self-hosted as needed

## **7.3 URL Embed Retained for Learning Video**

The Learn App lesson video embed (custom_fields.video_url in lesson records) accepts both URL-based and Ichebo Media HLS URLs. This means:

- A lesson created with a YouTube link continues to work after Ichebo Media launches
- A new lesson created with an Ichebo Media video uses the HLS player instead of the iframe embed
- The difference is handled by the Flutter player: if video_url starts with rtmp:// or is an HLS manifest, use the HLS player. If it is a YouTube/Vimeo URL, use the iframe embed.

**-- BUILD SEQUENCE**

**Layer 8 of the Roadmap**

Three phases. Entry requirement: Layer 5 (Go engines) complete.

## **8.1 Entry Requirement**

**Gate**

Ichebo Media build does not begin until: (1) Layer 5 Go foundation engines are complete and tested, (2) Ichebo Desktop MVP is in real-world use (Phase H.2), (3) the Version 2 URL-based approach has been confirmed insufficient for the network's video needs.

The gate exists because Ichebo Media is significant infrastructure investment. The Version 2 URL approach may serve the network for longer than expected - building Ichebo Media before it is genuinely needed would divert resources from higher-priority work.

## **8.2 Phase M.1 - Video Engine**

| **Task**                           | **Detail**                                                                                                              |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Go service scaffolding             | Video Engine service. HTTP API. Health check. Configuration (object storage credentials, FFmpeg path, MediaMTX config). |
| Hetzner Object Storage integration | Two-bucket setup (upload + delivery). Go S3 client. Presigned URL generation for chunk uploads.                         |
| Chunked upload handler             | POST /engine/upload/init, PUT /engine/upload/{id}/chunk/{n}, POST /engine/upload/{id}/complete.                         |
| FFmpeg integration                 | Transcoding worker. Quality profile definitions. Progress reporting via webhook.                                        |
| Transcoding queue                  | Go channel or Asynq job queue. Worker pool (one worker per CPU core minus 1).                                           |
| HLS manifest generation            | Master manifest linking quality variants. Per-quality manifests. Segment naming convention.                             |
| Webhook to Django                  | POST /api/media/transcode-complete/ - Django updates record status, sets video_url and thumbnail_url.                   |
| Django management UI               | Upload form, transcoding status display, video library browse.                                                          |

Exit criteria: Upload a 1-hour video, receive all quality variants within 2x the video duration, serve HLS to Flutter player, play without buffering on 5 Mbps connection.

## **8.3 Phase M.2 - Live Streaming**

| **Task**                | **Detail**                                                                                                       |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------- |
| MediaMTX setup          | Separate Hetzner VPS. MediaMTX installed and configured. RTMP port 1935 open. HLS output to Object Storage.      |
| Stream key management   | Generated by Django when broadcast is scheduled. Validated by MediaMTX on ingest.                                |
| DVR buffer              | MediaMTX DVR configuration. 2-hour rolling window. Seek-back enabled for live viewers.                           |
| Auto-archive            | On stream end: MediaMTX signals Video Engine. FFmpeg compiles DVR into complete VOD. Publish to delivery bucket. |
| Live manifest freshness | HLS live manifest must not be cached - CDN rules configured for .m3u8 files (no-cache).                          |
| Stream scheduling UI    | Django: schedule broadcast, generate stream key, display RTMP URL, display viewer URL.                           |
| Community notification  | On broadcast start: notification to community members via Notification service.                                  |

Exit criteria: Broadcaster streams from OBS on a laptop. 50 simultaneous viewers in Flutter player. All viewers see the stream within 10 seconds of the broadcaster going live.

## **8.4 Phase M.3 - Learning Video**

| **Task**                   | **Detail**                                                                                              |
| -------------------------- | ------------------------------------------------------------------------------------------------------- |
| Chapter marker authoring   | Learn App lesson editor: add chapter markers with timestamp and title.                                  |
| Flutter chapter navigator  | Timeline scrubber with chapter marker display. Tap to jump to chapter.                                  |
| Progress event integration | Activity Engine progress events at 25/50/75/100% milestones. Certification signal at 100%.              |
| Offline download           | Sync Engine download job for 480p variant. local_file_path written to SQLite video record.              |
| Offline playback           | Flutter player: check local_file_path before CDN URL. Play local if available.                          |
| Paraclete integration      | Progress data available to Paraclete for formation digest (which lessons completed, which in progress). |

Exit criteria: A formation lesson video plays on Ichebo Desktop with no internet connection. Chapter markers are navigable. Progress is tracked and syncs to cloud on reconnection.

## **8.5 Deferred Items**

- Captioning and subtitles - automated captions via Whisper or similar. Significant engineering. Phase 2.
- Multi-language audio tracks - teaching in multiple African languages from one video. Phase 2.
- Analytics dashboard - views, watch time, drop-off points per video. Phase 2.
- Broadcast from mobile - mobile RTMP broadcasting from the Flutter app (currently desktop streaming software only). Phase 2.
- Video rooms / virtual gatherings - bidirectional video for small groups. Requires WebRTC - significant complexity. Version 4+.
- AI-generated sermon summaries - transcript + LLM summary. Layer 10.

**Ichebo Christian Services**

_DOC G - Ichebo Media Product Specification v1.0 - May 2026 - Canonical Reference_