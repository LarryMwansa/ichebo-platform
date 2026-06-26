# Phase H.7 — Ichebo Channel (broadcast app + now-playing endpoint + channel scheduler UI)

> ## ⚠️ Correction, 2026-06-26 — not yet built; real fixes needed before execution
>
> H.7 has not been started — no `broadcast` app, no `ChannelConfig`/`ChannelSlot`, no now-playing endpoint exist anywhere in the codebase as of 2026-06-26. Fixes needed, found by checking every claim against the live repository:
>
> 1. **`ics_project/settings.py` doesn't exist.** `INSTALLED_APPS` lives in `ics_project/settings/base.py`. Task 1, Step 3's instruction is otherwise correct, just needs the right file.
> 2. **`competence_level` is a real `IntegerField` (`0`–`5`), not a string.** Task 4's `_require_architect` does `if getattr(user, 'competence_level', '0') != '5':` — comparing an int to the string `'5'` is always `True` in real Python, meaning **every user, including a real Level 5 Architect, would be denied** by this check as written. Fix: `if getattr(user, 'competence_level', 0) != 5:`.
> 3. **`Tenant.objects.filter(deleted_at__isnull=True)` is correct** (confirmed — `Tenant` uses `SoftDeleteMixin`, which provides `deleted_at`) — no fix needed there, called out only because it's one of the few claims in this plan that checked out on first read.
> 4. **`agency_urls.py` doesn't exist** — Task 4, Step 4 already hedges with "or the main `urls.py` for `app.ichebo.org`," which is the correct fallback: the real file is `ics_project/urls.py` (`ROOT_URLCONF = 'ics_project.urls'`). Add `path('channel/', include('broadcast.channel_urls'))` there.
> 5. **CSS classes throughout the scheduler templates (Task 4, Step 5) don't match this codebase's convention.** `class="btn btn-primary"`, `class="page-container"`, `class="label-tag"`, `class="field-group"`/`field-label`/`field-input`, `class="slot-item"` etc. are a generic system that doesn't exist here. Since this scheduler lives at `app.ichebo.org` (the existing Apostolic Command Shell), it should use the real, established `ws-`-prefixed classes and inline-style convention — see any real governance/community template (e.g. `templates/governance/governance.html`, `templates/community/partials/gathering_form.html`) for the actual pattern. Every template in Task 4 would render unstyled as written.
> 6. **The `video_record_id`/`loop_default_video_id` comments are slightly wrong about where the referenced data lives.** "FK to video_live VideoRecord or media VideoRecord — resolved at read time" (Task 1, Step 2) — `video_live` has no `VideoRecord` model at all; its only surviving model after Video Direction v2 (2026-06-23/24) is `BroadcastSchedule`. `media.VideoRecord` is real, but it's explicitly documented in its own docstring as "not a database model" — a typed Python wrapper around a `records.Record` with `record_family='media'`, with no primary key of its own. These fields should be understood as storing a `Record.id`, not a separate "VideoRecord" identifier. Functionally the field type (`UUIDField`) is still correct; only the comment is misleading.
> 7. **The test suite's `make_tenant` helper has the same `Tenant` field gaps as H.5 and H.6's test suites** — `Tenant.objects.create(name=..., tenant_path=...)` is missing `slug` (required, unique), uses the wrong field name (`path`, not `tenant_path`, which lives on `UserPermission`), and is missing required `tier` and `created_by`. See H.5's correction note, point 7, for a working helper shape.
> 8. **Server paths**: real repo path is `/home/scepter/ichebo-platform-repo/ichebo-platform` (user `scepter`), not implied elsewhere in this folder's docs as `/home/ics/...`. Not directly referenced in this particular plan's commands, but relevant if running any of Task 1–6's verification steps on the real server rather than locally.
>
> Fix all eight before running any task below — #2 is the most serious, since it would lock the real Architect out of the one tool this whole phase exists to build.

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the `broadcast` Django app with `ChannelConfig` and `ChannelSlot` configuration models, the `GET /api/broadcast/now/` now-playing endpoint with four-level fallback resolution, and the channel scheduler UI at `app.ichebo.org` (Architect only, Level 5).

**Architecture:** New `broadcast` Django app — configuration models, not content models (ADR-003 does not apply). `ChannelConfig` is one row per tenant (OneToOneField). `ChannelSlot` holds programme grid entries. The now-playing endpoint resolves the four-level fallback hierarchy in a single view with four ORM queries. No background process, no Celery, no new infrastructure. Channel scheduler UI lives in the existing Apostolic Command Shell at `app.ichebo.org`.

