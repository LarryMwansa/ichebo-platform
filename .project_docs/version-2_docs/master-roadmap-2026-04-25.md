# Ichebo Platform — Master Build Roadmap
**Version:** v5 — 2026-04-25
**Status:** Approved — Definitive Reference
**Author:** Chizola (domain); Claude (technical specification)

> This is the single authoritative roadmap for the entire Ichebo platform — from a blank Hetzner server to a fully operational, multi-tenant, mobile-capable formation platform. It covers every phase, every app, every technology decision, and every deferred item. No other roadmap supersedes this document.

---

## How to Read This Document

Every phase has four things:
- **What it builds** — the specific features and files
- **Entry requirement** — what must be complete before this phase starts
- **Exit criteria** — how you know the phase is done
- **Commit** — the git commit message when the phase closes

Phases are numbered. Within a phase, tasks are lettered. Do not skip phases. Do not start a task before its entry requirement is met. This order exists because each phase depends on the one before it — building out of order creates problems that are expensive to fix.

---

## Platform Overview

**What Ichebo is:** A multitenancy web platform and mobile app for Christian organisations to manage governance, discipleship, and ministry operations — the digital twin of the Kingdom Governance System (KGS) framework.

**Two client surfaces:**
- **Web app** (Django templates + HTMX) — the operator surface for desktop/tablet. Stewards, Coordinators, Level 4+, Level 5. Complex workflows: content authorship, governance, community management, certification review.
- **Mobile app** (Flutter + DRF API) — the primary surface for all users on their phones. Level 0 inductees through Level 5 architects. Everyday use: lessons, activities, community, Bible reading.

**Backend:** Django 4.2 LTS + Django REST Framework + PostgreSQL. One backend, two clients. The DRF API serves both.

**Infrastructure:** Hetzner VPS (Ubuntu 22.04), Nginx, Gunicorn, systemd. No Docker in Version 1 or 2.

---

## Architecture Decisions (Locked)

These decisions are final. They cannot be changed without producing a new ADR. Do not re-open them.

| Decision | What it means |
|----------|--------------|
| Django 4.2 LTS | Long-term support until April 2026+ — stable, well-documented |
| Single records table with discriminator | All content types use one `records` table with `record_family` / `record_type` fields. No new model tables for content types. |
| DRF retained for mobile | `/api/` endpoints are the mobile API. Template views call ORM directly. |
| Django templates + HTMX for web | No React, Vue, or JS framework on the web. HTMX handles dynamic interactions. |
| Flutter for mobile | Android-first. iOS later. Consumes DRF API. No HTMX on mobile. |
| No Celery or Redis until Version 3 | All automation uses Django signals (synchronous) or cron-scheduled management commands. |
| No Docker until Version 3 | Nginx + Gunicorn + systemd is the production stack. |
| `competence_level` one write path | Only `POST /api/learn/certifications/{id}/confirm/` may increment `competence_level`. Nothing else. |
| Paraclete is rule-based in MVP | Pure Python. No LLM calls. Reads ORM, returns digest. Writes nothing. |
| Email via Brevo | Free tier (300 emails/day). SMTP integration via Django email backend. |

---

## The Six Platform Apps — Full Feature Inventory

This table shows the complete feature scope for every app across all versions. Use it to understand what is in scope for each phase and what is explicitly deferred.

### Bible App
| Feature | Version |
|---------|---------|
| Scripture reader (KJV, ASV, WEB) | ✅ MVP |
| Personal annotations (notes on verses) | ✅ MVP |
| Tenant-scoped annotations | ✅ MVP |
| Handbook linkages (Level 5) | ✅ MVP |
| Reading plans | Version 2 |
| Verse highlights | Version 2 |
| Scripture full-text search | Version 2 |
| Paraclete "you haven't read today" | Version 2 |
| Licensed translations (NIV, ESV, NLT) | Version 3+ (requires publishing agreements) |
| African language translations | Version 3+ |
| Audio Bible | Version 3+ |
| Cross-reference chains | Version 3+ |

### Learn App
| Feature | Version |
|---------|---------|
| Content authorship (Level 4+) | ✅ MVP |
| Handbook review queue (Level 5) | ✅ MVP |
| Five qualification programmes (Certificate → Doctorate) | Version 2 |
| Programme catalogue with level gating | Version 2 |
| Enrolment and progress tracking | Version 2 |
| Lesson viewer with mark-complete | Version 2 |
| Assessments (quiz, assignment) | Version 2 |
| Certification flow (steward confirms → level advance) | Version 2 |
| URL video embed in lessons | Version 2 |
| Pathway banner ("You are on the Service Pathway") | Version 2 |
| My Learning Dashboard | Version 2 |
| Induction programmes (Reconditioning, Beginners, Community) | Version 2 |
| Rich text editor for authorship | Version 3+ |
| Quiz auto-grading | Version 3+ |
| Assignment peer review | Version 3+ |
| Learning analytics dashboard | Version 3+ |
| Offline lesson caching | Version 3+ |

### Activity App
| Feature | Version |
|---------|---------|
| Activity Engine (models, signals, DRF) | ✅ MVP |
| My Activities surface (task, habit, goal, skill, reminder) | Version 2 |
| Ministry surface (campaign, project, task, event) | Version 2 |
| Assigned-to-me queue | Version 2 |
| Calendar dated list view | Version 2 |
| Habit streak visualisation | Version 3+ |
| Full calendar grid UI | Version 3+ |
| Ministry analytics | Version 3+ |
| Cross-tenant campaign assignment | Version 3+ |

### Community App
| Feature | Version |
|---------|---------|
| Member directory | Version 2 |
| Announcements (create, broadcast to tenant) | Version 2 |
| Gatherings (dual-write with Activity event) | Version 2 |
| Community coordinator dashboard | Version 2 |
| Membership request flow | Version 2 |
| Pastoral notes | Version 3+ (privacy design required) |
| Attendance tracking | Version 3+ (privacy-sensitive) |
| Community analytics dashboard | Version 3+ |
| Collective-level gathering visibility | Version 3+ |
| Pastoral assignment model | Version 3+ |

### Governance App
| Feature | Version |
|---------|---------|
| Reference Library (Level 3+ read) | ✅ MVP (lite) |
| Mandate branch (Level 4+ read) | ✅ MVP (lite) |
| Keys Library (personal, Level 3+) | ✅ MVP (lite) |
| Record lifecycle (lock, supersede, version chain) | Version 2 |
| Linked Records panel (flat list) | Version 2 |
| HRS graph visualisation | Version 3+ |
| Level 4 tenant-scoped governance records | Version 3+ |

### Video / Live App
| Feature | Version |
|---------|---------|
| URL video embed (YouTube, Vimeo, direct .mp4) in lessons | Version 2 |
| Broadcast scheduler (church services, events) | Version 2 |
| Live stream embed surface | Version 2 |
| VOD library (past recordings) | Version 2 |
| Self-hosted video (MinIO + ffmpeg + HLS) | Version 3+ (if needed) |
| Virtual governance sessions | Version 3+ |
| In-service display app | Version 3+ |

---

## Complete Build Sequence

