# Phase H.6 — sceptre.ichebo.org Surface + Participant Home

> ## ⚠️ Correction, 2026-06-26 — not yet built; real fixes needed before execution
>
> H.6 has not been started — no `sceptre` app, no `SiteRouterMiddleware`, no DNS gap anymore (see point 8). Fixes needed, found by checking every claim against the live repository and production server:
>
> 1. **Server identity is wrong throughout.** Real path: `/home/scepter/ichebo-platform-repo/ichebo-platform` (user `scepter`, not `ics`). Real Gunicorn bind: `127.0.0.1:8001`, not `8000`. Real settings module: `ics_project.settings.production` / `ics_project.settings.base` — there is no single `ics_project/settings.py`. Every `cd`/`source venv/bin/activate`/`python manage.py ...` command in the Pre-Flight Checks and Task 5 needs these paths, and the venv is at `.venv/bin/` inside the repo, activated via `source .venv/bin/activate` (confirmed: production runs Django through `.venv/bin/gunicorn` directly, set by `Environment="PATH=..."` in the systemd unit, not a `source venv/bin/activate` shell step at all — there is no interactive shell session on production; deploys run `DJANGO_SETTINGS_MODULE=ics_project.settings.production .venv/bin/python3 manage.py ...` directly).
> 2. **`ics_project/settings.py` doesn't exist** — settings live in `ics_project/settings/base.py` (shared) and `production.py` (production overrides). `MIDDLEWARE` and `ALLOWED_HOSTS` both live in `base.py`. Task 1's instruction to "find `MIDDLEWARE` list... and add at the top" is otherwise correct — just in the right file.
> 3. **No URL-conf dispatcher function is needed in `ics_project/urls.py` at all.** Task 2 proposes a `get_urlconf(request)` function and an unclear wiring step ("Add to urlpatterns — this is the fallback for agency / sceptre URLs are served by the middleware-set urlconf"). The middleware setting `request.urlconf = 'sceptre.urls'` directly (which Task 2's own Step 3 correctly arrives at) is the *complete* mechanism — Django's resolver checks `request.urlconf` automatically on every request. Delete the `get_urlconf` function and the "Add to urlpatterns" step entirely; `ics_project/urls.py` needs zero changes for this phase.
> 4. **`competence_level` is a real `IntegerField` (`0`–`5`), not a string.** `sceptre/auth.py`'s `PARTICIPANT_LEVELS = ['0b', '1', '2', '3', '4', '5']` and `STEWARD_LEVELS = ['3', '4', '5']` are lists of strings being compared against an int — always `False`, which would lock out every real user. There is also no `'0b'` value in the model at all (see Doc J's Correction Log, item 5, for the open question about whether a 0a/0b distinction is needed and how to model it for real if so). Fix: `PARTICIPANT_LEVELS = (0, 1, 2, 3, 4, 5)`, `STEWARD_LEVELS = (3, 4, 5)`.
> 5. **`role__endswith='-steward'` (Task 3's `require_sceptre_steward`/`is_steward`) excludes `'admin'`.** Use `tenants.models.UserPermission.STEWARD_ROLES` instead — `role__in=UserPermission.STEWARD_ROLES`.
> 6. **`_get_tenant_for_user` (Task 4) is missing `.order_by('-level')`.** The established pattern this codebase actually uses everywhere else (`community/views.py:_get_user_permissions`) orders by `-level` before taking `.first()`, so a user with multiple `UserPermission` rows resolves to their *highest*-level tenant, not an arbitrary one. Add `.order_by('-level')` before `.first()`.
> 7. **`now_playing_partial` (Task 4) makes an unnecessary internal HTTP call to its own API**, including a `GUNICORN_PORT` setting that doesn't exist anywhere in this codebase (confirmed) and the wrong port (`8000`) even if it did. There is no reason for a Django view to make an HTTP round-trip to its own server's API to get data — call the resolution function directly instead: `from broadcast.services import resolve_now_playing` (built in H.7) and `result = resolve_now_playing(tenant)`, no `requests`, no token, no port. Delete `_get_api_token` entirely — it exists solely to support this unnecessary HTTP call.
> 8. **DNS is no longer a precondition — `sceptre.ichebo.org` already resolves** to the Django VPS (confirmed live 2026-06-26). Skip the "Confirm DNS A record" line in Pre-Flight Checks; go straight to the Nginx step.
> 9. **Nginx: one file, not a new one.** The real server keeps every subdomain as a `server {}` block pair inside a single file, `/etc/nginx/sites-available/ics` (confirmed by reading the live file) — there is no `sites-available/sceptre.ichebo.org` to create or symlink. Add the new blocks to the existing `ics` file instead, matching its established style (HTTP block that redirects to HTTPS, then the real HTTPS block with `ssl_certificate`/`ssl_certificate_key` paths under `/etc/letsencrypt/live/sceptre.ichebo.org/`, a `location /static/` alias to `/home/scepter/ichebo-platform-repo/ichebo-platform/staticfiles/`, and `proxy_pass http://127.0.0.1:8001;` — see Doc J Part 2.1 for the corrected, complete block). Task 5's Steps 1–2 (create file, symlink into `sites-enabled`) should be replaced with "edit the existing `ics` file directly," since it's already enabled.
> 10. **`SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN` are not set at all currently** (confirmed — absent from both `base.py` and `production.py`). Whether to add them (one login works across both subdomains) or leave them unset (separate logins per subdomain, acceptable for a pilot) is a real, open decision for Chizola — Doc J §11.3 already notes this; don't silently pick one without confirming.
> 11. **The real login URL is `/accounts/login/`** (`LOGIN_URL` in `base.py`, mounted via `accounts/urls.py`), not `/login/`. `sceptre/auth.py`'s manual `return redirect('/login/')` would 404. Using `@login_required` (Django's own decorator, which reads `LOGIN_URL` automatically) avoids this entirely — see the corrected `sceptre/auth.py` in Doc J Part 5.2, which this phase plan's Task 3 should match.
> 12. **The test suite's `make_tenant`/`make_user` helpers have the same `Tenant` field gaps as H.5 and H.7's test suites** — missing `slug`, using the wrong field name `tenant_path` instead of `path`, missing required `tier` and `created_by`. See H.5's correction note, point 7, for a working helper shape.
> 13. **Two separate CSS problems, not one.** The placeholder pages in Task 4, Step 7 (`templates/sceptre/community/community.html`, `learn/learn.html`, `profile/profile.html`, `steward/settings.html`) use `class="page-container"`/`"label-tag"`/`"page-title"` — a generic Bootstrap-style system that doesn't exist in this codebase (confirmed: the real convention is `ws-`-prefixed classes, e.g. `ws-label-tag`/`ws-page-title`, plus inline styles — see any real form like `templates/community/partials/gathering_form.html`). Separately, `base.html`, `_nav.html`, `home.html`, and `_now_playing.html` use new, purpose-built classes (`sceptre-shell`, `channel-player-container`, `quick-tile`, `now-playing`, etc.) — a legitimate design choice for a visually distinct consumer surface, *not* a mismatch with this codebase's convention — but **no stylesheet defining any of them exists yet, and this plan never adds one.** A new CSS file (e.g. `static/css/sceptre.css`, loaded from `sceptre/base.html`) needs to be designed and written as part of this phase; it isn't optional polish, the participant home screen renders as unstyled HTML without it.
> 14. **`_nav.html`'s steward section (Task 4, Step 2) doesn't match the real visual mockup.** The built mockup (`sceptre_comm_web-ui_mockup/03-sceptre-steward-panel.html`) shows a structurally different mechanism: a **"Manage" trigger button in the top nav** that **slides in a steward sidebar from the right** over a dimmed main view, with its own close (×) control — not a `<div class="steward-nav">` block sitting inline inside the always-visible profile area, as currently written. Restructure `_nav.html` to render a "Manage" trigger (visible only when `is_steward`) plus a separate, initially-hidden `steward-sidebar` element toggled by it — see Doc J Part 3.4's corrected description and the mockup file directly for the exact visual structure to copy.
>
> Fix all fourteen before running any task below — several (4, 5, 11) would otherwise make every gated view in this phase unusable for real users while appearing syntactically fine.

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build `sceptre.ichebo.org` as a role-adaptive Django surface — subdomain routing middleware, separate URL conf and template directories, participant home screen with channel video player and four quick-access tiles, steward management navigation, and Nginx + SSL configuration.

