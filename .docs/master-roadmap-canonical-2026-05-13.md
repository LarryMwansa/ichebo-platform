# Ichebo Platform — Master Build Roadmap

**Version:** v7 — 2026-05-13 (Canonical)
**Previous version:** v6 — 2026-04-27
**Status:** Approved — Definitive Reference
**Supersedes:** All previous roadmap versions (v1–v6)

> This is the single authoritative roadmap for the entire Ichebo platform and ecosystem. It covers every phase, every product, every technology decision, and every deferred item. No other roadmap supersedes this document.
>
> **How this was produced:** v6 (2026-04-27) was the canonical consolidation of all build history through Version 2 planning. This v7 amendment: (1) marks all Version 2 phases as complete, (2) adds the Apostolic Command Shell as a named architectural component, (3) adds DESIGN.md as a locked design authority reference, (4) adds Ichebo Desktop and the ecosystem product family, (5) adds the Go engine layer and Sync Engine, (6) updates the Layer and Phase structure to reflect the ecosystem vision, and (7) aligns all references to the ADR set (ADR-001 through ADR-021).

---

## How to Read This Document

Every phase has four things:
- **What it builds** — the specific features and files
- **Entry requirement** — what must be complete before this phase starts
- **Exit criteria** — how you know the phase is done
- **Commit** — the git commit message when the phase closes

Phases are numbered. Within a phase, tasks are lettered. Do not skip phases. Do not start a task before its entry requirement is met.

---

## Platform Overview

**What Ichebo is:** A Kingdom Governance System (KGS) platform — the digital expression of the Kingdom Governance System framework developed by Ichebo Christian Services, led by Paul Reuben (Founder and Principal Leader). The platform enables Christian organisations to digitally manage governance, discipleship, and ministry operations across three product surfaces.

**Three client surfaces:**

| Surface | Technology | Primary user | Role |
|---------|-----------|-------------|------|
| **Ichebo Web** (app.ichebo.org) | Django templates + HTMX | Level 3–5 stewards, coordinators, architects | Apostolic Command Shell — desktop governance and operations |
| **Ichebo Mobile** | Flutter + DRF API | All users Level 0b–5 | Daily companion — lessons, activities, community, Bible |
| **Ichebo Desktop** | Flutter + SQLite + Go Sync Engine | Community steward | Local-first community operating system — offline-capable |

**Backend:** Django 4.2 LTS + Django REST Framework + PostgreSQL. One backend, two web/mobile clients. DRF API serves Flutter Mobile and Ichebo Desktop sync. Go engine layer (Version 3+) provides portable domain logic.

**Infrastructure:** Hetzner VPS (Ubuntu 22.04), Nginx, Gunicorn, systemd. Hetzner Object Storage (S3-compatible, bucket: ics-media) for file and media storage.

---

## Architecture Decisions (Locked)

These decisions are final. They cannot be changed without producing a new ADR. Do not re-open them.

