# Architecture Decision Record — Ichebo Platform Version 2
**Version:** v1.0 — 2026-04-25
**Status:** Approved
**Author:** Chizola (domain); Claude (technical specification)

---

## ADR-001: Mobile Client — Flutter over HTMX

### Context
The MVP desktop experience is built on Django templates + HTMX. Post-MVP user testing identified two mobile limitations: (1) HTMX requires server round-trips per interaction, creating latency on variable mobile connections; (2) HTMX-rendered HTML is not portable to native mobile UI patterns (touch gestures, offline, push notifications).

### Decision
A Flutter mobile application is adopted as the Version 2 mobile client. Django templates + HTMX remains the locked architecture for the desktop/web operator surface. The DRF API (already built) serves as the shared backend for both clients. No changes to the backend are required.

### Consequences
- Django + HTMX: primary surface for complex operator workflows (Governance, Learn authorship, Community management, Paraclete)
- Flutter: all-levels mobile client (Levels 0–5), consuming existing DRF endpoints
- DRF API becomes the formal interface contract for both clients — breaking API changes require a version bump
- Mobile navigation shell is role-adaptive: screens available to a user are determined by `user.competence_level` returned in the auth token response
- No separate mobile permission logic — DRF enforces all access gates; Flutter renders what the API allows
- Flutter packages required (added at mobile build phase): `go_router`, `dio`, `provider` or `riverpod`, `sqflite` (offline), `firebase_messaging` (push notifications), `youtube_player_flutter`, `video_player`

### ADR Status: Approved — Version 2

---

## ADR-002: Induction Tenant Tier Strategy

### Context
The Induction Tenant is architecturally distinct from all other tenants: it has no geographic scope, no community coordinator, no Area of Operation, and special content scoping rules (Level 0 users see only induction content). The question was whether to model this with a flag (`is_induction: true`) or a distinct `tier` value.

### Decision
Add `"induction"` as a new value to the `Tenant.tier` enum. The Induction Tenant is seeded via a management command and treated as a system-managed singleton.

### Consequences
- `Tenant.tier` choices: `"branch" | "district" | "province" | "national" | "regional" | "continental" | "global" | "induction"` (new)
- The Induction Tenant is seeded at `path: "/global/induction/"`, `slug: "induction"`, `tier: "induction"`, `status: "active"`
- All views and permission checks that filter by `tier` can use `tenant.tier == "induction"` for special casing — no flag field needed
- The Induction Tenant cannot be deleted, renamed, or modified via normal UI flows — enforced at the view layer
- Data contract v10 amendment required: add `"induction"` to `Tenant.tier` enum

### ADR Status: Approved — Version 2

---

## ADR-003: Competence Level Write Path — Extended to Induction Completion

### Context
The locked rule is: `competence_level` has one write path only — `POST /api/learn/certifications/{id}/confirm/`. Version 2 introduces Level 0 → Level 1 advancement via induction completion, which must go through a steward confirmation (the Induction Coordinator). This is consistent with the existing write path, but the induction completion flow must explicitly use it.

### Decision
Level 0 → Level 1 advancement follows the same `certifications/confirm/` pathway as all other advancements. On Community Programme completion (Inner Court), the Learn App signal automatically creates a draft `certification` Record with `metadata.target_level: 1` and `metadata.context: "induction_completion"`. The Induction Coordinator (Level 3+ within the Induction Tenant) reviews the user's profile, programme progress, and assessment, then calls `POST /api/learn/certifications/{id}/confirm/` with the `placement_tenant_id` in the request body. The confirm endpoint is extended to handle placement logic when `metadata.context == "induction_completion"`.

### Consequences
- No bypass of the single write path — Level 0 → 1 goes through the existing confirm endpoint
- The confirm endpoint requires a one-time extension: when `context == "induction_completion"`, it additionally creates a `UserPermission` in the placement tenant and deactivates the Induction Tenant `UserPermission`
- `induction_completed_at` is set on `User` at the same time as `competence_level` increment
- All other level advancements (1→2, 2→3, etc.) are unchanged