**Tech Stack:** Django 4.2, DRF (for the now-playing API endpoint), HTMX (for the scheduler UI), existing `broadcast`, `video_live`, `tenants` models.

**Reference:** DOC J Parts 4 and 8 — authoritative spec. `2026-06-25-ichebo-sceptre-system-design_doc-j_v1_0.md`.

**Branch:** `v3-h7-ichebo-channel` (cut from `main` after H.5 merges)

**Commit on completion:** `feat(broadcast): H.7 — ChannelConfig, ChannelSlot, now-playing endpoint, channel scheduler UI`

---

## Pre-Flight Checks

```bash
git checkout main && git pull
git log --oneline main | grep "H.5"
git checkout -b v3-h7-ichebo-channel
source venv/bin/activate
python manage.py check
```

---

## Task 1 — Create broadcast Django app with ChannelConfig and ChannelSlot models

**Files:**
- Run: `python manage.py startapp broadcast`
- Modify: `broadcast/models.py`
- Modify: `ics_project/settings/base.py` — add `'broadcast'` to `INSTALLED_APPS`
- Create migration

**Step 1: Create the app**

```bash
python manage.py startapp broadcast
```

**Step 2: Write broadcast/models.py**

```python
# broadcast/models.py
import uuid
from django.conf import settings
from django.db import models


CONTENT_TYPE_CHOICES = [
    ('vod', 'Video on Demand'),
    ('live', 'Live Broadcast'),
]


class ChannelConfig(models.Model):
    """
    Per-tenant channel configuration.
    One row per Sceptre Community tenant.
    Holds the fallback hierarchy configuration for the Ichebo Channel.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='channel_config',
    )
    loop_default_video_id = models.UUIDField(null=True, blank=True)
    # UUID of VideoRecord — resolved at read time via video_live or media apps
    fallback_playlist = models.JSONField(default=list)
    # Ordered list of VideoRecord UUIDs (strings)
    fallback_position = models.IntegerField(default=0)
    # Current index in fallback_playlist — advances on each rotation
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='channel_configs_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Channel Configuration'
        verbose_name_plural = 'Channel Configurations'

    def __str__(self):
        return f'ChannelConfig for {self.tenant}'


class ChannelSlot(models.Model):
    """
    Programme grid entry — a scheduled piece of content on the Ichebo Channel.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='channel_slots',
    )
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)
    video_record_id = models.UUIDField(null=True, blank=True)
    # UUID of VideoRecord for content_type='vod'
    broadcast_schedule_id = models.UUIDField(null=True, blank=True)
    # UUID of BroadcastSchedule for content_type='live'
    title = models.CharField(max_length=255)
    # Denormalised — avoids a join on every now-playing call
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=255, null=True, blank=True)
    # RRULE string — nullable in v1
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='channel_slots_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['scheduled_start']
        indexes = [
            models.Index(fields=['tenant', 'scheduled_start', 'scheduled_end']),
        ]

    def __str__(self):
        return f'{self.title} ({self.scheduled_start:%Y-%m-%d %H:%M})'
```

**Step 3: Register app in settings**

In `ics_project/settings/base.py`, find `INSTALLED_APPS` and add:

```python
'broadcast',
```

**Step 4: Create broadcast/apps.py**

```python
# broadcast/apps.py
from django.apps import AppConfig


class BroadcastConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'broadcast'
    verbose_name = 'Broadcast Channel'
```

**Step 5: Generate and apply migration**

```bash
python manage.py makemigrations broadcast --name initial_channel_config_and_slot
python manage.py migrate
```

**Step 6: Verify**

```bash
python manage.py shell -c "
from broadcast.models import ChannelConfig, ChannelSlot
print(f'ChannelConfig table exists: {ChannelConfig.objects.count()} rows')
print(f'ChannelSlot table exists: {ChannelSlot.objects.count()} rows')
print('OK')
"
```

**Step 7: Commit**

```bash
git add broadcast/ ics_project/settings/base.py
git commit -m "feat(broadcast): create broadcast app with ChannelConfig and ChannelSlot models"
```

---

## Task 2 — Build the now-playing resolution logic

**Files:**
- Create: `broadcast/services.py`

**Context:** Pure Python — no DRF, no HTTP at this layer. Takes a `Tenant` instance, returns a dict. Four-level fallback hierarchy per DOC J §4.3.

**Step 1: Create broadcast/services.py**

