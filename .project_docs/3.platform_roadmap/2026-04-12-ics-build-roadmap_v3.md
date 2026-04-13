# ICS Platform — Full Build Roadmap

> **Version:** v3 — 2026-04-12
> **Previous version:** v2 — 2026-04-07
>
> **v3 Amendments:**
> 1. **Frontend architecture updated throughout** — All vanilla JS IIFE app files (`records-app.js`, `learn-app.js`, `activity-app.js`, etc.) and engine service files (`records.service.js`, `learn.service.js`, `activity.service.js`, etc.) are removed from the build plan. UI is now Django templates + HTMX per the HTMX Migration ADR (`2026-04-07-ics-htmx-migration-adr.md`). DRF endpoints are retained unchanged.
> 2. **Task 0.5 added** — Nginx + Gunicorn production setup extracted as its own task (previously spread across Phase 8). Includes updated Nginx config for SSR Django (not SPA), `collectstatic`, `DJANGO_SETTINGS_MODULE` export, and log/cache directory creation. Reference: `new_task-0.5_Nginx-Gunicorn_setup.md`.
> 3. **Phase 4 removed** — Identity + Tenant JS service layer (`identity.service.js`, `tenant.service.js`) does not exist in the HTMX architecture. Auth guard is Django `@login_required`. Tenant context is request-scoped in views.
> 4. **Phase 5 app order and task numbering corrected** — Actual build order: 5.1 Bible, 5.2 Learn, 5.3 Activity, 5.4 Community, 5.5 Governance, 5.6 Profile + Settings, 5.7 Notifications stub. Each task references its system design document as the authoritative implementation detail.
> 5. **Build status column added** to Phase Summary table — reflects completed phases and in-progress tasks as of v3 date.
> 6. **Dependency rules rewritten** — JS-centric rules replaced with Django templates + HTMX rules.
> 7. **Current State Audit updated** — reflects HTMX architecture and removed JS files.
> 8. **Deferred section consolidated** — all per-app deferred items carried from system design documents into a single section.
> 9. **Production hardening** (formerly Phase 8) renumbered to **Phase 7**; Dashboard (formerly Phase 7) renumbered to **Phase 6.2**.
>
> **Everything in v2 not listed above is either superseded by these amendments or carried forward unchanged into the relevant section below.**

> **For Claude:** When implementing, read the referenced system design document for each task before writing any code. The roadmap gives the what and the order; the system design doc gives the how. The data contract (`2026-04-08-ics-platform-data-contract_v8.md` + v9 amendments `2026-04-10-ics-platform-data-contract_v9-amendments.docx`) is the canonical schema reference throughout.

**Goal:** Build the ICS platform (digital twin of the Kingdom Governance System) from a fresh Django project on a VPS to a fully operational multi-tenant platform with a Django templates + HTMX frontend.

**Architecture:** Django 4.2 LTS + DRF backend (single source of truth). All app UI is rendered via Django templates + HTMX. No vanilla JS app files or engine service files. `storage.js` is retained for UI state only (theme preference, app drawer state). DRF endpoints remain as the canonical data API for mobile clients and future integrations.

**Tech Stack:** Python 3.11+, Django 4.2 LTS, Django REST Framework, PostgreSQL, Nginx, Gunicorn, Django templates, HTMX, mobile-first CSS (CSS variables, 768px desktop breakpoint).

---

## Current State Audit

### Architecture (locked 2026-04-07)

- **Backend:** Django 4.2 LTS + DRF + PostgreSQL. All data lives here.
- **Frontend:** Django templates + HTMX. No IIFE JS app files.
- **UI state only (JS):** `storage.js` (theme), `navbar.js` (drawer toggle, scroll-hide, bottom nav active state).
- **Auth:** Django session auth for templates. DRF token auth retained for mobile.
- **Tenant context:** Materialised path hierarchy. Active tenant scoped per request in views.
- **Data spine:** Single `records` table with `record_family` / `record_type` discriminator. No schema proliferation.

### What is COMPLETE

- **Phase 0** — VPS setup, Django scaffold, health check, Nginx + Gunicorn.
- **Phase 1** — Auth, tenants, permissions, HTMX shell (`base.html`, nav components).
- **Phase 2** — Records Engine: Django models, DRF endpoints, Django template views + HTMX partials.
- **Phase 3** — Activity Engine: Django models, DRF endpoints, `ActivityLog` signal, Django template views + HTMX partials.
- **Task 5.1** — Bible App: static `bible.json` serves scripture; annotations use Records Engine (`record_family: "bible"`, `record_type: "bible_note"`); three-panel mobile-first HTMX UI. Committed as `feat: bible app`.

### What is IN PROGRESS

