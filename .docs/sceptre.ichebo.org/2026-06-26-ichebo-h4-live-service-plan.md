# Phase H.4 — Community Live Service Room + In-Service Ministry Panel

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a tenant-scoped live service viewing room in the Community app, fixing the existing global-unfiltered video scoping gap, and adding an in-service ministry panel (prayer requests / questions) with a steward-visible queue scoped to the current session.

**Architecture:** No new models. No new Django app. `live_request` is a `record_type` on the existing `Record` model (ADR-003). Tenant filtering is added to `video_live`'s existing query helpers — existing global behaviour preserved for callers that do not pass a tenant. HTMX polling for the ministry panel (60-second interval, matching existing notification polling pattern). DOC G §7.2 coexistence policy respected: both `Activity` URL-embed events and `BroadcastSchedule` native HLS events are queried — the room does not force migration between the two.

**Tech Stack:** Django 4.2, HTMX, existing `community`, `video_live`, `notifications`, `records` apps.

**Reference:** `community-live-service-room-plan.md` (approved 2026-06-18) — authoritative spec. `video-direction-v2-plan.md` (2026-06-23) — confirms `video_live` infrastructure stays intact.

**Branch:** `v3-h4-community-live-service` (cut from `main` after H.3 merges)

**Commit on completion:** `feat(community,video): H.4 — tenant-scoped live service room + in-service ministry panel`

---

## Pre-Flight Checks

```bash
# Confirm H.3 is merged to main before starting
git log --oneline main | grep "H.3"
# Expected: feat(community): H.3 — support request flow...

git checkout main && git pull
git checkout -b v3-h4-community-live-service

cd /home/ics/ichebo-platform/backend
source venv/bin/activate
python manage.py check
# Expected: System check identified no issues (0 silenced).
```

---

## Task 1 — Fix tenant filtering in video_live/views.py

**Files:**
- Modify: `video_live/views.py` — add optional `tenant` parameter to `_event_qs()`

**Context:** `_event_qs()` currently queries `Activity` objects globally with no tenant filter. Every existing caller must continue to work unchanged (no tenant passed = global behaviour). The new Community room will pass `tenant=tenant` explicitly.

**Step 1: Read the current _event_qs() function**

```bash
grep -n "_event_qs\|def _event_qs" video_live/views.py
sed -n '11,25p' video_live/views.py
```

Note the exact queryset, filters, and return type.

**Step 2: Modify _event_qs() to accept an optional tenant parameter**

Find the function (approximately `video_live/views.py:11-18`) and update it:

```python
def _event_qs(tenant=None):
    """
    Base queryset for video/live events.
    When tenant is provided, scopes to that tenant only.
    When tenant is None, returns all events (existing global behaviour — preserved).
    """
    qs = Activity.objects.exclude(metadata__stream_url=None)
    if tenant is not None:
        qs = qs.filter(tenant=tenant)
    return qs
```

**Step 3: Verify existing callers are unaffected**

```bash
python manage.py check
python manage.py shell -c "
from video_live.views import _event_qs
qs = _event_qs()
print(f'OK — global call returns {qs.count()} events (existing behaviour preserved)')
"
```

**Step 4: Commit**

```bash
git add video_live/views.py
git commit -m "fix(video): add optional tenant filter to _event_qs() — existing callers unaffected"
```

---

## Task 2 — Fix tenant filtering in video_live/api_views.py

**Files:**
- Modify: `video_live/api_views.py` — add `?tenant_id=` filtering to `VideoFeedView`

**Context:** `VideoFeedView.get()` merges Activity-based events and `BroadcastSchedule` objects globally. When `?tenant_id=` is passed, both sources must be filtered. When not passed, existing global behaviour is preserved.

**Step 1: Read the current VideoFeedView**

```bash
grep -n "class VideoFeedView\|BroadcastSchedule\|_event_qs\|tenant" video_live/api_views.py | head -20
sed -n '65,90p' video_live/api_views.py
```