```python
# broadcast/services.py
"""
Ichebo Channel — now-playing resolution service.
Implements the four-level fallback hierarchy (DOC J §4.3, ADR-023).

Resolution order:
  1. ChannelSlot with scheduled_start <= now <= scheduled_end
  2. BroadcastSchedule with status='live' in the tenant
  3. ChannelConfig.fallback_playlist rotation
  4. ChannelConfig.loop_default_video_id
  5. Offline — no content configured
"""
from django.utils import timezone


def resolve_now_playing(tenant):
    """
    Resolve what the Ichebo Channel should be playing right now for `tenant`.

    Returns a dict matching the GET /api/broadcast/now/ response schema.
    Never raises — returns offline state on any resolution failure.
    """
    now = timezone.now()

    # ── Level 1: Scheduled ChannelSlot ───────────────────────────────────
    try:
        from broadcast.models import ChannelSlot
        slot = ChannelSlot.objects.filter(
            tenant=tenant,
            scheduled_start__lte=now,
            scheduled_end__gte=now,
            deleted_at__isnull=True,
        ).first()
        if slot:
            return _build_slot_response(slot, now)
    except Exception:
        pass

    # ── Level 2: Live BroadcastSchedule override ──────────────────────────
    try:
        from video_live.models import BroadcastSchedule
        live = BroadcastSchedule.objects.filter(
            tenant=tenant,
            status='live',
            deleted_at__isnull=True,
        ).first()
        if live:
            return _build_live_response(live)
    except Exception:
        pass

    # ── Level 3: Fallback playlist rotation ───────────────────────────────
    try:
        from broadcast.models import ChannelConfig
        config = ChannelConfig.objects.filter(
            tenant=tenant,
            deleted_at__isnull=True,
        ).first()
        if config and config.fallback_playlist:
            pos = config.fallback_position % len(config.fallback_playlist)
            video_id = config.fallback_playlist[pos]
            # Advance position atomically
            ChannelConfig.objects.filter(pk=config.pk).update(
                fallback_position=config.fallback_position + 1
            )
            return _build_vod_response(video_id, source='fallback')
    except Exception:
        pass

    # ── Level 4: Loop default ─────────────────────────────────────────────
    try:
        if config and config.loop_default_video_id:
            return _build_vod_response(str(config.loop_default_video_id), source='loop')
    except Exception:
        pass

    # ── Level 5: Offline ──────────────────────────────────────────────────
    return _offline_response()


def _build_slot_response(slot, now):
    return {
        'content_type': 'vod' if slot.content_type == 'vod' else 'live',
        'source': 'scheduled',
        'title': slot.title,
        'video_url': _resolve_video_url(slot),
        'hls_url': None,
        'is_live': slot.content_type == 'live',
        'thumbnail_url': None,
        'ends_at': slot.scheduled_end.isoformat(),
        'next_scheduled': _get_next_slot(slot.tenant, slot.scheduled_end),
    }


def _build_live_response(broadcast):
    return {
        'content_type': 'live',
        'source': 'live',
        'title': broadcast.title,
        'video_url': broadcast.viewer_hls_url or broadcast.hls_url or '',
        'hls_url': broadcast.viewer_hls_url or broadcast.hls_url or '',
        'is_live': True,
        'thumbnail_url': None,
        'ends_at': None,
        'next_scheduled': None,
    }


def _build_vod_response(video_id, source):
    return {
        'content_type': 'vod',
        'source': source,
        'title': None,
        'video_url': '',   # resolved by Flutter/web from video_id
        'hls_url': None,
        'is_live': False,
        'thumbnail_url': None,
        'ends_at': None,
        'next_scheduled': None,
        '_video_id': video_id,  # included so client can fetch full video details
    }


def _offline_response():
    return {
        'content_type': 'offline',
        'source': 'offline',
        'title': None,
        'video_url': None,
        'hls_url': None,
        'is_live': False,
        'thumbnail_url': None,
        'ends_at': None,
        'next_scheduled': None,
    }


def _resolve_video_url(slot):
    """Attempt to resolve a direct video URL from a ChannelSlot."""
    # If the slot has a broadcast_schedule_id, try BroadcastSchedule
    if slot.broadcast_schedule_id:
        try:
            from video_live.models import BroadcastSchedule
            bs = BroadcastSchedule.objects.get(id=slot.broadcast_schedule_id)
            return bs.viewer_hls_url or bs.hls_url or ''
        except Exception:
            pass
    return ''


def _get_next_slot(tenant, after):
    """Return a brief dict for the next scheduled slot after `after`."""
    from broadcast.models import ChannelSlot
    next_slot = ChannelSlot.objects.filter(
        tenant=tenant,
        scheduled_start__gt=after,
        deleted_at__isnull=True,
    ).order_by('scheduled_start').first()
    if next_slot:
        return {
            'title': next_slot.title,
            'starts_at': next_slot.scheduled_start.isoformat(),
        }
    return None
```