| ADR | Decision | What it means |
|-----|----------|--------------|
| ADR-001 (amended) | Flutter for all client surfaces | Flutter targets Desktop (Windows/macOS/Linux), Mobile (Android-first, iOS later). Not HTMX. Consumes DRF API. |
| ADR-002 | Django 4.2 LTS | Long-term support. Do not upgrade to 5.x without a new ADR. |
| ADR-003 | Single records table with discriminator | All content uses one records table with record_family / record_type discriminator. No new model tables for content types. |
| ADR-004 | DRF retained for mobile and sync | /api/ endpoints are the mobile API and the sync target for Ichebo Desktop. |
| ADR-005 | Django templates + HTMX for web | No React, Vue, or JS framework on the web. HTMX handles dynamic interactions. |
| ADR-006 | competence_level one write path | Only POST /api/learn/certifications/{id}/confirm/ may increment competence_level. Nothing else. |
| ADR-007 | URL-based video only in Version 2 | No self-hosted video transcoding in Version 2. YouTube/Vimeo iframe embed only. Ichebo Media is Version 3+. |
| ADR-008 | No Celery or Redis until Version 3 | All automation uses Django signals (synchronous) or cron management commands. |
| ADR-009 | No Docker until Version 3 | Nginx + Gunicorn + systemd is the production stack. |
| ADR-010 | Paraclete is rule-based in MVP | Pure Python. No LLM calls. Reads ORM, returns digest. Writes nothing. |
| ADR-011 | KGS programme and curriculum structure | Five qualification programmes (Certificate → Doctorate), four induction lessons, eight pathways. See VERSION_2_PLANNING for full specification. |
| ADR-012 | Apostolic Command Shell | Four-column desktop governance interface. Level 3+ only. The canonical desktop web surface. |
| ADR-013 | DESIGN.md + design-preview.html as locked design authority | All visual decisions governed by DESIGN.md. design-preview.html is the canonical visual reference. Neither may be contradicted without amendment. |
| ADR-014 (amended by ADR-022) | The Desk as governance authorship surface | Canonical authorship environment. **Amended 2026-06-09 (ADR-022):** The Desk is relocated into the Handbook surface. Canonical statement is now "The Handbook is the canonical governance authorship surface; The Desk editor is embedded within it." All governance record creation still routes through this editor — only its navigational home changed. |
| ADR-015 | Dual-shell rendering architecture | Stage Mode (Level 3+, desktop) and Mobile Mode (all users, mobile) are two first-class rendering paths. Neither is a degradation of the other. |
| ADR-016 | Local-first as Ichebo architectural philosophy | Device is primary computer. Cloud is coordination. Applies to Ichebo Desktop and native Flutter Mobile. Does not change the Django cloud platform. |
| ADR-017 | Ichebo Desktop as primary product | Desktop is the primary product. Cloud exists to coordinate and give visibility to local installations. MVP: People + Activity + Sync. |
| ADR-018 | Sync Engine as standalone Go binary | Bidirectional, conflict-aware sync engine. ChangeLog, Push/Pull/Resolve, conflict rules by data type. The strategic secret sauce. |
| ADR-019 | Go as language for foundation engines | Records Engine, Activity Engine, Relationships Engine, Bible Engine, Calendar Engine, Sync Engine — all Go modules. Django is the web layer and API adapter. |
| ADR-020 | Ichebo Handbook as standalone product | Supersedes Handbook-as-tenant decision. Handbook is institutional memory that precedes all tenants. Handbook-as-tenant remains in production pending migration. |
| ADR-021 | Ichebo Media as standalone product | Full video engine — upload, transcode, store, serve, live stream. Go + FFmpeg + Hetzner Object Storage + HLS. Version 3+. |
| ADR-022 | Handbook and Governance separation of concerns | Governance App becomes read-only public library (no write UI). Handbook becomes the invited Level 4-5 authorship workspace; The Desk relocates here. `HandbookRecord`/`HandbookRelationship` retired — Handbook is now a UI layer over `records.Record`, same as Governance. Records App gets a dedicated full-width desktop layout. Amends ADR-012 (sidebar order) and ADR-014 (Desk's canonical location). Does not amend ADR-020. |
| Email | Email via Brevo | Free tier (300 emails/day). SMTP integration via Django email backend. |

---

## Design Authority

**DESIGN.md** is the locked design system authority for all Ichebo surfaces (ADR-013). **design-preview.html** is its canonical visual reference implementation. Both are co-equal authorities.

| Token | Value |
|-------|-------|
| Primary Red | #AF3236 |
| Secondary Blue | #185ABC |
| Ink | #0E0E0E |
| Stone | #F5F3F0 |
| Display font | Playfair Display (700, 800, 900) |
| UI font | Inter (400, 500, 600) |
| Monospace | Fira Code (400) |

Pink (#FFC0CB or similar) is never a valid accent colour. All pink instances are bugs.

---

## Dependency Rules (Non-Negotiable)

```
Django auth → Django tenant → Django records engine → Django activity engine
Django models → DRF serializers → DRF views → DRF URLs
DRF endpoints live → Django template views → HTMX partials
Records engine complete → Activity engine begin
Activity engine complete → Learn App begin (Learn uses Activity for progress tracking)
All Phase 5 apps complete → Paraclete service begin
Paraclete service complete → Dashboard begin
One app per git commit — never mix app work across a single commit

Ecosystem (Version 3+):
UUID schema locked → ChangeLog built → Go engines built → Sync Engine built → Desktop UI built
```

---

## The Ichebo Product Family — Full Feature Inventory

### Ichebo Web — Apostolic Command Shell

| Feature | Version |
|---------|---------|
| Four-column grid (Sidebar, Context Bar, Stage, Options Bar) | ✅ Version 2 |
| The Desk — governance authorship canvas | ✅ Version 2 |
| Stage Mode / Mobile Mode dual-shell | ✅ Version 2 |
| DESIGN.md design system applied | ✅ Version 2 |
| Dashboard (Command Centre) | ✅ Version 2 |
| Governance App (Reference Library, Mandate, Keys) | ✅ Version 2 |
| Community App (members, announcements, gatherings) | ✅ Version 2 |
| Learn App (programmes, courses, lessons, certifications) | ✅ Version 2 |
| Activity App (personal + ministry surfaces) | ✅ Version 2 |
| Bible App (scripture reader, annotations) | ✅ Version 2 |
| Profile + Settings | ✅ Version 2 |
| Notifications (full) | ✅ Version 2 |
| Video / Live App (URL embed, broadcast scheduler, VOD) | ✅ Version 2 |
| Induction system (12-week, two pathways) | ✅ Version 2 |
| Steward dashboard + tenant self-service | ✅ Version 2 |
| Agency tenants + 24 Service Orders seeded | ✅ Version 2 |
| Paraclete service (rule-based) | ✅ Version 2 |
| HRS graph visualisation (full) | Version 3+ |
| Level 4 tenant-scoped governance records | Version 3+ |
| Paraclete AI (LLM-based) | Version 3+ |
| Real-time notifications (WebSockets) | Version 3+ |

### Bible App

| Feature | Version |
|---------|---------|
| Scripture reader (KJV, ASV, WEB) | ✅ Version 1 |
| Personal annotations | ✅ Version 1 |
| Tenant-scoped annotations | ✅ Version 1 |
| Handbook linkages (Level 5) | ✅ Version 1 |
| Reading plans | Version 3+ |
| Verse highlights | Version 3+ |
| Scripture full-text search | Version 3+ |
| Licensed translations (NIV, ESV, NLT) | Version 3+ (requires publishing agreements) |
| African language translations | Version 3+ |
| Audio Bible | Version 3+ |
| Cross-reference chains | Version 3+ |

### Learn App

| Feature | Version |
|---------|---------|
| Content authorship (Level 4+) | ✅ Version 2 |
| Handbook review queue (Level 5) | ✅ Version 2 |
| Five qualification programmes (Certificate → Doctorate) | ✅ Version 2 |
| Programme catalogue with level gating | ✅ Version 2 |
| Enrolment and progress tracking | ✅ Version 2 |
| Lesson viewer with mark-complete | ✅ Version 2 |
| Assessments (quiz, assignment) | ✅ Version 2 |
| Certification flow (steward confirms → level advance) | ✅ Version 2 |
| URL video embed in lessons | ✅ Version 2 |
| Pathway banner | ✅ Version 2 |
| My Learning Dashboard | ✅ Version 2 |
| Induction programmes (Reconditioning, Beginners, Community) | ✅ Version 2 |
| Rich text editor for authorship | Version 3+ |
| Quiz auto-grading | Version 3+ |
| Assignment peer review | Version 3+ |
| Learning analytics dashboard | Version 3+ |
| Offline lesson caching | Version 3+ |
| Self-hosted video lessons (Ichebo Media) | Version 3+ |

### Activity App

| Feature | Version |
|---------|---------|
| Activity Engine (models, signals, DRF) | ✅ Version 1 |
| My Activities surface (task, habit, goal, skill, reminder) | ✅ Version 2 |
| Ministry surface (campaign, project, task, event) | ✅ Version 2 |
| Assigned-to-me queue | ✅ Version 2 |
| Calendar dated list view | ✅ Version 2 |
| Habit streak visualisation | Version 3+ |
| Full calendar grid UI | Version 3+ |
| Ministry analytics | Version 3+ |
| Cross-tenant campaign assignment | Version 3+ |

### Community App

| Feature | Version |
|---------|---------|
| Member directory | ✅ Version 2 |
| Announcements (create, broadcast to tenant) | ✅ Version 2 |
| Gatherings (dual-write with Activity event) | ✅ Version 2 |
| Community coordinator dashboard | ✅ Version 2 |
| Membership request flow | ✅ Version 2 |
| Pastoral notes | Version 3+ (privacy design required) |
| Attendance tracking | Version 3+ (privacy-sensitive) |
| Community analytics dashboard | Version 3+ |
| Collective-level gathering visibility | Version 3+ |
| Pastoral assignment model | Version 3+ |

### Governance App

| Feature | Version |
|---------|---------|
| Reference Library (Level 3+ read) | ✅ Version 2 |
| Mandate branch (Level 4+ read) | ✅ Version 2 |
| Keys Library (personal, Level 3+) | ✅ Version 2 |
| Record lifecycle (lock, supersede, version chain) | ✅ Version 2 |
| Linked Records panel (flat list) | ✅ Version 2 |
| The Desk (governance authorship canvas) | ✅ Version 2 |
| HRS graph visualisation (full) | Version 3+ |
| Level 4 tenant-scoped governance records | Version 3+ |

### Video / Live App

| Feature | Version |
|---------|---------|
| URL video embed (YouTube, Vimeo, direct .mp4) | ✅ Version 2 |
| Broadcast scheduler (church services, events) | ✅ Version 2 |
| Live stream embed surface | ✅ Version 2 |
| VOD library (past recordings) | ✅ Version 2 |
| Ichebo Media — self-hosted video, transcoding, HLS | Version 3+ (ADR-021) |
| Live streaming engine (RTMP ingest, HLS delivery) | Version 3+ (ADR-021) |
| Offline video download for Desktop | Version 3+ (ADR-021) |
| Virtual governance sessions | Version 3+ |

### Ichebo Desktop (new — Version 3+)

| Feature | Version |
|---------|---------|
| People — member registry, levels, shepherd assignments | Version 3+ MVP |
| Activity — log attendance, service, participation | Version 3+ MVP |
| Sync — ChangeLog, Push/Pull/Resolve, conflict review | Version 3+ MVP |
| Local SQLite database (offline-first) | Version 3+ MVP |
| Go Sync Engine embedded | Version 3+ MVP |
| KGS licence key activation | Version 3+ MVP |
| Dark mode (non-optional) | Version 3+ MVP |
| Governance — view local handbook (read-only) | Version 3+ Phase 2 |
| Learn — formation pathway tracking | Version 3+ Phase 2 |
| Paraclete intelligence (local rule-based) | Version 3+ Phase 3 |
| Ichebo Media playback (offline download) | Version 3+ Phase 3 |

### Ichebo Mobile (Flutter — Version 3+)

| Feature | Version |
|---------|---------|
| Auth screens (login, register) | Version 3+ MVP |
| Home / Dashboard (Paraclete digest) | Version 3+ MVP |
| Bible (reader, notes, translation selector) | Version 3+ MVP |
| Learn (enrolments, lesson viewer, progress) | Version 3+ MVP |
| Activity (task list, habit tracking, goal progress) | Version 3+ MVP |
| Community (member directory, announcements, gatherings) | Version 3+ MVP |
| Profile (formation journey, settings) | Version 3+ MVP |
| Governance — Level 3+ read | Version 3+ MVP |
| Coordinator screens (Level 3+) | Version 3+ MVP |
| Offline read (after initial sync) | Version 3+ MVP |
| FCM push notifications | Version 3+ MVP |
| iOS | Version 3+ Phase 2 (after Android stable) |

---

## Complete Build Sequence

```
LAYER 0 — SERVER & TOOLS                    ✅ COMPLETE
LAYER 1 — DJANGO FOUNDATION                 ✅ COMPLETE
LAYER 2 — VERSION 1: MVP APPS               ✅ COMPLETE
LAYER 3 — VERSION 2: FORMATION & SHELL      ✅ COMPLETE
LAYER 4 — STABILISATION & HANDOFF           (current — pre-Version 3)
LAYER 5 — VERSION 3: ECOSYSTEM FOUNDATION   (Go engines, Sync Engine)
LAYER 6 — VERSION 3: ICHEBO DESKTOP        (Flutter Desktop, local-first)
LAYER 7 — VERSION 3: ICHEBO MOBILE         (Flutter Mobile, Android-first)
LAYER 8 — VERSION 3: ICHEBO MEDIA          (Video Engine, live streaming)
LAYER 9 — VERSION 3: ICHEBO HANDBOOK       (Standalone Handbook product)
LAYER 10 — SCALE                            (Docker, Redis, Celery, AI)
```

---

# LAYER 0 — Server & Tools ✅ COMPLETE

## Phase 0.1 — Hetzner Server Setup ✅

**What was built:** Hetzner VPS provisioned (Ubuntu 22.04), SSH key authentication, UFW firewall, non-root deploy user (ics), domain pointed to server IP, basic server hardening.

**Key file locations:**
```
/home/ics/ics/backend/          App code (git repo)
/home/ics/ics/backend/.env      Secrets (never committed)
/home/ics/ics/venv/             Python virtual environment
/home/ics/backups/              Database backups
/var/log/ics/                   Django error logs
/etc/nginx/sites-available/ics  Nginx config
/etc/systemd/system/ics.service Gunicorn systemd service
```

## Phase 0.2 — GitHub & Local Development ✅

**What was built:** GitHub repository, SSH deploy key, remote origin set, VS Code Remote-SSH confirmed working, branch structure established.

## Phase 0.3 — MinIO Object Storage ✅

**What was built:** MinIO installed on VPS, bucket `ics-media` created, Django-storages configured, MinIO proxied through Nginx at `/media/`. Used for: user avatars, governance document attachments, file records.

## Phase 0.4 — Email (Brevo) ✅

**What was built:** Brevo SMTP configured as Django email backend. Free tier (300 emails/day). Used for: certification confirmed, level advanced, tenant invitation emails.

## Phase 0.5 — Nginx + Gunicorn (production) ✅

**What was built:** Gunicorn as WSGI server (3 workers, 120s timeout), Nginx as reverse proxy with SSL (Let's Encrypt), systemd service for auto-restart, static files served by Nginx.

---

# LAYER 1 — Django Foundation ✅ COMPLETE

## Phase 1 — Auth + Tenants + HTMX Shell ✅

**What was built:** Custom User model (email as username, competence_level, status, preferences JSONField), UserProfile, UserPermission (role + level per tenant), Tenant model with materialised path hierarchy, Django session auth for web, DRF token auth for mobile, base.html with mobile nav shell, HTMX configuration, mobile-first CSS design system.

## Phase 2 — Records Engine ✅

**What was built:** Record model (single table, record_family / record_class / record_type discriminator), Relationship model (typed relationship types, bible_verse_id, metadata JSONField), full DRF CRUD, Django template views + HTMX partials.

## Phase 3 — Activity Engine ✅

**What was built:** Activity model (all types), ActivityLog (Django signal on every status transition), full DRF CRUD with filters, Django template views + HTMX partials.

---

# LAYER 2 — Version 1: MVP Apps ✅ COMPLETE

## Phase 5.1 — Bible App ✅

**What was built:** Scripture reader (KJV, ASV, WEB), flat JSON scripture data loaded by management command, personal and tenant-scoped annotations using Records Engine (record_family: "bible", record_type: "bible_note"), Handbook linkages (Level 5), three-panel mobile-first HTMX UI, translation switcher.

**Amendment 2026-06-09 (mobile reader) — approved, not yet built:** A dedicated mobile Bible reader was specified for `/bible/m/<book_code>/<chapter>/` — a standalone full-screen page (no workspace shell) with sticky topbar, chapter content, bottom nav strip, navigator/annotation/display-settings sheets, verse toolbar, and localStorage highlight persistence. **Status as of 2026-06-18 audit: not present in code** — `bible/urls.py` has no `/m/` route, and no `reader_mobile.html` template exists. Desktop reader at `/bible/<book_code>/<chapter>/` is unaffected either way. This is open implementation work, not yet a completed phase.

**Commit:** `feat: bible app`

## Phase 5.2 — Learn App ✅

**What was built:** CertificationConfirmation model, full DRF endpoints for programmes/courses/lessons/certifications, programme catalogue (F1), course browser (F2), enrolment with prerequisite check (F3), progress tracking (F4), lesson viewer (F5), assessments — quiz and assignment (F6), certification flow with steward confirm and level increment (F7), content authorship for Level 4+ (F8), Handbook review queue for Level 5 (F9), pathway banner (F10), My Learning Dashboard (F11), auto-certification signal on 100% programme progress.

**Commit:** `feat: learn app — complete`

## Phase 5.3 — Activity App UI ✅

**What was built:** My Activities surface (task, habit, goal, skill, reminder — flat structure), Ministry surface (campaign, project, task, event — two-level nesting), Assigned-to-me queue, Calendar dated list view, HTMX mark-complete, programme cards (Learn enrolments read-only).

**Commit:** `feat: activity app UI — my activities + ministry surfaces`

## Phase 5.4 — Community App ✅

**What was built:** Member directory, tenant profile card, announcements (read + create Level 3+), gathering schedule (read + create Level 3+), gathering dual-write (Record + Activity, atomic), community management surface (Level 3+), role assignment, shepherd assignment, service order assignment, membership request queue.

**Commit:** `feat: community app`

## Phase 5.5 — Governance App ✅

**What was built:** Reference Library (Level 3+ read, Level 5 write), Mandate Branch (Level 4+ read, Level 5 write), Keys Library (personal, Level 3+), record lifecycle (draft → active → locked → superseded), linked records panel (flat list), HRS property attributes in custom_fields, governance record authority matrix.

**Commit:** `feat: governance app`

## Phase 5.6 — Profile + Settings ✅

**What was built:** Profile view (display name, avatar, formation journey card, level badge), DB-persisted preferences (theme, language, timezone), Bible translation preference, profile registration fields (full_name, address, country, id_number encrypted, age, gender, occupation, education, born_again).

**Commit:** `feat: profile + settings`

## Phase 5.7 — Notifications Stub ✅

**What was built:** Notification model, nav entry, unread badge polling, empty list state. Full trigger system built in Version 2 (Phase V2.6).

**Commit:** `feat: notifications stub`

## Phase 6.1 — Paraclete Service ✅

**What was built:** ParacleteDigest Python dataclass, four data sources (Activity, ActivityLog, Record, UserProfile/UserPermission), rule-based MVP (pure Python, no LLM), ParacletePrompt model with 14-day least-active KGS pathway logic, DRF endpoints with Django filesystem cache (5-min TTL), widget-to-field Dashboard map gated by competence level.

**Commit:** `feat: paraclete service`

## Phase 6.2 — Dashboard ✅

**What was built:** Dashboard (Command Centre) — Paraclete digest hero, Divine Intel section, stat cards, quick links, activity widget, prayer count widget. Role-aware widgets (ministry section Level 3+ only).

**Commit:** `feat: dashboard`

## Phase 7 — Production Hardening ✅

**What was built:** SSL active (Let's Encrypt), static files served by Nginx, error logging to /var/log/ics/, Django admin accessible, Gunicorn restarts on reboot via systemd, security headers, smoke test passing.

**Commit:** `chore: production hardening — MVP complete`

---

# LAYER 3 — Version 2: Formation & Shell ✅ COMPLETE

## Stabilisation Phases ✅

### Phase S.1 — Email, MinIO, Backups ✅

**What was built:** Brevo email integration (certification confirmed, level advanced, tenant invitation), MinIO bucket ics-media with Django-storages, automated database backup scripts.

### Phase S.2 — Code Alignment Audit ✅

**What was built:** Full audit of code against data contract v9/v10. Breaking changes resolved. Journal family types corrected to MVP reality (prayer, spirit, dream, dar, note). Relationship.strength retained as enum. All apps aligned to HTMX architecture.

---

## The Apostolic Command Shell ✅ COMPLETE (ADR-012)

**What was built:** Four-column grid workspace (Primary Sidebar 72px, Context Bar 240px, Stage flexible, Options Bar 300px), workspace_shell.html as root desktop template, dual-shell switching (Stage Mode / Mobile Mode), DESIGN.md design system applied throughout, Playfair Display + Inter typography, Ink + Stone + Red colour system, all app templates updated with both {% block ws_content %} and {% block content %} blocks.

**Reference:** ADR-012, ADR-013, ADR-014, ADR-015, DESIGN.md, design-preview.html

**Amendment 2026-06-09 (ADR-015) — approved, partially built:** Two Mobile Mode rendering patterns are now recognised: Standard Mobile Mode (`{% block content %}`, unchanged) and Standalone Mobile Mode (dedicated `/m/` URL with a minimal base template, for full-screen experiences like the Bible reader). A `{% block mobile_fullscreen %}` slot was specified for `workspace_shell.html` to support this. **Status as of 2026-06-18 audit: the `mobile_fullscreen` block is not present in the current `workspace_shell.html`.** The Activity Hub HTMX tab-dispatch pattern (Decision 1 of the same amendment, consolidating Personal/Ministry/Calendar into one mobile shell URL) is similarly specified but not confirmed built as of this audit. See the web-ui-mobile-amendment doc for full pattern reference. Also amends ADR-012's sidebar order — see ADR-022 in the ADR table, which supersedes the navigation structure further.

---

## Version 2 Phases ✅ COMPLETE

### Phase V2.1 — Learn App Foundation ✅

**What was built:** Five qualification programmes seeded (New Life → Architect's), eight KGS pathways mapped per programme, Induction Training course seeded (four lessons inside New Life Programme), seed_programmes and seed_induction_course management commands, URL video embed utility (core/utils/video.py), video player partial.

**Reference:** ADR-011, VERSION_2_PLANNING

**Commit:** `feat: learn app foundation — programmes, induction course, video embed`

### Phase V2.2 — Induction System ✅

**What was built:** Induction Tenant (tier: "induction") created as system singleton, User model extended (induction_enrolled_at, induction_completed_at, induction_pathway), auto-enrolment on registration, Reconditioning and Beginners pathway differentiation, Induction Dashboard template, steward induction review queue, placement confirmation (extends certifications/confirm/ with context == "induction_completion"), Geographic tenant matching.

**Commits:**
```
feat: induction tenant — system singleton, tier model, seed command
feat: induction enrolment — auto-enrol on registration, pathway selection
feat: induction completion — steward review queue, placement confirmation
```

### Phase V2.3 — Formation UI + App Drawer Gating ✅

**What was built:** Formation Dashboard (level badge, active programme, next level, progress), App drawer gating by competence_level (apps unlock as level advances), FCM token field added to User model, Relationship.relationship_type: "community_ref" added.

**Commit:** `feat: formation dashboard + drawer gating`

### Phase V2.4 — Agency Tenants + Service Orders ✅

**What was built:** Prime Tenancy verified/seeded, six Agency Tenants seeded (six KGS Service Domains), ServiceOrder model (24 orders seeded as constitutional records), Formation & Teaching Authority Rule enforced in code (Executive Privilege fallback), management commands: seed_agency_tenants, seed_service_orders.

**Commit:**
```
feat: seed agency tenants — 6 service domain tenants under Prime
feat: seed service orders — 24 constitutional orders, ServiceOrder model
```

### Phase V2.5 — Steward Dashboard + Tenant Self-Service ✅

**What was built:** Tenant model extended (coordinator_user, community_theme, area_of_operation, is_agency flag), TenantInvitation model with accept logic (Level 1+ enforcement), Steward Dashboard routes (/steward/), tenant creation form (Level 3+), member management (invite, assign role, assign service order, assign shepherd, remove), multi-tenant content scoping.

**Commit:**
```
feat: tenant model extensions + TenantInvitation model
feat: steward dashboard — tenant creation, member management, invitation flow
feat: multi-tenant content scoping
```

### Phase V2.6 — Notifications (Full) ✅

**What was built:** Notification model (full), Django signals for all trigger points (announcement, task assigned, certification confirmed, induction placement confirmed, record locked, tenant invitation, member added/removed), HTMX polling (60s interval), Brevo email for certification and invitation events, FCM push via notifications/fcm.py.

**Commit:** `feat: notifications — full model, triggers, delivery`

### Phase V2.7 — Video / Live App ✅

**What was built:** video_live/ Django app, Broadcast Scheduler (Activity event + Gathering dual-write), Live Stream Surface (HTMX refresh every 60s, now-playing detection), VOD Library (past recordings archive), Programme Grid (7-day schedule), individual event player (YouTube/Vimeo iframe + direct .mp4 video tag).

**Commit:** `feat: video live app — broadcast scheduler + live stream + VOD`

---

## Flutter Mobile App — Phase V2.M

**Status:** In development — separate repository (ichebo-mobile). Android-first. Consumes existing DRF API. Delta Sync endpoint (GET /api/sync/changes/) active.

**Entry requirement:** V2.2 complete (DRF API stable, user levels established, induction system live). Runs in parallel with V2.3+.

**Architecture:** Flutter for Android (iOS Version 3+). DRF API is the backend. No HTMX on mobile. Separate repository. FCM push via Firebase.

**Core screens to build (in order):**
1. Auth screens (login, register, forgot password)
2. Home / Dashboard (Paraclete digest)
3. Bible (translation selector, reader, personal notes)
4. Learn (enrolments, lesson viewer, video embed, mark complete, certification status)
5. Activity (task list, habit tracking, goal progress, create, mark complete)
6. Community (member directory, announcement feed, gathering schedule)
7. Profile (formation journey card, level badge, active programme, settings)
8. Governance — Level 3+ read (Reference Library, record detail)
9. Coordinator screens — Level 3+ (community management, member roster, certification queue, induction review queue)

**Exit criteria:** All Level 0–3 screens functional on Android. Offline read works after initial sync. Push notifications received. Auth token persists across restarts.

---

# LAYER 4 — Stabilisation & Handoff (Current)

## Phase H.1 — Documentation Alignment

**Goal:** Align all reference documents with the Version 2 completed build. Produce canonical versions of all key documents.

**What this produces:**
- Master Roadmap v7 (this document) ✅
- Data Contract v11 (canonical) ✅
- ADR set ADR-012 through ADR-021 ✅
- Ecosystem Architecture v0.1 ✅
- DESIGN.md (locked) ✅

**Exit criteria:** All reference documents reflect the completed Version 2 build and the ecosystem architecture direction.

## Phase H.2 — Version 2 in Real-World Use

**Goal:** Get the platform in front of real communities. Collect real usage data. Validate KGS implementation in practice.

**Entry requirement:** Phase H.1 complete. Flutter Mobile MVP functional on Android.

**Exit criteria:** At least one Sceptre Community operating on the platform. Real formation journeys in progress. Real governance records in the Handbook.

---

# LAYER 5 — Version 3: Ecosystem Foundation ✅ COMPLETE

**Entry requirement:** Version 2 in real-world use (Phase H.2). At least one community operating.

## Phase E.1 — UUID Schema Migration ✅

**What was built:** UUID PKs applied across all platform models. `DEFAULT_AUTO_FIELD` set to `BigAutoField` with explicit UUID overrides. Custom `check_uuid_primary_keys` system check in `core/apps.py` enforces UUID PKs on all first-party models at startup. `BibleBook` migrated via truncate-and-reload strategy (`bible/migrations/0003_biblebook_uuid_pk.py`). `ParacletePrompt` migrated via two-step column swap (`paraclete/migrations/0002_paracleteprompt_uuid_pk.py`).

**Commit:** `chore: uuid primary key migration — all models`

## Phase E.2 — Soft Delete Pattern ✅

**What was built:** `SoftDeleteMixin` and `SoftDeleteManager` added to `core/managers.py`. Applied across: User, UserProfile, Activity, MembershipRequest, CertificationConfirmation, Notification, Record, Tenant, UserPermission, TenantInvitation, DesktopLicence. New migrations for each affected model. Default querysets filter `deleted_at IS NULL`.

**Commit:** `Implement soft delete functionality across multiple models`

## Phase E.3 — Go Engine Foundation ✅

**What was built:** Five Go engines in `ichebo-sync/engines/`, each independently compilable with tests:
- `engines/records/` — Records Engine
- `engines/activity/` — Activity Engine
- `engines/relationships/` — Relationships Engine
- `engines/bible/` — Bible Engine
- `engines/calendar/` — Calendar Engine

Shared engine interface in `engines/engine/engine.go`.

**Commit:** (included in soft delete / sync engine commits)

## Phase E.4 — Sync Engine ✅

**What was built:** Full Sync Engine in `ichebo-sync/` as standalone Go binary (`cmd/syncd/`). Packages: `pkg/changelog`, `pkg/device` (UUID identity), `pkg/push`, `pkg/pull`, `pkg/resolve` (conflict resolution), `pkg/queue` (ConflictQueue), `pkg/store`, `pkg/transport`, `pkg/status`, `pkg/clock`. FFI bridge in `ffi/bridge.go` + `ffi/main.go` for Flutter Desktop integration.

**Reference:** ADR-018

**Commit:** `feat: sync-engine v0.1 — changelog, push, pull, resolve`

---

# LAYER 6 — Version 3: Ichebo Desktop ✅ COMPLETE

**Entry requirement:** Layer 5 complete. Sync Engine tested and proven.

**Reference:** ADR-017

## Phase D.1 — Flutter Desktop Project ✅

**What was built:** `ichebo-desktop/` Flutter project targeting Windows/macOS/Linux. Core navigation shell in `lib/shell/`. Design system tokens in Dart. Dark mode (non-optional). Features scaffold: `lib/features/` — home, people, activity, governance, settings, sync, video, wizard.

**Commit:** `feat(desktop): D.1 — Ichebo Desktop shell scaffold`

## Phase D.2 — Local Data Layer ✅

**What was built:** SQLite integration (WAL mode) in `lib/core/database/`. Go Sync Engine FFI bridge wired via `lib/core/services/`. All local writes append to ChangeLog. Sync state management in `lib/sync/`.

**Commit:** `feat(desktop): D.2 — Local data layer + FFI bridge`

## Phase D.3 — People Surface ✅

**What was built:** Member registry in `lib/features/people/`. Competence levels, shepherd assignments. Full offline operation via local SQLite.

## Phase D.4 — Activity Surface ✅

**What was built:** Activity logging in `lib/features/activity/`. Attendance, service, participation tracking. Flutter state management (Riverpod).

## Phase D.5 — Sync Surface ✅

**What was built:** Sync status and state in `lib/sync/sync_engine.dart` + `lib/sync/sync_state.dart`. Sync feature surface in `lib/features/sync/`. Background sync goroutine via FFI bridge.

## Phase D.6 — KGS Onboarding ✅

**What was built:** `DesktopLicence` model and validation endpoint on the Django backend (`feat(licences)`). Activation wizard in `lib/features/wizard/`. Initial sync payload on activation.

**Commit:** `feat(wizard): implement activation and initial sync steps`

---

# LAYER 7 — Version 3: Ichebo Mobile (Flutter) ✅ COMPLETE

**Entry requirement:** Layer 5 complete (Go engines available). Can run in parallel with Layer 6.

**Note:** This is the full Flutter native mobile app — distinct from the Django Mobile Mode (which remains as web fallback). The Flutter app is the primary mobile surface long-term.

**Reference:** ADR-001 (amended), ADR-015

## Phase M.1 — App Shell + Auth ✅

**What was built:** `ichebo-mobile-v2/` Flutter project (Android-first). Core navigation shell, bottom nav, app shell. Auth screens (login, register) wired to DRF API. Token persistence across restarts.

**Commit:** `feat(mobile): M.1 — Layer 7 scaffold + auth + bottom nav`

## Phase M.2 — Local Data Layer + FFI Bridge ✅

**What was built:** Local data layer in `lib/core/`. Go engine FFI bridge. Riverpod state management wired throughout. Profile, settings, sync screens refactored to Riverpod.

**Commit:** `feat(mobile): M.2 — local data layer + FFI bridge`

## Phase M.3 — Core Screens ✅

**What was built:** All Level 0–3 screens functional on Android. Features in `lib/features/`: auth, bible, community, coordinator, governance, home, learn, profile, activity. Home and Community screens completed.

**Commit:** `feat(mobile): M.3 — Home + Community screens`

---

# LAYER 8 — Version 3: Ichebo Media ✅ COMPLETE

**Entry requirement:** Layer 5 complete. Video/Live App URL approach proven insufficient or network video hosting confirmed as direction.

**Reference:** ADR-021

## Phase M.1 — Video Engine ✅

**What was built:** `ichebo-media/` Go service (`cmd/mediad/`). Packages: `pkg/transcode/` (FFmpeg pipeline, queue, worker, profiles, progress tracking), `pkg/upload/` (chunked upload handler), `pkg/storage/` (Hetzner Object Storage / S3-compatible), `pkg/hls/` (HLS manifest generation), `pkg/config/`, `pkg/health/`. Django `media/` app with upload endpoint wired to the Go engine via `MEDIA_ENGINE_URL`.

**Commit:** `feat(media): Layer 8 scaffold — Video Engine, Django media app, Flutter HLS player`

## Phase M.2 — Live Streaming ✅

**What was built:** `pkg/stream/` — RTMP ingest session management with tests. MediaMTX integration via `deploy/mediamtx/mediamtx.service` systemd unit. `pkg/webhook/` for stream lifecycle events (start, end, archive).

## Phase M.3 — Learning Video ✅

**What was built:** HLS player integrated into `ichebo-mobile-v2` (Flutter). Video library and player screens in `ichebo-desktop/lib/features/video/`. Video progress tracking wired to Activity Engine. S3 storage backend functional (`feat(storage): implement S3 storage functionality and related tests`).

**Commit:** `feat(video): implement video library, player, and progress tracking`

---

# LAYER 9 — Version 3: Ichebo Handbook ✅ COMPLETE

**Entry requirement:** Layer 5 complete. The Desk (ADR-014) proven design pattern. Handbook-as-tenant migration planned.

**Reference:** ADR-020, DOC F

## Phase K.1 — Handbook Product Foundation ✅

**What was built:** Standalone `handbook` Django app. `HandbookRecord` (UUID PK, three branches, four status lifecycle, version chain), `HandbookRelationship` (HRS + scripture links in one model), `HandbookAccess` (reader/author/editor roles, global scope). Full DRF API: list/create, detail/patch, publish, lock, new-version, history. Migration `0001_initial` applied.

**Superseded by ADR-022 (2026-06-09):** `HandbookRecord` and `HandbookRelationship` are retired. Handbook is now a UI-only app over `records.Record` (`record_family='governance'`) — no owned content models, same pattern as Governance and Community. `HandbookAccess` is retained as the permission-gate model for the authorship workspace. The Desk editor (formerly its own sidebar icon) is relocated into Handbook. Migration `0002_retire_content_models.py` applied. See ADR-022 for full rationale and the Governance/Handbook/Records separation of concerns it establishes.

**Commit:** `feat(handbook): K.1 — Handbook product foundation`

## Phase K.2 — Workspace UI + The Desk ✅

**What was built:** Four-column Apostolic Command Shell for the Handbook — `home.html` (branch navigator, record list grouped by type), `record.html` (four-tab Properties Sidecar: Props/HRS/Scripture/History, `HBDesk` JS object, auto-save on keystroke), `access.html` (editor-only access management). Sidebar nav entry added to `workspace_shell.html`. Template URLs registered at `/handbook/`.

**Superseded by ADR-022 (2026-06-09):** The Desk (`governance/desk_views.py`) is relocated from its own sidebar icon into the Handbook surface. Handbook views now query `records.Record` directly rather than `HandbookRecord`. The `edit_note` Desk sidebar icon is removed; Handbook (`auto_stories`) becomes the single entry point for governance authorship, moving to sidebar position 2.

**Commit:** `feat(handbook): K.2 — Workspace UI and The Desk`

## Phase K.3 — HRS Relationships ✅

**What was built:** `HandbookRelationship` model with seven relationship types (part_of, derived_from, aligns_with, authorised_by, references, has_symbol, matches_pattern), direction field, six HRS attribute fields on `HandbookRecord` (complexity, relationship_position, position, direction, speed, emotional_tone). `HandbookRelationshipListCreateView` + `HandbookRelationshipDeleteView`. HRS tab in The Desk with relationship list and add form.

## Phase K.4 — Scripture Linking ✅

**What was built:** `HandbookRelationship.bible_verse` FK to `bible.BibleVerse`. Scripture tab in The Desk with verse search and link/unlink workflow. `clean()` enforces exactly one of `to_record`/`bible_verse` per relationship.

## Phase K.5 — Publish Feed ✅

**What was built:** `GET /api/handbook/publish-feed/?since={timestamp}` — returns active/locked non-key records modified since timestamp, 100-record window, ordered by `updated_at`. Used by Sync Engine delta pull.

## Phase K.6 — Keys Library Privacy ✅

**What was built:** Keys Library isolation invariant — key records are personal (owner-only), no `HandbookAccess` required to create/read/edit, never visible to other users including editors, blocked from publish and lock lifecycle, excluded from the publish feed. Enforced via `_is_key_record()`, `_assert_can_access_record()`, `_assert_can_write_record()` helpers across all API views and workspace views. 13 passing tests covering all privacy invariants.

**Commit:** `feat(handbook): K.6 — Keys Library privacy invariant`

---

# LAYER 10 — Scale

**Entry requirement:** Do not build any of these until Version 3 is in real-world use and a specific bottleneck has been identified. Layer 10 is demand-driven, not time-driven.

## Phase L10.1 — Redis + Celery ✅ COMPLETE

**What was built:** Full async task queue infrastructure. Redis as broker (DB 0) and Django cache backend (DB 1, replaces FileBasedCache). Celery 5.3.6 with django-celery-beat 2.6.0. `ics_project/celery.py` entry point, `ics_project/__init__.py` wired. `notifications/tasks.py` — `send_notification_email` (async Brevo SMTP, 3 retries) + `send_fcm_push` (async FCM, 3 retries — FCM wired for the first time). `paraclete/tasks.py` — `refresh_paraclete_digest` + `refresh_all_active_digests` (scheduled every 10 minutes via CELERY_BEAT_SCHEDULE). All notification email and FCM calls now off the request thread. Paraclete digest pre-computed on schedule, cache TTL bumped to 600s. `deploy/ics-celery.service` and `deploy/ics-celery-beat.service` systemd units.

**ADR-008 lifted:** Celery deferred until Version 3 in real-world use. That gate is passed.

**Commit:** `feat(infra): L10.1 — Redis + Celery async task queue`

## Phase L10.2 — Docker Compose ⏳

**Goal:** Containerise the full stack (web, db, redis, celery-worker, celery-beat, nginx) for reproducible deployment and easier developer onboarding. Replaces the manual Nginx + Gunicorn + systemd setup.

**Entry requirement:** Real-world production use proven stable. Actual need for easier deployment or horizontal scaling confirmed.

**ADR-009 lifts** when this phase begins.

## Phase L10.3 — Django Channels + WebSockets ⏳

**Goal:** Replace HTMX 60-second notification polling with instant WebSocket delivery. Unlock real-time notification push, live stream status updates, and future community chat.

**Entry requirement:** L10.1 complete (Redis already running as channel layer backend). Polling identified as a felt user problem — i.e., real users on the platform noticing the 60-second lag.

## Phase L10.4 — Paraclete AI (LLM) ⏳

**Goal:** LLM-generated formation insights via Celery async tasks. Rule-based fallback retained. New ADR-022 required before implementation (LLM provider, data boundary rules, cost management).

**Entry requirement:** L10.1 complete. Real usage data showing formation patterns. ADR-022 written and approved.

**ADR-010 lifts** when this phase begins.

## Phase L10.5 — iOS (Flutter) ⏳

**Goal:** iOS build of the Flutter mobile app submitted to App Store.

**Entry requirement:** Android app stable in production. Mac with Xcode available. Apple Developer account ($99/year) active.

---

## Deferred Items — Complete Reference

### Platform-wide
- Full RecordPermission table (fine-grained per-user permissions)
- CustomFieldSchema formal validation system
- Donations feature
- In-service Display app
- API versioning (/api/v1/) — needed before mobile production launch
- User-defined custom journal record types

### Bible App
- Reading plans, verse highlights, scripture full-text search
- Licensed translations (NIV/ESV/NLT — require publisher licensing agreements)
- African language translations, audio Bible, cross-reference chains

### Learn App
- Rich text editor for authorship (TipTap or similar)
- Quiz auto-grading, assignment peer review
- Learning analytics dashboard, offline lesson caching

### Activity App
- Full calendar grid UI, habit streak visualisation
- Ministry analytics, cross-tenant campaign assignment
- RRULE custom recurrence builder

### Community App
- Pastoral notes (privacy design required)
- Attendance tracking (privacy-sensitive)
- Community analytics dashboard, collective-level gathering visibility
- PastoralAssignment model (upgrade from UserPermission.metadata.shepherd_id)
- GinIndex on UserPermission.metadata

### Governance App
- Full HRS graph visualisation
- Level 4 tenant-scoped governance records
- calendar record type (registered in governance family — Phase 2)

### Notifications
- Real-time delivery (Django Channels + WebSockets) — L10.3
- Push notifications to iOS — when iOS app is built (L10.5)

### Paraclete
- AI-assisted pattern detection (LLM) — L10.4 (requires ADR-022)
- Link suggestion engine — L10.4
- Prophetic prompt generation (LLM) — L10.4

### Infrastructure
- Docker Compose — L10.2
- iOS app — L10.5

### Ichebo Ecosystem
- Ichebo Desktop — ✅ Complete (Layer 6)
- Ichebo Media — ✅ Complete (Layer 8)
- Ichebo Handbook — ✅ Complete (Layer 9)

---

## Open Decisions

| Decision | Status |
|----------|--------|
| Induction programme lesson content | ⏳ Open — seeded as structure; lesson content authored by Level 4+ after platform is live |
| Induction duration (configurable vs fixed 12-week) | ⏳ Open — default is programme completion; configurable duration deferred to Version 3 |
| Ichebo Desktop pricing model | ⏳ Open — per-installation vs per-seat vs network licence |
| Go engine specification format | ⏳ Open — each engine needs a language-agnostic spec document before Go implementation begins |

---

## Phase Summary — All Phases

| Phase | Layer | What it builds | Status |
|-------|-------|----------------|--------|
| 0.1–0.5 | 0 | Server, GitHub, MinIO, Brevo, Nginx/Gunicorn/SSL | ✅ Complete |
| 1 | 1 | Auth, Tenants, HTMX Shell | ✅ Complete |
| 2 | 1 | Records Engine | ✅ Complete |
| 3 | 1 | Activity Engine | ✅ Complete |
| 5.1 | 2 | Bible App | ✅ Complete |
| 5.2 | 2 | Learn App (full F1–F11) | ✅ Complete |
| 5.3 | 2 | Activity App UI | ✅ Complete |
| 5.4 | 2 | Community App | ✅ Complete |
| 5.5 | 2 | Governance App (full lifecycle + The Desk) | ✅ Complete |
| 5.6 | 2 | Profile + Settings | ✅ Complete |
| 5.7 | 2 | Notifications Stub | ✅ Complete |
| 6.1 | 2 | Paraclete Service | ✅ Complete |
| 6.2 | 2 | Dashboard | ✅ Complete |
| 7 | 2 | Production Hardening | ✅ Complete |
| S.1 | 3 | Stabilisation — Email, MinIO, Backups | ✅ Complete |
| S.2 | 3 | Code Alignment Audit | ✅ Complete |
| Shell | 3 | Apostolic Command Shell (four-column grid, all templates) | ✅ Complete |
| V2.1 | 3 | Learn: Programmes + Induction Course + Video Embed | ✅ Complete |
| V2.2 | 3 | Induction System | ✅ Complete |
| V2.3 | 3 | Formation UI + App Drawer Gating | ✅ Complete |
| V2.4 | 3 | Agency Tenants + Service Orders | ✅ Complete |
| V2.5 | 3 | Steward Dashboard + Tenant Self-Service | ✅ Complete |
| V2.6 | 3 | Notifications (Full) | ✅ Complete |
| V2.7 | 3 | Video / Live App | ✅ Complete |
| V2.M | 3 | Flutter Mobile App (Android) | 🔄 In progress |
| H.1 | 4 | Documentation Alignment | ✅ Complete |
| H.2 | 4 | Version 2 in Real-World Use | ⏳ Pending |
| E.1 | 5 | UUID Schema Migration — all models | ✅ Complete |
| E.2 | 5 | Soft Delete Pattern — SoftDeleteMixin, all models | ✅ Complete |
| E.3 | 5 | Go Engine Foundation — Records, Activity, Relationships, Bible, Calendar | ✅ Complete |
| E.4 | 5 | Sync Engine — ChangeLog, Push, Pull, Resolve, ConflictQueue, FFI | ✅ Complete |
| D.1 | 6 | Desktop shell scaffold — Flutter project, nav shell, dark mode | ✅ Complete |
| D.2 | 6 | Local data layer + FFI bridge | ✅ Complete |
| D.3 | 6 | People surface — member registry, levels, shepherd assignments | ✅ Complete |
| D.4 | 6 | Activity surface — attendance, service, participation | ✅ Complete |
| D.5 | 6 | Sync surface — sync state, background goroutine | ✅ Complete |
| D.6 | 6 | KGS Onboarding — licence model, activation wizard, initial sync | ✅ Complete |
| M.1 (mobile) | 7 | Mobile shell + auth screens | ✅ Complete |
| M.2 (mobile) | 7 | Mobile local data layer + FFI bridge | ✅ Complete |
| M.3 (mobile) | 7 | Mobile core screens — all Level 0–3 features | ✅ Complete |
| M.1 (media) | 8 | Video Engine — Go + FFmpeg + upload + HLS + Hetzner Storage | ✅ Complete |
| M.2 (media) | 8 | Live Streaming — RTMP ingest, HLS delivery, MediaMTX | ✅ Complete |
| M.3 (media) | 8 | Learning Video — HLS player, progress tracking, S3 storage | ✅ Complete |
| K.1 | 9 | Handbook Foundation — models, API, migrations | ✅ Complete |
| K.2 | 9 | Handbook Workspace UI — The Desk, four-column shell | ✅ Complete |
| K.3 | 9 | HRS Relationships — seven types, six attribute fields | ✅ Complete |
| K.4 | 9 | Scripture Linking — BibleVerse FK, Scripture tab | ✅ Complete |
| K.5 | 9 | Publish Feed — sync delta endpoint, excludes keys | ✅ Complete |
| K.6 | 9 | Keys Library Privacy — owner-only, 13 passing tests | ✅ Complete |
| L10.1 | 10 | Redis + Celery — async email, FCM, Paraclete schedule | ✅ Complete |
| L10.2 | 10 | Docker Compose | ⏳ Pending |
| L10.3 | 10 | Django Channels + WebSockets | ⏳ Pending |
| L10.4 | 10 | Paraclete AI (LLM) | ⏳ Pending |
| L10.5 | 10 | iOS (Flutter) | ⏳ Pending |

---

## Branch Structure

```
main                            ← production (always deployable)
├─ mvp                          ← MVP complete (6c43ce9) [frozen]
├─ version-2                    ← Version 2 complete [frozen]
│   ├─ v2-shell                 ← Apostolic Command Shell
│   ├─ v2-learn-formation       ← V2.1 programmes + induction course
│   ├─ v2-induction             ← V2.2 induction system
│   ├─ v2-formation-ui          ← V2.3 dashboard + drawer
│   ├─ v2-agency-seed           ← V2.4 agency tenants + service orders
│   ├─ v2-steward-dashboard     ← V2.5 steward dashboard + tenant self-service
│   ├─ v2-notifications         ← V2.6 full notifications
│   └─ v2-video                 ← V2.7 live video app
└─ version-3                    ← active ecosystem development
   ├─ v3-uuid-migration         ← E.1 UUID schema
   ├─ v3-soft-delete            ← E.2 soft deletes
   ├─ v3-go-engines             ← E.3 Go foundation engines
   └─ v3-sync-engine            ← E.4 Sync Engine

ichebo-mobile (separate repo)   ← Flutter Android app
   └─ main                      ← Android production

ichebo-desktop (separate repo)  ← Flutter Desktop app (future)
   └─ main                      ← Desktop production (future)
```

---

## Key Reference Documents

| Document | What it covers |
|----------|---------------|
| `master-roadmap-canonical-2026-05-13.md` | This document — the definitive reference |
| `data-contract-v11-canonical-2026-05-13.md` | Complete data contract — all schemas and rules |
| `2026-05-13-ichebo-adrs-012-021.docx` | ADRs 012–021 — all architecture decisions from this session |
| `2026-04-25-ichebo-adr-version-2.md` | ADRs 001–011 — architecture decisions from Version 2 |
| `2026-05-13-ichebo-ecosystem-architecture_v0.1.docx` | Ecosystem architecture — strategic vision |
| `DESIGN.md` | Design system authority — locked |
| `design-preview.html` | Design system visual reference — locked |
| `kingdom_governance_system.md` | KGS framework — domain authority |
| `2026-04-07-ics-learn-app-system-design_v2.md` | Learn App authoritative spec |
| `2026-04-08-ics-activity-app-system-design.md` | Activity App authoritative spec |
| `2026-04-08-ics-community-app-system-design.md` | Community App authoritative spec |
| `2026-04-10-ics-governance-app-system-design.docx` | Governance App authoritative spec |
| `2026-04-10-ics-paraclete-service-system-design.docx` | Paraclete authoritative spec |
| `2026-04-12-ics-production-engineering-guide.md` | Server operations reference |