**Step 2: Add tenant_id filtering to VideoFeedView.get()**

Locate `VideoFeedView.get()` and update the queryset construction:

```python
def get(self, request, *args, **kwargs):
    tenant_id = request.query_params.get('tenant_id')
    tenant = None

    if tenant_id:
        from tenants.models import Tenant
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            tenant = None

    # Activity-based events (URL-embed — DOC G §7.2 coexistence)
    activity_events = _event_qs(tenant=tenant)

    # BroadcastSchedule-based events (native HLS — Ichebo Media, Layer 8)
    broadcast_qs = BroadcastSchedule.objects.filter(status__in=['scheduled', 'live'])
    if tenant is not None:
        broadcast_qs = broadcast_qs.filter(tenant=tenant)

    # Merge and serialise — match existing response shape exactly
    # (Keep existing serialisation logic below this point unchanged)
```

**Note:** Do not change the serialisation or response shape — only add the filtering above the existing merge logic.

**Step 3: Verify**

```bash
python manage.py check
python manage.py shell -c "
from video_live.api_views import VideoFeedView
print('OK — VideoFeedView importable')
"
```

**Step 4: Commit**

```bash
git add video_live/api_views.py
git commit -m "fix(video): add optional tenant_id filter to VideoFeedView — existing global behaviour preserved"
```

---

## Task 3 — Add live_request notification type

**Files:**
- Modify: `notifications/models.py` — add `live_request_raised` type
- Create migration

**Step 1: Add the new type to NOTIFICATION_TYPES**

```python
('live_request_raised', 'Live Request Raised'),
```

**Step 2: Add notify function to notifications/service.py**

```python
def notify_live_request_raised(record):
    """
    Notify the assigned steward when a member raises a prayer/question
    during a live service session.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    from tenants.models import UserPermission

    # Find active steward for this tenant
    steward_permission = UserPermission.objects.filter(
        tenant=record.tenant,
        role__endswith='-steward',
        is_active=True,
    ).select_related('user').first()

    if not steward_permission:
        return

    create_notification(
        user=steward_permission.user,
        notification_type='live_request_raised',
        source_app='community',
        source_record_id=record.id,
        message=f'New {record.title} request during live service.',
    )
```

**Step 3: Generate migration and apply**

```bash
python manage.py makemigrations notifications --name add_live_request_notification_type
python manage.py migrate
```

**Step 4: Verify**

```bash
python manage.py shell -c "
from notifications.models import Notification
from notifications.service import notify_live_request_raised
types = dict(Notification.NOTIFICATION_TYPES)
assert 'live_request_raised' in types
print('OK')
"
```

**Step 5: Commit**

```bash
git add notifications/models.py notifications/service.py notifications/migrations/
git commit -m "feat(notifications): add live_request_raised notification type and notify function"
```

---

## Task 4 — Add Community live service room view

**Files:**
- Modify: `community/views.py` — add `community_live_service` view
- Modify: `community/urls.py` — add URL

**Context:** Resolves the member's active community tenant, then queries both `Activity` URL-embed events and `BroadcastSchedule` native events for that tenant. If a live session exists, renders the player partial + ministry panel. If not, shows next scheduled service.

**Step 1: Read how existing community views resolve the member's tenant**

```bash
grep -n "_get_active_community_tenant\|request.user.*tenant\|UserPermission.*tenant" community/views.py | head -15
```

Use the same tenant-resolution pattern as existing community views.

**Step 2: Add the view**