**Step 2: Verify**

```bash
python manage.py shell -c "
from broadcast.services import resolve_now_playing
from tenants.models import Tenant
t = Tenant.objects.first()
if t:
    result = resolve_now_playing(t)
    print(f'OK — resolved: {result[\"content_type\"]}')
else:
    print('OK — no tenants, import works')
"
```

**Step 3: Commit**

```bash
git add broadcast/services.py
git commit -m "feat(broadcast): now-playing resolution service with four-level fallback"
```

---

## Task 3 — Build the now-playing API endpoint

**Files:**
- Create: `broadcast/api_views.py`
- Create: `broadcast/urls.py`
- Modify: `ics_project/urls.py` — include broadcast URLs

**Step 1: Create broadcast/api_views.py**

```python
# broadcast/api_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from tenants.models import Tenant
from broadcast.services import resolve_now_playing


class NowPlayingView(APIView):
    """
    GET /api/broadcast/now/?tenant_id={uuid}

    Returns the current channel content for the given tenant.
    Called by Flutter mobile (every 60s) and sceptre.ichebo.org HTMX (every 60s).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.query_params.get('tenant_id')

        if not tenant_id:
            return Response(
                {'error': 'tenant_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return Response(
                {'error': 'Tenant not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        result = resolve_now_playing(tenant)
        return Response(result, status=status.HTTP_200_OK)
```

**Step 2: Create broadcast/urls.py**

```python
# broadcast/urls.py
from django.urls import path
from broadcast import api_views

urlpatterns = [
    path('now/', api_views.NowPlayingView.as_view(), name='broadcast-now-playing'),
]
```

**Step 3: Include in main urls.py**

Find `ics_project/urls.py` and add:

```python
path('api/broadcast/', include('broadcast.urls')),
```

**Step 4: Verify**

```bash
python manage.py check
python manage.py shell -c "
from django.urls import reverse
url = reverse('broadcast-now-playing')
print(f'OK — URL: {url}')
"
```

**Step 5: Commit**

```bash
git add broadcast/api_views.py broadcast/urls.py ics_project/urls.py
git commit -m "feat(broadcast): GET /api/broadcast/now/ now-playing API endpoint"
```

---

## Task 4 — Build channel scheduler UI at app.ichebo.org (Architect only)

**Files:**
- Create: `broadcast/views.py`
- Create: `broadcast/channel_urls.py`
- Modify: `agency_urls.py` (or the main `urls.py` for `app.ichebo.org`) — include channel URLs
- Create: `templates/broadcast/channel_overview.html`
- Create: `templates/broadcast/channel_slot_form.html`
- Create: `templates/broadcast/channel_config_form.html`

**Step 1: Read how existing Architect-level views are gated**

```bash
grep -n "competence_level.*5\|is_prime\|_require_level.*5" community/views.py governance/views.py | head -10
```

Match the exact gating pattern used for Level 5 / Architect views.

**Step 2: Create broadcast/views.py**

