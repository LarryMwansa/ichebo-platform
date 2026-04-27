# Ichebo Platform — Version 2 Build Roadmap
**Version:** v4 — 2026-04-25
**Previous version:** v3 — 2026-04-12 (MVP roadmap)
**Status:** Approved — Version 2 planning

> **v4 Scope:** Version 2 post-MVP build. Covers Phases 1–5 (Learn App, Induction System, Formation UI, Infrastructure, Live Video). All MVP phases (0–3, 5.1–5.7, 6–7) are complete or governed by the v3 roadmap.

> **Architecture decisions:** See `2026-04-25-ichebo-adr-version-2.md` for all ADRs referenced below.

---

## Pre-Build: Code Alignment Audit (Required Before Phase 1)

During MVP sessions, view code was written for apps that the v3 roadmap marks as Pending. This code exists on `main` and **must be audited before Version 2 build begins**. Building on unaligned code causes cascading rework.

**Audit process for each app:**
1. Open the app's locked system design document
2. Compare existing views against the spec'd URL routes, data patterns, access gates, and HTMX partial patterns
3. Mark each view: ✅ Conforms | ⚠️ Needs adjustment | ❌ Rewrite required
4. Document findings; fix before building on top

**Apps to audit:**

| App | Existing code | Reference doc |
|-----|--------------|---------------|
| Learn | `learn/views.py` (~478 LOC) | `2026-04-07-ics-learn-app-system-design_v2.md` |
| Governance | `governance/views.py` (~465 LOC) | `2026-04-10-ics-governance-app-system-design.docx` |
| Community | `community/views.py` | `2026-04-08-ics-community-app-system-design.md` |
| Paraclete | `paraclete/service.py` (~406 LOC) | `2026-04-10-ics-paraclete-service-system-design.docx` |
| Records linking | `records/views.py`, `activity/models.py` | Data contract v9 + v10 amendments |
| Notifications | `notifications/` | `2026-04-10-ics-profile-settings-notifications-spec.docx` |

**Also audit during pre-build:**
- Confirm production Django version is 4.2 LTS (not 5.2)
- Confirm `competence_level` write path is isolated to `POST /api/learn/certifications/{id}/confirm/` only
- Confirm `Activity.linked_record` FK exists or add it (ADR-010)

**Commit:** `git add . && git commit -m "chore: pre-build code alignment audit"`

---

## Phase 1 — Learn App Foundation
**Version:** 2.0
**Entry requirement:** Pre-build audit complete
**Exit criteria:** All five qualification programmes browsable and enrollable. Lesson completion and progress tracking work end-to-end. Steward can confirm certifications, advancing competence level. Level 4+ can author content; Level 5 can approve it. URL video embed player operational in lesson viewer.

> **Reference:** `2026-04-07-ics-learn-app-system-design_v2.md` — authoritative. Build against the system design phases (A–G) defined there.

### What this builds

**L1 — Learn App Backend**

- `CertificationConfirmation` model (if not already conformant with spec)
- All DRF endpoints: `GET /api/learn/health/`, curriculum endpoint, cert queue, cert confirm
- Five Qualification Programmes seeded as system Records:

| Programme | Level | Duration | Prerequisites |
|-----------|-------|----------|---------------|
| Certificate | 1 | 1 year | None |
| Diploma | 2 | 3 years | Certificate |
| Degree | 3 | 4 years | Diploma |
| Masters | 4 | 4–5 years | Degree |
| Doctorate | 5 | 7 years | Masters |

- Three Induction Programmes seeded (Level 0, Induction Tenant scope):

| Programme | Entrant type | Court |
|-----------|-------------|-------|
| Reconditioning Programme | Existing believers | Outer Court |
| Beginners Programme | Kingdom-curious | Outer Court |
| Community Programme | All inductees | Inner Court |

- `learn/signals.py`: programme Activity at 100% → draft `certification` Record created automatically
- `learn/service.py`: enrolment logic, prerequisite checks, `enrol_induction_programmes(user, pathway)` function

**L2 — Learn App UI (Django templates + HTMX)**