```
LAYER 0 — SERVER & TOOLS             (done once, never repeated)
LAYER 1 — DJANGO FOUNDATION          (Phases 0–3, complete)
LAYER 2 — MVP APPS                   (Phases 5.1–7, partially complete)
LAYER 3 — STABILISATION              (Pre-Version 2, required before new features)
LAYER 4 — VERSION 2: FORMATION       (Phases V2.1–V2.5, web + mobile)
LAYER 5 — VERSION 2: EXTENDED        (Phases V2.6–V2.8)
LAYER 6 — VERSION 3: SCALE          (future — Redis, Docker, AI, advanced features)
```

---

# LAYER 0 — Server & Tools
## Phase 0.1 — Hetzner Server Setup ✅ COMPLETE

**What was built:** Hetzner VPS provisioned (Ubuntu 22.04), SSH key authentication, UFW firewall, non-root deploy user (`ics`), domain pointed to server IP, basic server hardening.

**Key file locations established:**
```
/home/ics/ics/backend/          App code (git repo)
/home/ics/ics/backend/.env      Secrets (never committed)
/home/ics/ics/venv/             Python virtual environment
/home/ics/backups/              Database backups
/var/log/ics/                   Django error logs
/etc/nginx/sites-available/ics  Nginx config
/etc/systemd/system/ics.service Gunicorn systemd service
```

## Phase 0.2 — GitHub & Local Development ✅ COMPLETE

**What was built:** GitHub repository, deploy key, `.gitignore`, `.env.example`, `deploy.sh` script, local VS Code + Remote-SSH workflow.

## Phase 0.3 — Nginx + Gunicorn + SSL ✅ COMPLETE

**What was built:** Nginx reverse proxy, Gunicorn WSGI server (3 workers), systemd service for auto-restart on boot, Let's Encrypt SSL via certbot, `collectstatic` wired to deploy script.

---

# LAYER 1 — Django Foundation
## Phase 1 — Auth + Tenants + HTMX Shell ✅ COMPLETE

**What was built:** Custom User model (email as username, `competence_level`, `status`, `preferences` JSONField), UserProfile, UserPermission (role + level per tenant), Tenant model with materialised path hierarchy, Django session auth for web, DRF token auth for mobile, `base.html` with navbar, app drawer, bottom nav, theme toggle (`storage.js`), mobile-first CSS design system (CSS variables, dark mode, 44px touch targets, 8px spacing grid).

## Phase 2 — Records Engine ✅ COMPLETE

**What was built:** `Record` model (single table, `record_family` / `record_class` / `record_type` discriminator), `Relationship` model (16 typed relationship types, `bible_verse_id` amendment), full DRF CRUD at `/api/records/` and `/api/relationships/`, Django template views + HTMX partials.

## Phase 3 — Activity Engine ✅ COMPLETE

**What was built:** `Activity` model (9 activity types), `ActivityLog` signal (fires on status transitions), full DRF CRUD at `/api/activities/`, Django template views + HTMX partials.

---

# LAYER 2 — MVP Apps

## Phase 5.1 — Bible App ✅ COMPLETE

**What was built:** `BibleTranslation`, `BibleBook`, `BibleVerse` models, three translations loaded (KJV default, ASV, WEB — ~93,306 verse rows), scripture reader with chapter navigation, personal annotations (stored as Records with `record_family: "bible"`), tenant-scoped notes, Handbook linkages (Level 5), three-panel mobile-first HTMX UI.

**Deferred to Version 2:** Reading plans, verse highlights, scripture search.
**Deferred to Version 3+:** Licensed translations (NIV/ESV/NLT — require publisher licensing agreements and fees), African language translations, audio Bible.

---

## Phase 5.2 — Learn App 🔄 REQUIRES ALIGNMENT AUDIT

**Entry requirement:** Code alignment audit complete (see Phase S.2 below).

### What the Learn App must contain when complete:

**Backend (DRF):**
- `CertificationConfirmation` model — audit trail for every level advancement
- `GET /api/learn/health/`
- `GET /api/learn/programmes/{id}/curriculum/` — traverses `part_of` relationships
- `GET /api/learn/certifications/queue/` — steward queue (Level 3+)
- `POST /api/learn/certifications/{id}/confirm/` — the sole write path for `competence_level`
- `learn/signals.py` — programme Activity at 100% → draft certification Record created automatically

**Web UI (Django templates + HTMX):**
- F1 Programme Catalogue — pathway view + flat catalogue, locked state for above-level programmes
- F2 Course Browser
- F3 Enrolment — prerequisite check, one enrolment per programme per user
- F4 Progress Tracking — lesson completion, course and programme progress bars
- F5 Lesson Viewer — rendered content, mark complete, previous/next navigation
- F6 Assessments — inline quiz (multiple choice / short answer), assignment text submission
- F7 Certification — "Awaiting certification" state, steward queue, confirm → level increment
- F8 Content Authorship (Level 4+) — draft and submit programmes, courses, lessons
- F9 Handbook Review Queue (Level 5) — approve/return/lock
- F10 Pathway Banner — "You are on the Service Pathway"
- F11 My Learning Dashboard — active enrolments, certifications, formation summary

**Django template routes:**
```
GET  /learn/                                My Learning Dashboard
GET  /learn/catalogue/                      Programme catalogue
GET  /learn/programme/{id}/                 Programme detail
GET  /learn/course/{id}/                    Course detail
GET  /learn/lesson/{id}/                    Lesson viewer
POST /learn/htmx/enrol/{programme_id}/      Enrolment
POST /learn/htmx/lesson/{id}/complete/      Mark lesson complete
POST /learn/htmx/assessment/{id}/submit/    Submit assessment
GET  /learn/certifications/                 Steward cert queue (Level 3+)
POST /learn/htmx/certification/{id}/confirm/  Confirm certification
GET  /learn/author/                         Authorship dashboard (Level 4+)
GET  /learn/review/                         Handbook review queue (Level 5)
```

**Exit criteria:** `POST /api/learn/certifications/{id}/confirm/` correctly increments `competence_level` in DB. Verifiable in Django admin. All F1–F11 features functional. Mobile smoke test passes.

**Commit:** `git commit -m "feat: learn app — complete"`

---

## Phase 5.3 — Activity App UI 🔄 PENDING

**Entry requirement:** Phase 3 (Activity Engine) complete. Code alignment audit complete.

**What this builds:** UI layer only — the Activity Engine models and DRF are already built in Phase 3. This phase builds the two-surface interface.

**My Activities surface** (personal, `tenant_id: null`):
- Types: task, habit, goal, skill, reminder
- Flat structure only (no nesting)
- Mark complete via HTMX (no page reload)
- Read-only programme cards showing Learn enrolments

**Ministry surface** (organisational, tenant-scoped):
- Types: campaign, project, task, event
- Two-level nesting: campaign/project → task
- "Assigned to me" tab — first-class view
- Level 3+ can create campaigns and projects; Level 1+ can create tasks

**Calendar (dated list view):**
- Shows activities with due dates in chronological order
- Not a grid calendar — a dated list. Full grid deferred to Version 3.

**Django template routes:**
```
GET  /activity/                         My Activities home
GET  /activity/ministry/                Ministry surface
GET  /activity/calendar/                Dated list view
POST /activity/htmx/create/             Create activity (HTMX)
POST /activity/htmx/{id}/complete/      Mark complete (HTMX)
POST /activity/htmx/{id}/status/        Update status (HTMX)
```

**Exit criteria:** Member can create personal tasks and habits, mark them complete, and see progress. Steward can create campaigns and assign tasks to members.