```python
# broadcast/views.py
import uuid
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from broadcast.models import ChannelConfig, ChannelSlot
from tenants.models import Tenant


def _require_architect(user):
    """Gate: only Level 5 (Architect/Prime) may access channel scheduler."""
    if getattr(user, 'competence_level', 0) != 5:   # real IntegerField — compare to an int
        raise PermissionDenied


@login_required
def channel_overview(request):
    """Channel scheduler — overview of all tenants with ChannelConfig."""
    _require_architect(request.user)

    tenant_id = request.GET.get('tenant_id')
    tenants = Tenant.objects.filter(deleted_at__isnull=True).order_by('name')
    selected_tenant = None
    slots = []
    config = None

    if tenant_id:
        selected_tenant = get_object_or_404(Tenant, id=tenant_id)
        slots = ChannelSlot.objects.filter(
            tenant=selected_tenant,
            deleted_at__isnull=True,
        ).order_by('scheduled_start')
        config = ChannelConfig.objects.filter(
            tenant=selected_tenant,
            deleted_at__isnull=True,
        ).first()

    return render(request, 'broadcast/channel_overview.html', {
        'tenants': tenants,
        'selected_tenant': selected_tenant,
        'slots': slots,
        'config': config,
        'now': timezone.now(),
    })


@login_required
def channel_slot_add(request):
    """Add a ChannelSlot for a tenant."""
    _require_architect(request.user)

    tenants = Tenant.objects.filter(deleted_at__isnull=True).order_by('name')

    if request.method == 'POST':
        tenant_id = request.POST.get('tenant_id')
        title = request.POST.get('title', '').strip()
        content_type = request.POST.get('content_type', 'vod')
        scheduled_start = request.POST.get('scheduled_start')
        scheduled_end = request.POST.get('scheduled_end')

        errors = []
        if not title:
            errors.append('Title is required.')
        if not scheduled_start or not scheduled_end:
            errors.append('Start and end times are required.')
        if not tenant_id:
            errors.append('Tenant is required.')

        if not errors:
            from django.utils.dateparse import parse_datetime
            tenant = get_object_or_404(Tenant, id=tenant_id)
            ChannelSlot.objects.create(
                id=uuid.uuid4(),
                tenant=tenant,
                title=title,
                content_type=content_type,
                scheduled_start=parse_datetime(scheduled_start),
                scheduled_end=parse_datetime(scheduled_end),
                created_by=request.user,
            )
            return redirect(f'/channel/?tenant_id={tenant_id}')

        return render(request, 'broadcast/channel_slot_form.html', {
            'tenants': tenants,
            'errors': errors,
            'data': request.POST,
        })

    return render(request, 'broadcast/channel_slot_form.html', {
        'tenants': tenants,
        'errors': [],
        'data': {},
    })


@login_required
def channel_slot_delete(request, slot_id):
    """Soft-delete a ChannelSlot."""
    _require_architect(request.user)
    slot = get_object_or_404(ChannelSlot, id=slot_id)
    tenant_id = slot.tenant_id
    if request.method == 'POST':
        slot.deleted_at = timezone.now()
        slot.save()
    return redirect(f'/channel/?tenant_id={tenant_id}')


@login_required
def channel_config_edit(request, tenant_id):
    """Edit ChannelConfig (fallback playlist + loop default) for a tenant."""
    _require_architect(request.user)
    tenant = get_object_or_404(Tenant, id=tenant_id)
    config, _ = ChannelConfig.objects.get_or_create(
        tenant=tenant,
        defaults={'id': uuid.uuid4(), 'created_by': request.user},
    )

    if request.method == 'POST':
        loop_default = request.POST.get('loop_default_video_id', '').strip()
        fallback_raw = request.POST.get('fallback_playlist', '').strip()

        # Parse fallback playlist — one UUID per line
        fallback_list = [
            line.strip() for line in fallback_raw.splitlines()
            if line.strip()
        ]

        config.loop_default_video_id = uuid.UUID(loop_default) if loop_default else None
        config.fallback_playlist = fallback_list
        config.save()
        return redirect(f'/channel/?tenant_id={tenant_id}')

    return render(request, 'broadcast/channel_config_form.html', {
        'tenant': tenant,
        'config': config,
        'fallback_playlist_text': '\n'.join(config.fallback_playlist),
    })
```

**Step 3: Create broadcast/channel_urls.py**

```python
# broadcast/channel_urls.py
from django.urls import path
from broadcast import views

urlpatterns = [
    path('', views.channel_overview, name='channel_overview'),
    path('slots/add/', views.channel_slot_add, name='channel_slot_add'),
    path('slots/<uuid:slot_id>/delete/', views.channel_slot_delete, name='channel_slot_delete'),
    path('config/<uuid:tenant_id>/', views.channel_config_edit, name='channel_config_edit'),
]
```

**Step 4: Include channel URLs in agency URL conf**

Find the URL conf for `app.ichebo.org` (likely `agency_urls.py` or the main `urls.py`) and add:

```python
path('channel/', include('broadcast.channel_urls')),
```

**Step 5: Create templates**