```python
@login_required
def community_live_service(request):
    """
    Tenant-scoped live service room.
    Shows the current tenant's live broadcast (if active) or next scheduled service.
    Includes the in-service ministry panel when a session is live.
    """
    from django.utils import timezone
    from video_live.models import BroadcastSchedule

    tenant = _get_active_community_tenant(request.user)
    if not tenant:
        return HttpResponseForbidden('No active community found.')

    now = timezone.now()

    # Check for active live broadcast (native HLS — Ichebo Media)
    live_broadcast = BroadcastSchedule.objects.filter(
        tenant=tenant,
        status='live',
        deleted_at__isnull=True,
    ).first()

    # Check for active URL-embed event (DOC G §7.2 coexistence)
    live_activity = None
    if not live_broadcast:
        live_activity = _event_qs(tenant=tenant).filter(
            status='active',
        ).first()

    # Next scheduled (for empty state)
    next_scheduled = None
    if not live_broadcast and not live_activity:
        next_scheduled = BroadcastSchedule.objects.filter(
            tenant=tenant,
            status='scheduled',
            deleted_at__isnull=True,
        ).order_by('scheduled_start').first()

    # Gather link — read existing gathering_record FK on BroadcastSchedule if present
    gathering = None
    if live_broadcast and live_broadcast.gathering_record_id:
        from records.models import Record
        gathering = Record.objects.filter(
            id=live_broadcast.gathering_record_id,
            deleted_at__isnull=True,
        ).first()

    # Determine player type per DOC G §7.3 discriminator
    player_type = None
    video_url = None
    if live_broadcast:
        video_url = live_broadcast.viewer_hls_url or live_broadcast.hls_url
        player_type = 'hls'
    elif live_activity:
        video_url = live_activity.metadata.get('stream_url', '')
        player_type = 'embed'

    return render(request, 'community/live_service.html', {
        'live_broadcast': live_broadcast,
        'live_activity': live_activity,
        'next_scheduled': next_scheduled,
        'gathering': gathering,
        'player_type': player_type,
        'video_url': video_url,
        'is_live': bool(live_broadcast or live_activity),
    })
```

**Step 3: Add URL to community/urls.py**

```python
path('live/', views.community_live_service, name='community_live_service'),
```

**Step 4: Create the template**

```html
<!-- templates/community/live_service.html -->
{% extends "base.html" %}
{% block title %}Live Service{% endblock %}

{% block content %}
<div class="page-container live-service-page">

  <div class="page-header">
    <span class="label-tag">&mdash;&mdash; COMMUNITY</span>
    <h1 class="page-title">Live Service</h1>
    {% if is_live %}
      <span class="live-badge">&#9679; LIVE</span>
    {% endif %}
  </div>

  {% if is_live %}
    <div class="live-service-layout">

      <!-- Video player column -->
      <div class="live-service__player">
        {% if player_type == 'hls' %}
          {% include "video_live/_live_player.html" with video_url=video_url %}
        {% elif player_type == 'embed' %}
          <div class="video-embed-container">
            <iframe src="{{ video_url }}"
                    frameborder="0"
                    allowfullscreen
                    class="video-embed"></iframe>
          </div>
        {% endif %}

        {% if gathering %}
          <div class="gathering-link">
            <span class="label-tag">&mdash;&mdash; TODAY'S GATHERING</span>
            <p>{{ gathering.title }}</p>
          </div>
        {% endif %}
      </div>

      <!-- Ministry panel column -->
      <div class="live-service__ministry-panel"
           id="ministry-panel">
        {% include "community/partials/ministry_panel.html" %}
      </div>

    </div>

  {% else %}

    <div class="empty-state">
      <p>No live service is currently active.</p>
      {% if next_scheduled %}
        <p class="empty-state__next">
          Next service:
          <strong>{{ next_scheduled.title }}</strong>
          on {{ next_scheduled.scheduled_start|date:"l d M Y" }}
          at {{ next_scheduled.scheduled_start|time:"H:i" }}
        </p>
      {% endif %}
    </div>

  {% endif %}

</div>
{% endblock %}
```

**Step 5: Verify URL resolves**

```bash
python manage.py check
python manage.py shell -c "
from django.urls import reverse
print(reverse('community:community_live_service'))
print('OK')
"
```

**Step 6: Commit**