### ADR Status: Approved — Version 2

---

## ADR-004: No Celery or Redis in Version 2

### Context
Multiple planning documents proposed Celery + Redis for background tasks including advancement automation and notifications. The architectural constraint requires an ADR before adopting either.

### Decision
Celery and Redis are **not adopted in Version 2**. All automation that was proposed as Celery tasks is implemented using Django signals (synchronous, in-process) or management commands (run via cron). Specifically:
- Programme completion → draft certification creation: Django signal in `learn/signals.py` (synchronous)
- Induction completion detection: Django signal on Activity status transition
- Notifications: written synchronously to the Notification model at the point of the triggering event

Redis as a cache backend may be adopted in Version 3 when load justifies it. Celery may be adopted when a genuine async task requirement emerges that cannot be handled synchronously.

### Consequences
- Zero new infrastructure dependencies in Version 2
- All signal handlers must be fast — no heavy computation in the signal path
- Management command `python manage.py check_advancement` can be scheduled via system cron as a safety net for missed signals
- If a genuine async requirement emerges during Version 2 build, an ADR amendment is required before adoption

### ADR Status: Approved — Version 2

---

## ADR-005: Docker Compose — Deferred to Version 3

### Context
The Production Infrastructure Plan proposed Docker Compose + Daphne/Uvicorn to replace the current Nginx + Gunicorn + systemd setup. This would supersede the locked production engineering guide.

### Decision
Docker Compose is deferred to Version 3. The current Nginx + Gunicorn + systemd setup (per the production engineering guide) remains in place for Version 2. Reasons: (1) no Version 2 feature requires async ASGI; (2) containerising a working production system introduces migration risk without Version 2 benefit; (3) the sole developer constraint means migration overhead competes directly with feature delivery.

### Consequences
- Production engineering guide remains the authoritative infrastructure reference for Version 2
- Gunicorn (sync WSGI) remains the application server
- If Django Channels (WebSocket) is needed for live video scheduling or push notifications, this ADR must be revisited before that feature is built
- Docker Compose adoption is explicitly noted as a Version 3 infrastructure task

### ADR Status: Approved — Version 2

---

## ADR-006: Mobile Offline Strategy — Delta Sync API

### Context
The Flutter mobile app requires offline read capability and queued write capability for variable-connectivity environments.

### Decision
A delta sync endpoint `GET /api/sync/changes/?since={iso_timestamp}` is added in Version 2 Phase 4 (Infrastructure). It returns Records, Activities, and Notifications modified after the given timestamp. All models already have `updated_at = auto_now=True` — no model changes required. The mobile app stores a local SQLite cache via `sqflite` and syncs on reconnect.

### Consequences
- New file: `core/views/sync.py` — `SyncChangesView(APIView)`
- New URL: `api/sync/changes/` in `ics_project/urls.py`
- Response uses existing DRF serializers — no new serializer needed
- Write queue (offline POST → sync on reconnect) implemented in Flutter via `workmanager` package
- Desktop web offline (PWA service worker) is a Version 3 item

### ADR Status: Approved — Version 2 Phase 4

---

## ADR-007: Video Architecture — URL Embed Player (Phase 2) + Live Video App (Phase 5)

### Context
Two distinct video requirements were identified: (1) lesson videos embedded from YouTube/Vimeo/direct URLs in the Learn App; (2) a scheduled live video service for church services and events.

### Decision
These are separated into two distinct deliverables:

**URL Embed Player (Version 2 Phase 2 — Learn App):** A `core/utils/video.py` utility normalises YouTube, Vimeo, and direct `.mp4` URLs to embeddable form. A `templates/video/_player.html` partial renders `<iframe>` or `<video>` accordingly. Lesson Records store `custom_fields['video_url']` (no model field change). Built as part of the Learn App lesson viewer (L2).

