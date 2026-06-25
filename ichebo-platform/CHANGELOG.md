# Changelog — Ichebo Platform

All notable changes to the Ichebo Platform are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: Build layers as defined in `master-roadmap-canonical-2026-05-13.md`

---

## [Layer 11 — Video Direction v2 & Production Hardening] — 2026-06-22 to 2026-06-25

Video infrastructure went live on its own dedicated server (DOC G's two-server topology), which then exposed that the web UI had no real path to consume it — leading to a full retirement of the standalone `video_live` app in favour of native video inside Learn and Community. Alongside this, a run of real production bugs were found and fixed: two cross-tenant privacy leaks (live broadcasts, Handbook Keys), a silent miscategorization bug, a tenancy-visibility bug, and several infrastructure gaps found only once the video engine was actually deployed and driven end-to-end.

### Video VPS deployment — 2026-06-22 / 2026-06-23

Stood up the dedicated video server (`ics@46.62.211.72`: mediad, MinIO, MediaMTX) separate from the Django app server, per DOC G. Verified end-to-end with a real RTMP test stream against production.

#### Fixed
- `MEDIAMTX_RTMP_URL`/`HLS_BASE_URL` were read via `getattr(settings, ..., default)` in `video_live/models.py` but never actually defined in `settings/base.py` or `production.py` — no way to override the placeholder domain; native broadcasts would have silently pointed nowhere real
- The MediaMTX → Django → Go-engine live-stream handshake was never wired up end-to-end — `StreamStartWebhookView`/`StreamEndWebhookView` had no `MEDIA_ENGINE_API_KEY` bearer check despite their docstrings claiming one (DRF's global `IsAuthenticated` default rejected the call with 401 before the manual check ever ran), and the engine's own `/engine/stream/start` needs a `record_id` only Django's `BroadcastSchedule` table can resolve from a stream key — completed the real chain (MediaMTX → Django → Go engine)
- `media.views.TranscodeCompleteWebhookView` had the identical missing-auth-override bug, found while chasing the handshake — fixed in the same pass
- `(media)` Go engine: Django's outbound calls to the engine (upload/init, upload/complete, transcode) had zero retries, unlike the engine's own outbound webhooks (3 retries with backoff) — added `post_with_retry()` for symmetry, plus a Celery Beat task reconciling transcode jobs stuck in `status='draft'`
- `(media)` Go engine: transcode output (video/thumbnail URL, duration) was only ever passed as transient function args — lost forever if webhook delivery failed all 3 retries; now persisted on the `Job` so a status poll can fully recover it
- `(media)` Go engine: every "required" env var defaulted to an empty string with no startup check — a forgotten var would silently fall back to local disk storage or complete jobs without ever notifying Django; added `Config.Validate()`, fails fast on startup instead

### Real-time scheduling + tenant scoping bugs — 2026-06-22

Found while building Community's tenant-scoped live service room.

#### Fixed
- **Cross-tenant privacy leak**: every video-viewing path (`_event_qs()` in both `video_live/views.py` and `api_views.py`, `VideoFeedView`, `BroadcastListCreateView`'s default response) returned every tenant's broadcasts with no filter — a member could watch another community's live service. All now take an optional `tenant` filter; existing global (steward) callers are unaffected
- `video_manage()` and `htmx_studio_quick_schedule()` created Activity events with no `tenant` set at all, so they could never match the new live room's tenant-scoped lookup — added `_steward_tenant(user)` and wired it into both creation sites
- `<input type="datetime-local">` sends a timezone-less string; with `TIME_ZONE='UTC'`, the server treated it as UTC directly — a steward in UTC+2 scheduling "now" had it stored 2 hours later than intended. Added `_parse_local_datetime()`, correcting by the browser's own `Date.getTimezoneOffset()`
- Platform `TIME_ZONE` changed from `'UTC'` to `'Africa/Johannesburg'` — exposed 9 call sites using `timezone.now().date()` for "today" (schedule buckets, due-today filters, dashboard schedule, Paraclete digest day, habit streaks, age-from-DOB), all of which were silently wrong for ~2 hours around midnight SAST; fixed to `timezone.localtime(timezone.now()).date()`

#### Added
- Community **live service room** (`/community/live/`) + in-service ministry panel — members raise prayer requests/questions during a live session, stewards see a 15s-polling queue and can mark requests responding/done, notifications fan out to stewards only
- Community **member-to-steward support request flow** with 72h SLA tracking, routed via steward lookup with a tenant-coordinator fallback; stewards see an overdue-flagged queue at `/community/support/`

### Handbook editor — real mobile data loss, then a toolbar redesign — 2026-06-23

#### Fixed — severe
- The Handbook editor (`editor.html`) was included twice per page (desktop + mobile shells, same DOM, CSS-only show/hide) and hardcoded every element id — every `getElementById` lookup in `editorial_v2.js` always bound to the first (desktop) copy regardless of which was visible. **A mobile user's edits were silently discarded on save** — typing into the visible mobile field edited a hidden, stale desktop copy, and Save submitted that stale copy. Fixed with a `mount_suffix` parameter making every id unique per inclusion, and rewrote `EditorialUI` from a singleton to one keyed by suffix
- Found and fixed while writing this fix's own explanatory comment: Django's `{# #}` tag does not support multi-line content — the first draft rendered as literal visible text on the page. The actual fix is `{% comment %}...{% endcomment %}`; this exact mistake recurred at least once more later in the video work below and was caught the same way each time
- Focus Mode's chrome-hiding selectors (`#ws-context-bar`, `#ws-options-bar`, `.ws-topbar`, `.ws-primary-sidebar`) didn't exist anywhere in `workspace_shell.html` — Focus Mode never actually hid anything; fixed to the real selectors
- `grant_handbook_access` only ever created a `tenants.UserPermission` row — `handbook_home` actually gates on a separate model, `handbook.HandbookAccess`, so a user "granted Handbook access" via this command could reach `/governance/` but still see "invited architects only" on `/handbook/` itself
- `governance/views.py`'s `MANDATE_ACCESS_LEVEL` check had no superuser/staff bypass, unlike the equivalent Keys check — a misconfigured gate could lock out an operator with no recovery short of a shell command

#### Changed
- Editorial toolbar redesigned twice in the same pass: first collapsed the flat 8-button row into 4 category dropdowns (Text/Headings/Insert/View) identically on desktop and mobile, then expanded to 5 categories (Fonts, Headings, Paragraph, Insert, View) adding Strikethrough, Code, H3–H6, Body, Numbered/Task lists, Horizontal Rule, and a 2×2 starter Table

### Video Direction v2 — retiring the standalone video app — 2026-06-23 / 2026-06-24

The web UI had no working playback path to the new video infrastructure at all. Rather than build a parallel video app, the standalone `video_live` app surface was retired entirely — video is now native to Learn (lesson uploads) and Community (live broadcasts), with only `BroadcastSchedule` and the Go-engine/MediaMTX webhooks kept as shared infrastructure.

#### Added
- Shared HLS player (`templates/video/_player.html`) — hls.js with a native-`<video>` fallback, wired into Learn's lesson viewer and Community's live service room; supports multiple inclusions per page safely
- Community's Gathering form creates a real `BroadcastSchedule` (with a real RTMP ingest URL handed to the steward) for digital/hybrid format, replacing a typed stream-URL field entirely
- Learn's lesson-authoring video field is a real chunked upload straight to the Go engine (`learn/partials/_video_upload.html` + `learn_video_upload.js`), replacing the old pasted-URL input
- CORS support on mediad's upload routes (`MEDIA_CORS_ALLOWED_ORIGIN`) and a new `MEDIA_ENGINE_PUBLIC_URL` Django setting — required since chunk uploads are browser-direct to the engine, cross-origin, and distinct from the existing server-to-server `MEDIA_ENGINE_URL`
- `SessionAuthentication` added alongside `TokenAuthentication` on the relevant media API views, so Learn's page can call them from a browser session without exposing a long-lived API token in page HTML

#### Removed
- `video_live`'s entire standalone app surface: all template views, all of `templates/video_live/`, the mobile feed/CRUD API (zero Flutter client code ever consumed it), `video_live/tests.py` and `utils.py` (both tested only the removed code). `BroadcastSchedule`, the Go-engine/MediaMTX webhooks, and `admin.py` remain
- The "Video" entry from the sidebar, app launcher, and icon rail — no standalone surface left to link to

#### Fixed
- A real production 500: `ManifestStaticFilesStorage` requires every `{% static %}` reference to exist in a build manifest — `collectstatic` had been run without the production settings module set, so the manifest never picked up the new upload JS; the file existed on disk but the page crashed rendering the tag
- Production's `MEDIA_ENGINE_URL` was still its unconfigured default (`http://localhost:8090`) — never updated after the two-server split. The engine's raw port is firewalled from the app server; fixed to the public HTTPS domain
- `video.canPlayType('application/vnd.apple.mpegurl')` is not a reliable HLS-support signal — confirmed by direct test that real Chromium returns `"maybe"` for every MIME type. Player now prefers `Hls.isSupported()` first
- The dashboard's "Today's Schedule" widget queried the legacy `Activity.metadata.stream_url` pattern (confirmed zero live production rows before removing it) and linked to a URL that was never real (`/studio/watch/{id}/`); rewired to query `BroadcastSchedule` and link to Community's live room
- The same widget's LIVE badge was keyed off "is a broadcast" rather than "is actually live" — a merely-scheduled service showed LIVE before this was caught

### Tenancy visibility — global-steward oversight never reached the real pages — 2026-06-24

A freshly-seeded community (Genesis Sceptre Community) was invisible in Tenancy Management and My Communities to a Level 5 global-steward who should have automatic oversight of every descendant tenant — that hierarchy-walk rule only ever existed in the DRF API (`TenantViewSet`), never in the template-rendered pages people actually use.

#### Fixed
- Added `tenants/service.py:get_oversight_tenant_ids` — the one shared implementation of "every tenant a user can see: direct membership, plus every descendant of a tenant where they hold a steward role." `TenantViewSet`, `steward_dashboard`, `my_tenants`, `tenant_detail`'s access gate, and `create_tenant`'s sidebar all now use it instead of five independent, slowly-drifting copies of the same literal role list
- `my_tenants` (Communities member list) now shows oversight-only tenants labeled "`<role>` (oversight)", distinct from tenants you actually belong to

### Handbook — Keys silently miscategorized, no delete action existed — 2026-06-25

#### Fixed — privacy
- **Real privacy bug**: creating a record from Handbook's Keys branch (a personal, `created_by`-scoped record type) silently saved it as a governance Mandate record instead, visible to every Handbook author/editor. Root cause: `handbook_new`'s default-type logic was a two-way ternary with no `'keys'` case, so the hidden form fields the editor actually submits defaulted to `record_type='mandate'`, `record_family='governance'`. Two real, already-affected production records (genuine personal journal content) were found and corrected back to Keys in the same pass
- Handbook had no delete action at all anywhere (Lock/Publish/New Version existed, Delete never did) — added `handbook_delete`, permission-mirrored to `handbook_record`'s own Key-vs-governance branch (a Key can only be deleted by its creator; a governance record follows the same write-role rule as the other lifecycle actions)
- Hardened the editor's Save button against double-submission (`hx-disabled-elt`) as a general safety improvement — confirmed empirically that the first attempt (placing the attribute on the button itself) silently failed, since the button lives outside its `<form>` via the `form=` attribute and HTMX's `find`/`closest` keywords only search within the attribute-holder's own subtree; fixed by setting the attribute on the form with a plain id selector instead, verified live with an artificial response delay

---

## [Production readiness — Bible data, waitlist, env config] — 2026-06-22

### Bible data, waitlist form, and environment config

#### Fixed
- **Bible data was completely empty in production.** `0003_biblebook_uuid_pk`'s final step — an `AlterField` meant to update `BibleVerse.book_id`'s column type to match `BibleBook`'s new UUID primary key — was a silent no-op (confirmed via `sqlmigrate`: Django's autodetector only emits real DDL when a field's *state* differs between migrations, and the `AlterField` used an identical definition to what already existed, so there was nothing to detect as changed). `load_bible` failed with a type-mismatch error on every attempt, and `/bible/` 404'd with "Bible data is not loaded" on a fresh production database. Fixed with a real migration using `RemoveField`/`AddField` instead of `AlterField`, confirmed via `sqlmigrate` to produce genuine DDL on both SQLite and PostgreSQL
- `load_bible_xml` preferred the Zefania source XML's own (inconsistent — bare codes, a typo, mangled text) `biblename` attribute over its own curated `TRANSLATION_NAMES` dict; fixed to prefer the curated name first
- Loaded 8 additional translations beyond the original 3 (KJV/ASV/WEB): AMP, ESV, MSG, NASB, NIV, NKJV, NLT, TNIV — 11 total, ~31,100 verses each
- **The marketing site's waitlist form never worked at all.** It POSTed straight to Brevo's API from the browser using an API key read from a `<meta>` tag that was never actually present in the HTML — every real submission silently failed with an empty key, and no data ever reached the platform's `WaitlistEntry` model (which was already fully built and working, just never called). Fixed the form to POST to the Django backend instead
- `ALLOWED_HOSTS` in `.env.example` only listed the marketing domains (`ichebo.org`/`www.ichebo.org`) — the Django app is actually served at `app.ichebo.org`, which would have produced `DisallowedHost` errors on every real request once deployed

#### Added (ichebo-website)
- Programme page for The Sceptre Community Programme

#### Fixed (ichebo-website)
- `platform.html` and `programme.html` existed and were already linked from nav/footer, but were never added to `vite.config.js`'s build entries — both 404'd in production despite the page content existing
- Both pages' logo was 90px (nav) / 100px (footer), far larger than every other page's established 30px/50px sizing — brought in line

---

## [Layer 10 — Scale] — 2026-05-23

### L10.1 — Redis + Celery (async task queue)

**ADR-008 lifted.** Celery deferred until Version 3 in real-world use — that gate is passed.

#### Added
- `ics_project/celery.py` — Celery app entry point, autodiscovers tasks from all apps
- `ics_project/__init__.py` — wires `celery_app` into Django init so tasks load on startup
- `notifications/tasks.py` — two async tasks:
  - `send_notification_email` — Brevo SMTP delivery, 3 retries with 60s backoff
  - `send_fcm_push` — FCM push delivery, 3 retries with 30s backoff; **FCM wired for the first time**
- `paraclete/tasks.py` — two async tasks:
  - `refresh_paraclete_digest` — pre-computes and caches digest for a single user (600s TTL)
  - `refresh_all_active_digests` — fans out to all active users; scheduled every 10 minutes
- `deploy/ics-celery.service` — systemd unit for Celery worker (2 concurrency slots)
- `deploy/ics-celery-beat.service` — systemd unit for Celery Beat (DatabaseScheduler)
- `requirements.txt` — added: `celery==5.3.6`, `redis==5.0.3`, `django-celery-beat==2.6.0` and their dependencies

#### Changed
- `ics_project/settings/base.py`:
  - `CACHES` backend swapped from `FileBasedCache` → `RedisCache` (DB 1)
  - Added full `CELERY_*` config block (broker DB 0, acks late, prefetch multiplier 1)
  - Added `CELERY_BEAT_SCHEDULE` — `refresh-paraclete-digests` every 10 minutes
  - Added `django_celery_beat` to `INSTALLED_APPS`
- `ics_project/settings/production.py` — removed stale `CACHES` file-path override (Redis config now in base)
- `notifications/service.py`:
  - `_send_email()` replaced synchronous `send_mail()` with `send_notification_email.delay()`
  - `create_notification()` now dispatches `send_fcm_push.delay()` when user has `fcm_token`
  - `notify_tenant_invitation()` non-registered-user path updated to use async task
- `paraclete/views.py` — cache TTL bumped 300 → 600s to align with scheduled refresh interval
- `core/apps.py` — `django_celery_beat` added to `EXEMPT_APP_LABELS` in UUID PK system check

#### Migration
- `django_celery_beat` migrations applied (18 migrations — schedule, interval, crontab, clocked, solar tables)

### L10.6 — Platform Bootstrap (CLI scope) — 2026-06-22

Implements `platform-bootstrap-plan.md` steps 1–3 (CLI only; the `/platform/` browser UI is a deliberate follow-up).

#### Added
- `core.PlatformConfig` — singleton model tracking bootstrap state (`bootstrapped_at`/`by`/`version`) and the library access gates + email verification toggle the plan reserves for the future `/platform/` UI; fixed-UUID primary key per the platform-wide `check_uuid_primary_keys` system check; always fetched via `PlatformConfig.get_solo()`
- `tenants.seed_genesis_sceptre_community` — management command creating the default `church_node` tenant under Prime, so a fresh deployment has at least one working Sceptre Community
- `core.bootstrap_platform` — wraps all 11 seed steps from the plan's scope table; `--dry-run` prints the plan without writing, `--quiet` suppresses status lines, `--force` accepted for future repair-scenario use

#### Fixed (discrepancies found between the plan and the actual codebase)
- `seed_induction_programme` silently produced a programme with no courses unless `seed_induction_course` ran first — the plan never documented this dependency; correct order now wired into the bootstrap step
- `grant_handbook_access` takes a single `--user` email, not a bulk grant as the plan's step 7 implied — `bootstrap_platform` now grants directly via `UserPermission.get_or_create()` for every superuser/Level 5+ user instead of shelling out per-user

#### Verified
- `--dry-run` writes nothing; a full run completes with zero errors; three consecutive runs produce zero duplicates across every entity type; the bootstrap marker is set on a real run and never on `--dry-run`; the command halts cleanly with a clear instruction when no superuser exists

---

## [Layer 9 — Ichebo Handbook] — 2026-05-22

Standalone Handbook product (ADR-020). Own data domain, no tenant FK. Apostolic Command Shell four-column UI. HRS as first-class citizen.

### K.1 — Handbook Foundation

#### Added
- `handbook/` Django app, registered in `INSTALLED_APPS`
- `HandbookRecord` model — UUID PK, three branches (reference/mandate/keys), fourteen record types, four status lifecycle (draft/active/locked/superseded), version chain (`previous_version`, `superseded_by` self FKs), six HRS attribute fields, `publish()` / `lock()` / `new_version()` methods
- `HandbookRelationship` model — links `HandbookRecord` → `HandbookRecord` OR `HandbookRecord` → `BibleVerse`; seven relationship types; direction field; `clean()` enforces exactly one target
- `HandbookAccess` model — reader/author/editor roles, global scope (no tenant), one record per user
- `handbook/serializers.py` — write/list/detail serializers; `validate()` enforces branch/record_type pairing
- `handbook/api_views.py` — full API: list/create, detail/patch, publish, lock, new-version, history, relationships (list/create/delete), publish feed, access management, access/me
- `handbook/api_urls.py` — all API endpoints under `/api/handbook/`
- `handbook/template_urls.py` — workspace routes under `/handbook/` (`app_name='handbook'`)
- `handbook/migrations/0001_initial.py` — applied
- `ics_project/urls.py` — both URL includes registered

### K.2 — Workspace UI + The Desk

#### Added
- `templates/workspace/handbook/home.html` — branch navigator (Column 2), record list grouped by type (Column 3), role/access sidecar (Column 4)
- `templates/workspace/handbook/record.html` — four-tab Properties Sidecar (Props / HRS / Scripture / History); `HBDesk` JS object handles all CRUD, lifecycle, relationship operations; auto-save on keystroke (3s debounce for drafts)
- `templates/workspace/handbook/access.html` — editor-only access management page
- `templates/workspace_shell.html` — Handbook `auto_stories` icon added to sidebar nav

### K.3 — HRS Relationships + K.4 Scripture Linking

Implemented together in `HandbookRelationship` — single model handles both.

#### Added
- Seven HRS relationship types on `HandbookRelationship`
- Six HRS attribute fields on `HandbookRecord` (complexity, relationship_position, position, direction, speed, emotional_tone)
- `HandbookRelationshipListCreateView` + `HandbookRelationshipDeleteView`
- HRS tab in The Desk — relationship list, add form, bible verse search and link workflow
- Scripture tab in The Desk — linked verses display, verse search, link/unlink

### K.5 — Publish Feed

#### Added
- `HandbookPublishFeedView` — `GET /api/handbook/publish-feed/?since={timestamp}`
- Returns active/locked non-key records modified since timestamp; 100-record window; ordered by `updated_at`

### K.6 — Keys Library Privacy

**Privacy invariant:** key records are personal — owner-only, no `HandbookAccess` required, never visible to other users, never published to network.

#### Added
- `_is_key_record()` sentinel function used throughout API layer
- `_assert_can_access_record()` / `_assert_can_write_record()` helpers
- `handbook/tests.py` — 13 tests covering all privacy invariants (creation without HandbookAccess, isolation from other users and editors, publish blocked, lock blocked, publish feed exclusion, history owner-only, relationship privacy, has_symbol link allowed to Reference Library)

#### Changed
- All six lifecycle API views hardened: keys 404 for non-owners, 400 on publish/lock attempts
- `HandbookPublishFeedView` — `.exclude(branch=BRANCH_KEYS)` — keys never in sync feed
- `views.py` (workspace) — `_shared_readable_qs()` excludes keys; `_keys_qs(user)` owner-scoped; all three workspace views handle Keys branch independently of `HandbookAccess`

---

## [Layer 8 — Ichebo Media] — 2026-05-21

Video Engine scaffold (ADR-021). Go + FFmpeg + Hetzner Object Storage + HLS.

### M.1 Scaffold — Video Engine + Django media app + Flutter HLS player

#### Added
- `ichebo-media/` — Go video engine service scaffold
- `media/` Django app — upload handler, chunked video uploads
- Flutter HLS player integration in `ichebo-mobile-v2`
- Upload handler for chunked video uploads

---

## [Layer 6 — Ichebo Desktop] — 2026-05-13

Flutter Desktop local-first community operating system (ADR-017).

### D.1 — Flutter Desktop Shell Scaffold

#### Added
- `ichebo-desktop/` — Flutter project targeting Windows/macOS/Linux
- Core navigation shell, design system tokens in Dart
- Dark mode (non-optional per roadmap)

### D.2 — Local Data Layer + FFI Bridge

#### Added
- SQLite integration (WAL mode)
- Go engine FFI bridge
- All local writes append to ChangeLog

---

## [Layer 4 — Stabilisation] — 2026-05-13

### H.1 — Documentation Alignment

#### Added
- `master-roadmap-canonical-2026-05-13.md` — v7 canonical roadmap
- `data-contract-v11-canonical-2026-05-13.md` — complete data contract
- ADRs 012–021 — ecosystem architecture decisions
- `2026-05-13-ichebo-ecosystem-architecture_v0.1.md`
- `DESIGN.md` — locked design system authority
- Full spec set: DOC A–I

---

## [Layer 3 — Version 2: Formation & Shell] — 2026-04 / 2026-05

### Apostolic Command Shell (ADR-012)

#### Added
- `templates/workspace_shell.html` — four-column grid (Sidebar 72px / Context Bar 240px / Stage flexible / Options Bar 300px)
- Dual-shell switching (Stage Mode / Mobile Mode)
- DESIGN.md design system applied: Playfair Display + Inter, Ink + Stone + Red
- All app templates updated with `{% block ws_content %}` and `{% block content %}` blocks
- Ghost watermark via `data-watermark` CSS `::after`
- Rule of Left — 3px `#AF3236` left border on active sidebar items

### V2.1 — Learn: Programmes + Induction Course + Video Embed
### V2.2 — Induction System
### V2.3 — Formation UI + App Drawer Gating
### V2.4 — Agency Tenants + Service Orders (6 tenants, 24 orders seeded)
### V2.5 — Steward Dashboard + Tenant Self-Service
### V2.6 — Notifications (Full — signals, Brevo email, FCM stub)
### V2.7 — Video / Live App (broadcast scheduler, live stream, VOD)

---

## [Layer 2 — Version 1: MVP Apps] — 2026-03 / 2026-04

### Phase 5.1 — Bible App
### Phase 5.2 — Learn App (F1–F11 complete)
### Phase 5.3 — Activity App UI
### Phase 5.4 — Community App
### Phase 5.5 — Governance App (full lifecycle + The Desk)
### Phase 5.6 — Profile + Settings
### Phase 5.7 — Notifications Stub
### Phase 6.1 — Paraclete Service (rule-based)
### Phase 6.2 — Dashboard (Command Centre)
### Phase 7 — Production Hardening (SSL, Nginx, Gunicorn, systemd)

---

## [Layer 1 — Django Foundation] — 2026-02 / 2026-03

### Phase 1 — Auth + Tenants + HTMX Shell

#### Technical Stack (locked)
- **Backend:** Django 4.2.30 LTS + DRF 3.17 + PostgreSQL
- **Web frontend:** Django templates + HTMX (no React/Vue)
- **Auth:** Django SessionAuthentication (web) + DRF ExpiringTokenAuthentication (mobile/API)
- **Storage:** MinIO / Hetzner Object Storage (S3-compatible, bucket: `ics-media`)
- **Email:** Brevo SMTP (300 emails/day free tier)
- **Task queue:** Celery 5.3.6 + Redis (added L10.1)
- **Server:** Hetzner VPS, Ubuntu 22.04, Nginx + Gunicorn + systemd

### Phase 2 — Records Engine
### Phase 3 — Activity Engine

---

## [Layer 0 — Server & Tools] — 2026-01 / 2026-02

- Hetzner VPS provisioned, SSH, UFW, non-root deploy user
- GitHub repository, SSH deploy key
- MinIO object storage, bucket `ics-media`
- Brevo SMTP configured
- Nginx + Gunicorn + systemd + SSL (Let's Encrypt)

---

*Last updated: 2026-05-23*
*Maintained by: Larry Mwansa (Chizola)*