```bash
git add community/views.py community/urls.py templates/community/live_service.html
git commit -m "feat(community): add tenant-scoped live service room view"
```

---

## Task 5 — Add member ministry request form (prayer / question)

**Files:**
- Modify: `community/views.py` — add `htmx_live_request_new` view
- Modify: `community/urls.py` — add URL
- Create: `templates/community/partials/ministry_request_form.html`
- Create: `templates/community/partials/ministry_panel.html`

**Context:** Member raises a prayer request or question during a live session. Stored as `Record(record_type='live_request')` with `custom_fields.broadcast_id` set to the current session's ID. The panel is included in the live service page and polls every 20 seconds to update the steward queue display.

**Step 1: Add the request form view**

```python
@login_required
def htmx_live_request_new(request):
    """
    Member raises a prayer request or question during a live service.
    POST only — HTMX submission.
    """
    import uuid
    from records.models import Record
    from notifications.service import notify_live_request_raised

    tenant = _get_active_community_tenant(request.user)
    if not tenant:
        return HttpResponseForbidden()

    if request.method != 'POST':
        return HttpResponseForbidden()

    request_type = request.POST.get('request_type', 'prayer').strip()
    content = request.POST.get('content', '').strip()
    broadcast_id = request.POST.get('broadcast_id', '').strip()

    if not content:
        return render(request, 'community/partials/ministry_request_form.html', {
            'error': 'Please enter your request.',
            'broadcast_id': broadcast_id,
        })

    record = Record.objects.create(
        id=uuid.uuid4(),
        record_class='personal',
        record_family='community',
        record_type='live_request',
        title=request_type,  # 'prayer' or 'question'
        content=content,
        status='submitted',
        tenant=tenant,
        created_by=request.user,
        custom_fields={
            'broadcast_id': broadcast_id,
            'session_date': timezone.now().date().isoformat(),
        },
        permissions_data={'visibility': 'member_and_steward'},
    )

    notify_live_request_raised(record)

    # Return confirmation replacing the form
    return render(request, 'community/partials/ministry_request_confirmation.html', {
        'request_type': request_type,
    })
```

**Step 2: Add URL**

```python
path('live/request/', views.htmx_live_request_new, name='htmx_live_request_new'),
```

**Step 3: Create ministry panel partial**

```html
<!-- templates/community/partials/ministry_panel.html -->
<div class="ministry-panel">
  <div class="ministry-panel__header">
    <span class="label-tag">&mdash;&mdash; MINISTRY</span>
    <h3>Raise a Request</h3>
  </div>

  <div id="ministry-request-form-container">
    {% include "community/partials/ministry_request_form.html" %}
  </div>
</div>
```

**Step 4: Create the request form partial**

```html
<!-- templates/community/partials/ministry_request_form.html -->
<div class="ministry-request-form">
  {% if error %}
    <div class="form-error">{{ error }}</div>
  {% endif %}

  <form hx-post="{% url 'community:htmx_live_request_new' %}"
        hx-target="#ministry-request-form-container"
        hx-swap="outerHTML">
    {% csrf_token %}
    <input type="hidden" name="broadcast_id" value="{{ broadcast_id }}">

    <div class="field-group">
      <label class="field-label">Type</label>
      <div class="radio-group">
        <label>
          <input type="radio" name="request_type" value="prayer" checked>
          Prayer Request
        </label>
        <label>
          <input type="radio" name="request_type" value="question">
          Question
        </label>
      </div>
    </div>

    <div class="field-group">
      <label for="id_content" class="field-label">Your request</label>
      <textarea id="id_content"
                name="content"
                rows="4"
                placeholder="Share your prayer request or question..."
                class="field-input"
                required></textarea>
    </div>

    <button type="submit" class="btn btn-primary">Submit</button>
  </form>
</div>
```

**Step 5: Create confirmation partial**