All features F1–F11 per system design:
- Programme Catalogue (F1) — pathway view + flat catalogue, locked state for above-level programmes
- Course Browser (F2)
- Enrolment (F3) — prerequisite check, one enrolment per programme
- Progress Tracking (F4) — lesson completion, progress bars, resume from last incomplete
- Lesson Viewer (F5) — rendered content, mark complete, previous/next navigation
- **URL Video Embed Player** — `core/utils/video.py` + `templates/video/_player.html`; renders YouTube/Vimeo as `<iframe>`, direct `.mp4` as `<video>`; `custom_fields['video_url']` on lesson Records (no model field change)
- Assessments (F6) — quiz and assignment submission
- Certification (F7) — "Awaiting certification" state, steward queue, confirm → level increment
- Content Authorship (F8) — Level 4+ draft and submit programmes, courses, lessons
- Handbook Review Queue (F9) — Level 5 approve/return/lock
- Pathway Banner (F10) — "You are on the Service Pathway"
- My Learning Dashboard (F11) — active enrolments, certifications, formation summary

**Django template routes:**
```
GET  /learn/                              My Learning Dashboard
GET  /learn/catalogue/                    Programme catalogue
GET  /learn/programme/{id}/               Programme detail
GET  /learn/course/{id}/                  Course detail
GET  /learn/lesson/{id}/                  Lesson viewer
POST /learn/htmx/enrol/{programme_id}/    Enrolment
POST /learn/htmx/lesson/{id}/complete/    Mark lesson complete
POST /learn/htmx/assessment/{id}/submit/  Submit assessment
GET  /learn/certifications/               Steward certification queue (Level 3+)
POST /learn/htmx/certification/{id}/confirm/  Confirm certification
GET  /learn/author/                       Authorship dashboard (Level 4+)
GET  /learn/review/                       Handbook review queue (Level 5)
```

**Commits:** 2 (L1 backend, L2 UI)
**Effort:** ~40% of Version 2 velocity (~3–4 weeks)

---

## Phase 2 — Induction System
**Version:** 2.1
**Entry requirement:** Phase 1 complete (Learn App must exist for induction programmes to run)
**Exit criteria:** Every new user lands in the Induction Tenant automatically. Reconditioning and Beginners pathways serve different programmes. Steward can confirm induction completion and place users in their home tenant via the certifications confirm endpoint. No user enters a community without completing induction.

> **References:** `2026-04-25-ichebo-adr-version-2.md` (ADR-002, ADR-003); data contract v10

### What this builds

**G1 — Induction Tenant (System Tenant)**

- Add `"induction"` to `Tenant.tier` choices (ADR-002)
- Seed command: `python manage.py seed_induction_tenant`
- Induction Tenant: `path="/global/induction/"`, `slug="induction"`, `tier="induction"`, `status="active"`
- Cannot be deleted, renamed, or modified via normal UI flows — enforced at view layer
- Three induction programmes (seeded in Phase 1 L1) are scoped to this tenant

**G2 — Sign-up & Profile Registration**

Three-step flow:

*Step 1 — Sign-up:* Email + password, email verification, no competence level assigned, status: `"seeker"`

*Step 2 — Profile Registration:* Collects:
- Full Name, Email (read-only — from auth), Address, Country, ID Number or Passport Number, Age, Gender, Occupation, Education/Qualification, Born Again status (Yes/No)
- Entrant type selection: "I am already part of a church or faith community" (→ Reconditioning) vs "I am new to this or exploring" (→ Beginners)
- All saved to `UserProfile`

*Step 3 — Induction Placement:*
- `UserPermission` created: `tenant_path="/global/induction/"`, `level=0`, `role="seeker"`, `is_active=True`
- `induction_enrolled_at` set on User
- `induction_pathway` set based on entrant type (`"reconditioning"` | `"beginners"`)
- User redirected to Induction Dashboard

**New fields on User/UserProfile:**
- `induction_enrolled_at` (DateTimeField)
- `induction_completed_at` (DateTimeField)
- `induction_pathway` (`"reconditioning" | "beginners" | null`)

**Django template routes:**
```
GET  /accounts/register/              Sign-up form
POST /accounts/register/              Create user, send verification email
GET  /accounts/verify-email/{token}/  Verify, redirect to profile
GET  /accounts/profile-setup/         Profile registration form
POST /accounts/profile-setup/         Save profile + place in Induction Tenant
GET  /accounts/welcome/               Induction welcome / orientation
```