**Live/Scheduled Video App (Version 2 Phase 5):** A dedicated Django app (`video_live/`) providing a programme scheduler (broadcast schedule, time slots, duration), a live stream embed surface (using `stream_url` already on Gathering records), and a VOD (video on demand) library of past recordings via URL. No self-hosting or transcoding infrastructure. Built after the core formation stack is complete.

### Consequences
- No MinIO video storage required — URL-based only in both phases
- No ffmpeg, no HLS, no `ics-videos` bucket
- Live scheduling uses the existing `Activity (activity_type:'event')` + `Gathering` dual-write pattern for the broadcast schedule
- `stream_url` on Gathering is already a placeholder for this — no model change required for basic live embed

### ADR Status: Approved — Version 2

---

## ADR-008: MinIO Object Storage — Version 2 Phase 4

### Context
The Production Infrastructure Plan proposed MinIO for profile avatars, tenant logos, and document attachments. The locked data contract uses `URLField` for avatars and logos.

### Decision
MinIO is adopted in Version 2 Phase 4 (Infrastructure), replacing `URLField` with `ImageField` for avatars and logos. The `Attachment` model proposed in the infrastructure plan conflicts with the single-records-table architecture. File attachments are instead stored as Records with `record_type: "attachment"` and `custom_fields['file_url']` pointing to the MinIO presigned URL.

### Consequences
- `accounts/models.py`: `avatar_url = URLField` → `avatar = ImageField(upload_to='avatars/')`; `avatar_url` retained as a `@property` returning `avatar.url` for serializer backward-compat
- `tenants/models.py`: same pattern for `logo`
- MinIO buckets: `ics-avatars` (public read), `ics-logos` (public read), `ics-private` (private, presigned URLs)
- No `Attachment` model — file uploads become Records with `record_type: "attachment"`
- `django-storages[s3]` + `boto3` added to `requirements.txt`
- Switching to AWS S3 in future: change three environment variables, zero code changes

### ADR Status: Approved — Version 2 Phase 4

---

## ADR-009: `community_ref` Relationship Type — Data Contract Amendment Required

### Context
The Production Infrastructure Plan proposed adding `community_ref` to relationship types for linking community content to governance records.

### Decision
`community_ref` will be added as a new `relationship_type` value, but only via a formal data contract v10 amendment — not as a direct code change. This amendment is bundled with the other v10 changes required for Version 2 (Induction Tenant tier, User induction fields).

### ADR Status: Approved — Requires data contract v10 amendment before implementation

---

## ADR-010: `Activity.linked_record` Explicit FK — Version 2 Phase 1

### Context
Currently, Activity links to Records via loose metadata keys (`metadata['programme_record_id']`). The Production Infrastructure Plan proposed an explicit FK field.

### Decision
`Activity.linked_record = ForeignKey('records.Record', on_delete=SET_NULL, null=True, blank=True)` is added in Version 2 Phase 1 as part of the pre-build code alignment. Metadata keys are retained for backward compatibility. New code uses the FK.

### Consequences
- New migration for `activity` app
- `activity/serializers.py` exposes `linked_record_id` as a writable field
- Bundled with data contract v10

### ADR Status: Approved — Version 2 Phase 1

---

## ADR-011: Qualification Programme Structure — KGS Names, Six Levels, and Induction as Course

### Context

The roadmap and data contract (v10, Part 12.3–12.4) described five qualification programmes using generic academic names (Certificate → Doctorate) and three separate induction programmes (Reconditioning Programme, Beginners Programme, Community Programme) seeded as standalone `record_type: "programme"` records. Review of the authoritative KGS documents — `Oveview_Main Learning Programmes.md`, `Pathways Competence Levels Qualification Programmes, and Roles.md`, and `kingdom-governance-system_v1.md` — reveals these as placeholders that do not reflect the KGS formation architecture.

### Decision

**1. Six programmes, not five.** Level 0 is a real formation level with its own programme record. The full set is:

