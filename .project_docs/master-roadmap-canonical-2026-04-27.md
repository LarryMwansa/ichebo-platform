# Ichebo Platform — Master Build Roadmap

**Version:** v6 — 2026-04-27 (Canonical Consolidated)
**Previous version:** v5 — 2026-04-25
**Status:** Approved — Definitive Reference
**Supersedes:** All previous roadmap versions (v1–v5)

> This is the single authoritative roadmap for the entire Ichebo platform — from a blank Hetzner server to a fully operational, multi-tenant, mobile-capable formation platform. It covers every phase, every app, every technology decision, and every deferred item. No other roadmap supersedes this document.
>
> **How this was produced:** v3 (2026-04-12) was the most detailed document with full implementation steps and code samples. v4 (2026-04-25) added the Version 2 phases. v5 (2026-04-25) added platform overview, layer structure, Flutter, and the deferred reference. This document merges all three: v3 body with full code blocks restored, v4 Version 2 additions, v5 platform architecture additions, governance types corrected to canonical v9 list, and MinIO bucket naming confirmed as `ics-media`.

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
| Django 4.2 LTS | Long-term support — stable, well-documented. Do not upgrade to 5.x. |
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

## Dependency Rules (Non-Negotiable)

These rules govern build order. Violating them causes rework.

```
Django auth → Django tenant → Django records engine → Django activity engine
Django models → DRF serializers → DRF views → DRF URLs
DRF endpoints live → Django template views → HTMX partials
Records engine complete → Activity engine begin
Activity engine complete → Learn App begin (Learn uses Activity for progress tracking)
All Phase 5 apps complete → Paraclete service begin
Paraclete service complete → Dashboard begin
One app per git commit — never mix app work across a single commit
```

---

## The Six Platform Apps — Full Feature Inventory

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
LAYER 6 — VERSION 3: SCALE           (future — Redis, Docker, AI, advanced features)
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

### Task 0.1 — VPS baseline

1. SSH into VPS (Ubuntu 22.04)
2. Update packages: `sudo apt update && sudo apt upgrade -y`
3. Install dependencies:

```bash
sudo apt install -y python3.10 python3.10-venv python3-pip postgresql postgresql-contrib nginx git
```

4. Create deploy user: `sudo adduser ics && sudo usermod -aG sudo ics`
2. Switch to deploy user: `su - ics`

### Task 0.2 — PostgreSQL database

```bash
sudo systemctl start postgresql && sudo systemctl enable postgresql
sudo -u postgres psql
```

```sql
CREATE DATABASE ics_db;
CREATE USER ics_user WITH PASSWORD 'your-strong-password';
ALTER ROLE ics_user SET client_encoding TO 'utf8';
ALTER ROLE ics_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE ics_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE ics_db TO ics_user;
\q
```

Test: `psql -U ics_user -d ics_db -h localhost`

### Task 0.3 — Django project scaffold

**Files created:**

```
~/ics/requirements.txt
~/ics/ics_project/settings/base.py
~/ics/ics_project/settings/production.py
~/ics/ics_project/settings/local.py
```

Key settings in `base.py`:

```python
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    cast=lambda v: [s.strip() for s in v.split(',')]
)
```

`.env` file (project root, mode 600):

```
SECRET_KEY=generate-a-long-random-string-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
DB_NAME=ics_db
DB_USER=ics_user
DB_PASSWORD=your-strong-password
DB_HOST=localhost
DB_PORT=5432
CORS_ALLOWED_ORIGINS=http://localhost:8001,https://your-domain.com
```

**Commit:** `git init && git add . && git commit -m "chore: django project scaffold"`

### Task 0.4 — Health check endpoint

**Files:**

- Create: `~/ics/core/views.py`
- Create: `~/ics/core/urls.py`
- Modify: `~/ics/ics_project/urls.py`

```python
# core/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({'status': 'ok'})
```

```python
# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
]
```

```python
# ics_project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
]
```

**Commit:** `git commit -m "feat: health check endpoint"`

### Task 0.5 — Nginx + Gunicorn (production) ✅ COMPLETE

**`gunicorn.conf.py`** (project root):

```python
bind = "127.0.0.1:8001"
workers = 3
timeout = 120
accesslog = "/var/log/gunicorn/ics_access.log"
errorlog  = "/var/log/gunicorn/ics_error.log"
```