```html
<!-- templates/broadcast/channel_overview.html -->
{% extends "base.html" %}
{% block title %}Channel Scheduler{% endblock %}
{% block content %}
<div class="page-container">
  <div class="page-header">
    <span class="label-tag">&mdash;&mdash; ARCHITECT</span>
    <h1 class="page-title">Channel Scheduler</h1>
  </div>

  <div class="tenant-selector">
    <form method="get">
      <label for="id_tenant" class="field-label">Select Community</label>
      <select name="tenant_id" id="id_tenant" onchange="this.form.submit()" class="field-input">
        <option value="">-- Select --</option>
        {% for t in tenants %}
          <option value="{{ t.id }}" {% if t == selected_tenant %}selected{% endif %}>
            {{ t.name }}
          </option>
        {% endfor %}
      </select>
    </form>
  </div>

  {% if selected_tenant %}
    <div class="channel-actions">
      <a href="{% url 'channel_slot_add' %}?tenant_id={{ selected_tenant.id }}" class="btn btn-primary">
        + Add Slot
      </a>
      <a href="{% url 'channel_config_edit' selected_tenant.id %}" class="btn btn-secondary">
        Edit Fallback Config
      </a>
    </div>

    {% if config %}
      <div class="config-summary">
        <span class="label-tag">&mdash;&mdash; FALLBACK CONFIG</span>
        <p>Loop default: {{ config.loop_default_video_id|default:"Not set" }}</p>
        <p>Fallback playlist: {{ config.fallback_playlist|length }} item(s)</p>
      </div>
    {% endif %}

    <div class="slot-list">
      <span class="label-tag">&mdash;&mdash; PROGRAMME GRID</span>
      {% if not slots %}
        <p class="empty-state-inline">No slots scheduled.</p>
      {% else %}
        {% for slot in slots %}
          <div class="slot-item {% if slot.scheduled_end < now %}slot-item--past{% endif %}">
            <div class="slot-item__time">
              {{ slot.scheduled_start|date:"d M Y H:i" }} &rarr;
              {{ slot.scheduled_end|date:"H:i" }}
            </div>
            <div class="slot-item__title">{{ slot.title }}</div>
            <div class="slot-item__type">{{ slot.get_content_type_display }}</div>
            <form method="post"
                  action="{% url 'channel_slot_delete' slot.id %}"
                  style="display:inline">
              {% csrf_token %}
              <button type="submit" class="btn btn-sm btn-danger"
                      onclick="return confirm('Delete this slot?')">
                Delete
              </button>
            </form>
          </div>
        {% endfor %}
      {% endif %}
    </div>
  {% endif %}
</div>
{% endblock %}
```

```html
<!-- templates/broadcast/channel_slot_form.html -->
{% extends "base.html" %}
{% block title %}Add Channel Slot{% endblock %}
{% block content %}
<div class="page-container">
  <div class="page-header">
    <span class="label-tag">&mdash;&mdash; CHANNEL SCHEDULER</span>
    <h1 class="page-title">Add Slot</h1>
  </div>

  {% for error in errors %}
    <div class="form-error">{{ error }}</div>
  {% endfor %}

  <form method="post">
    {% csrf_token %}
    <div class="field-group">
      <label for="id_tenant" class="field-label">Community</label>
      <select name="tenant_id" id="id_tenant" class="field-input" required>
        {% for t in tenants %}
          <option value="{{ t.id }}" {% if data.tenant_id == t.id|stringformat:"s" %}selected{% endif %}>
            {{ t.name }}
          </option>
        {% endfor %}
      </select>
    </div>
    <div class="field-group">
      <label for="id_title" class="field-label">Title</label>
      <input type="text" id="id_title" name="title"
             value="{{ data.title }}" required class="field-input">
    </div>
    <div class="field-group">
      <label for="id_content_type" class="field-label">Content Type</label>
      <select name="content_type" id="id_content_type" class="field-input">
        <option value="vod">Video on Demand</option>
        <option value="live">Live Broadcast</option>
      </select>
    </div>
    <div class="field-group">
      <label for="id_start" class="field-label">Start</label>
      <input type="datetime-local" id="id_start" name="scheduled_start"
             value="{{ data.scheduled_start }}" required class="field-input">
    </div>
    <div class="field-group">
      <label for="id_end" class="field-label">End</label>
      <input type="datetime-local" id="id_end" name="scheduled_end"
             value="{{ data.scheduled_end }}" required class="field-input">
    </div>
    <div class="form-actions">
      <button type="submit" class="btn btn-primary">Add Slot</button>
      <a href="{% url 'channel_overview' %}" class="btn btn-secondary">Cancel</a>
    </div>
  </form>
</div>
{% endblock %}
```

```html
<!-- templates/broadcast/channel_config_form.html -->
{% extends "base.html" %}
{% block title %}Fallback Config — {{ tenant.name }}{% endblock %}
{% block content %}
<div class="page-container">
  <div class="page-header">
    <span class="label-tag">&mdash;&mdash; CHANNEL SCHEDULER</span>
    <h1 class="page-title">Fallback Configuration — {{ tenant.name }}</h1>
  </div>

  <form method="post">
    {% csrf_token %}
    <div class="field-group">
      <label for="id_loop" class="field-label">Loop Default Video ID</label>
      <input type="text" id="id_loop" name="loop_default_video_id"
             value="{{ config.loop_default_video_id|default:'' }}"
             placeholder="UUID of the video to loop when nothing else is playing"
             class="field-input">
    </div>
    <div class="field-group">
      <label for="id_fallback" class="field-label">Fallback Playlist (one UUID per line)</label>
      <textarea id="id_fallback" name="fallback_playlist"
                rows="8"
                placeholder="Paste one VideoRecord UUID per line"
                class="field-input">{{ fallback_playlist_text }}</textarea>
    </div>
    <div class="form-actions">
      <button type="submit" class="btn btn-primary">Save Config</button>
      <a href="{% url 'channel_overview' %}?tenant_id={{ tenant.id }}" class="btn btn-secondary">
        Cancel
      </a>
    </div>
  </form>
</div>
{% endblock %}
```