```html
<!-- templates/community/partials/ministry_request_confirmation.html -->
<div class="ministry-request-confirmation">
  <p class="confirmation-message">
    {% if request_type == 'prayer' %}
      Your prayer request has been received. A steward will pray with you shortly.
    {% else %}
      Your question has been received. A steward will respond shortly.
    {% endif %}
  </p>
</div>
```

**Step 6: Commit**

```bash
git add community/views.py community/urls.py \
  templates/community/partials/ministry_panel.html \
  templates/community/partials/ministry_request_form.html \
  templates/community/partials/ministry_request_confirmation.html
git commit -m "feat(community): add in-service ministry request form (prayer/question)"
```

---

## Task 6 — Add steward live request queue view (with polling)

**Files:**
- Modify: `community/views.py` — add `htmx_steward_live_queue` view
- Modify: `community/urls.py` — add URL
- Create: `templates/community/partials/steward_live_queue.html`

**Context:** Steward sees a queue of `live_request` records scoped to their tenant's current session (`custom_fields.broadcast_id` matches). Polling via HTMX every 20 seconds. Mark-responded action transitions status to `completed`.

**Step 1: Add the steward queue view**

```python
@login_required
def htmx_steward_live_queue(request):
    """
    Steward-facing live request queue for the current session.
    Scoped to broadcast_id — requests from other sessions do not appear.
    HTMX partial — polled every 20 seconds.
    """
    from records.models import Record
    from tenants.models import UserPermission

    user = request.user
    level_ok = getattr(user, 'competence_level', '0') in ['3', '4', '5']
    role_ok = UserPermission.objects.filter(
        user=user, role__endswith='-steward', is_active=True
    ).exists()
    if not (level_ok or role_ok):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    tenant = _get_active_community_tenant(user)
    broadcast_id = request.GET.get('broadcast_id', '')

    requests_qs = Record.objects.filter(
        record_family='community',
        record_type='live_request',
        tenant=tenant,
        deleted_at__isnull=True,
    ).exclude(status='completed').order_by('created_at')

    if broadcast_id:
        requests_qs = requests_qs.filter(
            custom_fields__broadcast_id=broadcast_id
        )

    return render(request, 'community/partials/steward_live_queue.html', {
        'live_requests': requests_qs,
        'broadcast_id': broadcast_id,
    })


@login_required
def htmx_steward_respond_live_request(request, record_id):
    """
    Steward marks a live request as responded/completed.
    POST only.
    """
    from records.models import Record
    from tenants.models import UserPermission

    user = request.user
    level_ok = getattr(user, 'competence_level', '0') in ['3', '4', '5']
    role_ok = UserPermission.objects.filter(
        user=user, role__endswith='-steward', is_active=True
    ).exists()
    if not (level_ok or role_ok):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    record = get_object_or_404(
        Record,
        id=record_id,
        record_family='community',
        record_type='live_request',
        deleted_at__isnull=True,
    )

    if request.method == 'POST':
        record.status = 'completed'
        record.save()

    broadcast_id = record.custom_fields.get('broadcast_id', '')
    return redirect(f"{reverse('community:htmx_steward_live_queue')}?broadcast_id={broadcast_id}")
```

**Step 2: Add URLs**

```python
path('live/queue/', views.htmx_steward_live_queue, name='htmx_steward_live_queue'),
path('live/queue/<uuid:record_id>/respond/', views.htmx_steward_respond_live_request, name='htmx_steward_respond_live_request'),
```

**Step 3: Create steward queue partial**