**`/etc/nginx/sites-available/ics`:**

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location /static/ {
        alias /home/ics/ics/staticfiles/;
        expires 30d;
        add_header Cache-Control "public";
    }

    location /media/ {
        proxy_pass http://localhost:9000/ics-media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Deployment steps (run in order):**

```bash
# 1. Create log/cache directories
sudo mkdir -p /var/log/gunicorn /var/log/ics /var/cache/ics
sudo chown www-data:www-data /var/cache/ics
sudo chown $USER:$USER /var/log/gunicorn /var/log/ics

# 2. Install dependencies
pip install -r requirements.txt

# 3. Collect static files
export DJANGO_SETTINGS_MODULE=ics_project.settings.production
python manage.py collectstatic --no-input

# 4. Run migrations
python manage.py migrate

# 5. Enable Nginx site
sudo ln -s /etc/nginx/sites-available/ics /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 6. SSL
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# 7. Start Gunicorn
export DJANGO_SETTINGS_MODULE=ics_project.settings.production
gunicorn ics_project.wsgi:application -c gunicorn.conf.py

# 8. Verify
curl https://your-domain.com/api/health/
# Expected: {"status": "ok"}
```

**Systemd service** (`/etc/systemd/system/ics.service`):

```ini
[Unit]
Description=ICS Gunicorn Service
After=network.target

[Service]
User=ics
WorkingDirectory=/home/ics/ics
ExecStart=/home/ics/ics/venv/bin/gunicorn ics_project.wsgi:application -c gunicorn.conf.py
Restart=on-failure
Environment=DJANGO_SETTINGS_MODULE=ics_project.settings.production

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ics
sudo systemctl start ics
```

**Commit:** `git commit -m "chore: nginx + gunicorn production setup"`

---

# LAYER 1 — Django Foundation

## Phase 1 — Auth + Tenants + HTMX Shell ✅ COMPLETE

**What was built:** Custom User model (email as username, `competence_level`, `status`, `preferences` JSONField), UserProfile, UserPermission (role + level per tenant), Tenant model with materialised path hierarchy, Django session auth for web, DRF token auth for mobile, `base.html` with navbar, app drawer, bottom nav, theme toggle (`storage.js`), mobile-first CSS design system (CSS variables, dark mode, 44px touch targets, 8px spacing grid).

**Exit criteria:** Register, login, create tenant, assign permission. `@login_required` redirects unauthenticated requests to `/accounts/login/`. `base.html` renders with navbar, app drawer, bottom nav, and theme toggle.

### Task 1.1 — Accounts app + custom User model ✅

**Files:**

- `accounts/models.py`
- `accounts/forms.py`
- `accounts/views.py`
- `accounts/urls.py`
- `accounts/serializers.py`
- `templates/accounts/login.html`
- `templates/accounts/register.html`

User model fields: `email` (username field), `display_name`, `competence_level` (0–5), `status` (`active | seeker | suspended | pending_verification`), `avatar_url`, `preferences` (JSONField).

`UserProfile` extension: `bio`, `preferred_bible_translation` (FK to BibleTranslation).

Django session auth for templates + DRF token auth for mobile (both active). `SessionAuthentication` added to `REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES`.

**Commit:** `git commit -m "feat: accounts app — user model, login, register"`

### Task 1.2 — Tenants app + materialised path ✅

**Files:**

- `tenants/models.py`
- `tenants/serializers.py`
- `tenants/views.py`
- `tenants/urls.py`

`Tenant` model: `name`, `path` (materialised path), `tier`, `slug`. `UserPermission` model: `user`, `tenant`, `role`, `level`, `is_active`, `granted_at`, `granted_by`, `metadata` (`shepherd_id`, `service_order`).

Handbook tenant at `/global/handbook/` created by management command on first deploy.

**Commit:** `git commit -m "feat: tenants app — tenant model, materialised path, permissions"`

### Task 1.3 — HTMX shell — base.html + nav components ✅

**Files:**

- `templates/base.html`
- `templates/base_partial.html`
- `templates/components/_navbar.html`
- `templates/components/_app_drawer.html`
- `templates/components/_bottom_nav.html`
- `templates/components/_toast.html`
- `templates/components/_spinner.html`
- `templates/components/_empty_state.html`

**JS load order (locked — do not reorder):**

```html
<!-- In <head> -->
<script src="{% static 'js/htmx.min.js' %}" defer></script>
<script src="{% static 'js/storage.js' %}"></script>

<!-- At end of <body> -->
<script src="{% static 'js/navbar.js' %}" defer></script>
```

**CSRF wiring for HTMX** (in `base.html`, once only):

```html
<script>
  document.addEventListener('htmx:configRequest', (e) => {
    e.detail.headers['X-CSRFToken'] = '{{ csrf_token }}';
  });
</script>
```

Smoke test: navbar renders, app drawer opens/closes, theme toggle works, `@login_required` redirects unauthenticated users.

**Commit:** `git commit -m "feat: base.html, nav components, HTMX shell"`

---

## Phase 2 — Records Engine ✅ COMPLETE

**What was built:** `Record` model (single table, `record_family` / `record_class` / `record_type` discriminator), `Relationship` model (typed relationship types, `bible_verse_id` amendment, `metadata` JSONField), full DRF CRUD at `/api/records/` and `/api/relationships/`, Django template views + HTMX partials.

**Exit criteria:** Full Record + Relationship CRUD via both DRF and Django template views. HTMX partials load record lists and detail without full page reload.

### Task 2.1 — Records Django app + models ✅

**Files:**

- `records/models.py` — `Record`, `Relationship`
- `records/serializers.py`
- `records/views.py` (DRF ViewSets)
- `records/filters.py`
- `records/permissions.py`
- `records/urls.py`
- `records/admin.py` — register both `Record` and `Relationship`

**Commit:** `git commit -m "feat: records engine — models, DRF endpoints"`

### Task 2.2 — Records Django template views + HTMX partials ✅

**Files:**

- `records/template_views.py`
- `templates/records/list.html`
- `templates/records/_list.html` (HTMX partial)
- `templates/records/detail.html`
- `templates/records/_detail.html` (HTMX partial)
- `templates/records/create.html`
- `templates/records/_form.html` (HTMX partial)
- `templates/records/edit.html`
- `templates/components/_record_card.html`

**`HX-Request` header detection pattern** (used across all apps):

```python
def get_template_names(self):
    if self.request.headers.get('HX-Request'):
        return ['records/_list.html']
    return ['records/list.html']
```

**Commit:** `git commit -m "feat: records app — Django template views, HTMX partials"`

---

## Phase 3 — Activity Engine ✅ COMPLETE

**What was built:** `Activity` model (9 activity types), `ActivityLog` signal (fires on every status transition), full DRF CRUD at `/api/activities/`, Django template views + HTMX partials.

**Exit criteria:** Full Activity CRUD via DRF. `ActivityLog` signal fires on status change. Django template views render from ORM. HTMX status-update partials work.

### Task 3.1 — Activity Django app + models ✅

**Files:**

- `activity/models.py` — `Activity`, `ActivityLog`
- `activity/serializers.py`
- `activity/views.py` (DRF ViewSets)
- `activity/filters.py` — `ActivityFilter`
- `activity/signals.py` — `ActivityLog` signal on every status transition (pre_save captures previous status; post_save creates log entry)
- `activity/urls.py`

Activity types: `task | habit | goal | event | campaign | project | programme | reminder | skill`.

**Endpoints:**

```
GET    /api/activities/
POST   /api/activities/
GET    /api/activities/{id}/
PATCH  /api/activities/{id}/
DELETE /api/activities/{id}/
GET    /api/activities/{id}/log/
GET    /api/calendar/events/
GET    /api/activity/health/
```

**Commit:** `git commit -m "feat: activity engine — models, signals, DRF endpoints"`

### Task 3.2 — Activity Django template views + HTMX partials ✅

**Files:**

- `activity/template_views.py`
- `templates/activity/list.html`
- `templates/activity/_list.html` (HTMX partial)
- `templates/activity/detail.html`
- `templates/components/_activity_card.html`

**Commit:** `git commit -m "feat: activity app — Django template views, HTMX partials"`

---

# LAYER 2 — MVP Apps

## Phase 5.1 — Bible App ✅ COMPLETE

**What was built:** `BibleTranslation`, `BibleBook`, `BibleVerse` models, three translations loaded (KJV default, ASV, WEB — ~93,306 verse rows), scripture reader with chapter navigation, personal annotations (stored as Records with `record_family: "bible"`), tenant-scoped notes, Handbook linkages (Level 5), three-panel mobile-first HTMX UI.

**Deferred to Version 2:** Reading plans, verse highlights, scripture search.
**Deferred to Version 3+:** Licensed translations (NIV/ESV/NLT — require publisher licensing agreements and fees), African language translations, audio Bible.

**Endpoints:**

```
GET  /api/bible/translations/
GET  /api/bible/books/
GET  /api/bible/verses/?book_code={code}&chapter={n}
GET  /api/bible/verse-context/{verse_id}/
GET  /bible/
GET  /bible/{book_code}/{chapter}/
GET  /bible/htmx/chapter/
GET  /bible/htmx/annotation/{verse_id}/
POST /bible/htmx/note/save/
DELETE /bible/htmx/note/{note_id}/delete/
POST /bible/htmx/translation/set/
GET  /api/bible/health/
```

**Commit:** `git commit -m "feat: bible app"`

---

## Phase 5.2 — Learn App 🔄 REQUIRES ALIGNMENT AUDIT

**Entry requirement:** Code alignment audit (Phase S.2) complete.

**Reference:** `2026-04-07-ics-learn-app-system-design_v2.md` — authoritative. Read in full before writing any code.

### Data model

- All learning content = `Record` objects (`record_family: "learning"`, types: `programme | course | lesson | assignment | quiz | certification`)
- Curriculum = `Relationship` objects (`relationship_type: "part_of"`) — no separate curriculum table
- Learner progress = `Activity (activity_type: "programme")` linked to content Records via `linked_record` FK
- Competence advancement: steward at Level 3+ confirms via `POST /api/learn/certifications/{id}/confirm/` → `user.competence_level` incremented

### New models

- `CertificationConfirmation` — links a certification Record to the confirming steward; triggers `competence_level` increment via `learn/services.py::confirm_certification_record()`

### Backend (DRF)

```
GET  /api/learn/health/
GET  /api/learn/programmes/{id}/curriculum/
GET  /api/learn/certifications/queue/
POST /api/learn/certifications/{id}/confirm/
```

`learn/signals.py` — programme Activity at `progress: 100` → draft certification Record created automatically.

### Web UI features (F1–F11)

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

### Build phases (A–G)

| Phase | What it builds |
|-------|----------------|
| A | Django `learn` app, `CertificationConfirmation` model, confirm + queue endpoints |
| B | Records endpoint filter verification, curriculum endpoint |
| C | `learn/` Django template views, HTMX partials: My Learning, Catalogue, Enrolment, Lesson Viewer |
| D | Quiz renderer, Assignment submission |
| E | Auto-certification signal, steward certification queue UI, competence level advancement |
| F | Content authorship UI (Level 4+), Handbook review queue UI (Level 5) |
| G | Role-aware navigation, Pathway banner, mobile smoke test |

### Django template routes

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

**Exit criteria:** `POST /api/learn/certifications/{id}/confirm/` correctly increments `competence_level` in DB. Verifiable in Django admin. All F1–F11 features functional.

**Commit:** `git commit -m "feat: learn app — complete"`

---

## Phase 5.3 — Activity App UI ⏳ PENDING

**Entry requirement:** Phase 3 (Activity Engine) complete. Code alignment audit complete.

**Note:** The Activity Engine (Phase 3) built the Django models, signals, and DRF endpoints. This phase builds the two-surface UI layer only.

### My Activities surface (personal, `tenant_id: null`)

- Types: task, habit, goal, skill, reminder
- Flat structure only (no nesting)
- Mark complete via HTMX (no page reload)
- Read-only programme cards showing Learn enrolments

### Ministry surface (organisational, tenant-scoped)

- Types: campaign, project, task, event
- Two-level nesting: campaign/project → task
- "Assigned to me" tab — first-class view
- Level 3+ can create campaigns and projects; Level 1+ can create tasks

### Calendar (dated list view)

- Shows activities with due dates in chronological order
- Not a grid calendar — a dated list. Full grid deferred to Version 3.

### Django template routes

```
GET  /activity/                         My Activities home
GET  /activity/ministry/                Ministry surface
GET  /activity/calendar/                Dated list view
GET  /activity/{id}/                    Activity detail
GET  /activity/htmx/my-list/            HTMX partial — personal activity list
GET  /activity/htmx/ministry-list/      HTMX partial — ministry activity list
GET  /activity/htmx/status/{id}/        HTMX partial — status chip
POST /activity/htmx/create/             Create activity (HTMX)
POST /activity/htmx/{id}/complete/      Mark complete (HTMX)
POST /activity/htmx/{id}/status/        Update status (HTMX)
GET  /api/activity/health/
```

**Exit criteria:** Member can create personal tasks and habits, mark them complete, and see progress. Steward can create campaigns and assign tasks to members. `ActivityLog` entries visible in Django admin.

**Commit:** `git commit -m "feat: activity app UI — my activities + ministry surfaces"`

---

## Phase 5.4 — Community App ⏳ PENDING

**Entry requirement:** Phases 2–3 complete. Code alignment audit complete.

**Reference:** `2026-04-08-ics-community-app-system-design.md`

**Note:** Community App owns no models. It is a UI + transaction coordination layer that writes to Records, Activity, and UserPermission via their DRF endpoints.

### Data patterns

- `record_family: "community"`, MVP types: `announcement | gathering`
- `gathering` dual-write: creating a Gathering writes both a `community/gathering` Record and an `activity/event` Activity atomically (`transaction.atomic`)
- `gathering` custom_fields: `format` (`in_person | digital | hybrid`), `location`, `stream_url`, `start_at`, `duration_minutes`
- `UserPermission.metadata`: `shepherd_id`, `service_order`
- `MembershipRequest` model: schema stubbed in MVP, no UI

### My Community surface (Level 1+)

- Member directory (members of user's tenant)
- Tenant profile card
- Announcements list (read + create for Level 3+)
- Gathering schedule (read + create for Level 3+)

### Community Management surface (Level 3+)

- Full member roster with roles and service orders
- Role assignment and shepherd assignment
- Membership request queue (approve/reject)

### Django template routes

```
GET  /community/                             My Community home
GET  /community/members/                     Member directory
GET  /community/announcements/               Announcements list
POST /community/htmx/announcements/create/   Create announcement
GET  /community/gatherings/                  Gathering schedule
POST /community/htmx/gatherings/create/      Create gathering (dual-write)
GET  /community/{id}/                        Gathering or announcement detail
GET  /community/htmx/members/               HTMX partial — member list
GET  /community/htmx/announcements/         HTMX partial — announcement list
GET  /community/htmx/gatherings/            HTMX partial — gatherings list
GET  /community/manage/                      Management surface (Level 3+)
GET  /community/manage/members/              Full member roster
POST /community/htmx/manage/assign-role/     Role assignment
POST /community/htmx/member/shepherd/        Shepherd assignment
POST /community/htmx/member/order/           Service order assignment
GET  /api/community/health/
```

**Exit criteria:** Member can see their community and read announcements. Level 3 coordinator can create announcements, gatherings, and manage member roles. Dual-write creates both Record and Activity atomically. Both verifiable in Django admin.

**Commit:** `git commit -m "feat: community app"`

---

## Phase 5.5 — Governance App ⏳ PENDING

**Entry requirement:** Phases 2–3 complete. Code alignment audit complete.

**Reference:** `2026-04-10-ics-governance-app-system-design.docx`

**Note:** Governance App owns no models. It is a UI + coordination layer over the Records Engine.

### Three surfaces

**Reference Library (Level 3+ read, Level 5 write)**

- Record types: `class`, `principle`, `concept`, `divine_pattern`
- Tenant scope: Handbook only
- Shared, objective, HRS-produced knowledge

**Mandate Branch (Level 4+ read, Level 5 write)**

- Record types: `mandate`, `statement`, `framework`, `narrative`, `subject`, `entity`, `protocol`, `procedure`, `programme`
- Tenant scope: Handbook only
- Directional governance documents

**Keys Library (owner only, Level 3+)**

- Record type: `key`
- Tenant scope: null (personal records)
- Private interpretive symbol library

### Record lifecycle

```
draft → active → locked → superseded
```

- Lock (Level 5): record becomes uneditable, `locked_at` set
- Supersede (Level 5): creates new draft with `previous_version_id` pointing to old; old record's `superseded_by` patched to new
- Version history chain: traversable timeline on record detail view

### Linked Records panel

- Flat list of all Relationship rows from/to this record
- Read-only. Includes scripture links via `bible_verse_id`.

### Journal → Governance linkage

- `Relationship (derived_from, directed)`: governance record ← journal entry
- Governance App authorship form includes "Source Journal Entry" typeahead

### Django template routes

```
GET  /governance/                              Surface selector home
GET  /governance/reference/                    Reference Library browse
GET  /governance/reference/{type}/             Browse by type
GET  /governance/reference/{id}/               Property detail + linked records
GET  /governance/mandate/                      Mandate branch browse
GET  /governance/mandate/{type}/               Browse by type
GET  /governance/mandate/{id}/                 Record detail + version history
GET  /governance/keys/                         Keys Library (personal)
GET  /governance/keys/{id}/                    Key detail
GET  /governance/htmx/reference/list/          HTMX partial
GET  /governance/htmx/mandate/list/            HTMX partial
POST /governance/htmx/record/create/           Create governance or key record (Level 5)
POST /governance/htmx/record/{id}/lock/        Lock a record (Level 5)
GET  /governance/htmx/record/{id}/supersede/   Begin supersession
POST /governance/htmx/record/{id}/supersede/   Confirm supersession
GET  /governance/htmx/record/{id}/links/       Linked records panel partial
GET  /governance/htmx/record/{id}/history/     Version history partial
GET  /governance/htmx/journal/search/          Journal entry typeahead for linking
GET  /api/governance/health/
```

**Exit criteria:** All three surfaces render data from Handbook tenant. Lock and supersede lifecycle transitions work. Linked Records panel populated. Version history chain traversable.

**Commit:** `git commit -m "feat: governance app — full lifecycle"`

---

## Phase 5.6 — Profile + Settings ⏳ PENDING

**Entry requirement:** Phase 1 complete.

**Note:** Profile and Settings are views within the existing `accounts/` Django app — not a new app. No new models in MVP.

### Profile view (`/accounts/profile/`)

- Identity: avatar (initials placeholder if null), display name (inline HTMX edit), email (read-only), member since, platform status badge
- Formation: competence level label + numeric level, active tenant display, service order (from `UserPermission.metadata.service_order`)
- Only `display_name` and `avatar_url` are inline-editable in MVP

### Settings view (`/accounts/settings/`)

- Appearance: theme (light/dark/system)
- Language & Region: language, timezone
- Bible: preferred translation
- All persisted to `User.preferences` JSONField — not localStorage

### Django template routes

```
GET   /accounts/profile/               Profile view
GET   /accounts/settings/              Settings view
POST  /accounts/htmx/profile/edit/     HTMX partial — inline display name / avatar edit
POST  /accounts/htmx/settings/save/    HTMX partial — save preferences
```

**Exit criteria:** Profile renders all identity and formation fields. Settings saves theme/language/timezone/translation to the database. Inline display name edit works via HTMX.

**Commit:** `git commit -m "feat: profile + settings"`

---

## Phase 5.7 — Notifications Stub ⏳ PENDING

**Entry requirement:** Phase 1 complete.

Notifications is a shell only in MVP. Full implementation is Version 2. No `Notification` model in MVP — no migration.

- `GET /api/notifications/` returns `{"count": 0, "next": null, "results": []}`
- `GET /api/notifications/unread-count/` returns `{"count": 0}`
- Navbar bell icon badge polls via HTMX `hx-trigger="every 60s"` (wired in `_navbar.html`)
- Notifications list view renders empty state component

### Routes

```
GET  /notifications/                          Notifications list (empty state)
GET  /api/notifications/                      DRF endpoint — returns []
GET  /api/notifications/unread-count/         Badge count
GET  /accounts/htmx/notifications-count/     HTMX partial — badge count
```

**Exit criteria:** Nav bell links to `/notifications/`. Empty state renders. Badge count shows 0 and is hidden.

**Commit:** `git commit -m "feat: notifications stub"`

---

## Phase 6.1 — Paraclete Service ⏳ PENDING

**Entry requirement:** Phases 3 + 5.1–5.7 all complete. Paraclete reads from all apps.

**Reference:** `2026-04-10-ics-paraclete-service-system-design.docx`

### What this builds

- `ParacletePrompt` model (24+ prompts seeded, 3 per KGS pathway, `is_active` flag, `min_level`, `pathway`)
- `paraclete/service.py` — pure Python, reads ORM, writes nothing, returns `ParacleteDigest`
- `build_digest(user)` — main orchestration function

### ParacleteDigest fields

```python
pending_count         # total pending + in_progress activities
overdue_count         # overdue activities (not reminders)
due_today             # up to 5 ActivityCards due today
overdue_items         # up to 5 ActivityCards overdue
habit_streaks         # active daily habits with consecutive-day streak count
pending_reminders     # reminders due within 24 hours
active_enrolments     # ProgrammeCards (in_progress/pending Learn enrolments)
next_lesson           # first uncompleted lesson in most recent active programme
discipline_prompt     # string from ParacletePrompt, weighted to least-used pathway
prompt_pathway        # KGS pathway label
dar_today             # DARCard if a DAR record was created today, else null
suggestions           # up to 5 rule-based suggestions [{text, priority, action_url}]
suggestion_method     # "rules"
team_pending_count    # Level 3+ only: team pending activities
team_overdue_count    # Level 3+ only: team overdue activities
```

**Level 0 (seeker):** prompt only — no activity surface.
**Level 1+:** full personal digest.
**Level 3+:** team counts added.

### DRF endpoints

```
GET /api/paraclete/digest/              Full daily digest (5-minute filesystem cache per user)
GET /api/paraclete/reminders/           Pending reminders only
GET /api/paraclete/prompt/              Discipline prompt only
GET /api/paraclete/suggest/{record_id}/ Stub — returns {"suggestions": [], "method": "deferred"}
POST /api/paraclete/respond/            Stub — returns {"status": "ok"}
GET /api/paraclete/health/
```

**Caching:** Django filesystem cache (`/var/cache/ics/`), 5-minute TTL per user. No Redis.

**Exit criteria:** `GET /api/paraclete/digest/` returns correct data for Level 0, 1, and 3 test users. Habit streak calculates correctly. Cache confirmed working (second request returns same `generated_at`).

**Commit:** `git commit -m "feat: paraclete service + digest endpoint"`

---

## Phase 6.2 — Dashboard ⏳ PENDING

**Entry requirement:** Phase 6.1 complete.

### What this builds

Dashboard calls `paraclete.service.build_digest()` via direct Python import (not HTTP). Role-aware widgets. Tenant-aware.

**Files:**

- `dashboard/views.py`
- `dashboard/urls.py`
- `templates/dashboard/index.html`
- `templates/dashboard/_digest_widget.html` (HTMX partial)
- `templates/dashboard/_activity_widget.html` (HTMX partial)
- `templates/dashboard/_prayer_widget.html` (HTMX partial)

### Widgets

- Today's focus (discipline prompt from Paraclete)
- Pending activities (tasks + habits due today)
- Recent records (last 5 created by user)
- Active prayer count
- Formation Journey card (current level, active programme, next level requirement) — Version 2 full version
- Ministry summary (Level 3+ only)

### Django template routes

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

### Task 7.1 — Error logging + Django admin

```python
# production.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/ics/django_errors.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
ADMINS = [('Chizola', 'bwanjidigital@gmail.com')]
```

```bash
python manage.py createsuperuser
# Verify Django admin at /admin/
```

**Commit:** `git commit -m "chore: error logging + admin setup"`

### Task 7.2 — Security settings

```python
# production.py
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

**Commit:** `git commit -m "chore: production security settings"`

### Task 7.3 — Final smoke test

```bash
sudo systemctl restart ics

curl https://your-domain.com/api/health/
curl https://your-domain.com/api/bible/health/
curl https://your-domain.com/api/activity/health/
curl https://your-domain.com/api/community/health/
curl https://your-domain.com/api/governance/health/
curl https://your-domain.com/api/paraclete/health/

# Verify SSL headers
curl -I https://your-domain.com/
# Expected: HTTP/2 200, Strict-Transport-Security header present
```

**Commit:** `git commit -m "chore: production hardening — MVP complete"`

---

# LAYER 3 — Stabilisation

# (Required before any Version 2 feature work begins)

## Phase S.1 — Infrastructure Additions

**Entry requirement:** Phase 7 complete (or run in parallel with Phase 7).

### S.1.1 — Email Service (Brevo)

**Why Brevo:** Free tier gives 300 emails/day, no credit card required, reliable delivery, simple SMTP setup. Running your own SMTP server requires managing IP reputation, SPF/DKIM/DMARC records, bounce handling, and spam blacklist monitoring — not appropriate for a sole developer.

**Setup:**

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

5. Test:

```bash
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Body', None, ['your@email.com'])
```

**Commit:** `git commit -m "chore: email service — Brevo SMTP configured"`

### S.1.2 — Media Storage (MinIO on Hetzner)

**Why MinIO:** Profile avatars and tenant logos need real file storage. MinIO runs locally on your Hetzner VPS, is S3-compatible (boto3/django-storages), and costs nothing beyond VPS disk space. If you later move to AWS S3, you change three environment variables and zero code.

**Install on VPS:**

```bash
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

sudo useradd -r minio-user -s /sbin/nologin
sudo mkdir -p /data/minio
sudo chown minio-user:minio-user /data/minio

sudo systemctl enable minio
sudo systemctl start minio
```

> **Note:** The `minio-user` is a dedicated system service account (created with `-r`, no login shell).
> It is separate from your VPS login user (`scepter`). MinIO runs as `minio-user` and owns `/data/minio`;
> your Django process runs as `scepter`. No changes needed to either account.

**If `sudo systemctl enable minio` fails** with "Unit file minio.service does not exist", create the service and environment files first:

```bash
# 1. Environment file
sudo nano /etc/default/minio
```

```bash

# Ensure that you create your Root user and password
MINIO_VOLUMES="/data/minio"
MINIO_ROOT_USER=your_access_key_here
MINIO_ROOT_PASSWORD=your_secret_key_here
MINIO_OPTS="--address :9000 --console-address :9001"

```

```bash
# 2. Systemd service file
sudo nano /etc/systemd/system/minio.service
```

```ini
[Unit]
Description=MinIO Object Storage
Documentation=https://docs.min.io
Wants=network-online.target
After=network-online.target
AssertFileIsExecutable=/usr/local/bin/minio

[Service]
WorkingDirectory=/data/minio
User=minio-user
Group=minio-user
EnvironmentFile=/etc/default/minio
ExecStartPre=/bin/bash -c "if [ -z \"${MINIO_VOLUMES}\" ]; then echo \"Variable MINIO_VOLUMES not set in /etc/default/minio\"; exit 1; fi"
ExecStart=/usr/local/bin/minio server $MINIO_OPTS $MINIO_VOLUMES
Restart=always
RestartSec=5
LimitNOFILE=65536
TasksMax=infinity
TimeoutStopSec=infinity
SendSIGKILL=no

[Install]
WantedBy=multi-user.target
```

```bash
# 3. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable minio
sudo systemctl start minio
sudo systemctl status minio
```

**MinIO buckets to create:**

- `ics-media` — public read (avatars, logos)
- `ics-private` — private (attachments, presigned URLs)


```bash

# Refresh Minio
sudo systemctl restart minio

# Install the MinIO client
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/

# Point it at your local MinIO
mc alias set local http://localhost:9000 your_access_key your_secret_key



# Create the buckets
mc mb local/ics-media
mc mb local/ics-private

# Make ics-media publicly readable
mc anonymous set download local/ics-media


```

Think of them as the MinIO admin account:


|Variable|What to put|Example|
|---|---|---|
|`MINIO_ROOT_USER`|Any username you choose (min 3 chars)|`icsadmin`|
|`MINIO_ROOT_PASSWORD`|Any strong password you choose (min 8 chars)|`SuperSecret123!`|

These become:

- The login for the MinIO web console at `:9001`
- The `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` you put in your Django `.env`

**So pick them once, write them down, and use the same values in your `.env`:**

```bash
# /etc/default/minio
MINIO_ROOT_USER=icsadmin
MINIO_ROOT_PASSWORD=your-strong-password-here
```

```bash
# .env (Django)
MINIO_ACCESS_KEY=icsadmin
MINIO_SECRET_KEY=your-strong-password-here
```

They only live on your server — never commit them to git.

**Django settings:**

```python
# requirements.txt: add django-storages[s3] boto3 Pillow
STORAGES = {"default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"}}
AWS_S3_ENDPOINT_URL   = config('MINIO_ENDPOINT')      # e.g. http://localhost:9000
AWS_ACCESS_KEY_ID     = config('MINIO_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = config('MINIO_SECRET_KEY')
AWS_STORAGE_BUCKET_NAME = 'ics-media'
AWS_S3_FILE_OVERWRITE = False
MEDIA_URL = config('MEDIA_URL')                        # e.g. https://your-domain.com/media/
```

**Model updates:**

```python
# accounts/models.py
avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

@property
def avatar_url(self):
    return self.avatar.url if self.avatar else None

# tenants/models.py — same pattern for logo
logo = models.ImageField(upload_to='logos/', blank=True, null=True)

@property
def logo_url(self):
    return self.logo.url if self.logo else None
```

**Commit:** `git commit -m "chore: MinIO media storage — avatars and logos"`

### S.1.3 — Database Backups

The roadmap script runs as the `ics` user and your VPS user is `scepter`. Here's what to run on the server, adapted to your actual setup:

**1. Create the backup directory and script:**

```bash
mkdir -p /home/scepter/backups
nano /home/scepter/backup.sh
```

Paste this:

```bash
#!/bin/bash
BACKUP_DIR="/home/scepter/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
pg_dump -U ics_user ics_db | gzip > $BACKUP_DIR/ics_backup_$DATE.sql.gz
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
echo "Backup complete: ics_backup_$DATE.sql.gz"
```

**2. Make it executable:**

```bash
chmod +x /home/scepter/backup.sh
```

**3. Test it once manually:**

```bash
sed -i 's/pg_dump -U/pg_dump -h localhost -U/' /home/scepter/backup.sh
/home/scepter/backup.sh
ls -lh /home/scepter/backups/

```

You should see a `.sql.gz` file. If `pg_dump` asks for a password, you need to create a `.pgpass` file:

```bash
echo 'localhost:5432:ics_db:your_db_password' > ~/.pgpass
chmod 600 ~/.pgpass
```

**4. Schedule the cron (runs at 2am daily):**

```bash
crontab -e
```

Add this line:

```
0 2 * * * /home/scepter/backup.sh >> /var/log/ics/backup.log 2>&1
```

Make sure the log directory exists:

```bash
sudo mkdir -p /var/log/ics
sudo chown scepter:scepter /var/log/ics
```

**Weekly manual step:** Download a backup copy to your laptop. Never rely solely on server-side backups.

**Commit:** `git commit -m "chore: PostgreSQL backup script + cron schedule"`

---

## Phase S.2 — Code Alignment Audit

**Entry requirement:** S.1 complete.

**What this is:** During MVP build sessions, view code was written for apps that the roadmap marks as Pending. This code must be audited against the locked system design documents before Version 2 is built on top of it.

**Process for each app:**

1. Open the app's locked system design document
2. Compare existing views against spec'd URL routes, data patterns, access gates, HTMX partial patterns
3. Mark each view: ✅ Conforms | ⚠️ Needs adjustment | ❌ Rewrite required
4. Fix before moving on. Do not skip this step.

**Apps to audit:**

| App | File | Reference doc |
|-----|------|--------------|
| Learn | `learn/views.py` | `2026-04-07-ics-learn-app-system-design_v2.md` |
| Governance | `governance/views.py` | `2026-04-10-ics-governance-app-system-design.docx` |
| Community | `community/views.py` | `2026-04-08-ics-community-app-system-design.md` |
| Paraclete | `paraclete/service.py` | `2026-04-10-ics-paraclete-service-system-design.docx` |
| Records linking | `records/views.py`, `activity/models.py` | Data contract v10 canonical |
| Notifications | `notifications/` | `2026-04-10-ics-profile-settings-notifications-spec.docx` |

**Also confirm during audit:**

- Django version in production is 4.2 LTS (not 5.x)
- `competence_level` write path is isolated to `POST /api/learn/certifications/{id}/confirm/` only — confirmed via `learn/services.py::confirm_certification_record()`
- `Activity.linked_record` FK exists (data contract v10 Amendment 10.4)
- `Relationship.metadata` JSONField exists

**Commit:** `git commit -m "chore: code alignment audit — all apps verified"`

---

# LAYER 4 — Version 2: Formation Platform

## Phase V2.1 — Learn App: Formation Foundation

**Entry requirement:** S.1 + S.2 complete. This is the most important phase in Version 2. The Induction System depends on it. Do not start Induction until Learn is complete and tested.

### V2.1.1 — Five Qualification Programmes (Seeded)

```python
# python manage.py seed_programmes
```

| Programme | Level | Duration | Prerequisites |
|-----------|-------|----------|---------------|
| Certificate | 1 | 1 year | None |
| Diploma | 2 | 3 years | Certificate |
| Degree | 3 | 4 years | Diploma |
| Masters | 4 | 4–5 years | Degree |
| Doctorate | 5 | 7 years | Masters |

Seeded as system Records (`record_family: "learning"`, `record_type: "programme"`, `origin: "system"`).

### V2.1.2 — Three Induction Programmes (Seeded, Induction Tenant scope)

```python
# python manage.py seed_induction_programmes
```

| Programme | Entrant type | Court |
|-----------|-------------|-------|
| Reconditioning Programme | Existing believers | Outer Court |
| Beginners Programme | Kingdom-curious newcomers | Outer Court |
| Community Programme | All inductees | Inner Court (auto-enrolled on Outer Court completion) |

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

Before building any Induction views, run these migrations in order:

```python
# tenants/migrations: add "induction" to Tenant.tier choices
# accounts/migrations: add to User model:
#   induction_enrolled_at  = DateTimeField(null=True)
#   induction_completed_at = DateTimeField(null=True)
#   induction_pathway      = CharField(max_length=20, null=True)  # "reconditioning"|"beginners"
# accounts/migrations: add to UserProfile:
#   full_name   = CharField(max_length=255, blank=True)
#   address     = TextField(blank=True, null=True)
#   country     = CharField(max_length=2, blank=True, null=True)  # ISO 3166-1 alpha-2
#   id_number   = EncryptedCharField(max_length=100, null=True)   # MUST BE ENCRYPTED
#   age         = IntegerField(null=True)
#   gender      = CharField(max_length=20, null=True)
#   occupation  = CharField(max_length=100, blank=True, null=True)
#   education   = CharField(max_length=200, blank=True, null=True)
#   born_again  = BooleanField(null=True)
```

**CRITICAL — `id_number` encryption:**

```bash
pip install django-encrypted-model-fields
```

```python
from encrypted_model_fields.fields import EncryptedCharField
id_number = EncryptedCharField(max_length=100, blank=True, null=True)
```

Store `FIELD_ENCRYPTION_KEY` in `.env`. Never return `id_number` in any API response without an explicit Level 4+ admin endpoint.

### V2.2.2 — Induction Tenant Seed

```python
# python manage.py seed_induction_tenant
Tenant.objects.get_or_create(
    slug='induction',
    defaults={
        'name':   'Induction',
        'path':   '/global/induction/',
        'tier':   'induction',
        'status': 'active',
    }
)
```

Cannot be deleted or renamed via normal UI flows. Enforce at view layer: check `tenant.tier == 'induction'` before any destructive operation.

### V2.2.3 — Sign-up & Profile Registration (Three-Step Flow)

**Step 1 — Sign-up:**

- Email + password
- Email verification via Brevo
- User created: `status: "seeker"`, no competence level, no tenant assignment

**Step 2 — Profile Registration:**
Collects: Full Name, Email (read-only), Address, Country, ID/Passport Number (encrypted), Age, Gender, Occupation, Education/Qualification, Born Again (Yes/No), Entrant type ("I am already part of a church or faith community" → Reconditioning | "I am new to this or exploring" → Beginners).

**Step 3 — Induction Placement:**

- `UserPermission` created: `tenant_path="/global/induction/"`, `level=0`, `role="seeker"`, `is_active=True`
- `user.induction_enrolled_at` set
- `user.induction_pathway` set from entrant type
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

Community Programme enrolment triggered on Outer Court completion via Django signal. Induction Dashboard is a Learn App view filtered to `tier="induction"` scope.

### V2.2.5 — Induction Completion & Tenant Placement

**Flow:**

1. User completes Community Programme (Inner Court)
2. `learn/signals.py` creates draft `certification` Record: `metadata.context: "induction_completion"`, `metadata.target_level: 1`
3. Induction Coordinator (Level 3+ in Induction Tenant) opens induction review queue
4. Coordinator reviews: profile data, programme completion, assessment submissions
5. System narrows tenant list by matching user's Country/City from profile (suggest + coordinator confirms)
6. Coordinator calls `POST /api/learn/certifications/{id}/confirm/` with `placement_tenant_id` in request body
7. Extended confirm logic:
   - Sets `competence_level = 1`
   - Sets `user.induction_completed_at`
   - Creates `UserPermission` in placement tenant (`level=1`, `role="disciple"`)
   - Deactivates Induction Tenant `UserPermission` (`is_active=False`)
   - Writes ActivityLog entry
   - Sends email notification via Brevo

**Django template routes:**

```
GET  /learn/induction/review/                  Coordinator: pending completions list
GET  /learn/induction/review/{user_id}/        Coordinator: individual review
POST /learn/htmx/induction/confirm/{user_id}/  Coordinator confirms + places
GET  /accounts/formation/                      User: post-placement welcome
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
- Pathway affiliation

**Formation history view:**

- Timeline of level advancements
- Data source: `CertificationConfirmation` records
- Each entry: from level, to level, date, confirming steward name

**Django template routes:**

```
GET  /accounts/formation/              Full formation history
GET  /learn/htmx/formation-card/       HTMX dashboard card partial
```

### V2.3.2 — App Drawer Level Gating

```python
# settings.py
APP_LEVEL_REQUIREMENTS = {
    'bible':      0,   # Seeker and above
    'learn':      0,   # Browse at 0, enrol at 1
    'activity':   1,
    'community':  1,
    'governance': 3,   # Reference Library; Mandate at Level 4
    'paraclete':  1,
}
```

**Drawer behaviour:**

- Available apps: rendered normally, clickable
- Locked apps: lock icon + "Requires Level X" tooltip
- Click on locked app: modal — "To access Governance, you need Level 3. Complete the Diploma Programme to advance."

**Files:**

- `accounts/context_processors.py` — expose `user_level` to all templates
- `templates/partials/app_drawer.html` — conditional rendering by level
- `templates/partials/_app_locked_modal.html` — info modal

```python
# accounts/context_processors.py
def user_level(request):
    if request.user.is_authenticated:
        return {'user_level': request.user.competence_level}
    return {'user_level': 0}
```

**Commits:** `git commit -m "feat: formation dashboard + level badge"` then `git commit -m "feat: app drawer level gating"`

---

## Phase V2.4 — Notifications (Full)

**Entry requirement:** V2.3 complete. All trigger sources now built.

### Notification model

```python
class Notification(models.Model):
    id                  = UUIDField(primary_key=True, default=uuid.uuid4)
    user                = ForeignKey(User, on_delete=CASCADE, related_name='notifications')
    notification_type   = CharField(max_length=50)
    # Types: announcement | task_assigned | certification_confirmed |
    #        induction_completed | level_advanced | gathering_scheduled
    source_app          = CharField(max_length=50)  # community | learn | activity | governance
    source_record_id    = UUIDField(null=True, blank=True)
    source_activity_id  = UUIDField(null=True, blank=True)
    message             = TextField()
    is_read             = BooleanField(default=False)
    created_at          = DateTimeField(auto_now_add=True)
```

### Trigger points (Django signals)

- Community App: `announcement` created → notify all tenant members
- Activity App: task `assigned_to` set → notify assignee
- Learn App: `certifications/confirm/` → notify learner (level advanced)
- Induction: placement confirmed → notify user (welcome to community)
- Governance App: record `locked` → notify Level 4+ in scope

### Delivery

- **In-app:** HTMX polling at 60-second intervals (`hx-trigger="every 60s"`) — no WebSockets in Version 2
- **Email:** Brevo SMTP for `certification_confirmed` and `level_advanced` events only (highest value). Other types in-app only.
- **Push (mobile):** FCM via `notifications/fcm.py::send_push()` — see Phase V2.M.5

### Django template routes

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

- `/tenants/create/` form: name, slug, tier, parent tenant, description, location (country/province/city), logo (uploaded to MinIO `ics-media` bucket)
- `TenantInvitation` model: `tenant`, `email`, `invited_by`, `accepted_at`, `status` (`pending | accepted | declined | expired`)
- Invitation workflow: invite → email (Brevo) → accept link → `UserPermission` created
- Tenant hierarchy correctly reflected in materialised path

### V2.5.2 — Member Management

- Invite users by email
- Assign roles: Coordinator, Shepherd, Net Caster, Net Mender, Member
- Assign service orders (`UserPermission.metadata.service_order`)
- Assign shepherd (`UserPermission.metadata.shepherd_id`)

### V2.5.3 — Extend Tenant model

```python
# tenants/models.py
coordinator_user  = ForeignKey(User, on_delete=SET_NULL, null=True, related_name='coordinating_tenants')
community_theme   = CharField(max_length=100, blank=True)   # e.g. "Education", "Healthcare"
area_of_operation = TextField(blank=True)
```

### V2.5.4 — Multi-Tenant Content Scoping

- Governance records filtered by user's tenant(s)
- Learn content filtered by user's tenant(s)
- Handbook visible to Level 4+ across all tenants
- Induction Tenant: Level 0 sees induction content only (`metadata.source_app == "induction"`)
- Users in multiple tenants see content from all their tenants

**Commit:** `git commit -m "feat: tenant self-service — creation, invitations, member management, content scoping"`

---

## Phase V2.6 — Video / Live App

**Entry requirement:** V2.5 complete. Learn App operational (V2.1).

**Architecture:** URL-based video only. No self-hosting, no MinIO video bucket, no ffmpeg (ADR-007).

### V2.6.1 — Broadcast Scheduler

New Django app: `video_live/`

Broadcast schedule stored as `Activity (activity_type: "event")` + `Gathering` dual-write (same pattern as Community App). `stream_url` on Gathering carries the live stream URL.

**Scheduler logic:**

- Events with `start_at` and `duration_minutes` form the programme grid
- "Now playing" detection: current time falls within `start_at` + `duration_minutes`
- Upcoming events: next 7 days, ordered by `start_at`
- Past events: automatically become VOD entries (stream URL archived in `custom_fields`)

### V2.6.2 — Live Stream Surface

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

**Exit criteria:** Broadcast schedule visible and navigable. Live stream renders for active events. VOD library browsable. HTMX auto-refresh detects live status changes.

**Commit:** `git commit -m "feat: video live app — broadcast scheduler + live stream + VOD"`

---

# LAYER 5 — Version 2: Mobile App

## Phase V2.M — Flutter Mobile App

**Entry requirement:** V2.2 complete (DRF API stable, user levels established, induction system live). Start this phase in parallel with V2.3 — do not wait until V2.6 is done.

**Architecture:** Flutter for mobile. Android-first. iOS later. Consumes existing DRF API. No HTMX on mobile. The DRF API already built is the mobile backend. Only new backend work: Delta Sync (V2.M.4) and FCM token (V2.M.5).

**Repository:** Separate repository `ichebo-mobile` — different toolchain, different deployment.

### V2.M.1 — Flutter Project Setup

**Prerequisites:**

- Flutter SDK (stable channel) — flutter.dev
- Android Studio (Android SDK + emulator)
- Android device for physical testing (recommended)
- VS Code with Flutter extension

```bash
flutter create ichebo_mobile
cd ichebo_mobile
flutter run
```

**Key packages (`pubspec.yaml`):**

```yaml
dependencies:
  flutter:
    sdk: flutter
  dio: ^5.0.0                       # HTTP client
  riverpod: ^2.0.0                  # State management
  go_router: ^12.0.0                # Navigation + deep links
  sqflite: ^2.0.0                   # Local SQLite (offline cache)
  path_provider: ^2.0.0
  firebase_messaging: ^14.0.0       # Push notifications (FCM)
  youtube_player_flutter: ^9.0.0
  video_player: ^2.0.0
  workmanager: ^0.5.0               # Background sync
  cached_network_image: ^3.0.0
  shared_preferences: ^2.0.0        # Auth token storage
```

### V2.M.2 — Authentication

1. User enters email + password in Flutter login screen
2. Flutter sends `POST /api/auth/login/` → DRF returns `{"token": "abc123..."}`
3. Flutter stores token in `shared_preferences`
4. Every subsequent API call: `Authorization: Token abc123...`
5. DRF validates token and returns user data

**`GET /api/auth/me/` response shape:**

```json
{
  "id":                    "uuid",
  "email":                 "user@email.com",
  "display_name":          "Full Name",
  "avatar_url":            "https://...",
  "competence_level":      1,
  "status":                "active",
  "preferences":           {"theme": "system", "language": "en", "timezone": "Africa/Johannesburg"},
  "active_tenant":         {"id": "uuid", "name": "Sceptre Pretoria", "slug": "...", "tier": "...", "path": "..."},
  "induction_pathway":     "beginners",
  "induction_completed_at": "2026-05-01T00:00:00Z",
  "created_at":            "ISO-8601",
  "updated_at":            "ISO-8601"
}
```

### V2.M.3 — Role-Adaptive Navigation

| Level | Role | Bottom Navigation |
|-------|------|------------------|
| 0 | Seeker/Inductee | Home, Bible, Learn (induction), Profile |
| 1 | Member | + Activity, Community |
| 2 | Disciple | + Governance (read) |
| 3 | Steward/Coordinator | + Community management, Cert queue, Induction review |
| 4 | Senior Steward | + Governance (write), Programme oversight |
| 5 | Architect | + Full operator console |

```dart
GoRouter(
  redirect: (context, state) {
    final userLevel = ref.read(authProvider).user?.competenceLevel ?? 0;
    // Route to appropriate shell based on level
  }
)
```

### V2.M.4 — Offline SQLite Cache + Delta Sync

**Django backend — new endpoint:**

```python
# core/views/sync.py — SyncChangesView
# GET /api/sync/changes/?since=2026-05-01T00:00:00Z
# Returns Records + Activities + Notifications modified after timestamp
# Uses existing updated_at fields — no model changes
# Scoped to requesting user's tenant permissions
# Max 500 items per type; has_more: true if more exist
```

**Flutter — sqflite local database:**

- First launch: full sync (since a very old date)
- Subsequent launches: delta sync (since last sync timestamp)
- Write operations: save locally + queue to backend
- On reconnect: flush write queue via `workmanager`

**Cached locally:** Bible verses (all three translations on first sync), Records (user's tenant scope), Activities (user's activities), Learn content (programmes, courses, lessons), Notifications (recent 50).

### V2.M.5 — Push Notifications (FCM)

**Setup:**

1. Create Firebase project at console.firebase.google.com
2. Add Android app (use Flutter app's package name)
3. Download `google-services.json` → place in `android/app/`
4. Flutter sends `PATCH /api/auth/me/` with `{"fcm_token": "<token>"}` on each login

**Django push helper:**

```python
# notifications/fcm.py
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

**When to send push:** certification confirmed, induction placement confirmed, task assigned, new announcement (topic messaging).

### V2.M.6 — Core Screens (build in this order)

1. **Auth screens:** Login, Register (links to web sign-up flow), Forgot Password
2. **Home / Dashboard:** Paraclete digest summary, today's focus, pending activities
3. **Bible:** Translation selector, book/chapter browser, verse reader, personal notes
4. **Learn:** My Learning (active enrolments), Programme Catalogue (level-gated), Lesson Viewer (with video embed), Mark Complete, Certification status
5. **Activity:** My Activities (task list, habit tracking, goal progress), Create Activity, Mark Complete
6. **Community:** Member directory, Announcement feed, Gathering schedule, Community profile
7. **Profile:** Formation journey card (level badge, active programme, next level), Formation history, Settings
8. **Governance (Level 3+ read):** Reference Library browse, Record detail with linked records
9. **Coordinator screens (Level 3+):** Community management, Member roster, Certification review queue, Induction review queue

**Exit criteria:** All Level 0–3 screens functional on Android. Offline read works after initial sync. Push notifications received and tapped. Auth token persists across app restarts.

**Commit progression:** `git commit -m "feat(mobile): auth + home screens"` → `"feat(mobile): bible + learn screens"` → etc.

---

# LAYER 6 — Version 3 (Future Scale)

Do not build any of these until Version 2 is complete and in real-world use.

## Version 3 Technology Additions (each requires an ADR)

**Redis + Celery:** When background tasks are too slow to run synchronously (e.g. sending 500 push notifications at once, processing uploaded files).

**Docker Compose:** When containerisation is needed for easier deployment, scaling, or handing off to another developer.

**Django Channels + WebSockets:** For real-time features — live notification delivery (instead of polling), live video scheduling updates, real-time community chat.

**LLM integration for Paraclete:** When Paraclete needs AI-generated insights rather than rule-based prompts. Requires significant architectural thought — privacy implications, cost management, data boundaries.

## Version 3 Feature Additions

**Bible App:** Licensed translations (NIV, ESV, NLT — require publisher licensing agreements), African language translations, audio Bible, cross-reference chains, scripture full-text search.

**Learn App:** Rich text editor (TipTap or similar) for lesson authorship, quiz auto-grading, assignment peer review, offline lesson caching, learning analytics dashboard.

**Activity App:** Full calendar grid UI, habit streak visualisation, ministry analytics, cross-tenant campaign assignment.

**Community App:** Pastoral notes (requires privacy design), attendance tracking (privacy-sensitive), community analytics, pastoral assignment model.

**Governance App:** HRS full graph visualisation (not just flat list), Level 4 tenant-scoped governance records, Governance App Phase 2.

**iOS (Flutter):** After Android is stable in production. Requires Mac + Apple Developer account ($99/year).

**Self-hosted video:** Only if URL-based approach proves insufficient — MinIO + ffmpeg + HLS pipeline.

---

## Deferred Items — Complete Reference

### Platform-wide

- Full `RecordPermission` table (fine-grained per-user permissions)
- `CustomFieldSchema` formal validation system
- Donations feature
- In-service Display app
- API versioning (prefix `/api/v1/`) — needed before mobile app goes to production with real users
- User-defined custom journal record types — Version 3+

### Bible App

- Reading plans, verse highlights, scripture search
- Licensed translations (NIV/ESV/NLT)
- African language translations, audio Bible, cross-reference chains

### Learn App

- Rich text editor for authorship
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
- Pastoral assignment model

### Governance App

- Full HRS graph visualisation
- Level 4 tenant-scoped governance records
- Governance App Phase 2
- `calendar` record type (registered in family, Phase 2 only)

### Notifications

- Real-time delivery (Django Channels + WebSockets) — Version 3
- Push notification to iOS — when iOS app is built

### Paraclete

- AI-assisted pattern detection (LLM) — Version 3
- Link suggestion engine — Version 3
- Prophetic prompt generation (LLM) — Version 3

### Infrastructure

- Docker Compose — Version 3
- Redis + Celery — Version 3
- iOS app — Version 3

---

## Open Decisions

| Decision | Status |
|----------|--------|
| Induction programmes content (lessons) | ⏳ Open — seeded as structure; lesson content authored by Level 4+ after platform is live |
| Induction duration (configurable vs fixed) | ⏳ Open — default behaviour is programme completion; configurable duration deferred to Version 3 |

---

## Phase Summary — All Phases

| Phase | Version | What it builds | Est. weeks |
|-------|---------|----------------|------------|
| 0.1–0.5 | — | Server, GitHub, Nginx/Gunicorn/SSL | ✅ Done |
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
├─ mvp                      ← MVP reference [frozen]
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
| `master-roadmap-canonical-2026-04-27.md` | This document — the definitive reference |
| `data-contract-v10-canonical-2026-04-27.md` | Complete data contract — all schemas and rules |
| `2026-04-25-ichebo-adr-version-2.md` | All architecture decisions |
| `2026-04-07-ics-learn-app-system-design_v2.md` | Learn App authoritative spec |
| `2026-04-08-ics-activity-app-system-design.md` | Activity App authoritative spec |
| `2026-04-08-ics-community-app-system-design.md` | Community App authoritative spec |
| `2026-04-10-ics-governance-app-system-design.docx` | Governance App authoritative spec |
| `2026-04-10-ics-paraclete-service-system-design.docx` | Paraclete authoritative spec |
| `2026-04-12-ics-production-engineering-guide.md` | Server operations reference |
| `kingdom_governance_system.md` | KGS framework — domain authority |