**Step 6: Verify URLs**

```bash
python manage.py check
python manage.py shell -c "
from django.urls import reverse
print(reverse('channel_overview'))
print(reverse('channel_slot_add'))
print(reverse('channel_config_edit', args=['00000000-0000-0000-0000-000000000000']))
print('OK')
"
```

**Step 7: Commit**

```bash
git add broadcast/views.py broadcast/channel_urls.py \
  templates/broadcast/
git commit -m "feat(broadcast): channel scheduler UI — overview, add slot, fallback config (Level 5 only)"
```

---

## Task 5 — Write tests

**Files:**
- Create: `broadcast/tests/test_now_playing.py`

```python
# broadcast/tests/test_now_playing.py
"""
Tests for Phase H.7 — Ichebo Channel.
Covers: now-playing resolution (all five fallback levels),
API endpoint authentication and response shape,
scheduler UI access control.
"""
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from broadcast.models import ChannelConfig, ChannelSlot
from broadcast.services import resolve_now_playing
from tenants.models import Tenant

User = get_user_model()


def make_tenant(name='Channel Tenant', slug='channel-test'):
    # Tenant requires slug (unique), path (the real field — tenant_path
    # lives on UserPermission, not Tenant), tier, and created_by.
    admin = User.objects.create_user(
        username='_test_admin_h7', email='_test_admin_h7@test.com',
    )
    return Tenant.objects.create(
        name=name, slug=slug, path=f'/global/{slug}/',
        tier='church_node', created_by=admin,
    )


def make_user(username, level=1):
    user = User.objects.create_user(
        username=username, password='testpass123',
        email=f'{username}@test.com',
    )
    user.competence_level = level   # real IntegerField — pass an int
    user.save()
    return user


class TestNowPlayingResolution(TestCase):
    """resolve_now_playing — all five fallback levels."""

    def setUp(self):
        self.tenant = make_tenant()
        self.now = timezone.now()

    def test_level5_offline_when_nothing_configured(self):
        result = resolve_now_playing(self.tenant)
        self.assertEqual(result['content_type'], 'offline')
        self.assertEqual(result['source'], 'offline')
        self.assertIsNone(result['video_url'])

    def test_level4_loop_default(self):
        video_id = uuid.uuid4()
        ChannelConfig.objects.create(
            id=uuid.uuid4(),
            tenant=self.tenant,
            loop_default_video_id=video_id,
            fallback_playlist=[],
        )
        result = resolve_now_playing(self.tenant)
        self.assertEqual(result['content_type'], 'vod')
        self.assertEqual(result['source'], 'loop')
        self.assertEqual(result['_video_id'], str(video_id))

    def test_level3_fallback_playlist_rotation(self):
        v1 = str(uuid.uuid4())
        v2 = str(uuid.uuid4())
        config = ChannelConfig.objects.create(
            id=uuid.uuid4(),
            tenant=self.tenant,
            fallback_playlist=[v1, v2],
            fallback_position=0,
        )
        result1 = resolve_now_playing(self.tenant)
        self.assertEqual(result1['source'], 'fallback')
        self.assertEqual(result1['_video_id'], v1)

        config.refresh_from_db()
        self.assertEqual(config.fallback_position, 1)

        result2 = resolve_now_playing(self.tenant)
        self.assertEqual(result2['_video_id'], v2)

    def test_level1_scheduled_slot_takes_priority(self):
        # Configure fallback (lower priority)
        ChannelConfig.objects.create(
            id=uuid.uuid4(),
            tenant=self.tenant,
            loop_default_video_id=uuid.uuid4(),
        )
        # Add a currently-active slot (higher priority)
        ChannelSlot.objects.create(
            id=uuid.uuid4(),
            tenant=self.tenant,
            title='Sunday Teaching',
            content_type='vod',
            scheduled_start=self.now - timedelta(minutes=30),
            scheduled_end=self.now + timedelta(minutes=30),
        )
        result = resolve_now_playing(self.tenant)
        self.assertEqual(result['source'], 'scheduled')
        self.assertEqual(result['title'], 'Sunday Teaching')

    def test_past_slot_does_not_resolve(self):
        ChannelSlot.objects.create(
            id=uuid.uuid4(),
            tenant=self.tenant,
            title='Past Slot',
            content_type='vod',
            scheduled_start=self.now - timedelta(hours=2),
            scheduled_end=self.now - timedelta(hours=1),
        )
        result = resolve_now_playing(self.tenant)
        self.assertEqual(result['content_type'], 'offline')

    def test_future_slot_does_not_resolve(self):
        ChannelSlot.objects.create(
            id=uuid.uuid4(),
            tenant=self.tenant,
            title='Future Slot',
            content_type='vod',
            scheduled_start=self.now + timedelta(hours=1),
            scheduled_end=self.now + timedelta(hours=2),
        )
        result = resolve_now_playing(self.tenant)
        self.assertEqual(result['content_type'], 'offline')


class TestNowPlayingAPIEndpoint(TestCase):
    """GET /api/broadcast/now/ — authentication, response shape, tenant scoping."""

    def setUp(self):
        self.tenant = make_tenant(name='API Channel', slug='apichannel')
        self.user = make_user('api_user')
        self.client = Client()

    def test_requires_authentication(self):
        url = reverse('broadcast-now-playing')
        response = self.client.get(url + f'?tenant_id={self.tenant.id}')
        self.assertEqual(response.status_code, 401)

    def test_missing_tenant_id_returns_400(self):
        self.client.login(username='api_user', password='testpass123')
        url = reverse('broadcast-now-playing')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_invalid_tenant_id_returns_404(self):
        self.client.login(username='api_user', password='testpass123')
        url = reverse('broadcast-now-playing')
        response = self.client.get(url + f'?tenant_id={uuid.uuid4()}')
        self.assertEqual(response.status_code, 404)

    def test_valid_request_returns_200_with_schema(self):
        self.client.login(username='api_user', password='testpass123')
        url = reverse('broadcast-now-playing')
        response = self.client.get(url + f'?tenant_id={self.tenant.id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # All required schema fields present
        for field in ['content_type', 'source', 'title', 'video_url', 'is_live']:
            self.assertIn(field, data, f'Missing field: {field}')
        self.assertEqual(data['content_type'], 'offline')


class TestChannelSchedulerAccessControl(TestCase):
    """Channel scheduler UI — only accessible to Level 5."""

    def setUp(self):
        self.tenant = make_tenant(name='Sched Tenant', slug='sched')
        self.architect = make_user('architect_h7', level=5)
        self.member = make_user('member_h7', level=1)
        self.client = Client()

    def test_architect_can_access_overview(self):
        self.client.login(username='architect_h7', password='testpass123')
        response = self.client.get(reverse('channel_overview'))
        self.assertEqual(response.status_code, 200)

    def test_member_cannot_access_overview(self):
        self.client.login(username='member_h7', password='testpass123')
        response = self.client.get(reverse('channel_overview'))
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_redirected(self):
        response = self.client.get(reverse('channel_overview'))
        self.assertEqual(response.status_code, 302)
```