**Architecture:** Subdomain-aware URL routing in one Django project — no multi-site framework (ADR-023, renumbered from the original draft's ADR-022 — see correction note above). `SiteRouterMiddleware` detects the host and sets `request.site` and `request.urlconf`. `sceptre/urls.py` is a new URL conf. Templates: only `templates/sceptre/` is new — the existing flat `templates/` tree is untouched. Same `User`, `Tenant`, `Record` models underpin both subdomains. Role-adaptive shell: steward navigation rendered only for Level 3+ or a role in `UserPermission.STEWARD_ROLES`. Channel video calls `GET /api/broadcast/now/` (built in H.7) — or, better, calls `broadcast.services.resolve_now_playing(tenant)` directly (see correction note point 7).

**Tech Stack:** Django 4.2, HTMX, Nginx, certbot SSL, existing all apps.

**Reference:** DOC J Parts 2 and 3 — authoritative spec. `2026-06-25-ichebo-sceptre-system-design_doc-j_v1_0.md`.

**Branch:** `v3-h6-sceptre-surface` (cut from `main` after H.7 merges)

**Commit on completion:** `feat(sceptre): H.6 — sceptre.ichebo.org shell, participant home, steward management side`

**Pre-condition:** H.7 (Ichebo Channel) must be merged to `main` before this phase begins — the participant home screen depends on `GET /api/broadcast/now/`.

---

## Pre-Flight Checks

```bash
git checkout main && git pull
git log --oneline main | grep "H.7"
# Expected: H.7 merge commit present

git checkout -b v3-h6-sceptre-surface
source venv/bin/activate
python manage.py check

# Confirm sceptre.ichebo.org DNS A record is pointing to the Django VPS
# (37.27.82.169) before the Nginx step — this can be done in parallel.
```

---

## Task 1 — Create SiteRouterMiddleware

**Files:**
- Create: `middleware/site_router.py`
- Modify: `ics_project/settings/base.py` — add middleware. `ALLOWED_HOSTS` is read from `.env` via `config()` — add `sceptre.ichebo.org` to production's `.env` `ALLOWED_HOSTS` value instead of hardcoding it in `base.py`.

**Step 1: Create the middleware**

```python
# middleware/site_router.py
"""
SiteRouterMiddleware — sets request.site based on incoming Host header.
Used to serve sceptre.ichebo.org from the same Django process as app.ichebo.org.
ADR-023.
"""


class SiteRouterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()
        if host == 'sceptre.ichebo.org':
            request.site = 'community'
        else:
            request.site = 'agency'
        return self.get_response(request)
```

**Step 2: Add to settings**

In `ics_project/settings/base.py`:

Find `MIDDLEWARE` list and add at the top (before `SecurityMiddleware`):

```python
'middleware.site_router.SiteRouterMiddleware',
```

`ALLOWED_HOSTS` is not a literal list in `base.py` — it's `config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])`, read from the `.env` file. On the server, edit `/home/scepter/ichebo-platform-repo/ichebo-platform/.env` and add `sceptre.ichebo.org` to the existing `ALLOWED_HOSTS` value (currently `app.ichebo.org,ichebo.org,www.ichebo.org`).

`SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN` are not set anywhere currently (confirmed — absent from both `base.py` and `production.py`). **Before adding them, confirm with Chizola** whether a steward should get one shared login across both subdomains (needs these two settings) or a separate login per subdomain (leave them unset — simpler, acceptable for a pilot). If sharing is wanted, add to `base.py`:

```python
if not DEBUG:
    SESSION_COOKIE_DOMAIN = '.ichebo.org'
    CSRF_COOKIE_DOMAIN = '.ichebo.org'
```

(guarded by `not DEBUG` because Django's test client doesn't set domain cookies, which would otherwise break the test suite in Task 6).

**Step 3: Verify middleware loads**

```bash
python manage.py check
python manage.py shell -c "
from middleware.site_router import SiteRouterMiddleware
print('OK — middleware importable')
"
```

**Step 4: Commit**

```bash
git add middleware/site_router.py ics_project/settings/base.py
git commit -m "feat(sceptre): add SiteRouterMiddleware for subdomain detection (ADR-023)"
```

---

## Task 2 — Create sceptre URL conf and URL dispatcher

**Files:**
- Create: `sceptre/urls.py`
- Modify: `ics_project/urls.py` — subdomain-aware dispatcher

**Step 1: Read the current ROOT_URLCONF and urls.py**

```bash
grep -n "ROOT_URLCONF\|urlpatterns\|include" ics_project/settings/base.py ics_project/urls.py | head -20
```

Note how the current `urls.py` is structured. The dispatcher must preserve all existing URL patterns for `app.ichebo.org` while routing `sceptre.ichebo.org` to its own conf.

**Step 2: Create sceptre/urls.py (start with skeleton)**

```python
# sceptre/urls.py
"""
URL configuration for sceptre.ichebo.org.
All participant and steward URLs for the Sceptre Community surface.
"""
from django.urls import path
from sceptre import views

app_name = 'sceptre'

urlpatterns = [
    # Participant routes
    path('', views.participant_home, name='home'),
    path('community/', views.community_area, name='community'),
    path('learn/', views.learn_summary, name='learn'),
    path('bible/', views.bible_redirect, name='bible'),
    path('support/', views.support_redirect, name='support'),
    path('profile/', views.profile_summary, name='profile'),

    # Steward routes (gated at view level)
    path('steward/members/', views.steward_members, name='steward_members'),
    path('steward/gatherings/', views.steward_gatherings, name='steward_gatherings'),
    path('steward/formation/', views.steward_formation, name='steward_formation'),
    path('steward/announcements/', views.steward_announcements, name='steward_announcements'),
    path('steward/support/', views.steward_support_redirect, name='steward_support'),
    path('steward/settings/', views.steward_settings, name='steward_settings'),
]
```

**Step 3: Wire the dispatcher in ics_project/urls.py**

Add to the top-level URL patterns (or create a dispatcher function):

```python
# ics_project/urls.py
from django.conf import settings


def get_urlconf(request):
    """Return the correct URL conf based on request.site (set by SiteRouterMiddleware)."""
    if getattr(request, 'site', 'agency') == 'community':
        return 'sceptre.urls'
    return None  # use ROOT_URLCONF default


# Add to urlpatterns — this is the fallback for agency
# sceptre URLs are served by the middleware-set urlconf
```

**Note:** The exact Django mechanism for per-request URL conf switching is `request.urlconf`. Set it in the middleware or a custom URL resolver. The cleanest approach is to extend `SiteRouterMiddleware` to also set `request.urlconf`:

Update `middleware/site_router.py`:

```python
class SiteRouterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()
        if host == 'sceptre.ichebo.org':
            request.site = 'community'
            request.urlconf = 'sceptre.urls'
        else:
            request.site = 'agency'
            # request.urlconf not set — Django uses ROOT_URLCONF
        return self.get_response(request)
```

**Step 4: Verify**

```bash
python manage.py check
python manage.py shell -c "
import sceptre.urls
print(f'OK — sceptre URL conf has {len(sceptre.urls.urlpatterns)} patterns')
"
```

**Step 5: Commit**

```bash
git add sceptre/urls.py middleware/site_router.py
git commit -m "feat(sceptre): sceptre/urls.py and urlconf dispatcher via SiteRouterMiddleware"
```

---

## Task 3 — Create sceptre app and auth helpers

**Files:**
- Run: `python manage.py startapp sceptre`
- Create: `sceptre/auth.py`

**Step 1: Create the app**

```bash
python manage.py startapp sceptre
```

Add to `INSTALLED_APPS` in `ics_project/settings/base.py`:

```python
'sceptre',
```

**Step 2: Create sceptre/auth.py**

Corrected against the real `competence_level` `IntegerField` and the real `UserPermission.STEWARD_ROLES` set (which includes `'admin'`, unlike a `-steward` suffix match) — see Doc J Part 5.2 for the same code with full reasoning:

```python
# sceptre/auth.py
"""
View decorators for sceptre.ichebo.org access control.
Participant gate: competence_level 0+ (any authenticated user — see Doc J
Part 5.1's open question on whether a finer-grained "has completed
induction" check is needed here; not modeled as a fake level value).
Steward gate: Level 3+ OR a role in UserPermission.STEWARD_ROLES.
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from tenants.models import UserPermission

PARTICIPANT_LEVELS = (0, 1, 2, 3, 4, 5)   # real IntegerField values
STEWARD_LEVELS = (3, 4, 5)


def require_sceptre_participant(view_func):
    """Gate: authenticated user with competence_level 0+."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.competence_level not in PARTICIPANT_LEVELS:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def require_sceptre_steward(view_func):
    """Gate: Level 3+ OR an active steward-role UserPermission."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        level_ok = user.competence_level in STEWARD_LEVELS
        role_ok = UserPermission.objects.filter(
            user=user,
            role__in=UserPermission.STEWARD_ROLES,
            is_active=True,
        ).exists()
        if not (level_ok or role_ok):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def is_steward(user):
    """Helper — returns True if user has steward access."""
    if user.competence_level in STEWARD_LEVELS:
        return True
    return UserPermission.objects.filter(
        user=user, role__in=UserPermission.STEWARD_ROLES, is_active=True
    ).exists()
```

`@login_required` (Django's own decorator) handles the unauthenticated case and redirects to the real `LOGIN_URL` (`/accounts/login/`) automatically — no manual `redirect('/login/')` needed, and no `from django.shortcuts import redirect` import either, since nothing in this file calls it directly anymore.

**Step 3: Verify**

```bash
python manage.py shell -c "
from sceptre.auth import require_sceptre_participant, require_sceptre_steward, is_steward
print('OK — sceptre auth helpers importable')
"
```

**Step 4: Commit**

```bash
git add sceptre/ ics_project/settings/base.py
git commit -m "feat(sceptre): create sceptre app with participant and steward auth decorators"
```

---

## Task 4 — Build participant home screen

**Files:**
- Modify: `sceptre/views.py` — add participant views
- Create: `templates/sceptre/base.html`
- Create: `templates/sceptre/_nav.html`
- Create: `templates/sceptre/home/home.html`
- Create: `templates/sceptre/home/_now_playing.html`

**Step 1: Create templates/sceptre/base.html**

```html
<!-- templates/sceptre/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Ichebo{% endblock %} — Sceptre Community</title>
  {% load static %}
  <link rel="stylesheet" href="{% static 'css/main.css' %}">
  <script src="{% static 'js/htmx.min.js' %}" defer></script>
</head>
<body class="sceptre-shell">
  {% include "sceptre/_nav.html" %}
  <main class="sceptre-main">
    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

**Note:** Use the existing static files paths — do not invent new CSS files. Reuse existing CSS classes from the current platform where possible.

**Step 2: Create templates/sceptre/_nav.html**

```html
<!-- templates/sceptre/_nav.html -->
{% load static %}
<nav class="sceptre-nav">
  <div class="sceptre-nav__brand">
    <a href="{% url 'sceptre:home' %}">
      <img src="{% static 'img/ichebo-mark.svg' %}" alt="Ichebo" height="32">
    </a>
  </div>

  <div class="sceptre-nav__links">
    <a href="{% url 'sceptre:home' %}"
       class="nav-link {% if request.resolver_match.url_name == 'home' %}nav-link--active{% endif %}">
      Channel
    </a>
    <a href="{% url 'sceptre:community' %}"
       class="nav-link {% if request.resolver_match.url_name == 'community' %}nav-link--active{% endif %}">
      Community
    </a>
    <a href="{% url 'sceptre:learn' %}"
       class="nav-link {% if request.resolver_match.url_name == 'learn' %}nav-link--active{% endif %}">
      Learn
    </a>
    <a href="{% url 'sceptre:bible' %}" class="nav-link">Bible</a>
    <a href="{% url 'sceptre:support' %}" class="nav-link">Support</a>
  </div>

  <div class="sceptre-nav__profile">
    {% if user.is_authenticated %}
      <a href="{% url 'sceptre:profile' %}" class="nav-avatar">
        {{ user.get_full_name|default:user.username|slice:":1"|upper }}
      </a>

      {% if is_steward %}
        <!-- Steward management section -->
        <div class="steward-nav">
          <span class="label-tag">&mdash;&mdash; COMMUNITY MANAGEMENT</span>
          <a href="{% url 'sceptre:steward_members' %}" class="nav-link nav-link--steward">Members</a>
          <a href="{% url 'sceptre:steward_gatherings' %}" class="nav-link nav-link--steward">Gatherings</a>
          <a href="{% url 'sceptre:steward_formation' %}" class="nav-link nav-link--steward">Formation</a>
          <a href="{% url 'sceptre:steward_announcements' %}" class="nav-link nav-link--steward">Announcements</a>
          <a href="{% url 'sceptre:steward_support' %}" class="nav-link nav-link--steward">Support Queue</a>
          <a href="{% url 'sceptre:steward_settings' %}" class="nav-link nav-link--steward">Settings</a>
        </div>
      {% endif %}
    {% endif %}
  </div>
</nav>
```

**Step 3: Add views to sceptre/views.py**

```python
# sceptre/views.py
"""
sceptre.ichebo.org — participant and steward views.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from sceptre.auth import require_sceptre_participant, require_sceptre_steward, is_steward


def _get_tenant_for_user(user):
    """Resolve the user's active community tenant."""
    from tenants.models import UserPermission
    perm = UserPermission.objects.filter(
        user=user,
        is_active=True,
        deleted_at__isnull=True,
    ).select_related('tenant').first()
    return perm.tenant if perm else None


@require_sceptre_participant
def participant_home(request):
    """
    Participant home — channel video first, four quick-access tiles below.
    """
    tenant = _get_tenant_for_user(request.user)
    user_is_steward = is_steward(request.user)

    return render(request, 'sceptre/home/home.html', {
        'tenant': tenant,
        'tenant_id': str(tenant.id) if tenant else '',
        'is_steward': user_is_steward,
    })


@require_sceptre_participant
def now_playing_partial(request):
    """
    HTMX partial — polls GET /api/broadcast/now/ and returns the now-playing strip.
    Called by hx-trigger='every 60s' from the home template.
    """
    tenant = _get_tenant_for_user(request.user)
    now_playing = None

    if tenant:
        import requests as http_requests
        from django.conf import settings
        try:
            token = _get_api_token(request.user)
            resp = http_requests.get(
                f'http://127.0.0.1:{settings.GUNICORN_PORT if hasattr(settings, "GUNICORN_PORT") else 8000}'
                f'/api/broadcast/now/?tenant_id={tenant.id}',
                headers={'Authorization': f'Token {token}'},
                timeout=5,
            )
            if resp.status_code == 200:
                now_playing = resp.json()
        except Exception:
            pass

    return render(request, 'sceptre/home/_now_playing.html', {
        'now_playing': now_playing,
        'tenant_id': str(tenant.id) if tenant else '',
    })


def _get_api_token(user):
    """Get or create a DRF auth token for the user."""
    from rest_framework.authtoken.models import Token
    token, _ = Token.objects.get_or_create(user=user)
    return token.key


@require_sceptre_participant
def community_area(request):
    """Community area — announcements, gatherings, community info summary."""
    tenant = _get_tenant_for_user(request.user)
    user_is_steward = is_steward(request.user)

    from records.models import Record
    announcements = Record.objects.filter(
        record_family='community',
        record_type='community_post',
        tenant=tenant,
        status='active',
        deleted_at__isnull=True,
    ).order_by('-created_at')[:5]

    return render(request, 'sceptre/community/community.html', {
        'tenant': tenant,
        'announcements': announcements,
        'is_steward': user_is_steward,
    })


@require_sceptre_participant
def learn_summary(request):
    """Learn summary — next lesson, active programme, progress."""
    user_is_steward = is_steward(request.user)
    # Delegate full learn experience to learn.ichebo.org when built.
    # For now, show a summary and link to the existing Learn app at app.ichebo.org.
    return render(request, 'sceptre/learn/learn.html', {
        'is_steward': user_is_steward,
    })


@require_sceptre_participant
def bible_redirect(request):
    """Bible — redirect to bible.ichebo.org when live, else app.ichebo.org/bible/."""
    # Redirect to bible.ichebo.org once that surface is built.
    # Interim: redirect to the existing Bible app.
    return redirect('/bible/')


@require_sceptre_participant
def support_redirect(request):
    """Support — redirect to the community support request list."""
    return redirect('/community/support/')


@require_sceptre_participant
def profile_summary(request):
    """Profile summary — interim until identity.ichebo.org ships."""
    user_is_steward = is_steward(request.user)
    return render(request, 'sceptre/profile/profile.html', {
        'is_steward': user_is_steward,
    })


# ── Steward views ──────────────────────────────────────────────────────────

@require_sceptre_steward
def steward_members(request):
    """Member roster — delegate to community app's member management."""
    return redirect('/community/members/')


@require_sceptre_steward
def steward_gatherings(request):
    return redirect('/community/gatherings/')


@require_sceptre_steward
def steward_formation(request):
    return redirect('/community/formation/')


@require_sceptre_steward
def steward_announcements(request):
    return redirect('/community/feed/new/')


@require_sceptre_steward
def steward_support_redirect(request):
    return redirect('/community/support/queue/')


@require_sceptre_steward
def steward_settings(request):
    return render(request, 'sceptre/steward/settings.html', {
        'is_steward': True,
    })
```

**Step 4: Create participant home template**

```html
<!-- templates/sceptre/home/home.html -->
{% extends "sceptre/base.html" %}
{% block title %}Home{% endblock %}

{% block content %}
<div class="sceptre-home">

  <!-- Channel video player — full width, dominant -->
  <div class="channel-player-container">
    <div id="channel-player"
         hx-get="/sceptre/now-playing/"
         hx-trigger="load, every 60s"
         hx-swap="innerHTML">
      {% include "sceptre/home/_now_playing.html" with now_playing=None tenant_id=tenant_id %}
    </div>
  </div>

  <!-- Quick-access tiles -->
  <div class="quick-tiles">
    <a href="{% url 'sceptre:community' %}" class="quick-tile">
      <div class="quick-tile__left-rule"></div>
      <div class="quick-tile__icon">&#128101;</div>
      <div class="quick-tile__label">Community</div>
    </a>
    <a href="{% url 'sceptre:learn' %}" class="quick-tile">
      <div class="quick-tile__left-rule"></div>
      <div class="quick-tile__icon">&#127979;</div>
      <div class="quick-tile__label">Learn</div>
    </a>
    <a href="{% url 'sceptre:bible' %}" class="quick-tile">
      <div class="quick-tile__left-rule"></div>
      <div class="quick-tile__icon">&#128214;</div>
      <div class="quick-tile__label">Bible</div>
    </a>
    <a href="{% url 'sceptre:support' %}" class="quick-tile">
      <div class="quick-tile__left-rule"></div>
      <div class="quick-tile__icon">&#128172;</div>
      <div class="quick-tile__label">Support</div>
    </a>
  </div>

</div>
{% endblock %}
```

**Step 5: Create now-playing partial**

```html
<!-- templates/sceptre/home/_now_playing.html -->
{% if now_playing and now_playing.content_type != 'offline' %}

  <div class="now-playing">
    {% if now_playing.is_live %}
      <!-- Live HLS stream -->
      <video id="channel-video"
             class="channel-video"
             controls
             autoplay
             muted>
        <source src="{{ now_playing.hls_url }}" type="application/x-mpegURL">
      </video>
      <div class="now-playing-strip">
        <span class="live-badge">&#9679; LIVE</span>
        <span class="now-playing-title">{{ now_playing.title }}</span>
      </div>
    {% else %}
      <!-- VOD -->
      <video id="channel-video"
             class="channel-video"
             controls
             autoplay
             muted>
        <source src="{{ now_playing.video_url }}" type="video/mp4">
      </video>
      <div class="now-playing-strip">
        <span class="now-playing-title">{{ now_playing.title|default:"" }}</span>
        {% if now_playing.ends_at %}
          <span class="now-playing-ends">Until {{ now_playing.ends_at }}</span>
        {% endif %}
      </div>
    {% endif %}

    {% if now_playing.next_scheduled %}
      <div class="up-next">
        Up next: <strong>{{ now_playing.next_scheduled.title }}</strong>
        at {{ now_playing.next_scheduled.starts_at }}
      </div>
    {% endif %}
  </div>

{% else %}
  <!-- Channel offline state -->
  <div class="channel-offline">
    <div class="channel-offline__frame">
      <div class="channel-offline__brand">Ichebo</div>
      <p class="channel-offline__message">Channel offline</p>
    </div>
  </div>
{% endif %}
```

**Step 6: Add now-playing URL**

Add to `sceptre/urls.py`:

```python
path('now-playing/', views.now_playing_partial, name='now_playing_partial'),
```

**Step 7: Create placeholder templates for remaining pages**

```bash
mkdir -p templates/sceptre/community templates/sceptre/learn \
         templates/sceptre/profile templates/sceptre/steward
```

Create minimal templates for each (they redirect to existing app views — just need to not 500):

```html
<!-- templates/sceptre/community/community.html -->
{% extends "sceptre/base.html" %}
{% block title %}Community{% endblock %}
{% block content %}
<div class="page-container">
  <div class="page-header">
    <span class="label-tag">&mdash;&mdash; COMMUNITY</span>
    <h1 class="page-title">Community</h1>
  </div>
  {% for post in announcements %}
    <div class="feed-item">
      <div class="feed-item__left-rule"></div>
      <div class="feed-item__body">
        <div class="feed-item__title">{{ post.title }}</div>
        <div class="feed-item__meta">{{ post.created_at|date:"d M Y" }}</div>
      </div>
    </div>
  {% empty %}
    <p class="empty-state">No announcements yet.</p>
  {% endfor %}
</div>
{% endblock %}
```

```html
<!-- templates/sceptre/learn/learn.html -->
{% extends "sceptre/base.html" %}
{% block title %}Learn{% endblock %}
{% block content %}
<div class="page-container">
  <div class="page-header">
    <span class="label-tag">&mdash;&mdash; FORMATION</span>
    <h1 class="page-title">Learn</h1>
  </div>
  <p>Your formation journey continues at
    <a href="/learn/">the Learn platform</a>.
  </p>
</div>
{% endblock %}
```

```html
<!-- templates/sceptre/profile/profile.html -->
{% extends "sceptre/base.html" %}
{% block title %}Profile{% endblock %}
{% block content %}
<div class="page-container">
  <div class="page-header">
    <span class="label-tag">&mdash;&mdash; IDENTITY</span>
    <h1 class="page-title">{{ user.get_full_name|default:user.username }}</h1>
  </div>
  <p>Level: {{ user.competence_level }}</p>
  <p><a href="/profile/">Full profile settings</a></p>
</div>
{% endblock %}
```

```html
<!-- templates/sceptre/steward/settings.html -->
{% extends "sceptre/base.html" %}
{% block title %}Community Settings{% endblock %}
{% block content %}
<div class="page-container">
  <div class="page-header">
    <span class="label-tag">&mdash;&mdash; COMMUNITY MANAGEMENT</span>
    <h1 class="page-title">Settings</h1>
  </div>
  <p><a href="/community/">Community management</a></p>
</div>
{% endblock %}
```

**Step 8: Commit**

```bash
git add sceptre/views.py sceptre/urls.py \
  templates/sceptre/
git commit -m "feat(sceptre): participant home, now-playing channel player, quick-access tiles, community area, steward redirects"
```

---

## Task 5 — Nginx configuration and SSL

**This task runs on the server — SSH as ics@37.27.82.169**

**Step 1: Create Nginx server block**

```bash
sudo nano /etc/nginx/sites-available/sceptre.ichebo.org
```

Paste:

```nginx
server {
    listen 80;
    server_name sceptre.ichebo.org;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/ics/ichebo-platform/staticfiles/;
    }

    location /media/ {
        alias /home/ics/ichebo-platform/media/;
    }
}
```

**Step 2: Enable the site**

```bash
sudo ln -s /etc/nginx/sites-available/sceptre.ichebo.org \
           /etc/nginx/sites-enabled/sceptre.ichebo.org
sudo nginx -t
# Expected: syntax is ok / test is successful
sudo systemctl reload nginx
```

**Step 3: Obtain SSL certificate**

```bash
# Confirm DNS A record is live first:
dig sceptre.ichebo.org +short
# Expected: 37.27.82.169

sudo certbot --nginx -d sceptre.ichebo.org
# Follow prompts — certbot will update the Nginx config and create HTTPS redirect
```

**Step 4: Test HTTPS**

```bash
curl -I https://sceptre.ichebo.org/
# Expected: HTTP/2 200 or 302 (if login redirect)
```

**Step 5: Deploy the code**

```bash
cd /home/ics/ichebo-platform
git pull origin main
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart ics-gunicorn
```

**Step 6: Commit the Nginx config to the repo**

```bash
# On local machine
cp /etc/nginx/sites-available/sceptre.ichebo.org \
   deploy/nginx/sceptre.ichebo.org.conf
git add deploy/nginx/sceptre.ichebo.org.conf
git commit -m "ops: add Nginx config for sceptre.ichebo.org"
```

---

## Task 6 — Write tests

**Files:**
- Create: `sceptre/tests/test_sceptre_surface.py`

```python
# sceptre/tests/test_sceptre_surface.py
"""
Tests for Phase H.6 — sceptre.ichebo.org surface.
Covers: middleware routing, participant access control,
steward gating, home page rendering, now-playing partial.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse

from middleware.site_router import SiteRouterMiddleware
from sceptre.auth import is_steward
from tenants.models import Tenant, UserPermission

User = get_user_model()


def make_tenant(name='Sceptre Tenant', slug='sceptre-test'):
    # Tenant requires slug (unique), path (the real field — not
    # tenant_path, which lives on UserPermission), tier, and created_by —
    # none of which the original draft of this helper supplied.
    admin = User.objects.create_user(
        username='_test_admin_h6', email='_test_admin_h6@test.com',
    )
    return Tenant.objects.create(
        name=name, slug=slug, path=f'/global/{slug}/',
        tier='church_node', created_by=admin,
    )


def make_user(username, level=1, tenant=None, role=None):
    user = User.objects.create_user(
        username=username, password='testpass123',
        email=f'{username}@test.com',
    )
    user.competence_level = level   # real IntegerField — pass an int, not a string
    user.save()
    if tenant and role:
        UserPermission.objects.create(
            user=user, tenant=tenant, role=role,
            is_active=True, tenant_path=tenant.path,
        )
    return user


class TestSiteRouterMiddleware(TestCase):
    """Middleware sets request.site and request.urlconf correctly."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SiteRouterMiddleware(lambda r: r)

    def test_sceptre_host_sets_community_site(self):
        request = self.factory.get('/', HTTP_HOST='sceptre.ichebo.org')
        self.middleware(request)
        self.assertEqual(request.site, 'community')
        self.assertEqual(request.urlconf, 'sceptre.urls')

    def test_app_host_sets_agency_site(self):
        request = self.factory.get('/', HTTP_HOST='app.ichebo.org')
        self.middleware(request)
        self.assertEqual(request.site, 'agency')
        self.assertFalse(hasattr(request, 'urlconf'))

    def test_unknown_host_defaults_to_agency(self):
        request = self.factory.get('/', HTTP_HOST='localhost')
        self.middleware(request)
        self.assertEqual(request.site, 'agency')


class TestSceptreAccessControl(TestCase):
    """Participant and steward gates."""

    def setUp(self):
        self.tenant = make_tenant()
        self.participant = make_user('part_h6', level=1, tenant=self.tenant, role='member')
        self.steward = make_user('stew_h6', level=3, tenant=self.tenant, role='branch-steward')
        self.guest = make_user('guest_h6', level='0a')
        self.client = Client()

    def test_participant_can_access_home(self):
        self.client.login(username='part_h6', password='testpass123')
        response = self.client.get('/', HTTP_HOST='sceptre.ichebo.org', follow=True)
        # Should not get 403 or 500
        self.assertNotEqual(response.status_code, 403)
        self.assertNotEqual(response.status_code, 500)

    def test_unauthenticated_redirected_to_login(self):
        response = self.client.get('/', HTTP_HOST='sceptre.ichebo.org')
        self.assertEqual(response.status_code, 302)

    def test_guest_level_0a_gets_403(self):
        self.client.login(username='guest_h6', password='testpass123')
        response = self.client.get('/', HTTP_HOST='sceptre.ichebo.org')
        self.assertEqual(response.status_code, 403)

    def test_steward_view_rejects_participant(self):
        self.client.login(username='part_h6', password='testpass123')
        response = self.client.get(
            '/steward/members/', HTTP_HOST='sceptre.ichebo.org'
        )
        self.assertEqual(response.status_code, 403)

    def test_steward_can_access_steward_view(self):
        self.client.login(username='stew_h6', password='testpass123')
        response = self.client.get(
            '/steward/members/', HTTP_HOST='sceptre.ichebo.org', follow=True
        )
        self.assertNotEqual(response.status_code, 403)


class TestIsStew(TestCase):
    """is_steward helper function."""

    def setUp(self):
        self.tenant = make_tenant(name='Stew T', slug='stewt')

    def test_level_3_is_steward(self):
        user = make_user('s_l3', level=3)
        self.assertTrue(is_steward(user))

    def test_level_1_not_steward(self):
        user = make_user('s_l1', level=1)
        self.assertFalse(is_steward(user))

    def test_level_1_with_steward_role_is_steward(self):
        user = make_user('s_role', level=1, tenant=self.tenant, role='branch-steward')
        self.assertTrue(is_steward(user))


class TestParticipantHomeTemplate(TestCase):
    """Participant home renders without error."""

    def setUp(self):
        self.tenant = make_tenant(name='Home T', slug='homet')
        self.user = make_user('home_user', level=1, tenant=self.tenant, role='member')
        self.client = Client()

    def test_home_renders_200(self):
        self.client.login(username='home_user', password='testpass123')
        response = self.client.get('/', HTTP_HOST='sceptre.ichebo.org')
        self.assertEqual(response.status_code, 200)

    def test_home_contains_quick_tiles(self):
        self.client.login(username='home_user', password='testpass123')
        response = self.client.get('/', HTTP_HOST='sceptre.ichebo.org')
        self.assertContains(response, 'Community')
        self.assertContains(response, 'Learn')
        self.assertContains(response, 'Bible')
        self.assertContains(response, 'Support')

    def test_steward_nav_hidden_from_participant(self):
        self.client.login(username='home_user', password='testpass123')
        response = self.client.get('/', HTTP_HOST='sceptre.ichebo.org')
        self.assertNotContains(response, 'COMMUNITY MANAGEMENT')

    def test_steward_nav_visible_to_steward(self):
        steward = make_user('home_stew', level=3, tenant=self.tenant, role='branch-steward')
        self.client.login(username='home_stew', password='testpass123')
        response = self.client.get('/', HTTP_HOST='sceptre.ichebo.org')
        self.assertContains(response, 'COMMUNITY MANAGEMENT')
```

**Run tests:**

```bash
python manage.py test sceptre.tests.test_sceptre_surface -v 2
python manage.py test --verbosity=1 2>&1 | tail -5
```

**Commit:**

```bash
git add sceptre/tests/
git commit -m "test(sceptre): H.6 middleware routing, access control, home template test suite"
```

---

## Task 7 — Final verification and merge

```bash
python manage.py check
python manage.py showmigrations | grep "\[ \]"

# Verify sceptre.ichebo.org responds correctly in production
curl -I https://sceptre.ichebo.org/
# Expected: 302 → /login/ (unauthenticated) or 200 (if test account active)

git log --oneline main..HEAD
# 7 commits expected (including Nginx config)

git checkout main
git merge --no-ff v3-h6-sceptre-surface \
  -m "feat(sceptre): H.6 — sceptre.ichebo.org shell, participant home, steward side"
git push origin main
```

---

## Exit Criteria

- [ ] `sceptre.ichebo.org` resolves with valid SSL certificate
- [ ] `SiteRouterMiddleware` sets `request.site = 'community'` and `request.urlconf = 'sceptre.urls'` for `sceptre.ichebo.org` requests
- [ ] `app.ichebo.org` behaviour is completely unchanged
- [ ] Participant home (`/`) renders with channel video player, now-playing strip, four quick-access tiles
- [ ] Channel offline state renders correctly when no content is configured
- [ ] Steward navigation section (`COMMUNITY MANAGEMENT`) visible only to Level 3+ users
- [ ] Unauthenticated users get redirected to `/accounts/login/`
- [ ] All steward views return 403 for Level 0–2 users
- [ ] Templates isolated: `templates/sceptre/` renders without bleed from the existing flat `templates/` tree

The original draft of this checklist had two contradictory lines here — "Level 0a users get 403 on all participant routes" alongside "steward views return 403 for Level 0b–2 users" — which only make sense if 0a and 0b are different gating outcomes, but no such distinction exists in the real `competence_level` model (a single integer `0`). Removed the contradictory line; if a real 0a/0b-equivalent distinction is wanted (e.g. "hasn't started induction" vs. "mid-induction"), it needs its own exit criterion once that's actually decided and modeled — see Doc J Part 5.1's open question.
- [ ] `python manage.py check` — 0 issues
- [ ] All tests in `sceptre/tests/test_sceptre_surface.py` pass