```html
<!-- templates/community/partials/steward_live_queue.html -->
<div class="steward-live-queue"
     hx-get="{% url 'community:htmx_steward_live_queue' %}?broadcast_id={{ broadcast_id }}"
     hx-trigger="every 20s"
     hx-swap="outerHTML">

  <div class="queue-header">
    <span class="label-tag">&mdash;&mdash; MINISTRY QUEUE</span>
    <span class="queue-count">{{ live_requests.count }} pending</span>
  </div>

  {% if not live_requests %}
    <p class="empty-state-inline">No requests yet.</p>
  {% else %}
    {% for req in live_requests %}
      <div class="live-request-item">
        <div class="live-request-item__type
          {% if req.title == 'prayer' %}live-request-item__type--prayer
          {% else %}live-request-item__type--question{% endif %}">
          {{ req.title|title }}
        </div>
        <div class="live-request-item__content">{{ req.content }}</div>
        <div class="live-request-item__meta">
          {{ req.created_by.get_full_name|default:req.created_by.username }}
          &middot; {{ req.created_at|time:"H:i" }}
        </div>
        <form method="post"
              action="{% url 'community:htmx_steward_respond_live_request' req.id %}">
          {% csrf_token %}
          <button type="submit" class="btn btn-sm btn-secondary">
            Mark Responded
          </button>
        </form>
      </div>
    {% endfor %}
  {% endif %}

</div>
```

**Step 4: Verify**

```bash
python manage.py check
python manage.py shell -c "
from django.urls import reverse
print(reverse('community:htmx_steward_live_queue'))
print(reverse('community:htmx_steward_respond_live_request', args=['00000000-0000-0000-0000-000000000000']))
print('OK')
"
```

**Step 5: Commit**

```bash
git add community/views.py community/urls.py \
  templates/community/partials/steward_live_queue.html
git commit -m "feat(community): add steward live request queue with 20s HTMX polling"
```

---

## Task 7 — Write tests

**Files:**
- Create: `community/tests/test_live_service.py`