**Run tests:**

```bash
python manage.py test broadcast.tests.test_now_playing -v 2
python manage.py test --verbosity=1 2>&1 | tail -5
```

**Commit:**

```bash
git add broadcast/tests/
git commit -m "test(broadcast): H.7 now-playing resolution, API endpoint, scheduler access control"
```

---

## Task 6 — Final verification and merge

```bash
python manage.py check
python manage.py showmigrations | grep "\[ \]"

git log --oneline main..HEAD
# 6 commits expected

git checkout main
git merge --no-ff v3-h7-ichebo-channel \
  -m "feat(broadcast): H.7 — ChannelConfig, ChannelSlot, now-playing endpoint, channel scheduler UI"
git push origin main
```

---

## Exit Criteria

- [ ] `broadcast` app created with `ChannelConfig` and `ChannelSlot` models
- [ ] Migrations run cleanly against production schema
- [ ] `GET /api/broadcast/now/?tenant_id={uuid}` returns correct content for each fallback level
- [ ] Level 1: active `ChannelSlot` resolves to `source='scheduled'`
- [ ] Level 2: live `BroadcastSchedule` resolves to `source='live'`
- [ ] Level 3: fallback playlist rotates — `fallback_position` advances on each call
- [ ] Level 4: loop default resolves to `source='loop'`
- [ ] Level 5: offline state returns `content_type='offline'`
- [ ] Channel scheduler accessible only to Level 5 — Level 1–4 get 403
- [ ] `python manage.py check` — 0 issues
- [ ] All 10 tests pass