**Commit:** `git commit -m "feat: activity app UI — my activities + ministry surfaces"`

---

## Phase 5.4 — Community App 🔄 PENDING

**Entry requirement:** Phases 2–3 complete. Code alignment audit complete.

**What this builds:**

**My Community surface (Level 1+):**
- Member directory (members of user's tenant)
- Tenant profile card (name, theme, area of operation, coordinator)
- Announcements list (read + create for Level 3+)
- Gathering schedule (read + create for Level 3+)

**Community Management surface (Level 3+):**
- Full member roster with roles and service orders
- Role assignment (Shepherd, Net Caster, Net Mender, Member)
- Shepherd assignment
- Membership request queue (approve/reject)

**Gatherings (dual-write):**
- Creating a gathering creates both a `Gathering` Record and an `Activity (activity_type:'event')` atomically via `transaction.atomic()`
- `stream_url` field on Gathering for live stream URL (placeholder for Video App)
- Format: in_person / digital / hybrid

**Django template routes:**
```
GET  /community/                             My Community home
GET  /community/members/                     Member directory
GET  /community/announcements/               Announcements list
POST /community/htmx/announcements/create/   Create announcement
GET  /community/gatherings/                  Gathering schedule
POST /community/htmx/gatherings/create/      Create gathering (dual-write)
GET  /community/manage/                      Management surface (Level 3+)
GET  /community/manage/members/              Full member roster
POST /community/htmx/manage/assign-role/     Role assignment
```

**Exit criteria:** Member can see their community and read announcements. Level 3 coordinator can create announcements, gatherings, and manage member roles. Dual-write creates both Record and Activity atomically.

**Commit:** `git commit -m "feat: community app"`

---

## Phase 5.5 — Governance App 🔄 PENDING

**Entry requirement:** Phases 2–3 complete. Code alignment audit complete.

**What this builds (full spec — the lite version from MVP sessions needs alignment):**

**Three surfaces:**
- Reference Library (Level 3+ read) — doctrine, divine_pattern, covenant, decree, protocol, ordinance, standard
- Mandate branch (Level 4+ read, Level 5 write) — mandate, law, statute, framework, constitution
- Keys Library (personal, Level 3+) — private interpretive symbol library

**Record lifecycle (not in lite MVP):**
- `draft → active → locked → superseded`
- Lock action (Level 5): makes record uneditable, sets `locked_at`
- Supersede flow (Level 5): creates new draft linked to previous via `previous_version_id`
- Version history chain: traversable timeline on record detail view

**Linked Records panel:**
- Flat list of all Relationships from/to this record
- Read-only. Includes scripture links via `bible_verse_id`.

**Journal → Governance linkage:**
- `Relationship (derived_from)`: governance record linked to journal entry
- No new model — uses existing Relationship engine

**Django template routes:**
```
GET  /governance/                              Surface selector home
GET  /governance/reference/                    Reference Library browse
GET  /governance/reference/{type}/             Browse by type
GET  /governance/reference/{id}/               Property detail
GET  /governance/mandate/                      Mandate branch browse
GET  /governance/mandate/{id}/                 Record detail + version history
GET  /governance/keys/                         Keys Library
GET  /governance/keys/{id}/                    Key detail
POST /governance/htmx/record/create/           Create record (Level 5)
POST /governance/htmx/record/{id}/lock/        Lock (Level 5)
GET  /governance/htmx/record/{id}/supersede/   Begin supersession
POST /governance/htmx/record/{id}/supersede/   Confirm supersession
GET  /governance/htmx/record/{id}/links/       Linked records panel partial
GET  /governance/htmx/record/{id}/history/     Version history partial
```

**Exit criteria:** All three surfaces render data from Handbook tenant. Lock and supersede lifecycle transitions work. Linked Records panel populated. Version history chain traversable.

**Commit:** `git commit -m "feat: governance app — full lifecycle"`

---

## Phase 5.6 — Profile + Settings ⏳ PENDING

**Entry requirement:** Phase 1 complete.

**Profile view (`/accounts/profile/`):**
- Identity: avatar (initials placeholder if null), display name (inline HTMX edit), email (read-only), member since, platform status badge
- Formation: competence level label + numeric level, active tenant display, service order

**Settings view (`/accounts/settings/`):**
- Appearance: theme (light/dark/system)
- Language & Region: language, timezone
- Bible: preferred translation
- All persisted to `User.preferences` JSONField — not localStorage

**Exit criteria:** Profile renders. Settings saves to database. Inline display name edit works via HTMX without page reload.

**Commit:** `git commit -m "feat: profile + settings"`

---

## Phase 5.7 — Notifications Stub ⏳ PENDING

**Entry requirement:** Phase 1 complete.

Notifications is a shell only. Full implementation is Version 2 (triggers from Community, Activity, Governance, Learn not yet wired).

- `GET /api/notifications/` returns `{"count": 0, "next": null, "results": []}`
- `GET /api/notifications/unread-count/` returns `{"count": 0}`
- Navbar bell icon badge reads count on page load via HTMX. Hidden when 0.
- No `Notification` model in MVP — no migration.

**Exit criteria:** Nav bell links to `/notifications/`. Empty state renders. Badge count shows 0 and is hidden.

**Commit:** `git commit -m "feat: notifications stub"`

---

## Phase 6.1 — Paraclete Service ⏳ PENDING

**Entry requirement:** Phases 3 + 5.1–5.7 all complete. Paraclete reads from all apps.

**What this builds:**
- `ParacletePrompt` model (24+ prompts seeded, 3 per KGS pathway)
- `paraclete/service.py` — pure Python, reads ORM, writes nothing, returns `ParacleteDigest`
- `build_digest(user)` — main orchestration function
- Five DRF endpoints:
  - `GET /api/paraclete/digest/` — full daily digest (5-minute filesystem cache)
  - `GET /api/paraclete/reminders/` — pending reminders
  - `GET /api/paraclete/prompt/` — discipline prompt
  - `GET /api/paraclete/suggest/{record_id}/` — stub returning `{"suggestions": [], "method": "deferred"}`
  - `POST /api/paraclete/respond/` — stub returning `{"status": "ok"}`

**ParacleteDigest fields:**
- `pending_count`, `overdue_count`, `due_today` (up to 5), `overdue_items` (up to 5)
- `habit_streaks` — active daily habits with streak count
- `pending_reminders` — due within 24 hours
- `active_enrolments`, `next_lesson` — Learn surface
- `discipline_prompt`, `prompt_pathway`
- `dar_today` — today's Daily Analysis Record (if written)
- `team_pending_count`, `team_overdue_count` — Level 3+ only

**Caching:** Django filesystem cache, 5-minute TTL per user. No Redis.

**Exit criteria:** `GET /api/paraclete/digest/` returns correct data for Level 0, 1, and 3 test users. Habit streak calculates correctly. Cache confirmed working (second request same `generated_at`).

**Commit:** `git commit -m "feat: paraclete service + digest endpoint"`

---

## Phase 6.2 — Dashboard ⏳ PENDING

**Entry requirement:** Phase 6.1 complete.

**What this builds:**
- Dashboard calls `paraclete.service.build_digest()` via direct Python import (not HTTP)
- Role-aware widgets (Level 3+ sees ministry summary)
- Tenant-aware

**Widgets:**
- Today's focus (discipline prompt)
- Pending activities (tasks + habits due today)
- Recent records (last 5 created by user)
- Active prayer count
- Formation Journey card (current level, active programme, next level requirement) — Version 2 full version
- Ministry summary (Level 3+ only)

**Django template routes:**
```
GET  /                                  Dashboard home
GET  /dashboard/htmx/digest/            Full digest reload partial
GET  /dashboard/htmx/activities/        Pending activities widget
GET  /dashboard/htmx/prayers/           Prayer count widget
```

**Exit criteria:** Dashboard renders digest widgets. Role-aware display correct. HTMX partials refresh without full page reload.

**Commit:** `git commit -m "feat: dashboard"`

---

## Phase 7 — Production Hardening ⏳ PENDING

**Entry requirement:** Phases 6.1–6.2 complete.

**Task 7.1 — Error logging:**
```python
# production.py
LOGGING = {
    'version': 1,
    'handlers': {'file': {'class': 'logging.FileHandler', 'filename': '/var/log/ics/django_errors.log'}},
    'loggers': {'django': {'handlers': ['file'], 'level': 'ERROR'}},
}
ADMINS = [('Chizola', 'your-email@example.com')]
```

**Task 7.2 — Security settings:**
```python
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

**Task 7.3 — Django admin:** Register all models. Create superuser. Verify at `/admin/`.

**Task 7.4 — Final smoke test:** All health endpoints return 200. SSL headers present. Gunicorn restarts via systemd after reboot.

**Commit:** `git commit -m "chore: production hardening — MVP complete"`

---

# LAYER 3 — Stabilisation
# (Required before any Version 2 feature work begins)

## Phase S.1 — Infrastructure Additions

**Entry requirement:** Phase 7 complete (or run in parallel with Phase 7).

### S.1.1 — Email Service (Brevo)

**Why Brevo:** Free tier gives 300 emails/day, no credit card required, reliable delivery, simple SMTP setup. Adequate for hundreds of monthly active users. Upgrade path is straightforward when needed.

**Why not self-hosted email:** Running your own SMTP server (Postfix etc.) requires managing IP reputation, SPF/DKIM/DMARC records, bounce handling, and spam blacklist monitoring. Emails will land in spam until the IP builds a reputation (months). Not appropriate for a sole developer building a complex platform.

**Setup steps:**
1. Create account at brevo.com (free)
2. Go to SMTP & API → SMTP settings → generate credentials
3. Add to `.env`:
```
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-brevo-login@email.com
EMAIL_HOST_PASSWORD=your-brevo-smtp-key
DEFAULT_FROM_EMAIL=noreply@your-domain.com
```
4. Add to `settings/base.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')
```
5. Test: `python manage.py shell` → `from django.core.mail import send_mail; send_mail('Test', 'Body', None, ['your@email.com'])`

**Commit:** `git commit -m "chore: email service — Brevo SMTP configured"`

### S.1.2 — Media Storage (MinIO on Hetzner)

**Why:** Profile avatars and tenant logos need real file storage. URLField points to external URLs — not acceptable for user-uploaded content. MinIO runs locally on your Hetzner VPS, is S3-compatible (boto3/django-storages), and costs nothing beyond VPS disk space. If you later move to AWS S3, you change three environment variables and zero code.

**Install on VPS:**
```bash
# Download and install MinIO
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

# Create data directory and MinIO user
sudo useradd -r minio-user -s /sbin/nologin
sudo mkdir -p /data/minio
sudo chown minio-user:minio-user /data/minio

# Create systemd service at /etc/systemd/system/minio.service
# (see production engineering guide for full service file)

sudo systemctl enable minio
sudo systemctl start minio
```

**Django settings:**
```python
# requirements.txt: add django-storages[s3] boto3 Pillow
STORAGES = {"default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"}}
AWS_S3_ENDPOINT_URL = config('MINIO_ENDPOINT')  # e.g. http://localhost:9000
AWS_ACCESS_KEY_ID = config('MINIO_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = config('MINIO_SECRET_KEY')
AWS_STORAGE_BUCKET_NAME = 'ics-media'
AWS_S3_FILE_OVERWRITE = False
MEDIA_URL = config('MEDIA_URL')  # e.g. https://your-domain.com/media/
```

**Nginx proxy** (add to Nginx site config):
```nginx
location /media/ {
    proxy_pass http://localhost:9000/ics-media/;
}
```

**MinIO buckets to create:**
- `ics-media` — public read (avatars, logos)
- `ics-private` — private (attachments, presigned URLs)

**Model updates:**
```python
# accounts/models.py
avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

@property
def avatar_url(self):
    return self.avatar.url if self.avatar else None

# tenants/models.py — same pattern for logo
```

**Commit:** `git commit -m "chore: MinIO media storage — avatars and logos"`

### S.1.3 — Database Backups

**Why:** PostgreSQL data on a VPS with no backup = single point of failure. One corrupted disk and everything is gone.

**Setup:**
```bash
# Create backup script at /home/ics/backup.sh
#!/bin/bash
BACKUP_DIR="/home/ics/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

pg_dump -U ics_user ics_db | gzip > $BACKUP_DIR/ics_backup_$DATE.sql.gz
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete  # keep 7 days
echo "Backup complete: ics_backup_$DATE.sql.gz"
```

**Schedule via cron:**
```bash
crontab -e
# Add:
0 2 * * * /home/ics/backup.sh >> /var/log/ics/backup.log 2>&1
```

**Weekly manual step:** Download a backup copy to your laptop. Never rely solely on server-side backups.

**Commit:** `git commit -m "chore: PostgreSQL backup script + cron schedule"`

---

## Phase S.2 — Code Alignment Audit

**Entry requirement:** S.1 complete.

**What this is:** During MVP build sessions, view code was written for apps that the roadmap marks as Pending. This code must be audited before Version 2 is built on top of it. Building on misaligned code causes cascading rework.

**Process for each app:**
1. Open the app's locked system design document
2. Read the system design's URL routes, data patterns, access level gates, and HTMX partial patterns
3. Open the existing view file
4. Mark each view: ✅ Conforms | ⚠️ Needs adjustment | ❌ Rewrite required
5. Fix before moving on. Do not skip this step.

**Apps to audit:**

| App | File | Reference doc |
|-----|------|--------------|
| Learn | `learn/views.py` | `2026-04-07-ics-learn-app-system-design_v2.md` |
| Governance | `governance/views.py` | `2026-04-10-ics-governance-app-system-design.docx` |
| Community | `community/views.py` | `2026-04-08-ics-community-app-system-design.md` |
| Paraclete | `paraclete/service.py` | `2026-04-10-ics-paraclete-service-system-design.docx` |
| Records linking | `records/views.py`, `activity/models.py` | Data contract v9 + v10 |
| Notifications | `notifications/` | `2026-04-10-ics-profile-settings-notifications-spec.docx` |

**Also confirm during audit:**
- Django version in production is 4.2 LTS (not 5.2)
- `competence_level` write path is isolated to `POST /api/learn/certifications/{id}/confirm/` only
- `Activity.linked_record` FK exists or add it (see data contract v10 Amendment 10.4)

**Commit:** `git commit -m "chore: code alignment audit — all apps verified against system design specs"`

---

# LAYER 4 — Version 2: Formation Platform

## Phase V2.1 — Learn App: Formation Foundation

**Entry requirement:** S.1 + S.2 complete. This is the most important phase in Version 2. The Induction System depends on it. Do not start Induction until Learn is complete and tested.

**What this adds to the existing Learn App:**

### V2.1.1 — Five Qualification Programmes (Seeded)

Seed as system Records (`record_family: "learning"`, `record_type: "programme"`):

| Programme | Level | Duration | Prerequisites |
|-----------|-------|----------|---------------|
| Certificate | 1 | 1 year | None |
| Diploma | 2 | 3 years | Certificate |
| Degree | 3 | 4 years | Diploma |
| Masters | 4 | 4–5 years | Degree |
| Doctorate | 5 | 7 years | Masters |

Management command: `python manage.py seed_programmes`

### V2.1.2 — Three Induction Programmes (Seeded, Induction Tenant scope)

| Programme | Entrant type | Court |
|-----------|-------------|-------|
| Reconditioning Programme | Existing believers | Outer Court |
| Beginners Programme | Kingdom-curious newcomers | Outer Court |
| Community Programme | All inductees | Inner Court |

Management command: `python manage.py seed_induction_programmes`

### V2.1.3 — URL Video Embed Player

```python
# core/utils/video.py
def get_embed_url(url):
    """Convert YouTube/Vimeo watch URLs to embeddable form. Returns direct URLs unchanged."""
    # youtube.com/watch?v=ID → youtube.com/embed/ID
    # youtu.be/ID → youtube.com/embed/ID
    # vimeo.com/ID → player.vimeo.com/video/ID
    # direct .mp4 URL → returned as-is
```

```html
<!-- templates/video/_player.html -->
{% if video_url %}
  {% if 'youtube' in video_url or 'youtu.be' in video_url %}
    <iframe src="{{ embed_url }}" allowfullscreen class="video-player"></iframe>
  {% elif 'vimeo.com' in video_url %}
    <iframe src="{{ embed_url }}" allowfullscreen class="video-player"></iframe>
  {% else %}
    <video src="{{ video_url }}" controls class="video-player"></video>
  {% endif %}
{% endif %}
```

Stored in lesson Records as `custom_fields['video_url']` — no model field change.

**Exit criteria:** All five qualification programmes seedable and retrievable. Three induction programmes seeded. Video embed renders correctly in lesson viewer for YouTube, Vimeo, and direct URLs.

**Commit:** `git commit -m "feat: version 2 — learn app formation foundation"`

---

## Phase V2.2 — Induction System

**Entry requirement:** V2.1 complete. Email service operational (S.1.1). Induction requires email for verification.

### V2.2.1 — Data Contract v10: Required Migrations

Before building any Induction views, run these migrations:

```python
# tenants/migrations: add "induction" to Tenant.tier choices
# accounts/migrations: add to User model:
#   induction_enrolled_at = DateTimeField(null=True)
#   induction_completed_at = DateTimeField(null=True)  
#   induction_pathway = CharField(max_length=20, null=True)  # "reconditioning"|"beginners"
# accounts/migrations: add to UserProfile:
#   full_name = CharField(max_length=255, blank=True)
#   address = TextField(blank=True, null=True)
#   country = CharField(max_length=2, blank=True, null=True)  # ISO 3166-1 alpha-2
#   id_number = CharField(max_length=100, blank=True, null=True)  # MUST BE ENCRYPTED
#   age = IntegerField(null=True)
#   gender = CharField(max_length=20, null=True)
#   occupation = CharField(max_length=100, blank=True, null=True)
#   education = CharField(max_length=200, blank=True, null=True)
#   born_again = BooleanField(null=True)
# activity/migrations: add to Activity:
#   linked_record = ForeignKey('records.Record', SET_NULL, null=True, blank=True)
```

**CRITICAL — `id_number` encryption:** National ID and passport numbers are legally sensitive PII (South Africa POPIA and international equivalents). Install `django-encrypted-model-fields`:
```bash
pip install django-encrypted-model-fields
```
```python
from encrypted_model_fields.fields import EncryptedCharField
id_number = EncryptedCharField(max_length=100, blank=True, null=True)
```
The encrypted value is stored in the database. The decryption key is in your `.env` as `FIELD_ENCRYPTION_KEY`. Never store `id_number` in plaintext. Never return it in any API response without an explicit admin-only endpoint with Level 4+ gate.

### V2.2.2 — Induction Tenant Seed

```python
# Management command: python manage.py seed_induction_tenant
Tenant.objects.get_or_create(
    slug='induction',
    defaults={
        'name': 'Induction',
        'path': '/global/induction/',
        'tier': 'induction',  # new tier value
        'status': 'active',
    }
)
```

The Induction Tenant cannot be deleted or renamed via normal UI flows. Enforce this at the view layer by checking `tenant.tier == 'induction'` before any destructive operation.

### V2.2.3 — Sign-up & Profile Registration (Three-Step Flow)

**Step 1 — Sign-up:**
- Email + password
- Email verification (sends via Brevo)
- User created with `status: "seeker"`, no competence level
- No tenant assignment yet

**Step 2 — Profile Registration:**
Form collects: Full Name, Email (read-only), Address, Country, ID/Passport Number (encrypted), Age, Gender, Occupation, Education/Qualification, Born Again (Yes/No), Entrant type ("I am already part of a church or faith community" → Reconditioning, "I am new to this or exploring" → Beginners).

**Step 3 — Induction Placement:**
- `UserPermission` created: `tenant_path="/global/induction/"`, `level=0`, `role="seeker"`, `is_active=True`
- `user.induction_enrolled_at` set
- `user.induction_pathway` set from entrant type selection
- `learn/service.py → enrol_induction_programmes(user, pathway)` called automatically
- User redirected to Induction Dashboard

**Django template routes:**
```
GET  /accounts/register/              Sign-up form
POST /accounts/register/              Create user, send verification email
GET  /accounts/verify-email/{token}/  Verify email, redirect to profile setup
GET  /accounts/profile-setup/         Profile registration form (Step 2)
POST /accounts/profile-setup/         Save profile + place in Induction Tenant (Step 3)
GET  /accounts/welcome/               Induction welcome screen
```

### V2.2.4 — Induction Programme Enrolment

Called automatically from Step 3 of profile registration:

| Entrant type | Outer Court | Inner Court |
|-------------|-------------|-------------|
| Reconditioning | Reconditioning Programme | Community Programme |
| Beginners | Beginners Programme | Community Programme |

Both enrolled in sequence. Community Programme enrolment triggered on Outer Court completion (Django signal). Induction Dashboard is a Learn App view filtered to `tier="induction"` scope.

### V2.2.5 — Induction Completion & Tenant Placement

**Flow:**
1. User completes Community Programme (Inner Court)
2. `learn/signals.py` creates draft `certification` Record with `metadata.context: "induction_completion"`, `metadata.target_level: 1`
3. Induction Coordinator (Level 3+ in Induction Tenant) opens induction review queue
4. Coordinator reviews profile data, programme completion, assessment submissions
5. System narrows tenant list by matching user's Country/City from profile to tenant hierarchy (suggest + coordinator confirms)
6. Coordinator calls `POST /api/learn/certifications/{id}/confirm/` with `placement_tenant_id` in request body
7. Extended confirm logic (when `metadata.context == "induction_completion"`):
   - Sets `competence_level = 1`
   - Sets `user.induction_completed_at`
   - Creates `UserPermission` in placement tenant (`level=1`, `role="disciple"`)
   - Deactivates Induction Tenant `UserPermission` (`is_active=False`)
   - Writes ActivityLog entry
   - Sends email notification to user via Brevo

**Django template routes:**
```
GET  /learn/induction/review/                  Coordinator: pending completions list
GET  /learn/induction/review/{user_id}/        Coordinator: individual review
POST /learn/htmx/induction/confirm/{user_id}/  Coordinator confirms + places
GET  /accounts/formation/                      User: post-placement welcome + Level 1 orientation
```

**Exit criteria:** New user completes sign-up → profile → lands in Induction Dashboard. Correct programme enrolled automatically. Induction Coordinator can confirm completion and place user in home tenant. User receives email notification. `competence_level` set to 1 in database.

**Commit:** `git commit -m "feat: induction system — sign-up, profile, enrolment, placement"`

---

## Phase V2.3 — Formation UI & App Drawer Gating

**Entry requirement:** V2.2 complete.

### V2.3.1 — Formation Dashboard

**Level badge in navbar:**
- Visual badge showing current level (0=grey, 1=green, 2=blue, 3=purple, 4=orange, 5=red)
- Click → modal showing next level requirements

**"Your Formation Journey" card on dashboard:**
- Current competence level with KGS name (e.g. "Foundational Disciple — Level 1")
- Active qualification programme with progress bar
- Next level: which programme must be completed and estimated time
- Pathway affiliation (e.g. "You are on the Service Pathway")

**Formation history view:**
- Timeline of level advancements
- Each entry: from level, to level, date, confirming steward name, reason (induction_completion / certification)
- Data source: `CertificationConfirmation` records

**Django template routes:**
```
GET  /accounts/formation/              Full formation history
GET  /learn/htmx/formation-card/       HTMX dashboard card partial
```

### V2.3.2 — App Drawer Level Gating

**Access levels (configured in `settings.py` — no new model):**
```python
APP_LEVEL_REQUIREMENTS = {
    'bible':      0,   # Seeker and above
    'learn':      0,   # Browse at 0, enrol at 1
    'activity':   1,   # Level 1 and above
    'community':  1,   # Level 1 and above
    'governance': 3,   # Level 3 and above
    'paraclete':  1,   # Level 1 and above
}
```

**Drawer behaviour:**
- Available apps: rendered normally, clickable
- Locked apps: lock icon + "Requires Level X" tooltip
- Click on locked app: modal — "To access Governance, you need Level 3. Complete the Diploma Programme to advance."

**Context processor:**
```python
# accounts/context_processors.py
def user_level(request):
    if request.user.is_authenticated:
        return {'user_level': request.user.userprofile.competence_level}
    return {'user_level': 0}
```

**Commits:** `git commit -m "feat: formation dashboard + level badge"` then `git commit -m "feat: app drawer level gating"`

---

## Phase V2.4 — Notifications (Full)

**Entry requirement:** V2.3 complete. All trigger sources now built.

**Notification model:**
```python
class Notification(models.Model):
    id = UUIDField(primary_key=True)
    user = ForeignKey(User, on_delete=CASCADE, related_name='notifications')
    notification_type = CharField(max_length=50)
    # Types: announcement, task_assigned, certification_confirmed, 
    #        induction_completed, level_advanced, gathering_scheduled
    source_app = CharField(max_length=50)  # community, learn, activity, governance
    source_record_id = UUIDField(null=True)
    source_activity_id = UUIDField(null=True)
    message = TextField()
    is_read = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
```

**Trigger points (Django signals):**
- Community App: `announcement` created → notify all tenant members
- Activity App: task `assigned_to` set → notify assignee
- Learn App: `certifications/confirm/` → notify learner (level advanced)
- Induction: placement confirmed → notify user (welcome to community)
- Governance App: record `locked` → notify Level 4+ in scope

**Delivery:**
- In-app: badge polls every 60 seconds via HTMX (`hx-trigger="every 60s"`)
- Email: Brevo SMTP — send email for `certification_confirmed` and `level_advanced` events (highest value notifications). Other types in-app only.

**Real-time push (HTMX polling, not WebSockets):** HTMX polling at 60-second intervals is sufficient for MVP notifications. WebSockets (Django Channels) are Version 3.

**Django template routes:**
```
GET  /notifications/                         Notifications list (paginated)
GET  /api/notifications/                     DRF endpoint (paginated list)
GET  /api/notifications/unread-count/        Badge count
POST /api/notifications/{id}/read/           Mark as read
POST /api/notifications/read-all/            Mark all as read
```

**Commit:** `git commit -m "feat: notifications — full model, triggers, delivery"`

---

## Phase V2.5 — Tenant Self-Service

**Entry requirement:** V2.4 complete.

### V2.5.1 — Tenant Creation (Level 3+)

- `/tenants/create/` form: name, slug, tier, parent tenant, description, location (country/province/city), logo (uploaded to MinIO)
- `TenantInvitation` model: `tenant`, `email`, `invited_by`, `accepted_at`, `status`
- Invitation workflow: invite → email (Brevo) → accept link → `UserPermission` created
- Tenant hierarchy correctly reflected in materialised path

### V2.5.2 — Member Management

- Invite users by email
- Assign roles: Coordinator, Shepherd, Net Caster, Net Mender, Member
- Assign service orders (from `UserPermission.metadata.service_order`)
- Assign shepherd (`UserPermission.metadata.shepherd_id`)

### V2.5.3 — Multi-Tenant Content Scoping

- Governance records filtered by user's tenant(s)
- Learn content filtered by user's tenant(s)
- Handbook visible to Level 4+ across all tenants
- Induction Tenant: Level 0 sees induction content only
- Users in multiple tenants see content from all their tenants

**Extend `Tenant` model:**
```python
coordinator_user = ForeignKey(User, on_delete=SET_NULL, null=True, related_name='coordinating_tenants')
community_theme = CharField(max_length=100, blank=True)  # e.g. "Education", "Healthcare"
area_of_operation = TextField(blank=True)
```

**Commit:** `git commit -m "feat: tenant self-service — creation, invitations, member management, content scoping"`

---

## Phase V2.6 — Video / Live App

**Entry requirement:** V2.5 complete. Learn App operational (V2.1).

### V2.6.1 — Broadcast Scheduler

**New Django app:** `video_live/`

Broadcast schedule stored as `Activity (activity_type: "event")` + `Gathering` dual-write (same pattern as Community App). `stream_url` on Gathering carries the live stream URL (field already exists from Community App).

**Scheduler logic:**
- Events with a start time and duration form the programme grid
- "Now playing" detection: current time falls within event's `start_at` + `duration_minutes`
- Upcoming events: next 7 days, ordered by `start_at`
- Past events: automatically become VOD entries (stream URL archived in `custom_fields`)

### V2.6.2 — Live Stream Surface

**Django template routes:**
```
GET  /video/                           Home (now playing + schedule)
GET  /video/live/                      Current live stream (HTMX refresh every 60s)
GET  /video/schedule/                  Programme grid (today + 7 days)
GET  /video/vod/                       Past recordings library
GET  /video/watch/{event_id}/          Individual event player (live or VOD)
```

**Player logic:**
- YouTube/Vimeo URLs → `<iframe>` embed (reuses `core/utils/video.py` from V2.1)
- Direct `.mp4` URLs → `<video>` tag
- No self-hosted transcoding. No MinIO video bucket. No ffmpeg.

**Exit criteria:** Broadcast schedule visible and navigable. Live stream renders for active events. VOD library browsable. HTMX auto-refresh detects live status changes.

**Commit:** `git commit -m "feat: video live app — broadcast scheduler + live stream + VOD"`

---

# LAYER 5 — Version 2: Mobile App

## Phase V2.M — Flutter Mobile App

**Entry requirement:** V2.2 complete (DRF API stable, user levels established, induction system live). Start this phase in parallel with V2.3 — do not wait until V2.6 is done.

**Architecture decision (ADR-001):** Flutter for mobile. Android-first. iOS later. Consumes existing DRF API. No HTMX on mobile. The DRF API you have already built is the mobile backend. No new backend work required except Delta Sync (V2.M.4).

**Repository structure:** Flutter project lives in a `mobile/` subdirectory of the same repository, or in a separate repository `ichebo-mobile`. Separate repository is cleaner for a sole developer — different toolchain, different deployment.

### V2.M.1 — Flutter Project Setup

**Prerequisites on your development machine:**
- Flutter SDK installed (flutter.dev — choose stable channel)
- Android Studio installed (for Android SDK + emulator)
- Android device for physical testing (recommended)
- VS Code with Flutter extension

**Project creation:**
```bash
flutter create ichebo_mobile
cd ichebo_mobile
flutter run  # Should show demo app on emulator
```

**Key packages (`pubspec.yaml`):**
```yaml
dependencies:
  flutter:
    sdk: flutter
  dio: ^5.0.0              # HTTP client (calls DRF API)
  riverpod: ^2.0.0         # State management
  go_router: ^12.0.0       # Navigation + deep links
  sqflite: ^2.0.0          # Local SQLite (offline cache)
  path_provider: ^2.0.0    # File system paths
  firebase_messaging: ^14.0.0  # Push notifications (FCM)
  youtube_player_flutter: ^9.0.0  # YouTube player
  video_player: ^2.0.0     # Direct .mp4 player
  workmanager: ^0.5.0      # Background sync
  cached_network_image: ^3.0.0  # Image caching
  shared_preferences: ^2.0.0   # Simple key-value (auth token)
```

### V2.M.2 — Authentication

**How DRF token auth works with Flutter:**
1. User enters email + password in Flutter login screen
2. Flutter sends `POST /api/auth/login/` → DRF returns `{"token": "abc123..."}`
3. Flutter stores token in `shared_preferences` (secure storage)
4. Every subsequent API call includes header: `Authorization: Token abc123...`
5. DRF validates token and returns the user's data

**`GET /api/auth/me/` response shape (mobile needs this):**
```json
{
  "id": "uuid",
  "email": "user@email.com",
  "display_name": "Full Name",
  "competence_level": 1,
  "status": "active",
  "avatar_url": "https://...",
  "active_tenant": {"id": "uuid", "name": "Sceptre Pretoria", "slug": "..."},
  "induction_pathway": "beginners",
  "induction_completed_at": "2026-05-01T00:00:00Z"
}
```

Confirm this endpoint returns all fields Flutter needs before starting the app.

### V2.M.3 — Role-Adaptive Navigation

One Flutter app, one codebase. Navigation shell adapts to `user.competence_level`:

| Level | Role | Bottom Navigation |
|-------|------|------------------|
| 0 | Seeker/Inductee | Home, Bible, Learn (induction), Profile |
| 1 | Member | Home, Bible, Learn, Activity, Community, Profile |
| 2 | Disciple | + Governance (read), Certifications tab in Learn |
| 3 | Steward/Coordinator | + Community management, Cert queue, Induction review |
| 4 | Senior Steward | + Governance (write), Programme oversight |
| 5 | Architect | + Full operator console |

Implementation with `go_router`:
```dart
// Router reads user level from state, redirects to correct shell
GoRouter(
  redirect: (context, state) {
    final userLevel = ref.read(authProvider).user?.competenceLevel ?? 0;
    // Route to appropriate shell based on level
  }
)
```

### V2.M.4 — Offline SQLite Cache + Delta Sync

**The problem:** Mobile users may have no internet connection in a church building, in a rural area, or during load-shedding. The app must still work for reading.

**Solution: Local SQLite database + delta sync**

**Django backend — new endpoint (add to `core/views/sync.py`):**
```python
# GET /api/sync/changes/?since=2026-05-01T00:00:00Z
# Returns all Records, Activities, Notifications modified after the timestamp
# Uses existing updated_at fields — no model changes needed
# Scoped to requesting user's tenant permissions
# Max 500 items per type per response; has_more: true if more
```

**Flutter — sqflite local database:**
- On first launch: fetch full sync (since a very old date)
- On subsequent launches: fetch delta sync (since last sync timestamp)
- Write operations: save locally + queue to backend
- On reconnect: flush write queue to backend via `workmanager`

**What is cached locally:**
- Bible verses (read-only — cache all three translations on first sync)
- Records (user's tenant scope)
- Activities (user's activities)
- Learn content (programmes, courses, lessons — needed for offline lesson reading)
- Notifications (recent 50)

### V2.M.5 — Push Notifications (FCM)

**Firebase Cloud Messaging (FCM):** Google's free push notification service. Free tier is unlimited messages. No credit card required for FCM itself.

**Setup:**
1. Create Firebase project at console.firebase.google.com
2. Add Android app to Firebase project (use your Flutter app's package name)
3. Download `google-services.json` → place in `android/app/`
4. Install `firebase_messaging` Flutter package
5. Add to `accounts/models.py`: `fcm_token = CharField(max_length=255, blank=True, null=True)`
6. Flutter sends `PATCH /api/auth/me/` with `{"fcm_token": "<token>"}` on each login

**Django sends push notification via `notifications/fcm.py`:**
```python
import requests

def send_push(user, title, body, data=None):
    if not user.fcm_token:
        return
    requests.post(
        'https://fcm.googleapis.com/fcm/send',
        headers={'Authorization': f'key={settings.FCM_SERVER_KEY}'},
        json={
            'to': user.fcm_token,
            'notification': {'title': title, 'body': body},
            'data': data or {}
        }
    )
```

**When to send push:**
- Certification confirmed → push to learner
- Induction placement confirmed → push to new member
- Task assigned → push to assignee
- New announcement → push to all tenant members (use topic messaging for this)

### V2.M.6 — Core Screens

Build screens in this order — each depends on the API below it being stable:

**1. Auth screens:** Login, Register (links to web sign-up flow), Forgot Password

**2. Home / Dashboard:** Paraclete digest summary, today's focus, pending activities

**3. Bible:** Translation selector, book/chapter browser, verse reader, personal notes

**4. Learn:** My Learning (active enrolments), Programme Catalogue (level-gated), Lesson Viewer (with video embed for YouTube/Vimeo URLs), Mark Complete button, Certification status

**5. Activity:** My Activities (task list, habit tracking, goal progress), Create Activity, Mark Complete

**6. Community:** Member directory, Announcement feed, Gathering schedule, Community profile

**7. Profile:** Formation journey card (level badge, active programme, next level), Formation history, Settings (theme, timezone, Bible translation)

**8. Governance (Level 3+ read):** Reference Library browse, Record detail with linked records

**9. Coordinator screens (Level 3+):** Community management, Member roster, Certification review queue, Induction review queue

**Exit criteria:** All Level 0–3 screens functional on Android. Offline read works after initial sync. Push notifications received and tapped. Auth token persists across app restarts.

**Commit progression:** One commit per screen set, e.g. `git commit -m "feat(mobile): auth + home screens"` → `"feat(mobile): bible + learn screens"` → etc.

---

# LAYER 6 — Version 3 (Future Scale)

Do not build any of these until Version 2 is complete and in real-world use. Version 3 items are defined here so you understand what is coming — not so you build them now.

## Version 3 Technology Additions (each requires an ADR)

**Redis + Celery:** When you have background tasks that are too slow to run synchronously (e.g. sending 500 push notifications at once, processing uploaded files). Not needed until Version 2 is live and you observe actual bottlenecks.

**Docker Compose:** When you want to containerise the application for easier deployment, scaling, or handing off to another developer. Replaces Nginx + Gunicorn + systemd setup.

**Django Channels + WebSockets:** When you need real-time features — live notification delivery (instead of polling), live video scheduling updates, real-time community chat.

**LLM integration for Paraclete:** When Paraclete needs AI-generated insights rather than rule-based prompts. Requires significant architectural thought — what data goes to the LLM, privacy implications, cost management.

## Version 3 Feature Additions

**Bible App:** Licensed translations (NIV, ESV, NLT — require publisher licensing agreements), African language translations, audio Bible, cross-reference chains, scripture full-text search.

**Learn App:** Rich text editor (TipTap or similar) for lesson authorship, quiz auto-grading, assignment peer review, offline lesson caching, learning analytics dashboard.

**Activity App:** Full calendar grid UI, habit streak visualisation, ministry analytics, cross-tenant campaign assignment.

**Community App:** Pastoral notes (requires privacy design), attendance tracking (privacy-sensitive), community analytics, pastoral assignment model.

**Governance App:** HRS full graph visualisation (not just flat list), Level 4 tenant-scoped governance records, Governance App Phase 2.

**iOS (Flutter):** After Android is stable and tested in production. Requires Mac + Apple Developer account ($99/year).

**Self-hosted video:** If the ministry needs to host confidential video not suitable for YouTube — MinIO + ffmpeg + HLS pipeline. Only if URL-based approach proves insufficient.

---

## Deferred Items — Complete Reference

Every item below is explicitly deferred. It is not forgotten — it is here, in this document, so it can be found and planned when the time comes.

### Platform-wide
- Full `RecordPermission` table (fine-grained per-user permissions)
- `CustomFieldSchema` formal validation system
- Donations feature
- In-service Display app
- API versioning (prefix `/api/v1/`) — needed before mobile app goes to production with real users

### Bible App
- Reading plans, verse highlights, scripture search
- Licensed translations (NIV/ESV/NLT)
- African language translations
- Audio Bible
- Cross-reference chains

### Learn App
- Rich text editor for authorship
- Quiz auto-grading, assignment peer review
- Learning analytics dashboard
- Offline lesson caching (service worker)

### Activity App
- Full calendar grid UI
- Habit streak visualisation
- Ministry analytics
- Cross-tenant campaign assignment
- RRULE custom recurrence builder

### Community App
- Pastoral notes (privacy design required)
- Attendance tracking (privacy-sensitive)
- Community analytics dashboard
- Collective-level gathering visibility
- Pastoral assignment model

### Governance App
- Full HRS graph visualisation
- Level 4 tenant-scoped governance records
- Governance App Phase 2

### Notifications
- Real-time delivery (Django Channels + WebSockets) — Version 3
- Push notification to iOS — when iOS app is built

### Paraclete
- AI-assisted pattern detection (LLM) — Version 3
- Link suggestion engine — Version 3
- Weekly habit streak tracking
- Prophetic prompt generation (LLM) — Version 3

### Infrastructure
- Docker Compose — Version 3
- Redis + Celery — Version 3
- API versioning (`/api/v1/`) — before mobile production launch
- iOS app — Version 3

---

## Phase Summary — All Phases

| Phase | Version | What it builds | Weeks* |
|-------|---------|----------------|--------|
| 0.1–0.3 | — | Server, GitHub, Nginx/Gunicorn/SSL | ✅ Done |
| 1 | — | Auth, Tenants, HTMX Shell | ✅ Done |
| 2 | — | Records Engine | ✅ Done |
| 3 | — | Activity Engine | ✅ Done |
| 5.1 | — | Bible App | ✅ Done |
| 5.2 | MVP | Learn App (full) | 2–3 |
| 5.3 | MVP | Activity App UI | 1 |
| 5.4 | MVP | Community App | 1–2 |
| 5.5 | MVP | Governance App (full lifecycle) | 2 |
| 5.6 | MVP | Profile + Settings | 0.5 |
| 5.7 | MVP | Notifications Stub | 0.5 |
| 6.1 | MVP | Paraclete Service | 1 |
| 6.2 | MVP | Dashboard | 0.5 |
| 7 | MVP | Production Hardening | 0.5 |
| S.1 | Pre-V2 | Email (Brevo), MinIO, Backups | 1 |
| S.2 | Pre-V2 | Code Alignment Audit | 1 |
| V2.1 | V2 | Learn: Programmes + Video Embed | 1 |
| V2.2 | V2 | Induction System | 2–3 |
| V2.3 | V2 | Formation UI + App Drawer Gating | 1 |
| V2.4 | V2 | Notifications (Full) | 1 |
| V2.5 | V2 | Tenant Self-Service + Content Scoping | 2 |
| V2.6 | V2 | Video / Live App | 2 |
| V2.M | V2 | Flutter Mobile App (parallel) | 8–12 |
| V3+ | V3 | Scale, AI, iOS, advanced features | TBD |

*Estimates assume 1 developer, daily build, minimal QA*

---

## Branch Structure

```
main                        ← production (always deployable)
├─ mvp                      ← MVP reference (6c43ce9) [frozen]
└─ version-2                ← active development branch
   ├─ v2-pre-stabilisation  ← S.1 email + MinIO + backups
   ├─ v2-audit              ← S.2 code alignment
   ├─ v2-learn-formation    ← V2.1 programmes + video
   ├─ v2-induction          ← V2.2 induction system
   ├─ v2-formation-ui       ← V2.3 dashboard + drawer
   ├─ v2-notifications      ← V2.4 full notifications
   ├─ v2-tenants            ← V2.5 tenant self-service
   └─ v2-video              ← V2.6 live video app

ichebo-mobile (separate repo)
   └─ main                  ← Android production
```

---

## Key Reference Documents

| Document | What it covers |
|----------|---------------|
| `2026-04-25-ichebo-master-roadmap.md` | This document — the definitive reference |
| `2026-04-25-ichebo-adr-version-2.md` | All architecture decisions |
| `2026-04-25-ichebo-data-contract-v10-amendments.md` | Data schema changes for Version 2 |
| `2026-04-07-ics-learn-app-system-design_v2.md` | Learn App authoritative spec |
| `2026-04-08-ics-activity-app-system-design.md` | Activity App authoritative spec |
| `2026-04-08-ics-community-app-system-design.md` | Community App authoritative spec |
| `2026-04-10-ics-governance-app-system-design.docx` | Governance App authoritative spec |
| `2026-04-10-ics-paraclete-service-system-design.docx` | Paraclete authoritative spec |
| `2026-04-12-ics-production-engineering-guide.md` | Server operations reference |
| `kingdom_governance_system.md` | KGS framework — domain authority |