**G3 — Induction Programme Enrolment**

Triggered automatically on G2 placement:

| Entrant type | Outer Court programme | Inner Court programme |
|---|---|---|
| Reconditioning | Reconditioning Programme | Community Programme |
| Beginners | Beginners Programme | Community Programme |

- `learn/service.py` → `enrol_induction_programmes(user, pathway)` called from profile setup view
- Community Programme enrolment triggered on Outer Court programme completion (Django signal)
- Induction Dashboard rendered from the Learn App (special view for `tier="induction"` users)

**G4 — Induction Completion & Tenant Placement**

Completion flow:
1. User completes Community Programme (Inner Court)
2. Learn App signal creates draft `certification` Record with `metadata.context: "induction_completion"`, `metadata.target_level: 1`
3. Induction Coordinator (Level 3+ in Induction Tenant) opens induction review queue
4. Coordinator reviews: profile data, programme completion, assessment submissions
5. Coordinator selects placement tenant — system narrows list by user's Country/City from profile (suggest + steward confirms — ADR-003)
6. Coordinator calls `POST /api/learn/certifications/{id}/confirm/` with `placement_tenant_id`
7. On confirm: `induction_completed_at` set, `competence_level` → 1, `UserPermission` created in home tenant (`level=1`, `role="disciple"`), Induction Tenant `UserPermission` deactivated, ActivityLog entry written

**Extended confirm endpoint (ADR-003):**
- When `metadata.context == "induction_completion"`: handle placement logic in addition to standard level increment
- `placement_tenant_id` required in request body when context is induction_completion

**Django template routes:**
```
GET  /learn/induction/review/                    Steward: pending induction list
GET  /learn/induction/review/{user_id}/          Steward: individual review
POST /learn/htmx/induction/confirm/{user_id}/    Steward confirms + places
GET  /accounts/formation/                        User: post-placement welcome
```

**Commits:** 4 (G1 seed, G2 sign-up + profile, G3 enrolment, G4 completion + placement)
**Effort:** ~35% of Version 2 velocity (~2–3 weeks)

---

## Phase 3 — Formation UI & App Drawer Gating
**Version:** 2.2
**Entry requirement:** Phase 2 complete (users must have levels from induction)
**Exit criteria:** Users can see their level, active programme, and progress at a glance. App drawer correctly reflects access by level. Users understand the path to unlock new apps.

### What this builds

**H1 — Formation Dashboard**

- Level badge in navbar (coloured: 0=grey, 1=green, 2=blue, 3=purple, 4=orange, 5=red)
- "Your Formation Journey" card on dashboard:
  - Current competence level with KGS name (e.g. "Foundational Disciple")
  - Active qualification programme with progress bar
  - Next level: which programme must be completed
  - Pathway affiliation
- Formation history: timeline of level advancements (from `CertificationConfirmation` records)
- "Level up requirements" modal on level badge click

**Data sources:**
- `user.competence_level` — current level
- `CertificationConfirmation` records — history
- Active `activity_type: "programme"` Activity — current enrolment

**Django template routes:**
```
GET  /accounts/formation/              Full formation history
GET  /learn/htmx/formation-card/       HTMX dashboard card partial
```

**H2 — App Drawer Level Gating**

Access levels per app (stored in `settings.py` as `APP_LEVEL_REQUIREMENTS` dict — no new model):

| App | Minimum level | Notes |
|-----|-------------|-------|
| Bible | 0b (Seeker) | Always accessible |
| Learn | 0b (Seeker) | Browse only; enrol at Level 1 |
| Activity | 1 | Full access |
| Community | 1 | My Community; Management at Level 3 |
| Governance | 3 | Reference Library; Mandate at Level 4 |
| Paraclete | 1 | Level 1+ |

Drawer behaviour:
- Available apps: rendered normally, clickable
- Locked apps: lock icon + tooltip "Requires Level X"
- Click on locked app: modal "To access Governance, advance to Level 3. Complete the Diploma Programme."