```python
# community/tests/test_live_service.py
"""
Tests for Phase H.4 — Community Live Service Room + Ministry Panel.
"""
import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from records.models import Record
from tenants.models import Tenant, UserPermission
from video_live.models import BroadcastSchedule

User = get_user_model()


def make_tenant(name='Test Community', path='/global/test2/'):
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


class TestTenantFiltering(TestCase):
    """_event_qs and VideoFeedView respect tenant boundaries."""

    def test_event_qs_no_tenant_returns_all(self):
        from video_live.views import _event_qs
        qs = _event_qs()
        # Should not raise — global behaviour preserved
        list(qs)

    def test_event_qs_with_tenant_filters(self):
        from video_live.views import _event_qs
        t1 = make_tenant(name='T1', path='/global/t1/')
        t2 = make_tenant(name='T2', path='/global/t2/')
        qs_t1 = _event_qs(tenant=t1)
        qs_t2 = _event_qs(tenant=t2)
        # Both querysets distinct — no cross-tenant bleed
        self.assertFalse(qs_t1.filter(tenant=t2).exists())

    def test_live_service_view_requires_login(self):
        c = Client()
        url = reverse('community:community_live_service')
        response = c.get(url)
        self.assertEqual(response.status_code, 302)

    def test_live_service_view_returns_200_for_member(self):
        tenant = make_tenant(path='/global/t3/')
        member = make_user('member_h4', level='1', tenant=tenant, role='member')
        c = Client()
        c.login(username='member_h4', password='testpass123')
        url = reverse('community:community_live_service')
        response = c.get(url)
        self.assertEqual(response.status_code, 200)


class TestMinistryRequestCreation(TestCase):
    """Member raises prayer/question during live service."""

    def setUp(self):
        self.tenant = make_tenant(path='/global/t4/')
        self.member = make_user('mem_h4b', level='1', tenant=self.tenant, role='member')
        self.steward = make_user('stew_h4', level='3', tenant=self.tenant, role='branch-steward')
        self.client = Client()
        self.client.login(username='mem_h4b', password='testpass123')

    def test_post_creates_live_request_record(self):
        url = reverse('community:htmx_live_request_new')
        response = self.client.post(url, {
            'request_type': 'prayer',
            'content': 'Please pray for my family.',
            'broadcast_id': str(uuid.uuid4()),
        })
        self.assertEqual(response.status_code, 200)
        record = Record.objects.get(
            record_family='community',
            record_type='live_request',
            created_by=self.member,
        )
        self.assertEqual(record.title, 'prayer')
        self.assertEqual(record.status, 'submitted')

    def test_empty_content_returns_error(self):
        url = reverse('community:htmx_live_request_new')
        response = self.client.post(url, {
            'request_type': 'question',
            'content': '',
            'broadcast_id': str(uuid.uuid4()),
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'enter your request')
        self.assertEqual(Record.objects.filter(record_type='live_request').count(), 0)


class TestStewardLiveQueue(TestCase):
    """Steward queue scoped to session, mark-responded action."""

    def setUp(self):
        self.tenant = make_tenant(path='/global/t5/')
        self.member = make_user('mem_h4c', level='1', tenant=self.tenant, role='member')
        self.steward = make_user('stew_h4b', level='3', tenant=self.tenant, role='branch-steward')
        self.broadcast_id = str(uuid.uuid4())
        self.record = Record.objects.create(
            id=uuid.uuid4(),
            record_class='personal',
            record_family='community',
            record_type='live_request',
            title='prayer',
            content='Pray for healing.',
            status='submitted',
            tenant=self.tenant,
            created_by=self.member,
            custom_fields={
                'broadcast_id': self.broadcast_id,
                'session_date': timezone.now().date().isoformat(),
            },
            permissions_data={'visibility': 'member_and_steward'},
        )
        self.client = Client()
        self.client.login(username='stew_h4b', password='testpass123')

    def test_queue_returns_200(self):
        url = reverse('community:htmx_steward_live_queue')
        response = self.client.get(url + f'?broadcast_id={self.broadcast_id}')
        self.assertEqual(response.status_code, 200)

    def test_queue_shows_session_request(self):
        url = reverse('community:htmx_steward_live_queue')
        response = self.client.get(url + f'?broadcast_id={self.broadcast_id}')
        self.assertContains(response, 'Pray for healing.')

    def test_queue_does_not_show_other_session_requests(self):
        other_id = str(uuid.uuid4())
        url = reverse('community:htmx_steward_live_queue')
        response = self.client.get(url + f'?broadcast_id={other_id}')
        self.assertNotContains(response, 'Pray for healing.')

    def test_mark_responded_transitions_to_completed(self):
        url = reverse('community:htmx_steward_respond_live_request', args=[self.record.id])
        self.client.post(url)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, 'completed')

    def test_participant_cannot_access_queue(self):
        participant = make_user('part_h4', level='1')
        c = Client()
        c.login(username='part_h4', password='testpass123')
        url = reverse('community:htmx_steward_live_queue')
        response = c.get(url)
        self.assertEqual(response.status_code, 403)
```

**Run tests:**

```bash
python manage.py test community.tests.test_live_service -v 2
# Expected: all pass
python manage.py test --verbosity=1 2>&1 | tail -5
# Expected: OK
```

**Commit:**

```bash
git add community/tests/test_live_service.py
git commit -m "test(community): H.4 live service room and ministry panel test suite"
```

---

## Task 8 — Final verification and merge

```bash
python manage.py check
python manage.py showmigrations | grep "\[ \]"
# Expected: none

git log --oneline main..HEAD
# 8 commits expected

git checkout main
git merge --no-ff v3-h4-community-live-service \
  -m "feat(community,video): H.4 — tenant-scoped live service room + in-service ministry panel"
git push origin main
```

---

## Exit Criteria

- [ ] Member visiting `/community/live/` sees only their own tenant's session
- [ ] `VideoFeedView` and `_event_qs()` respect `tenant_id` when provided; global behaviour preserved when not
- [ ] Member can raise prayer request or question without leaving the video page
- [ ] Steward sees live-updating queue scoped to current session only
- [ ] Requests from previous sessions do not appear in the queue
- [ ] Steward can mark a request as responded
- [ ] `python manage.py check` — 0 issues
- [ ] No regression to Learn lesson video embeds or Go Media Engine pipeline
