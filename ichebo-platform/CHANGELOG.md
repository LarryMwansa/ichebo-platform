# Changelog — Ichebo Platform

All notable changes to the Ichebo Platform are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: Build layers as defined in `master-roadmap-canonical-2026-05-13.md`

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