**Files:**
- `templates/partials/app_drawer.html` — conditional rendering via `request.user.userprofile.competence_level`
- `templates/partials/_app_locked_modal.html` — info modal
- `settings.py` — `APP_LEVEL_REQUIREMENTS = {'governance': 3, 'community': 1, ...}`
- `accounts/context_processors.py` — expose level to all templates

**Commits:** 2 (H1 formation dashboard, H2 drawer gating)
**Effort:** ~15% of Version 2 velocity (~1 week)

---

## Phase 4 — Infrastructure & Tenant Self-Service
**Version:** 2.3
**Entry requirement:** Phase 3 complete
**Exit criteria:** MinIO operational for avatars and logos. Delta sync endpoint available. Records aggregated relationships endpoint available. Tenant creation and member invitation working for Level 3+ users.

### What this builds

**P1 — MinIO Object Storage (ADR-008)**

- `requirements.txt`: add `django-storages[s3]`, `boto3`, `Pillow`
- `accounts/models.py`: `avatar_url = URLField` → `avatar = ImageField`; `avatar_url` property retained
- `tenants/models.py`: `logo_url = URLField` → `logo = ImageField`
- MinIO buckets: `ics-avatars`, `ics-logos`, `ics-private`
- Settings: `STORAGES`, `AWS_S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- Nginx: proxy `/media/` to MinIO

**P2 — Records API Improvements**

- `GET /api/records/{id}/related/` — aggregated relationships (outgoing + incoming, grouped by type). Reuses `get_linked_records()` from `governance/services.py`. No new logic.
- `activity/models.py` — `linked_record = ForeignKey('records.Record', SET_NULL, null=True)` (ADR-010)
- `records/admin.py` — register `Relationship` model
- Data contract v10 amendment: `community_ref` relationship type (ADR-009)

**P3 — Delta Sync API (ADR-006)**

- `core/views/sync.py` — `SyncChangesView`: `GET /api/sync/changes/?since={iso_timestamp}`
- Returns delta of Records + Activities + Notifications using existing `updated_at` fields
- Prerequisite for Flutter mobile offline capability

**P4 — FCM Token**

- `accounts/models.py` — `fcm_token = CharField(max_length=255, blank=True)`
- Migration; exposed via `GET /api/auth/me/`
- `notifications/fcm.py` — `send_push_notification()` helper stub (wired when mobile app is built)

**I1 — Tenant Creation & Management (Level 3+)**

- `/tenants/create/` form: name, slug, tier, parent tenant, description, location, logo
- `TenantInvitation` model: tenant, email, invited_by, accepted_at, status
- Invitation workflow: invite → email → accept → `UserPermission` created
- Member management: assign roles (`Coordinator, Shepherd, Net Caster, Net Mender, Member`)
- Extend `Tenant`: `coordinator_user_id`, `community_theme`, `area_of_operation`

**I2 — Multi-Tenant Content Visibility**

- Governance records filtered by user's tenant(s)
- Learn content filtered by user's tenant(s)
- Handbook content visible to Level 4+ across all tenants
- Induction Tenant special scoping: Level 0 sees induction content only

**Commits:** 5 (MinIO, records API, sync API, tenant creation, content scoping)
**Effort:** ~10% of Version 2 velocity (~2 weeks)

---

## Phase 5 — Live/Scheduled Video App
**Version:** 2.4
**Entry requirement:** Phase 4 complete; Learn App operational (Phase 1)
**Exit criteria:** Broadcast schedule visible and navigable. Live stream embeds render for active events. VOD library of past recordings browsable. Scheduler produces a time-based programme list.

> **Reference:** ADR-007 — URL-based video only; no self-hosting, no MinIO video bucket, no ffmpeg.

### What this builds

**V1 — Broadcast Scheduler**

- New Django app: `video_live/`
- Broadcast schedule: a list of time-slotted events with title, description, stream URL, start time, duration
- Stored as `Activity (activity_type: "event")` + `Gathering` dual-write (existing Community App pattern)
- `stream_url` field on Gathering (already exists) carries the live stream URL
- Scheduler view: programme grid by time slot (today, this week)
- Past events automatically become VOD entries (stream URL archived on the Record)

**V2 — Live Stream Surface**

- `GET /video/live/` — current live stream (if any active event) + schedule
- `GET /video/schedule/` — programme grid (today + upcoming 7 days)
- `GET /video/vod/` — past recordings library
- `GET /video/watch/{event_id}/` — individual event player (live or VOD)
- HTMX auto-refresh on `/video/live/` every 60 seconds to detect live status changes

**V3 — Flutter Mobile Video (parallel with mobile build)**

- `youtube_player_flutter` for YouTube stream URLs
- `video_player` + `chewie` for direct `.mp4` URLs
- URL type detected from `stream_url` field in API response

**Commits:** 3 (V1 scheduler + model, V2 UI, V3 mobile integration)
**Effort:** ~8 weeks from Phase 4 completion

---

## Flutter Mobile App (Parallel Track)
**Version:** 2.x (parallel with Phases 3–5)
**Entry requirement:** Phase 2 complete (DRF API stable, user levels established); ADR-001 approved
**Exit criteria:** All user levels (0–5) can authenticate and access role-appropriate screens. Core apps (Bible, Learn, Activity, Community) accessible. Offline read via SQLite cache. Push notifications via FCM.

> **Architecture:** ADR-001 — Flutter consumes existing DRF API. No backend changes except delta sync (Phase 4 P3) and FCM token (Phase 4 P4).

### Navigation shells by level

| Level | Role | Screens available |
|-------|------|------------------|
| 0 | Seeker/Inductee | Bible, Learn (induction), Profile |
| 1 | Member | + Activity, Community |
| 2 | Disciple | + Governance (read) |
| 3 | Steward/Coordinator | + Community management, Cert queue |
| 4 | Senior Steward | + Governance (write), Programme oversight |
| 5 | Architect | + Full operator console |

### Packages
`go_router`, `dio`, `riverpod`, `sqflite`, `firebase_messaging`, `youtube_player_flutter`, `video_player`, `workmanager`, `path_provider`, `file_picker`

**Commits:** phased per app screen set
**Effort:** parallel track; estimated 8–12 weeks

---

## Implementation Roadmap

```
MVP (COMPLETE — 6c43ce9)

