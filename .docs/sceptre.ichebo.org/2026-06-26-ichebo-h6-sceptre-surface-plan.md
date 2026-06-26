# Phase H.6 — sceptre.ichebo.org Surface + Participant Home

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build `sceptre.ichebo.org` as a role-adaptive Django surface — subdomain routing middleware, separate URL conf and template directories, participant home screen with channel video player and four quick-access tiles, steward management navigation, and Nginx + SSL configuration.

**Architecture:** Subdomain-aware URL routing in one Django project — no multi-site framework (ADR-022). `SiteRouterMiddleware` detects the host and sets `request.site`. `sceptre/urls.py` is a new URL conf. Templates live in `templates/sceptre/`. Same `User`, `Tenant`, `Record` models underpin both subdomains. Role-adaptive shell: steward navigation rendered only for Level 3+ or `-steward` role holders. Channel video calls `GET /api/broadcast/now/` (built in H.7).

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
- Modify: `ics_project/settings.py` — add middleware and `sceptre.ichebo.org` to `ALLOWED_HOSTS`

**Step 1: Create the middleware**

```python
# middleware/site_router.py
"""
SiteRouterMiddleware — sets request.site based on incoming Host header.
Used to serve sceptre.ichebo.org from the same Django process as app.ichebo.org.
ADR-022.
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

In `ics_project/settings.py`:

Find `MIDDLEWARE` list and add at the top (before `SecurityMiddleware` if present, or first):

```python
'middleware.site_router.SiteRouterMiddleware',
```

Find `ALLOWED_HOSTS` and add:

```python
'sceptre.ichebo.org',
```

Find `SESSION_COOKIE_DOMAIN` (or add it):

```python
SESSION_COOKIE_DOMAIN = '.ichebo.org'
CSRF_COOKIE_DOMAIN = '.ichebo.org'
```

**Note on SESSION_COOKIE_DOMAIN:** If this causes test failures (Django test client does not set domain cookies), wrap it in an environment check:

```python
if not DEBUG:
    SESSION_COOKIE_DOMAIN = '.ichebo.org'
    CSRF_COOKIE_DOMAIN = '.ichebo.org'
```

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
git add middleware/site_router.py ics_project/settings.py
git commit -m "feat(sceptre): add SiteRouterMiddleware for subdomain detection (ADR-022)"
```

---

## Task 2 — Create sceptre URL conf and URL dispatcher

**Files:**
- Create: `sceptre/urls.py`
- Modify: `ics_project/urls.py` — subdomain-aware dispatcher

**Step 1: Read the current ROOT_URLCONF and urls.py**

```bash
grep -n "ROOT_URLCONF\|urlpatterns\|include" ics_project/settings.py ics_project/urls.py | head -20
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

Add to `INSTALLED_APPS` in `settings.py`:

```python
'sceptre',
```

**Step 2: Create sceptre/auth.py**

```python
# sceptre/auth.py
"""
View decorators for sceptre.ichebo.org access control.
Participant gate: Level 0b+.
Steward gate: Level 3+ OR -steward role.
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


PARTICIPANT_LEVELS = ['0b', '1', '2', '3', '4', '5']
STEWARD_LEVELS = ['3', '4', '5']


def require_sceptre_participant(view_func):
    """Gate: authenticated user with competence_level 0b+."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        level = getattr(request.user, 'competence_level', '0a')
        if level not in PARTICIPANT_LEVELS:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def require_sceptre_steward(view_func):
    """Gate: Level 3+ OR active -steward UserPermission role."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        level_ok = getattr(user, 'competence_level', '0') in STEWARD_LEVELS
        if not level_ok:
            from tenants.models import UserPermission
            role_ok = UserPermission.objects.filter(
                user=user,
                role__endswith='-steward',
                is_active=True,
            ).exists()
            if not role_ok:
                raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def is_steward(user):
    """Helper — returns True if user has steward access."""
    if getattr(user, 'competence_level', '0') in STEWARD_LEVELS:
        return True
    from tenants.models import UserPermission
    return UserPermission.objects.filter(
        user=user, role__endswith='-steward', is_active=True
    ).exists()
```

**Step 3: Verify**

```bash
python manage.py shell -c "
from sceptre.auth import require_sceptre_participant, require_sceptre_steward, is_steward
print('OK — sceptre auth helpers importable')
"
```

**Step 4: Commit**

```bash
git add sceptre/ ics_project/settings.py
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


def make_tenant(name='Sceptre Tenant', path='/global/sceptre_test/'):
    return Tenant.objects.create(name=name, tenant_path=path)


def make_user(username, level='1', tenant=None, role=None):
    user = User.objects.create_user(
        username=username, password='testpass123',
        email=f'{username}@test.com',
    )
    user.competence_level = level
    user.save()
    if tenant and role:
        UserPermission.objects.create(
            user=user, tenant=tenant, role=role,
            is_active=True, tenant_path=tenant.tenant_path,
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
        self.participant = make_user('part_h6', level='1', tenant=self.tenant, role='member')
        self.steward = make_user('stew_h6', level='3', tenant=self.tenant, role='branch-steward')
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
        self.tenant = make_tenant(name='Stew T', path='/global/stewt/')

    def test_level_3_is_steward(self):
        user = make_user('s_l3', level='3')
        self.assertTrue(is_steward(user))

    def test_level_1_not_steward(self):
        user = make_user('s_l1', level='1')
        self.assertFalse(is_steward(user))

    def test_level_1_with_steward_role_is_steward(self):
        user = make_user('s_role', level='1', tenant=self.tenant, role='branch-steward')
        self.assertTrue(is_steward(user))


class TestParticipantHomeTemplate(TestCase):
    """Participant home renders without error."""

    def setUp(self):
        self.tenant = make_tenant(name='Home T', path='/global/homet/')
        self.user = make_user('home_user', level='1', tenant=self.tenant, role='member')
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
        steward = make_user('home_stew', level='3', tenant=self.tenant, role='branch-steward')
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
- [ ] Level 0a users get 403 on all participant routes
- [ ] Unauthenticated users get redirected to login
- [ ] All steward views return 403 for Level 0b–2 users
- [ ] Templates isolated: `templates/sceptre/` renders without bleed from `templates/` (agency templates)
- [ ] `python manage.py check` — 0 issues
- [ ] All tests in `sceptre/tests/test_sceptre_surface.py` pass