| Level | Programme Name                                            | KGS Qualification     | Duration                      |
| ----- | --------------------------------------------------------- | --------------------- | ----------------------------- |
| 0     | New Life Programme (entry via Induction Training course)  | Certificate (Entrant) | 12 weeks (Induction) + 1 year |
| 1     | New Life Programme                                        | Certificate           | 1 year                        |
| 2     | Foundation Programme                                      | Diploma               | 3 years                       |
| 3     | Leaders Programme                                         | Degree                | 6–12 months                   |
| 4     | Builders Programme                                        | Masters               | 6–12 months                   |
| 5     | Architect's Programme                                     | Doctorate             | 2 years                       |

All five named programmes (Levels 1–5) are seeded as system Records (`record_family: "learning"`, `record_type: "programme"`, `origin: "system"`). Level 0 entry is handled through the Induction Training course within the New Life Programme.

**2. Induction Training is a course, not a programme.** The three previously specified standalone induction programmes (Reconditioning Programme, Beginners Programme, Community Programme) are retired as separate records. They are replaced by a single course record — `Induction Training` — seeded as `record_type: "course"` and linked to the New Life Programme via `Relationship (part_of)`. Its four modules are seeded as `record_type: "lesson"` records:

| Lesson                                                | Covers                       |
| ----------------------------------------------------- | ---------------------------- |
| Keys To the Kingdom                                   | Beginners pathway foundation |
| Repentance & Reformation                              | Reconditioning pathway       |
| Community Programme                                   | Sceptre Community life       |
| The Secret of Living a Fulfilled Life (HAL Beginners) | Practical formation          |

All entrant types (existing believers and newcomers) complete all four lessons. The `induction_pathway` field on User records background only — it does not gate individual lessons.

**3. KGS programme names replace academic placeholders.** "Certificate", "Diploma", "Degree", "Masters", "Doctorate" were interim labels. The canonical KGS names above are used in all UI display, seed data, and documentation from V2.1 onward.

**4. Pathways are multi-valued per programme.** Each programme record carries `custom_fields.kgs_pathways` (array) rather than a single pathway value:

| Programme             | kgs_pathways                                                |
| --------------------- | ----------------------------------------------------------- |
| New Life Programme    | `["new_life", "community_life", "learning"]`                |
| Foundation Programme  | `["spiritual_formation", "service", "mission", "learning"]` |
| Leaders Programme     | `["leadership", "service", "learning"]`                     |
| Builders Programme    | `["leadership", "apostolic_stewardship"]`                   |
| Architect's Programme | `["leadership", "apostolic_stewardship"]`                   |

**5. Curriculum is open — not locked at seed time.** Seeded programme and course records are created with `status: "active"` but are not locked governance records. Level 4+ authors can add courses and lessons to any programme post-seed. Level 5 locks governance records — learning content follows its own lifecycle (`draft → active`), not the governance lifecycle. The seed commands establish structure; they do not freeze it.

**6. The 24 Service Orders are the controlled vocabulary for `UserPermission.metadata.service_order`.** No model change required. The 24 Order names (from `Pathways Competence Levels Qualification Programmes, and Roles.md`) are referenced as the valid values. UI dropdowns built in V2.3+.

**7. The 12 Administrative Offices are deferred to V2.5+.** They are modelled as Agency-level tenants (`/global/agency/{office-slug}/`) under the existing tenant hierarchy. No new models required. This is a seed data and tenant creation task, not an architectural change.

### Consequences

- `seed_programmes` management command updated to seed 5 named programmes (Levels 1–5) with KGS names and multi-pathway tags
- `seed_induction_course` management command created: seeds Induction Training course + 4 lessons inside New Life Programme
- Data contract v10 Part 12.3 and 12.4 superseded by this ADR for programme names and induction structure
- No model changes required — existing `Record`, `Relationship`, and `Activity` models support this fully
- `induction_pathway` on User is retained as background metadata (not a content gate)

### ADR Status: Approved — Version 2 Phase V2.1