Pre-Build: Code Alignment Audit
  └─ Audit learn, governance, community, paraclete, records linking, notifications
  └─ Confirm Django 4.2, competence_level write path isolation
  └─ Add Activity.linked_record FK (ADR-010)
  └─ Data Contract v10 amendment

Version 2.0 — Learn App Foundation
  └─ L1: Learn App Backend (models, DRF, qualification framework, induction programmes)
  └─ L2: Learn App UI (catalogue, enrolment, lesson viewer, cert queue, URL video embed)

Version 2.1 — Induction System
  └─ G1: Induction Tenant (seed command, tier enum)
  └─ G2: Sign-up & Profile Registration (entrant type, placement)
  └─ G3: Induction Programme Enrolment (auto-enrol on placement)
  └─ G4: Induction Completion & Tenant Placement (steward confirms → Level 1)

Version 2.2 — Formation UI & Drawer Gating
  └─ H1: Formation Dashboard (level badge, progress card, history)
  └─ H2: App Drawer Level Gating (locked state, path to unlock)

Version 2.3 — Infrastructure & Tenant Self-Service
  └─ P1: MinIO (avatars, logos, private docs)
  └─ P2: Records API improvements (aggregated relationships, Activity FK)
  └─ P3: Delta Sync API (mobile offline prerequisite)
  └─ P4: FCM token (push notification foundation)
  └─ I1: Tenant Creation & Management (Level 3+)
  └─ I2: Multi-Tenant Content Visibility

Version 2.4 — Live/Scheduled Video App
  └─ V1: Broadcast Scheduler
  └─ V2: Live Stream + VOD surface
  └─ V3: Flutter mobile video (parallel)

Flutter Mobile App (Parallel Track — begins after Version 2.1)
  └─ Authentication + role-adaptive shell
  └─ Bible, Learn, Activity, Community screens
  └─ Offline SQLite cache + delta sync
  └─ Push notifications (FCM)
  └─ Video player (YouTube, Vimeo, direct .mp4)