- **Task 5.2** — Learn App: advisory and system design complete; build pending.
  Reference: `2026-04-07-ics-learn-app-system-design_v2.md`

### What is DESIGNED (system design complete, build not started)

- **Task 5.3** — Activity App: `2026-04-08-ics-activity-app-system-design.md`
- **Task 5.4** — Community App: `2026-04-08-ics-community-app-system-design.md`
- **Task 5.5** — Governance App: `2026-04-10-ics-governance-app-system-design.docx`
- **Task 5.6** — Profile + Settings: `2026-04-10-ics-profile-settings-notifications-spec.docx`
- **Task 5.7** — Notifications stub: same spec doc as 5.6
- **Phase 6** — Paraclete Service + Dashboard: `2026-04-10-ics-paraclete-service-system-design.docx`

### What does NOT exist yet (build in order)

- Learn App Django views, templates, HTMX partials (Task 5.2)
- Activity App Django views, templates, HTMX partials (Task 5.3)
- Community App Django views, templates (Task 5.4)
- Governance App Django views, templates (Task 5.5)
- Profile + Settings views (Task 5.6)
- Notifications stub (Task 5.7)
- Paraclete orchestration service (Phase 6.1)
- Dashboard (Phase 6.2)
- Production hardening (Phase 7)

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

## Phase 0 — VPS + Django Project Setup ✅ COMPLETE

**Exit criteria:** `https://your-domain.com/api/health/` returns `{"status": "ok"}`. Nothing else. Do not proceed to Phase 1 until this passes.

### Task 0.1 — VPS baseline ✅

**Files:** none (server commands only)

1. SSH into VPS (Ubuntu 22.04)
2. Update packages: `sudo apt update && sudo apt upgrade -y`
3. Install dependencies:

   ```bash
   sudo apt install -y python3.11 python3.11-venv python3-pip postgresql postgresql-contrib nginx git
   ```

4. Create deploy user: `sudo adduser ics && sudo usermod -aG sudo ics`
5. Switch to deploy user: `su - ics`

### Task 0.2 — PostgreSQL database ✅

**Files:** none (DB commands only)

1. Start PostgreSQL: `sudo systemctl start postgresql && sudo systemctl enable postgresql`
2. Create DB and user:

   ```bash
   sudo -u postgres psql
   CREATE DATABASE ics_db;
   CREATE USER ics_user WITH PASSWORD 'your-strong-password';
   ALTER ROLE ics_user SET client_encoding TO 'utf8';
   ALTER ROLE ics_user SET default_transaction_isolation TO 'read committed';
   ALTER ROLE ics_user SET timezone TO 'UTC';
   GRANT ALL PRIVILEGES ON DATABASE ics_db TO ics_user;
   \q
   ```

3. Test connection: `psql -U ics_user -d ics_db -h localhost`

### Task 0.3 — Django project scaffold ✅

**Files created:**

- `~/ics/` (project root)
- `~/ics/requirements.txt`
- `~/ics/ics_project/settings/base.py`
- `~/ics/ics_project/settings/production.py`
- `~/ics/ics_project/settings/local.py`

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

