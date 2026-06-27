# Phase H.6 — sceptre.ichebo.org Surface + Participant Home

> ## ⚠️ Correction, 2026-06-26 — not yet built; real fixes needed before execution (v2 — body code now fixed, not just flagged)
>
> **v2 update:** the 14-point list below was the first pass — it found real problems but left most of them as notes without touching the body code. This second pass fixed the body directly, task by task, the same treatment H.5/H.7 already got: `now_playing_partial`/`_get_api_token`'s dead HTTP-self-call code deleted and replaced with a direct `resolve_now_playing(tenant)` call; `community_area`'s fake `record_type='community_post'` replaced with the real `'announcement'` plus the established tenant-wide-OR-scoped `Q()` filter; all three broken steward redirect targets (`/community/formation/`, `/community/feed/new/`, `/community/support/queue/` — none of which exist) replaced with their real paths; `_get_tenant_for_user` given the missing `.order_by('-level')`; `_nav.html` actually restructured to the real slide-in steward-sidebar mechanism (point 14 below only flagged this — Task 4 now implements it, including a small vanilla-JS toggle since the mockup itself has none); the four placeholder templates' fake `page-container`/`label-tag`/`feed-item`/`empty-state` classes replaced with the real inline-style + `ws-`-prefixed convention; `base.html`'s `<head>` fixed to load the real multi-file stylesheet chain (`variables.css`, `workspace.css`) it was missing entirely — without which every `var(--primary)` and `ws-*` class anywhere in this phase would render unstyled; the test suite's `make_tenant`/`make_user` helpers fixed for a real, previously-undiscovered bug (calling `make_tenant()` twice in one `setUp`, which `TestSceptreAccessControl` does, raised `IntegrityError` on a duplicate admin username — verified against the real dev database); Task 5's Nginx block replaced with Doc J's already-corrected version; Task 5/7's stale `venv`/`ics` user/bare `python manage.py` commands fixed to the real `scepter` user, `.venv/`, and `DJANGO_SETTINGS_MODULE` throughout; the exit criteria's stale "0a/0b doesn't exist" paragraph replaced with the real, locked criteria now that the distinction is resolved (see Doc J §5.1, v1.3).
>
> H.6 has not been started — no `sceptre` app, no `SiteRouterMiddleware`, no DNS gap anymore (see point 8). Fixes needed, found by checking every claim against the live repository and production server:
>
> 1. **Server identity is wrong throughout.** Real path: `/home/scepter/ichebo-platform-repo/ichebo-platform` (user `scepter`, not `ics`). Real Gunicorn bind: `127.0.0.1:8001`, not `8000`. Real settings module: `ics_project.settings.production` / `ics_project.settings.base` — there is no single `ics_project/settings.py`. Every `cd`/`source venv/bin/activate`/`python manage.py ...` command in the Pre-Flight Checks and Task 5 needs these paths, and the venv is at `.venv/bin/` inside the repo, activated via `source .venv/bin/activate` (confirmed: production runs Django through `.venv/bin/gunicorn` directly, set by `Environment="PATH=..."` in the systemd unit, not a `source venv/bin/activate` shell step at all — there is no interactive shell session on production; deploys run `DJANGO_SETTINGS_MODULE=ics_project.settings.production .venv/bin/python3 manage.py ...` directly).
> 2. **`ics_project/settings.py` doesn't exist** — settings live in `ics_project/settings/base.py` (shared) and `production.py` (production overrides). `MIDDLEWARE` and `ALLOWED_HOSTS` both live in `base.py`. Task 1's instruction to "find `MIDDLEWARE` list... and add at the top" is otherwise correct — just in the right file.
> 3. **No URL-conf dispatcher function is needed in `ics_project/urls.py` at all.** Task 2 proposes a `get_urlconf(request)` function and an unclear wiring step ("Add to urlpatterns — this is the fallback for agency / sceptre URLs are served by the middleware-set urlconf"). The middleware setting `request.urlconf = 'sceptre.urls'` directly (which Task 2's own Step 3 correctly arrives at) is the *complete* mechanism — Django's resolver checks `request.urlconf` automatically on every request. Delete the `get_urlconf` function and the "Add to urlpatterns" step entirely; `ics_project/urls.py` needs zero changes for this phase.
> 4. **`competence_level` is a real `IntegerField` (`0`–`5`), not a string** — `sceptre/auth.py`'s `PARTICIPANT_LEVELS = ['0b', '1', '2', '3', '4', '5']` and `STEWARD_LEVELS = ['3', '4', '5']` are lists of strings being compared against an int — always `False`, which would lock out every real user. **Separately, the participant gate's logic itself is wrong, not just the types** — Chizola confirmed (2026-06-26) the 0a/0b distinction is real and already implemented: 0a (visitor) has no `UserPermission` on an `induction`-tier tenant at all and should NOT reach this surface (their front door is `join.ichebo.org`); 0b (seeker) has an active induction-tenant `UserPermission` and is the lowest level that should. `competence_level not in (0,1,2,3,4,5)` admits every Level-0 user including pure visitors — wrong. Fix: gate on `competence_level >= 1 OR an active UserPermission on an induction-tier tenant`, mirroring `community/views.py:my_community`'s existing Level-0 branch exactly. See Doc J §5.1/§5.2 (v1.3) for the full reasoning and the corrected code, reproduced below in Task 3.
> 5. **`role__endswith='-steward'` (Task 3's `require_sceptre_steward`/`is_steward`) excludes `'admin'`.** Use `tenants.models.UserPermission.STEWARD_ROLES` instead — `role__in=UserPermission.STEWARD_ROLES`.
> 6. **`_get_tenant_for_user` (Task 4) is missing `.order_by('-level')`.** The established pattern this codebase actually uses everywhere else (`community/views.py:_get_user_permissions`) orders by `-level` before taking `.first()`, so a user with multiple `UserPermission` rows resolves to their *highest*-level tenant, not an arbitrary one. Add `.order_by('-level')` before `.first()`.
> 7. **`now_playing_partial` (Task 4) makes an unnecessary internal HTTP call to its own API**, including a `GUNICORN_PORT` setting that doesn't exist anywhere in this codebase (confirmed) and the wrong port (`8000`) even if it did. There is no reason for a Django view to make an HTTP round-trip to its own server's API to get data — call the resolution function directly instead: `from broadcast.services import resolve_now_playing` (built in H.7) and `result = resolve_now_playing(tenant)`, no `requests`, no token, no port. Delete `_get_api_token` entirely — it exists solely to support this unnecessary HTTP call.
> 8. **DNS is no longer a precondition — `sceptre.ichebo.org` already resolves** to the Django VPS (confirmed live 2026-06-26). Skip the "Confirm DNS A record" line in Pre-Flight Checks; go straight to the Nginx step.
> 9. **Nginx: one file, not a new one.** The real server keeps every subdomain as a `server {}` block pair inside a single file, `/etc/nginx/sites-available/ics` (confirmed by reading the live file) — there is no `sites-available/sceptre.ichebo.org` to create or symlink. Add the new blocks to the existing `ics` file instead, matching its established style (HTTP block that redirects to HTTPS, then the real HTTPS block with `ssl_certificate`/`ssl_certificate_key` paths under `/etc/letsencrypt/live/sceptre.ichebo.org/`, a `location /static/` alias to `/home/scepter/ichebo-platform-repo/ichebo-platform/staticfiles/`, and `proxy_pass http://127.0.0.1:8001;` — see Doc J Part 2.1 for the corrected, complete block). Task 5's Steps 1–2 (create file, symlink into `sites-enabled`) should be replaced with "edit the existing `ics` file directly," since it's already enabled.
> 10. **`SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN` decision locked (Chizola, 2026-06-26): set them to `.ichebo.org`, shared login across both subdomains.** Confirmed absent from both `base.py` and `production.py` before this change. See Task 1 Step 2 for the exact setting to add.
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
DJANGO_SETTINGS_MODULE=ics_project.settings.local python3 manage.py check

# DNS already resolves (confirmed live 2026-06-26) — no DNS precondition
# remains; the Nginx step (Task 5) can proceed straight to editing the
# config, no "confirm DNS first" step needed.
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

`SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN` are not set anywhere currently (confirmed — absent from both `base.py` and `production.py`). **Locked, 2026-06-26: shared login across both subdomains** — a steward logged in on either `app.ichebo.org` or `sceptre.ichebo.org` is authenticated on both, no second login. Add to `base.py`:

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

Corrected against the real `competence_level` `IntegerField`, the real `UserPermission.STEWARD_ROLES` set (which includes `'admin'`, unlike a `-steward` suffix match), and the real, locked 0a/0b participant gate (Doc J §5.1/§5.2, v1.3 — confirmed by Chizola 2026-06-26: 0a/visitor has no induction-tenant placement and should not reach this surface; 0b/seeker does and is the lowest level that should, mirroring `community/views.py:my_community`'s existing Level-0 branch exactly):

```python
# sceptre/auth.py
"""
View decorators for sceptre.ichebo.org access control.
Participant gate: competence_level >= 1, OR an active UserPermission on
an induction-tier tenant (0b/seeker — placed in induction but not yet in
a real Sceptre Community). A 0a/visitor with no induction placement at
all is correctly excluded — their front door is join.ichebo.org, not
this surface. Mirrors community/views.py:my_community's existing
Level-0 branch; not a new rule.
Steward gate: Level 3+ OR a role in UserPermission.STEWARD_ROLES.
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from tenants.models import UserPermission

STEWARD_LEVELS = (3, 4, 5)


def _is_seeker_or_above(user):
    """0b+ — see this file's module docstring."""
    if user.competence_level >= 1:
        return True
    return UserPermission.objects.filter(
        user=user, tenant__tier='induction', is_active=True,
    ).exists()


def require_sceptre_participant(view_func):
    """Gate: 0b (seeker, placed in induction) or higher."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not _is_seeker_or_above(request.user):
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

**Note on how often the 0a branch actually fires, found while verifying this fix:** `accounts/signals.py:auto_place_new_user_in_induction_tenant` auto-places every newly-created `User` into the induction tenant immediately — so in normal operation there's no authenticated user who is genuinely 0a (no induction placement at all); they're 0b the instant their account exists. `_is_seeker_or_above`'s `False` branch is real, correct defensive code for a genuine edge case (the signal's own missing-induction-tenant fallback, or a legacy pre-signal account) — confirmed with Chizola (2026-06-26) to keep it exactly as written rather than simplify it away, since the edge case is real even though it's rare.

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

The original draft only loaded `main.css`. Confirmed against `templates/workspace_shell.html` (the real shell every other authenticated page uses): stylesheets are a multi-file chain — `variables.css` defines every `--primary`/`--card`/`--border`/`--muted`/`--text` custom property, and `workspace.css` defines every `ws-`-prefixed class (`ws-label-tag`, `ws-page-title`). Without both, the placeholder templates in Step 7 (which use exactly these) would render unstyled. `sceptre.css` (new, see correction note point 13) is added last so it can override where the consumer surface needs to look different:

```html
<!-- templates/sceptre/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Ichebo{% endblock %} — Sceptre Community</title>
  {% load static %}
  <link rel="stylesheet" href="{% static 'css/variables.css' %}">
  <link rel="stylesheet" href="{% static 'css/main.css' %}">
  <link rel="stylesheet" href="{% static 'css/workspace.css' %}">
  <link rel="stylesheet" href="{% static 'css/sceptre.css' %}">
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

`static/css/sceptre.css` doesn't exist yet — it needs to be designed and written as part of Task 4 (not deferred to "polish later"), defining every new class introduced in this task: `sceptre-shell`, `top-nav`, `top-nav__brand`/`__links`/`__right`, `steward-trigger`, `avatar`, `steward-sidebar` and its `__header`/`__close`/`__label`/`__title` children, `steward-nav`/`__item`, `channel-player-container`, `channel-video`, `now-playing`/`now-playing-strip`, `live-badge`, `up-next`, `channel-offline`/`__frame`/`__brand`/`__message`, `quick-tiles`/`quick-tile` and its `__left-rule`/`__icon`/`__label` children. The visual reference for all of these is the four mockup files in `sceptre_comm_web-ui_mockup/` — copy their inline `<style>` blocks into this file rather than re-deriving colors/spacing from scratch.

**Step 2: Create templates/sceptre/_nav.html**

Restructured against the real mockup (`sceptre_comm_web-ui_mockup/03-sceptre-steward-panel.html`), confirmed by reading its markup directly — the steward section is **not** an inline block in the profile area (as the original draft had it). It's a `top-nav__right` "Manage" trigger button, plus a separate, normally-hidden `steward-sidebar` panel that slides in from the right over a dimmed `shell-with-steward` wrapper when the trigger is clicked. The mockup is a static design comp with no JS — the open/close toggle below is new, minimal vanilla JS added to make it functional:

```html
<!-- templates/sceptre/_nav.html -->
{% load static %}
<nav class="top-nav">
  <div class="top-nav__brand">
    <a href="{% url 'sceptre:home' %}">
      <img src="{% static 'img/ichebo-mark.svg' %}" alt="Ichebo" height="32">
    </a>
  </div>

  <div class="top-nav__links">
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

  <div class="top-nav__right">
    {% if user.is_authenticated %}
      {% if is_steward %}
        <button type="button" class="steward-trigger" id="steward-trigger" aria-expanded="false" aria-controls="steward-sidebar">
          <svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>
          Manage
        </button>
      {% endif %}
      <a href="{% url 'sceptre:profile' %}" class="avatar">
        {{ user.get_full_name|default:user.username|slice:":1"|upper }}
      </a>
    {% endif %}
  </div>
</nav>

{% if is_steward %}
<!-- Steward sidebar — hidden by default, toggled by #steward-trigger -->
<div class="steward-sidebar" id="steward-sidebar" hidden>
  <div class="steward-sidebar__header">
    <div class="steward-sidebar__close">
      <div class="steward-sidebar__label">Community Management</div>
      <button type="button" class="steward-sidebar__close-btn" id="steward-sidebar-close" aria-label="Close">
        <svg viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>
    {% if tenant %}<div class="steward-sidebar__title">{{ tenant.name }}</div>{% endif %}
  </div>

  <nav class="steward-nav">
    <a href="{% url 'sceptre:steward_members' %}" class="steward-nav__item">Members</a>
    <a href="{% url 'sceptre:steward_gatherings' %}" class="steward-nav__item">Gatherings</a>
    <a href="{% url 'sceptre:steward_formation' %}" class="steward-nav__item">Formation</a>
    <a href="{% url 'sceptre:steward_announcements' %}" class="steward-nav__item">Announcements</a>
    <a href="{% url 'sceptre:steward_support' %}" class="steward-nav__item">Support Queue</a>
    <a href="{% url 'sceptre:steward_settings' %}" class="steward-nav__item">Settings</a>
  </nav>
</div>

<script>
  (function () {
    var trigger = document.getElementById('steward-trigger');
    var sidebar = document.getElementById('steward-sidebar');
    var closeBtn = document.getElementById('steward-sidebar-close');
    if (!trigger || !sidebar) return;

    function open() {
      sidebar.hidden = false;
      trigger.setAttribute('aria-expanded', 'true');
    }
    function close() {
      sidebar.hidden = true;
      trigger.setAttribute('aria-expanded', 'false');
    }

    trigger.addEventListener('click', function () {
      sidebar.hidden ? open() : close();
    });
    closeBtn.addEventListener('click', close);
  })();
</script>
{% endif %}
```

Note: `tenant` must be in every view's context for `{{ tenant.name }}` to render in the sidebar header — already true for `participant_home` (Task 3) but **not** for the steward redirect views (`steward_members`, `steward_gatherings`, etc.), which redirect immediately and never render `_nav.html` themselves. This is fine — the sidebar only actually renders on pages that include `_nav.html` with a real `tenant` in context, i.e. the participant home and `community_area`; the steward views below redirect straight into the existing `app.ichebo.org`-style `/community/...` pages, which have their own nav.

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
    """Resolve the user's active community tenant — their highest-level
    UserPermission, matching the established pattern
    (community/views.py:_get_user_permissions). Without .order_by('-level'),
    a user with multiple UserPermission rows would resolve to an
    arbitrary one rather than their highest-level tenant. The explicit
    deleted_at__isnull=True filter is also redundant and dropped here —
    UserPermission's default manager (SoftDeleteMixin) already excludes
    soft-deleted rows."""
    from tenants.models import UserPermission
    perm = (
        UserPermission.objects.filter(user=user, is_active=True)
        .select_related('tenant')
        .order_by('-level')
        .first()
    )
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
    HTMX partial — resolves the current channel content and returns the
    now-playing strip. Called by hx-trigger='every 60s' from the home
    template. Calls broadcast.services.resolve_now_playing(tenant)
    directly — no HTTP round-trip to this server's own API (the original
    draft's requests.get(...) self-call, with a nonexistent
    GUNICORN_PORT setting and the wrong port even if it existed, has
    been removed — see correction note point 7).
    """
    from broadcast.services import resolve_now_playing

    tenant = _get_tenant_for_user(request.user)
    now_playing = resolve_now_playing(tenant) if tenant else None

    return render(request, 'sceptre/home/_now_playing.html', {
        'now_playing': now_playing,
        'tenant_id': str(tenant.id) if tenant else '',
    })


@require_sceptre_participant
def community_area(request):
    """Community area — announcements, gatherings, community info summary."""
    tenant = _get_tenant_for_user(request.user)
    user_is_steward = is_steward(request.user)

    from django.db.models import Q
    from records.models import Record

    # record_type='community_post' does not exist — the real value used
    # throughout community/views.py is 'announcement'. Tenant-wide
    # announcements (tenant_id IS NULL) are included via Q(), matching
    # the established pattern (e.g. community/views.py:214-223) rather
    # than a plain tenant=tenant filter, which would silently drop them.
    announcements = [] if not tenant else list(
        Record.objects.filter(
            record_family='community',
            record_type='announcement',
            status='active',
            deleted_at__isnull=True,
        ).filter(
            Q(tenant_id=tenant.id) | Q(tenant_id__isnull=True)
        ).order_by('-created_at')[:5]
    )

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
    # Real path is /community/pipeline/ (community/urls.py:
    # name='community-pipeline') — /community/formation/ does not exist.
    return redirect('/community/pipeline/')


@require_sceptre_steward
def steward_announcements(request):
    # /community/feed/new/ does not exist. Announcement authorship is
    # composed inline on the steward dashboard (management_home, real
    # path /community/management/) via the
    # community/htmx/announcement/create/ HTMX endpoint — there is no
    # separate authorship page to redirect to.
    return redirect('/community/management/')


@require_sceptre_steward
def steward_support_redirect(request):
    # Real path is /community/support/ (name='support-requests-queue')
    # — /community/support/queue/ does not exist.
    return redirect('/community/support/')


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

Create minimal templates for each (they redirect to existing app views — just need to not 500).

**`page-container`/`label-tag`/`page-title`/`feed-item`/`empty-state` is not a real class system in this codebase** (confirmed — no matches anywhere in `templates/`). The real convention, confirmed directly in `templates/community/partials/gathering_form.html` and `templates/governance/governance.html`, is inline styles built on CSS custom properties (`var(--card)`, `var(--border)`, `var(--muted)`, `var(--text)`) plus a small set of real `ws-`-prefixed classes for specific reusable widgets (`ws-label-tag`, `ws-page-title`) — not a generic Bootstrap-style grid of container/header/title classes. Rewritten below to match:

```html
<!-- templates/sceptre/community/community.html -->
{% extends "sceptre/base.html" %}
{% block title %}Community{% endblock %}
{% block content %}
<div style="padding: 24px 28px;">
  <div style="margin-bottom: 20px;">
    <div class="ws-label-tag">Community</div>
    <h1 class="ws-page-title" style="font-size: 1.25rem; margin-top: 8px;">{{ tenant.name|default:"Community" }}</h1>
  </div>
  {% for post in announcements %}
    <div style="background: var(--card); border: 1px solid var(--border); border-radius: 12px;
                padding: 16px 20px; margin-bottom: 12px;">
      <div style="font-size: 14px; font-weight: 600; color: var(--text);">{{ post.title }}</div>
      <div style="font-size: 12px; color: var(--muted); margin-top: 4px;">{{ post.created_at|date:"d M Y" }}</div>
    </div>
  {% empty %}
    <p style="color: var(--muted); font-size: 13px;">No announcements yet.</p>
  {% endfor %}
</div>
{% endblock %}
```

```html
<!-- templates/sceptre/learn/learn.html -->
{% extends "sceptre/base.html" %}
{% block title %}Learn{% endblock %}
{% block content %}
<div style="padding: 24px 28px;">
  <div style="margin-bottom: 20px;">
    <div class="ws-label-tag">Formation</div>
    <h1 class="ws-page-title" style="font-size: 1.25rem; margin-top: 8px;">Learn</h1>
  </div>
  <p style="color: var(--text); font-size: 13px;">Your formation journey continues at
    <a href="/learn/" style="color: var(--primary);">the Learn platform</a>.
  </p>
</div>
{% endblock %}
```

```html
<!-- templates/sceptre/profile/profile.html -->
{% extends "sceptre/base.html" %}
{% block title %}Profile{% endblock %}
{% block content %}
<div style="padding: 24px 28px;">
  <div style="margin-bottom: 20px;">
    <div class="ws-label-tag">Identity</div>
    <h1 class="ws-page-title" style="font-size: 1.25rem; margin-top: 8px;">{{ user.get_full_name|default:user.username }}</h1>
  </div>
  <p style="color: var(--text); font-size: 13px;">Level: {{ user.competence_level }}</p>
  <p style="font-size: 13px;"><a href="/profile/" style="color: var(--primary);">Full profile settings</a></p>
</div>
{% endblock %}
```

```html
<!-- templates/sceptre/steward/settings.html -->
{% extends "sceptre/base.html" %}
{% block title %}Community Settings{% endblock %}
{% block content %}
<div style="padding: 24px 28px;">
  <div style="margin-bottom: 20px;">
    <div class="ws-label-tag">Community Management</div>
    <h1 class="ws-page-title" style="font-size: 1.25rem; margin-top: 8px;">Settings</h1>
  </div>
  <p style="font-size: 13px;"><a href="/community/management/" style="color: var(--primary);">Community management</a></p>
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

**This task runs on the server — SSH as `scepter@37.27.82.169`** (not `ics` — see correction note point 1). DNS already resolves (confirmed live 2026-06-26); skip straight to editing Nginx.

**Step 1: Edit the existing Nginx config — do not create a new file**

The real server keeps every subdomain as a `server {}` block pair inside one file, `/etc/nginx/sites-available/ics` (confirmed by reading the live file). There is no `sites-available/sceptre.ichebo.org` to create and no symlink step — it's already enabled as part of `ics`.

```bash
sudo nano /etc/nginx/sites-available/ics
```

Add this block pair alongside the existing `app.ichebo.org` blocks already in the file — copied verbatim from Doc J Part 2.1, the version checked against the real file's style (HTTP→HTTPS redirect, `ssl_certificate` paths, the real `/static/` alias path, the real Gunicorn port):

```nginx
server {
    listen 80;
    server_name sceptre.ichebo.org;
    return 301 https://sceptre.ichebo.org$request_uri;
}

server {
    listen 443 ssl;
    server_name sceptre.ichebo.org;

    ssl_certificate /etc/letsencrypt/live/sceptre.ichebo.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sceptre.ichebo.org/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location /static/ {
        alias /home/scepter/ichebo-platform-repo/ichebo-platform/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
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
        proxy_read_timeout 120;
    }
}
```

**Step 2: Validate and reload**

```bash
sudo nginx -t
# Expected: syntax is ok / test is successful
sudo systemctl reload nginx
```

**Step 3: Obtain the SSL certificate**

```bash
sudo certbot --nginx -d sceptre.ichebo.org
# Follow prompts — certbot will update the Nginx config and create the HTTPS redirect
```

The HTTP→HTTPS `server {}` block above may get rewritten by certbot to its own managed form — that's expected and matches how the existing subdomains' blocks already look (confirmed by reading the live file before this phase).

**Step 4: Test HTTPS**

```bash
curl -I https://sceptre.ichebo.org/
# Expected: HTTP/2 302 → /accounts/login/ (unauthenticated; real LOGIN_URL,
# not /login/ — see correction note point 11)
```

**Step 5: Deploy the code**

Real path is `/home/scepter/ichebo-platform-repo/ichebo-platform`, real venv is `.venv/` not `venv/`, real settings module is `ics_project.settings.production` (no single `ics_project/settings.py` — see correction note points 1–2). Production runs Django through `.venv/bin/gunicorn` directly via a systemd unit — there is no interactive `source venv/bin/activate` shell step on the server itself, deploys run `.venv/bin/python3` directly with `DJANGO_SETTINGS_MODULE` set inline:

```bash
cd /home/scepter/ichebo-platform-repo/ichebo-platform
git pull origin main
DJANGO_SETTINGS_MODULE=ics_project.settings.production .venv/bin/python3 manage.py migrate
DJANGO_SETTINGS_MODULE=ics_project.settings.production .venv/bin/python3 manage.py collectstatic --noinput
sudo systemctl restart ics-gunicorn
```

**Gunicorn systemd unit confirmed live via SSH (2026-06-26):** `ics-gunicorn.service` — "ICS Platform Gunicorn", loaded and active. Also present on the same server: `ics-celery.service` and `ics-celery-beat.service`, neither relevant to this restart.

**Step 6: Commit the Nginx config to the repo**

```bash
# On local machine
cp /etc/nginx/sites-available/ics deploy/nginx/ics.conf
git add deploy/nginx/ics.conf
git commit -m "ops: add sceptre.ichebo.org server blocks to the shared ics Nginx config"
```

Commits the whole `ics` file, not a `sceptre.ichebo.org`-specific one — there is no such file on the server to copy from (see Step 1).

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


def _test_admin():
    """Shared admin user for created_by/granted_by FKs below. get_or_create,
    not create_user — TestSceptreAccessControl.setUp calls make_tenant()
    twice (once for the main tenant, once for the induction tenant); the
    original draft's plain create_user() call inside make_tenant would
    raise IntegrityError on the second call (duplicate username)."""
    admin, _ = User.objects.get_or_create(
        username='_test_admin_h6', defaults={'email': '_test_admin_h6@test.com'},
    )
    return admin


def make_tenant(name='Sceptre Tenant', slug='sceptre-test'):
    # Tenant requires slug (unique), path (the real field — not
    # tenant_path, which lives on UserPermission), tier, and created_by —
    # none of which the original draft of this helper supplied.
    return Tenant.objects.create(
        name=name, slug=slug, path=f'/global/{slug}/',
        tier='church_node', created_by=_test_admin(),
    )


def make_user(username, level=1, tenant=None, role=None):
    user = User.objects.create_user(
        username=username, password='testpass123',
        email=f'{username}@test.com',
    )
    user.competence_level = level   # real IntegerField — pass an int, not a string
    user.save()
    if tenant and role:
        # UserPermission.created_by is a required FK (on_delete=PROTECT,
        # no null=True) — the original draft's UserPermission.objects.create
        # call omitted it entirely, which would raise IntegrityError.
        UserPermission.objects.create(
            user=user, tenant=tenant, role=role, created_by=_test_admin(),
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
    """Participant and steward gates, including the real 0a/visitor vs
    0b/seeker boundary (Doc J §5.1/§5.2, v1.3) — not the fake '0a' string
    level the original draft of this test used."""

    def setUp(self):
        self.tenant = make_tenant()
        self.participant = make_user('part_h6', level=1, tenant=self.tenant, role='member')
        self.steward = make_user('stew_h6', level=3, tenant=self.tenant, role='branch-steward')
        # 0a/visitor — competence_level 0, no induction-tenant UserPermission at all.
        self.visitor = make_user('visitor_h6', level=0)
        # 0b/seeker — competence_level 0, but placed in an induction-tier tenant.
        self.induction_tenant = make_tenant(slug='induction-h6')
        self.induction_tenant.tier = 'induction'
        self.induction_tenant.save(update_fields=['tier'])
        self.seeker = make_user('seeker_h6', level=0, tenant=self.induction_tenant, role='seeker')
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

    def test_visitor_0a_gets_403(self):
        """A pure visitor — no induction placement at all — must not
        reach this surface. Their front door is join.ichebo.org."""
        self.client.login(username='visitor_h6', password='testpass123')
        response = self.client.get('/', HTTP_HOST='sceptre.ichebo.org')
        self.assertEqual(response.status_code, 403)

    def test_seeker_0b_can_access_home(self):
        """A seeker — placed in induction, competence_level still 0 —
        is the lowest level that should reach this surface."""
        self.client.login(username='seeker_h6', password='testpass123')
        response = self.client.get('/', HTTP_HOST='sceptre.ichebo.org', follow=True)
        self.assertNotEqual(response.status_code, 403)
        self.assertNotEqual(response.status_code, 500)

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

Run locally against `ics_project.settings.local` (not bare `python manage.py`, which has no `DJANGO_SETTINGS_MODULE` set):

```bash
DJANGO_SETTINGS_MODULE=ics_project.settings.local python3 manage.py test sceptre.tests.test_sceptre_surface -v 2
```

**Note on the project-wide test run** — `DJANGO_SETTINGS_MODULE=ics_project.settings.local python3 manage.py test` (no app scoping) is currently broken for the whole project by a pre-existing, unrelated migration bug in the `paraclete` app (`duplicate column name: id` on `paraclete_paracleteprompt`), confirmed to predate this branch and reproduce identically on `main` — found while testing H.7. Scoping to `sceptre.tests.test_sceptre_surface` as above does not avoid it, since `manage.py test` always builds the full test database regardless of which app's tests are requested. If this is still unfixed when H.6 is executed, verify test logic manually against the real dev database instead (the approach used throughout H.7) rather than blocking on it.

**Commit:**

```bash
git add sceptre/tests/
git commit -m "test(sceptre): H.6 middleware routing, access control, home template test suite"
```

---

## Task 7 — Final verification and merge

```bash
DJANGO_SETTINGS_MODULE=ics_project.settings.local python3 manage.py check
DJANGO_SETTINGS_MODULE=ics_project.settings.local python3 manage.py showmigrations | grep "\[ \]"

# Verify sceptre.ichebo.org responds correctly in production
curl -I https://sceptre.ichebo.org/
# Expected: 302 → /accounts/login/ (unauthenticated; real LOGIN_URL — not
# /login/, which would be the wrong, 404ing URL) or 200 (if test account active)

git log --oneline main..HEAD
# Commit count will differ from the original draft's "7" once Tasks 1+2
# are merged into one middleware commit (see Task 2's correction) — count
# whatever this branch's actual commits are, don't assume a fixed number.

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
- [ ] Steward navigation section (`Community Management` — real template text is title case; CSS `text-transform: uppercase` only changes the display, not what `assertContains` sees) visible only to Level 3+ users
- [ ] Unauthenticated users get redirected to `/accounts/login/`
- [ ] All steward views return 403 for Level 1–2 users (and for 0b/seeker — stewardship starts at Level 3, not at any participant level)
- [ ] A 0a/visitor (no induction-tenant `UserPermission` at all) gets 403 on every participant route — the rare, real edge case covered by `_is_seeker_or_above`'s `False` branch (see Doc J §5.1, resolved 2026-06-26 — not the prior "open question")
- [ ] A 0b/seeker (placed in induction, `competence_level` still 0) **can** access the participant home and other participant routes — the lowest level that should
- [ ] Templates isolated: `templates/sceptre/` renders without bleed from the existing flat `templates/` tree
- [ ] `static/css/sceptre.css` exists and the participant home / steward sidebar render styled, not as bare unstyled HTML (Task 4 correction note point 13)
- [ ] `DJANGO_SETTINGS_MODULE=ics_project.settings.local python3 manage.py check` — 0 issues
- [ ] All tests in `sceptre/tests/test_sceptre_surface.py` pass (verified manually against real dev data if the pre-existing `paraclete` migration bug still blocks `manage.py test`)