```

---

## Data Contract Amendment Required (v10)

Produce data contract v10 before Phase 2 (G1) build begins. Covers:

| Change | ADR |
|--------|-----|
| `Tenant.tier` enum: add `"induction"` | ADR-002 |
| `User`: add `induction_enrolled_at`, `induction_completed_at`, `induction_pathway` | ADR-003 |
| `Activity`: add `linked_record = ForeignKey(records.Record)` | ADR-010 |
| `Relationship.relationship_type`: add `community_ref` | ADR-009 |
| `certifications/confirm/` endpoint: extended for induction completion context | ADR-003 |

---

## Effort Estimation

| Phase | Version | Commits | Weeks | Notes |
|-------|---------|---------|-------|-------|
| Pre-Build audit | — | 1 | 0.5 | Non-negotiable first step |
| 1 — Learn App | 2.0 | 2 | 3–4 | Largest single build |
| 2 — Induction | 2.1 | 4 | 2–3 | Depends on Phase 1 |
| 3 — Formation UI | 2.2 | 2 | 1 | Mostly template work |
| 4 — Infrastructure | 2.3 | 5 | 2 | Model + infra additions |
| 5 — Live Video | 2.4 | 3 | 3 | After Phase 4 |
| Flutter (parallel) | 2.x | phased | 8–12 | Parallel from Phase 2 |

*Estimates assume 1 developer, daily testing, minimal QA*

---

## Open Decisions (Locked or Pending)

| Decision | Status |
|----------|--------|
| G2 profile registration fields | ✅ Locked — see above |
| G1 Induction Tenant tier | ✅ Locked — new `"induction"` tier value (ADR-002) |
| G4 placement logic | ✅ Locked — suggest by geography + steward confirms (ADR-003) |
| Celery/Redis | ✅ Locked — deferred to Version 3 (ADR-004) |
| Docker Compose | ✅ Locked — deferred to Version 3 (ADR-005) |
| Mobile client | ✅ Locked — Flutter (ADR-001) |
| Video architecture | ✅ Locked — URL embed (L2) + Live Video App (Phase 5) (ADR-007) |
| G4 Induction programmes content (lessons) | ⏳ Open — seeded as structure; lesson content authored by Level 4+ after platform is live |
| Induction duration (configurable vs fixed 12 weeks) | ⏳ Open — 12 weeks is default; configurability deferred to Version 3 |

---

## Branch Structure

```
main                        ← production
├─ mvp                      ← MVP complete (6c43ce9) [frozen]
└─ version-2                ← all v2 work branches here
   ├─ version-2-audit        ← pre-build code alignment
   ├─ version-2-l1           ← Learn App backend
   ├─ version-2-l2           ← Learn App UI
   ├─ version-2-g1           ← Induction Tenant
   ├─ version-2-g2           ← Sign-up & profile
   ├─ version-2-g3           ← Induction enrolment
   ├─ version-2-g4           ← Induction completion
   ├─ version-2-h1           ← Formation dashboard
   ├─ version-2-h2           ← Drawer gating
   ├─ version-2-infra        ← MinIO, API, sync, FCM
   ├─ version-2-tenants      ← Tenant creation + scoping
   └─ version-2-video        ← Live Video App
```

---

## Success Metrics

### After Phase 1 (Learn App)
- All five qualification programmes browsable and enrollable
- Lesson completion and progress tracking working end-to-end
- Steward can confirm certifications, advancing competence level
- Level 4+ can author content; Level 5 can approve it

### After Phase 2 (Induction)
- Every new user lands in the Induction Tenant automatically
- Reconditioning and Beginners pathways serve different programmes
- Steward can confirm induction completion and place users in home tenant
- No user enters a community without completing induction

### After Phase 3 (Formation UI)
- Users can see their level, programme, and progress at a glance
- App drawer correctly reflects access by level
- Users understand the path to unlock new apps

### After Phase 4 (Infrastructure + Tenants)
- Avatars and logos stored in MinIO
- New Sceptre Communities can be established digitally by Level 3+ stewards
- Tenant hierarchy grows through steward action
- Delta sync endpoint available for mobile client

### After Phase 5 (Live Video)
- Broadcast schedule visible and navigable
- Live stream embeds render for active events
- VOD library of past recordings browsable

### After Flutter Mobile (parallel)
- All user levels (0–5) can authenticate and access role-appropriate screens
- Core apps accessible on mobile
- Offline read functional
- Push notifications operational