# Django auth redirects (HTMX architecture)
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
CORS_ALLOWED_ORIGINS=http://localhost:8000,https://your-domain.com
```

Commit: `git init && git add . && git commit -m "chore: django project scaffold"`

### Task 0.4 — Health check endpoint ✅

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

Commit: `git add . && git commit -m "feat: health check endpoint"`

### Task 0.5 — Nginx + Gunicorn (production) ✅

> **Reference:** `new_task-0.5_Nginx-Gunicorn_setup.md` — authoritative detail for this task.

**`gunicorn.conf.py`** (project root):

```python
bind = "127.0.0.1:8001"
workers = 3
timeout = 120
accesslog = "/var/log/gunicorn/ics_access.log"
errorlog = "/var/log/gunicorn/ics_error.log"
```

**`/etc/nginx/sites-available/ics`:**

```nginx
# Redirect HTTP → HTTPS
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

    # Static files — served by Nginx, not Gunicorn
    location /static/ {
        alias /home/ics/ics/staticfiles/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # Everything else → Gunicorn (SSR Django, not SPA)
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

# 3. Collect static files (must use production settings)
export DJANGO_SETTINGS_MODULE=ics_project.settings.production
python manage.py collectstatic --no-input

# 4. Run migrations
python manage.py migrate

# 5. Enable Nginx site
sudo ln -s /etc/nginx/sites-available/ics /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 6. SSL (Let's Encrypt)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# 7. Start Gunicorn
export DJANGO_SETTINGS_MODULE=ics_project.settings.production
gunicorn ics_project.wsgi:application -c gunicorn.conf.py

# 8. Verify
curl https://your-domain.com/api/health/
# Expected: {"status": "ok"}
```

**User ownership:** The `ics` deploy user owns `/home/ics/ics/`. Gunicorn runs as `ics`. Nginx proxies to Gunicorn on port 8001. Static files at `staticfiles/` are readable by Nginx. Full decision record in `new_task-0.5_Nginx-Gunicorn_setup.md`.

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

Commit: `git add . && git commit -m "chore: nginx + gunicorn production setup"`

---

## Phase 1 — Auth + Tenants + HTMX Shell ✅ COMPLETE

**Exit criteria:** Register, login, create tenant, assign permission. `@login_required` redirects unauthenticated requests to `/accounts/login/`. `base.html` renders with navbar, app drawer, bottom nav, and theme toggle.

### Task 1.1 — Accounts app + custom User model ✅

**Files:**

- Create: `~/ics/accounts/models.py`
- Create: `~/ics/accounts/forms.py`
- Create: `~/ics/accounts/views.py`
- Create: `~/ics/accounts/urls.py`
- Create: `~/ics/accounts/serializers.py`
- Create: `~/ics/templates/accounts/login.html`
- Create: `~/ics/templates/accounts/register.html`

User model fields: `email` (username field), `display_name`, `competence_level` (1–5), `status` (`active | seeker | suspended`), `avatar_url`, `preferences` (JSONField). `UserProfile` extension: `bio`, `preferred_bible_translation` (FK to BibleTranslation).

Django session auth for templates + DRF token auth for mobile (both active). `SessionAuthentication` added to `REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES`.

Commit: `git add . && git commit -m "feat: accounts app — user model, login, register"`

### Task 1.2 — Tenants app + materialised path ✅

**Files:**

- Create: `~/ics/tenants/models.py`
- Create: `~/ics/tenants/serializers.py`
- Create: `~/ics/tenants/views.py`
- Create: `~/ics/tenants/urls.py`

`Tenant` model: `name`, `path` (materialised path, e.g. `/global/ichebo/`), `tier` (`organisation | ministry | cell | handbook`), `parent` (self-FK). `UserPermission` model: `user`, `tenant`, `role` (steward-suffix naming), `metadata` (`shepherd_id`, `service_order`).

Handbook tenant at `/global/handbook/` created by management command on first deploy.

Commit: `git add . && git commit -m "feat: tenants app — tenant model, materialised path, permissions"`

### Task 1.3 — HTMX shell — base.html + nav components ✅

**Files:**

- Create: `~/ics/templates/base.html`
- Create: `~/ics/templates/base_partial.html`
- Create: `~/ics/templates/components/_navbar.html`
- Create: `~/ics/templates/components/_app_drawer.html`
- Create: `~/ics/templates/components/_bottom_nav.html`
- Create: `~/ics/templates/components/_toast.html`
- Create: `~/ics/templates/components/_spinner.html`
- Create: `~/ics/templates/components/_empty_state.html`

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

Commit: `git add . && git commit -m "feat: base.html, nav components, HTMX shell"`

---

## Phase 2 — Records Engine ✅ COMPLETE

**Exit criteria:** Full Record + Relationship CRUD via both DRF (`/api/records/`) and Django template views. HTMX partials load record lists and detail without full page reload. Mobile smoke test passes.

### Task 2.1 — Records Django app + models ✅

**Files:**

- Create: `~/ics/records/models.py` — `Record`, `Relationship`
- Create: `~/ics/records/serializers.py`
- Create: `~/ics/records/views.py` (DRF ViewSets)
- Create: `~/ics/records/filters.py`
- Create: `~/ics/records/permissions.py`
- Create: `~/ics/records/urls.py`

Core models: `Record` (single table, `record_class` / `record_family` / `record_type` discriminator), `Relationship`. All records carry: `id` (UUID), `tenant_id`, `created_by`, `created_at`.

Commit: `git add . && git commit -m "feat: records engine — models, DRF endpoints"`

### Task 2.2 — Records Django template views + HTMX partials ✅

**Files:**

- Create: `~/ics/records/template_views.py` (CBVs for Django template rendering)
- Create: `~/ics/templates/records/list.html`
- Create: `~/ics/templates/records/_list.html` (HTMX partial)
- Create: `~/ics/templates/records/detail.html`
- Create: `~/ics/templates/records/_detail.html` (HTMX partial)
- Create: `~/ics/templates/records/create.html`
- Create: `~/ics/templates/records/_form.html` (HTMX partial)
- Create: `~/ics/templates/records/edit.html`
- Create: `~/ics/templates/components/_record_card.html`

`HX-Request` header detection pattern (used across all apps):

```python
def get_template_names(self):
    if self.request.headers.get('HX-Request'):
        return ['records/_list.html']
    return ['records/list.html']
```

Commit: `git add . && git commit -m "feat: records app — Django template views, HTMX partials"`

---

## Phase 3 — Activity Engine ✅ COMPLETE

**Exit criteria:** Full Activity CRUD via DRF. `ActivityLog` signal fires on status change. Django template views for My Activities surface render from ORM. HTMX status-update partials work on mobile.

> **Reference:** `2026-04-08-ics-activity-app-system-design.md` — full six-phase build specification (Phases A–F) and 16-point smoke test checklist.

### Task 3.1 — Activity Django app + models ✅

**Files:**

- Create: `~/ics/activity/models.py` — `Activity`, `ActivityLog`
- Create: `~/ics/activity/serializers.py`
- Create: `~/ics/activity/views.py` (DRF ViewSets)
- Create: `~/ics/activity/filters.py` — `ActivityFilter`
- Create: `~/ics/activity/signals.py` — `ActivityLog` signal on status change
- Create: `~/ics/activity/urls.py`

Activity types: `campaign | project | task | habit | goal | reminder | skill | event`. `ActivityLog` records every status transition at no additional schema cost. The `skill` type is the gifts and competence register.

**Endpoints:**

```
GET    /api/activities/
POST   /api/activities/
GET    /api/activities/{id}/
PATCH  /api/activities/{id}/
DELETE /api/activities/{id}/
GET    /api/activities/{id}/log/
GET    /api/calendar/events/        (aggregation — reads Activity table)
GET    /api/activity/health/
```

Commit: `git add . && git commit -m "feat: activity engine — models, signals, DRF endpoints"`

### Task 3.2 — Activity Django template views + HTMX partials ✅

**Files:**

- Create: `~/ics/activity/template_views.py`
- Create: `~/ics/templates/activity/list.html`
- Create: `~/ics/templates/activity/_list.html` (HTMX partial)
- Create: `~/ics/templates/activity/detail.html`
- Create: `~/ics/templates/components/_activity_card.html`

Two-surface model: **My Activities** (personal, `tenant_id: null`) and **Ministry** (tenant-scoped campaigns/projects/tasks). Calendar is a Django aggregation service only — no calendar UI in MVP.

Commit: `git add . && git commit -m "feat: activity app — Django template views, HTMX partials"`

---

## Phase 4 — ~~Identity + Tenant JS Services~~ REMOVED

> **This phase is removed in v3.** `identity.service.js` and `tenant.service.js` do not exist in the Django templates + HTMX architecture. Auth guard is Django's `@login_required` decorator and `LoginRequiredMixin`. Tenant context is resolved from `request.user.active_tenant` inside Django views. No JS layer required.

---

## Phase 5 — App Layer

**Exit criteria per task:** App renders real data from the Django ORM via Django template views and HTMX. Mobile-first layout at 768px breakpoint. Manual smoke test on phone passes.

**Build order is fixed — do not reorder.**

---

### Task 5.1 — Bible App ✅ COMPLETE

> **Reference:** `2026-04-08-ics-bible-app-system-design_v2.md`

- Scripture text served from static `bible.json` — no DB queries for scripture.
- User annotations use Records Engine: `record_family: "bible"`, `record_type: "bible_note"`.
- Three-panel mobile-first HTMX UI: book/chapter navigator, reader, annotation panel.
- `BibleTranslation`, `BibleBook`, `BibleVerse` models loaded by management command (read-only reference data; exempt from the four mandatory fields rule per Part 1.1 of the data contract).

**Endpoints:**

```
GET  /api/bible/translations/
GET  /api/bible/books/
GET  /api/bible/chapters/{book_id}/{chapter}/
GET  /bible/                        (Django template view)
GET  /bible/htmx/chapter/           (HTMX partial)
GET  /bible/htmx/annotations/       (HTMX partial)
POST /bible/htmx/annotations/       (HTMX partial — creates bible_note Record)
GET  /api/bible/health/
```

Commit: `git add . && git commit -m "feat: bible app"`

---

### Task 5.2 — Learn App 🔄 IN PROGRESS

> **Reference:** `2026-04-07-ics-learn-app-system-design_v2.md` — authoritative implementation detail. Read this document in full before writing any code.

**Data model:**

- All learning content = `Record` objects (`record_family: "learning"`, types: `programme | course | lesson | assignment | quiz | certification`).
- Curriculum = `Relationship` objects (`relationship_type: "part_of"`) — no separate curriculum table.
- Learner progress = `Activity` hierarchy (`programme → project → task`) linked to content Records via `Relationship (tracks)`.
- Competence advancement: learner self-logs progress; steward at Level 3+ confirms via `POST /api/learn/certifications/{id}/confirm/` → `user.competence_level` incremented.
- Content authorship: Level 4+ authors content as governance Records; Level 5 Prime tenant users review/approve.
- `"submitted"` status added to the Record status vocabulary to support the certification review queue.

**New models:**

- `CertificationConfirmation` — links a certification Record to the confirming steward; triggers `competence_level` increment.

**Schema notes:**

- `competence_level` removed from `UserSerializer.read_only_fields` — the confirm endpoint is the sole authorised write path.
- Auto-certification signal: fires when a programme Activity reaches `progress: 100` and `status: "completed"`, creating a draft Certification Record.

**Endpoints:**

```
GET  /api/learn/health/
GET  /api/learn/programmes/{id}/curriculum/
GET  /api/learn/certifications/queue/
POST /api/learn/certifications/{id}/confirm/
```

**Django template URL routes:**

```
GET  /learn/                              Learn App home (My Learning)
GET  /learn/catalogue/                    Programme catalogue
GET  /learn/programme/{id}/               Programme detail
GET  /learn/lesson/{id}/                  Lesson viewer
GET  /learn/htmx/my-learning/             HTMX partial — enrolled programmes
GET  /learn/htmx/catalogue/               HTMX partial — browseable catalogue
GET  /learn/htmx/progress/{id}/           HTMX partial — progress bar update
GET  /learn/htmx/cert-queue/              HTMX partial — steward cert queue
POST /learn/htmx/enrol/{id}/              HTMX partial — enrol in programme
POST /learn/htmx/progress/{id}/update/    HTMX partial — log progress
```

**Build phases (A–G) — see system design doc for full task breakdown:**

| Phase | What it builds |
|-------|----------------|
| A | Django `learn` app, `CertificationConfirmation` model, confirm + queue endpoints |
| B | Records endpoint filter verification, curriculum endpoint |
| C | `learn/` Django template views, HTMX partials: My Learning, Catalogue, Enrolment, Lesson Viewer |
| D | Quiz renderer, Assignment submission |
| E | Auto-certification signal, steward certification queue UI, competence level advancement |
| F | Content authorship UI (Level 4+), Handbook review queue UI (Level 5) |
| G | Role-aware navigation, Pathway banner, mobile smoke test |

**Exit criteria:** All seven phases (A–G) pass. `POST /api/learn/certifications/{id}/confirm/` correctly increments `competence_level` in the DB. Verifiable in Django admin.

Commit per phase: see system design doc. Final commit: `git add . && git commit -m "feat: learn app"`

---

### Task 5.3 — Activity App ⏳ PENDING

> **Reference:** `2026-04-08-ics-activity-app-system-design.md` — authoritative implementation detail. Six build phases (A–F) and 16-point smoke test checklist defined there.

**Note:** The Activity Engine (Phase 3) built the Django models, signals, and DRF endpoints. Task 5.3 builds the full Activity App UI layer on top — all Django template views and HTMX interactions.

**Two-surface model:**

- **My Activities** — personal surface (`tenant_id: null`). Types: task, habit, goal, skill, reminder. Flat structure. Personal disciplines and gifts register.
- **Ministry** — tenant-scoped surface. Types: campaign, project, task, event. Nested hierarchy. Steward coordination layer.

**Django template URL routes:**

```
GET  /activity/                             Activity App home (My Activities)
GET  /activity/ministry/                    Ministry surface
GET  /activity/{id}/                        Activity detail
GET  /activity/htmx/my-list/               HTMX partial — personal activity list
GET  /activity/htmx/ministry-list/         HTMX partial — ministry activity list
GET  /activity/htmx/status/{id}/           HTMX partial — status chip update
POST /activity/htmx/create/                HTMX partial — create activity
POST /activity/htmx/status/{id}/update/    HTMX partial — update status
GET  /api/activity/health/
```

**Build phases (A–F) — see system design doc for full task breakdown.**

**Exit criteria:** Both surfaces render real data. Status updates fire via HTMX. `ActivityLog` entries visible in Django admin. 16-point smoke test passes.

Commit: `git add . && git commit -m "feat: activity app"`

---

### Task 5.4 — Community App ⏳ PENDING

> **Reference:** `2026-04-08-ics-community-app-system-design.md` — authoritative implementation detail.

**Data patterns (data contract v8):**

- `record_family: "community"`, MVP types: `announcement | gathering`.
- `gathering` dual-write: creating a Gathering writes both a `community/gathering` Record and an `activity/event` Activity atomically. The Community App view is the transaction coordinator.
- `gathering` custom_fields: `format` (`in_person | digital | hybrid`), `location`, `stream_url` (Video App placeholder, deferred), `capacity`.
- `UserPermission.metadata`: `shepherd_id` (pastoral supervisor FK), `service_order` (KGS service order label).
- `MembershipRequest` model: schema stubbed in MVP (Django model created), no UI.

**Two-surface model:**

- **Community** — announcements, gatherings, member directory for the user's tenant scope.
- **Admin/Steward** — membership management, pastoral oversight (Level 3+).

**Django template URL routes:**

```
GET  /community/                              Community App home
GET  /community/members/                      Member directory
GET  /community/gatherings/                   Gatherings list
GET  /community/{id}/                         Gathering or announcement detail
GET  /community/htmx/members/                 HTMX partial — member list
GET  /community/htmx/announcements/           HTMX partial — announcement list
GET  /community/htmx/gatherings/              HTMX partial — gatherings list
POST /community/htmx/gathering/create/        HTMX partial — dual-write gathering
POST /community/htmx/announcement/create/     HTMX partial
GET  /api/community/health/
```

**Exit criteria:** Member directory renders tenant-scoped members. Announcements display. Gathering creation dual-writes a `community/gathering` Record and an `activity/event` Activity. Both verifiable in Django admin.

Commit: `git add . && git commit -m "feat: community app"`

---

### Task 5.5 — Governance App ⏳ PENDING

> **Reference:** `2026-04-10-ics-governance-app-system-design.docx` — authoritative implementation detail.

**Data patterns (data contract v9):**

- Governance App is a UI and coordination layer over the Records Engine. No new Django models.
- Three surfaces: Reference Library, Mandate Branch, Keys Library.
- `"article"` added to `record_family: "journal"` (Level 1+ personal record type; not a governance type).
- Access rules: Reference Library types (`class`, `principle`, `concept`, `divine_pattern`) — Level 3+ read, Level 5 write. Mandate branch types — Level 4+ read, Level 5 write. Keys Library — owner only, Level 3+.
- Governance record lifecycle: `draft → active → locked → superseded`. No approval queue in MVP.
- HRS Relationship Viewer: Linked Records panel on all governance record detail views (read-only flat list).
- Version history chain: traversable via `previous_version_id` / `superseded_by` fields, rendered as a timeline.
- Journal → Governance linkage: `Relationship (derived_from)` pattern. No new model.
- `calendar` record type: registered in governance family but deferred to Phase 2.

**Django template URL routes:**

```
GET  /governance/                              Governance App home (surface selector)
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
POST /governance/htmx/record/create/           Create governance or key record
POST /governance/htmx/record/{id}/lock/        Lock a record (Level 5)
POST /governance/htmx/record/{id}/supersede/   Begin supersession flow
GET  /governance/htmx/record/{id}/links/       Linked records panel partial
GET  /governance/htmx/record/{id}/history/     Version history partial
GET  /governance/htmx/journal/search/          Journal entry typeahead for linking
GET  /api/governance/health/
```

**Exit criteria:** All three surfaces render data from Handbook tenant. Lock and supersede lifecycle transitions work. Linked Records panel populated. Version history chain traversable.

Commit: `git add . && git commit -m "feat: governance app"`

---

### Task 5.6 — Profile + Settings ⏳ PENDING

> **Reference:** `2026-04-10-ics-profile-settings-notifications-spec.docx` — authoritative implementation detail. No advisory session required — no new models or KGS access rules.

**Note:** Profile and Settings are views within the existing `accounts/` Django app — not a new app. No new models.

**Profile view (`/accounts/profile/`):**

- Identity section: avatar (placeholder initials if null), display name (inline HTMX edit via PATCH `/api/auth/me/`), email (read-only), member since, platform status badge.
- Formation section: competence level label + numeric level, active tenant display, service order (from `UserPermission.metadata.service_order`).
- Only `display_name` and `avatar_url` are inline-editable in MVP.

**Settings view (`/accounts/settings/`):**

- Controls: theme, language, timezone, preferred Bible translation.
- All persisted to `User.preferences` JSONField (database, not localStorage). **The v1/v2 roadmap stub that said localStorage is superseded by the data contract.**

**Django template URL routes:**

```
GET   /accounts/profile/               Profile view
GET   /accounts/settings/              Settings view
POST  /accounts/htmx/profile/edit/     HTMX partial — inline display name / avatar edit
POST  /accounts/htmx/settings/save/    HTMX partial — save preferences
```

**Exit criteria:** Profile renders all identity and formation fields. Settings saves theme/language/timezone/translation to the database. Inline display name edit works via HTMX.

Commit: `git add . && git commit -m "feat: profile + settings"`

---

### Task 5.7 — Notifications Stub ⏳ PENDING

> **Reference:** `2026-04-10-ics-profile-settings-notifications-spec.docx`

Notifications is a nav entry point only in MVP. Full implementation depends on trigger sources not yet built (Activity, Community, Governance signals).

- `GET /api/notifications/` returns an empty list.
- Navbar badge shows zero. Badge polls via HTMX `hx-trigger="every 60s"` (already wired in `_navbar.html`).
- Notifications list view renders empty state component.
- No new model in MVP.

**Routes:**

```
GET  /notifications/                        Notifications list (empty state)
GET  /api/notifications/                    DRF endpoint — returns []
GET  /accounts/htmx/notifications-count/   HTMX partial — badge count
```

Commit: `git add . && git commit -m "feat: notifications stub"`

---

## Phase 6 — Paraclete Service + Dashboard ⏳ PENDING

**Exit criteria:** `GET /api/paraclete/digest/` returns a real `ParacleteDigest` for the logged-in user. Dashboard renders digest widgets. Role-aware and tenant-aware.

> **Reference:** `2026-04-10-ics-paraclete-service-system-design.docx` — authoritative implementation detail.

### Task 6.1 — Paraclete Django app

**Files:**

- Create: `~/ics/paraclete/` (Django app)
- Create: `~/ics/paraclete/service.py` — orchestration logic (reads from ORM, writes nothing in MVP)
- Create: `~/ics/paraclete/views.py` — DRF endpoints
- Create: `~/ics/paraclete/urls.py`

`paraclete/service.py` calls the Django ORM directly — it is a Python orchestration module, not a web service calling itself.

**Endpoints:**

```
GET  /api/paraclete/digest/              Daily digest
GET  /api/paraclete/reminders/           Pending reminders
GET  /api/paraclete/suggest/{record_id}/ Link suggestions
GET  /api/paraclete/prompt/              Discipline prompt
POST /api/paraclete/respond/             Accept/dismiss suggestion
GET  /api/paraclete/health/
```

**`ParacleteDigest` shape:**

```json
{
  "user_id": "uuid",
  "generated_at": "ISO-8601",
  "today_focus": "string",
  "pending_activities": [],
  "pending_habits": [],
  "recent_records": [],
  "active_prayer_count": 0,
  "discipline_prompt": "string",
  "reminders": []
}
```

Commit: `git add . && git commit -m "feat: paraclete service + endpoints"`

### Task 6.2 — Dashboard

**Files:**

- Create: `~/ics/dashboard/views.py`
- Create: `~/ics/dashboard/urls.py`
- Create: `~/ics/templates/dashboard/index.html`
- Create: `~/ics/templates/dashboard/_digest_widget.html` (HTMX partial)
- Create: `~/ics/templates/dashboard/_activity_widget.html` (HTMX partial)
- Create: `~/ics/templates/dashboard/_prayer_widget.html` (HTMX partial)

Dashboard calls `paraclete.service` directly via Python import (not via HTTP). Role-aware: competence level determines which widgets are visible. Tenant-aware: ministry widgets visible to Level 3+ only.

**Widgets:**

- Today's focus (discipline prompt from Paraclete)
- Pending activities (tasks + habits due today)
- Recent records (last 5 records created by user)
- Active prayer count
- Ministry summary (Level 3+ only)

**Django template URL routes:**

```
GET  /                                Dashboard home
GET  /dashboard/htmx/digest/          HTMX partial — full digest reload
GET  /dashboard/htmx/activities/      HTMX partial — pending activities widget
GET  /dashboard/htmx/prayers/         HTMX partial — prayer count widget
```

Commit: `git add . && git commit -m "feat: dashboard"`

---

## Phase 7 — Production Hardening ⏳ PENDING

**Exit criteria:** Platform runs stably on VPS. SSL active. Static files served by Nginx. Error logging in place. Gunicorn restarts on reboot via systemd. Django admin accessible. All health endpoints return 200.

> **Note:** Nginx + Gunicorn setup is in Task 0.5. Phase 7 covers the hardening steps that require the full app to be built and verified.

### Task 7.1 — Error logging + Django admin

Modify `~/ics/ics_project/settings/production.py`:

```python
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
```

```bash
python manage.py createsuperuser
# Verify Django admin at /admin/
```

Commit: `git add . && git commit -m "chore: error logging + admin setup"`

### Task 7.2 — Security hardening

Add to `production.py`:

```python
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

Commit: `git add . && git commit -m "chore: production security settings"`

### Task 7.3 — Final smoke test

```bash
# Restart Gunicorn via systemd
sudo systemctl restart ics

# Verify all health endpoints
curl https://your-domain.com/api/health/
curl https://your-domain.com/api/bible/health/
curl https://your-domain.com/api/activity/health/
curl https://your-domain.com/api/community/health/
curl https://your-domain.com/api/governance/health/
curl https://your-domain.com/api/paraclete/health/

# Verify SSL and security headers
curl -I https://your-domain.com/
# Expected: HTTP/2 200, Strict-Transport-Security header present
```

Commit: `git add . && git commit -m "chore: production smoke test — MVP complete"`

---

## Phase Summary

| Phase | What it builds | Entry requirement | Exit criteria | Status |
|-------|----------------|-------------------|---------------|--------|
| 0 | VPS + Django scaffold + Nginx/Gunicorn | VPS access | `/api/health/` returns 200 | ✅ Complete |
| 1 | Auth + Tenants + HTMX shell | Phase 0 done | Register, login, tenant, `base.html` renders | ✅ Complete |
| 2 | Records Engine (Django + HTMX) | Phase 1 done | Full Record + Relationship CRUD, template views wired | ✅ Complete |
| 3 | Activity Engine (Django + HTMX) | Phase 2 done | Full Activity CRUD, ActivityLog, template views wired | ✅ Complete |
| ~~4~~ | ~~Identity + Tenant JS services~~ | — | — | ❌ Removed — HTMX ADR |
| 5.1 | Bible App | Phases 2–3 done | Scripture reader, annotations, HTMX UI | ✅ Complete |
| 5.2 | Learn App | Phases 2–3 done | Courses, progress, certification, steward confirm | 🔄 In Progress |
| 5.3 | Activity App (UI layer) | Phase 3 done | My Activities + Ministry surfaces | ⏳ Pending |
| 5.4 | Community App | Phases 2–3 done | Members, announcements, gathering dual-write | ⏳ Pending |
| 5.5 | Governance App | Phases 2–3 done | Reference Library, Mandate, Keys Library, lifecycle | ⏳ Pending |
| 5.6 | Profile + Settings | Phase 1 done | Profile view, DB-persisted preferences | ⏳ Pending |
| 5.7 | Notifications stub | Phase 1 done | Nav entry, empty list, badge polling | ⏳ Pending |
| 6.1 | Paraclete service | Phase 3 + all Phase 5 done | `ParacleteDigest` returns real data | ⏳ Pending |
| 6.2 | Dashboard | Phase 6.1 done | Digest renders, role-aware widgets | ⏳ Pending |
| 7 | Production hardening | Phase 6 done | SSL, logging, security headers, systemd, smoke test | ⏳ Pending |

---

## Deferred (Post-MVP)

### Platform-wide

- Full `RecordPermission` table (fine-grained per-user permissions)
- `CustomFieldSchema` formal validation system
- Video/Live streaming app
- In-service Display app
- Donations feature
- Advanced Paraclete AI features (pattern detection, auto-linking)
- Push notifications (mobile)
- Mobile application

### Learn App

*(carried from `2026-04-07-ics-learn-app-system-design_v2.md`)*

- Rich text editor (TipTap or similar) for lesson authorship — markdown textarea suffices for MVP
- Quiz auto-grading with score display
- Assignment peer review
- Paraclete "continue your lesson" integration
- Learning analytics dashboard (completion rates per programme)
- Offline lesson caching (service worker)
- Video lessons (`record_type: "video_lesson"` — deferred with Video/Live app)
- Programme ordering / sequencing UI (drag-and-drop curriculum builder)

### Activity App

*(carried from `2026-04-08-ics-activity-app-system-design.md`)*

- Collective and network assignment (assign a task to a group or network of tenants)
- Full calendar UI (Calendar App is aggregation service only in MVP — dated list view only for events)
- Habit streak visualisation
- Ministry analytics

### Community App

*(carried from `2026-04-08-ics-community-app-system-design.md`)*

- `MembershipRequest` model UI (model stubbed in MVP, no UI)
- Pastoral notes (`record_type: "pastoral_note"`) — deferred record type
- Community reports (`record_type: "report"`) — deferred record type
- Video App integration (`stream_url` in gathering `custom_fields` is a placeholder)

### Governance App

*(carried from `2026-04-10-ics-governance-app-system-design.docx`)*

- `calendar` record type (registered in governance family, deferred to Governance Phase 2)
- Level 4 create access for tenant-scoped governance records (Governance App is Handbook-only in MVP)
- Full HRS graph visualisation (Linked Records panel is a flat list in MVP)
- Governance App Phase 2: tenant-scoped governance records for Senior Stewards (Level 4)

### Notifications

- Full notification trigger system (depends on Activity, Community, and Governance signals)
- In-app notification preferences
- Email digest notifications
