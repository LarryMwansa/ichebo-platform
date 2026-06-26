# Phase H.3 — Community Support Requests Implementation Plan

> ## ⚠️ Correction, 2026-06-26 — ALREADY SHIPPED, do not execute
>
> This plan was written without access to the live repository. By the time it was written, **this work was already built and live in production** — `commit 16bfbab feat: add member-to-steward support request flow with SLA tracking`, 2026-06-22. Do not run the tasks below; they would attempt to recreate code that already exists.
>
> **Where the real, shipped code actually lives:**
> - `community/views.py` — search for `# ── Support requests — member-to-steward, SLA-tracked ──`. `SUPPORT_REQUEST_RESPONSE_WINDOW_HOURS = 72` is the real SLA constant (matches Task 4 below exactly).
> - `community/services.py:resolve_steward_for_tenant(tenant)` — exists, and matches Task 2's design exactly, including its `role__endswith='-steward'` filter. **This is a real, still-live gap, not yet fixed**: it silently excludes `'admin'`-role holders, since that role string doesn't end in `-steward`. `tenants.models.UserPermission.STEWARD_ROLES` (a set added 2026-06-24 for an unrelated tenancy-visibility fix, which correctly includes `'admin'`) would be the right fix if this routing gap ever needs closing — flagging it here since it was found by direct comparison, not fixing it as part of this correction pass (out of scope for "fix the docs").
> - `notifications/models.py` — `support_request_created` and `support_request_acknowledged` are both already present in `NOTIFICATION_TYPES`, exactly as Task 1 below specifies.
> - **Real bug in this plan's Task 3, found by checking the actual `create_notification` signature:** the plan's `notify_support_request_created`/`notify_support_request_acknowledged` call `create_notification(user=..., notification_type=..., source_app=..., source_record_id=..., message=...)`. The real signature (`notifications/service.py`) is `create_notification(user, notification_type, title, body='', data=None)` — there is no `source_app`, `source_record_id`, or `message` parameter. Calling it as written below would raise `TypeError`. The actual shipped code does not have this bug — check the real `notifications/service.py` for the correct call shape rather than copying Task 3's code.
> - Real URLs (`community/urls.py`): `/community/support/`, `/community/htmx/support/create/`, `/community/htmx/support/mine/`, `/community/htmx/support/{id}/acknowledge/`.
>
> The task-by-task plan below is preserved as a historical record of the original design intent — useful for understanding *why* the shipped code looks the way it does, not as a build checklist. If extending Community Support later, start from the real files above.

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a member-initiated support request flow routed to the community steward, with SLA tracking visible in a steward queue view — entirely within the existing `community` Django app, using the existing `Record` model with no new models.

**Architecture:** `Record(record_family='community', record_type='support_request')` is the data shape (ADR-003 followed). Steward routing via `UserPermission` role lookup. SLA overdue state computed at read-time (no Celery). Two new `Notification` types wired via `post_save` signal. No new Django app required.

**Tech Stack:** Django 4.2, Django REST Framework, PostgreSQL, HTMX, existing `records`, `community`, `notifications`, `tenants` apps.

**Reference:** `community-support-requests-plan.md` (approved 2026-06-18) — authoritative spec. This plan implements it exactly.

**Branch:** `v3-h3-community-support` (cut from `main`)

**Commit on completion:** `feat(community): H.3 — support request flow, member-to-steward with SLA tracking`

---

## Pre-Flight Checks

Before starting any task, verify:

```bash
# On the Django VPS (SSH as ics@37.27.82.169)
cd /home/ics/ichebo-platform/backend
source venv/bin/activate
python manage.py check
# Expected: System check identified no issues (0 silenced).

git checkout main && git pull
git checkout -b v3-h3-community-support
```

---

## Task 1 — Add support_request notification types to Notification model

**Files:**
- Modify: `notifications/models.py` — add two new `notification_type` choices
- Create: `notifications/migrations/XXXX_add_support_request_notification_types.py` (auto-generated)

**Context:** `Notification.NOTIFICATION_TYPES` is a list of `(value, label)` tuples at `notifications/models.py:16` (or nearby). The data contract (Part 16.1) defines the existing types. Two new types are being appended.

**Step 1: Read the current NOTIFICATION_TYPES definition**

```bash
grep -n "NOTIFICATION_TYPES\|notification_type" notifications/models.py | head -20
```

Note the exact line and format. Match it exactly when adding the new types.

**Step 2: Add the two new types**

In `notifications/models.py`, find `NOTIFICATION_TYPES` and append:

```python
('support_request_created', 'Support Request Created'),
('support_request_acknowledged', 'Support Request Acknowledged'),
```

The list must remain in the same format as existing entries. Do not reorder existing entries.

**Step 3: Generate and apply the migration**

```bash
python manage.py makemigrations notifications --name add_support_request_notification_types
python manage.py migrate
```

**Step 4: Verify**

```bash
python manage.py shell -c "
from notifications.models import Notification
types = dict(Notification.NOTIFICATION_TYPES)
assert 'support_request_created' in types, 'missing support_request_created'
assert 'support_request_acknowledged' in types, 'missing support_request_acknowledged'
print('OK — both notification types present')
"
```

**Step 5: Commit**

```bash
git add notifications/models.py notifications/migrations/
git commit -m "feat(notifications): add support_request_created and support_request_acknowledged types"
```

---

## Task 2 — Add steward routing helper to community/services.py

**Files:**
- Create: `community/services.py` (new file — does not currently exist)

**Context:** When a support request is created, the system must resolve which steward to assign it to. The routing logic is: (1) query `UserPermission` for the tenant for any active `-steward` role, (2) fall back to `Tenant.coordinator_user` if no steward role found, (3) if neither, leave `assigned_steward_id=null` (surfaces as "needs routing" in the queue). This logic must be in a service layer, not in the view or the signal handler.

**Step 1: Read the UserPermission model to confirm field names**

```bash
grep -n "role\|is_active\|tenant\b" tenants/models.py | head -30
```

Confirm: `UserPermission.role` (CharField, choices include `*-steward` values), `UserPermission.is_active` (BooleanField), `UserPermission.tenant` (FK to Tenant). Also confirm: `Tenant.coordinator_user` exists and is nullable.

**Step 2: Create community/services.py**

```python
# community/services.py
"""
Community App service layer.
Business logic that does not belong in views or signal handlers.
"""
from tenants.models import Tenant, UserPermission


def resolve_steward_for_tenant(tenant: Tenant):
    """
    Resolve the assigned steward for a community tenant.

    Resolution order:
      1. Any active UserPermission with a -steward role in this tenant.
      2. Tenant.coordinator_user (nullable FK).
      3. None — request is flagged as needs-routing in the queue.

    Returns a User instance or None.
    """
    steward_permission = UserPermission.objects.filter(
        tenant=tenant,
        role__endswith='-steward',
        is_active=True,
    ).select_related('user').first()

    if steward_permission:
        return steward_permission.user

    if tenant.coordinator_user_id:
        return tenant.coordinator_user

    return None
```

**Step 3: Verify the helper resolves without import errors**

```bash
python manage.py shell -c "
from community.services import resolve_steward_for_tenant
from tenants.models import Tenant
t = Tenant.objects.first()
if t:
    result = resolve_steward_for_tenant(t)
    print(f'OK — resolved steward for {t}: {result}')
else:
    print('OK — no tenants yet, import works')
"
```

**Step 4: Commit**

```bash
git add community/services.py
git commit -m "feat(community): add resolve_steward_for_tenant service helper"
```

---

## Task 3 — Add notification service functions for support requests

**Files:**
- Modify: `notifications/service.py` — add two new notify functions

**Context:** `notifications/service.py` contains `create_notification()` at line 16 (or nearby) and existing `notify_*` functions (e.g. `notify_membership_approved`). The two new functions follow the exact same pattern. Neither is an EMAIL_TYPE — in-app and FCM push only.

**Step 1: Read the existing notify function pattern**

```bash
grep -n "def notify_\|create_notification" notifications/service.py
```

Read one complete existing `notify_*` function to understand the exact call signature for `create_notification()`. Match it exactly.

**Step 2: Add the two new service functions at the end of notifications/service.py**

```python
def notify_support_request_created(record):
    """
    Notify the assigned steward when a new support request is submitted.
    No-ops silently if no steward is assigned (needs-routing case).
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    steward_id = record.custom_fields.get('assigned_steward_id')
    if not steward_id:
        return  # needs-routing — no recipient yet

    try:
        steward = User.objects.get(id=steward_id)
    except User.DoesNotExist:
        return

    create_notification(
        user=steward,
        notification_type='support_request_created',
        source_app='community',
        source_record_id=record.id,
        message=f'New support request: {record.title}',
    )


def notify_support_request_acknowledged(record):
    """
    Notify the request creator when a steward acknowledges (status → active).
    """
    create_notification(
        user=record.created_by,
        notification_type='support_request_acknowledged',
        source_app='community',
        source_record_id=record.id,
        message='Your support request has been seen. A steward is working on it.',
    )
```

**Note:** The `create_notification()` call signature must exactly match what you found in Step 1. If the existing calls use keyword argument names differently (e.g. `title` instead of `message`), match the existing pattern — do not invent new kwargs.

**Step 3: Verify import**

```bash
python manage.py shell -c "
from notifications.service import notify_support_request_created, notify_support_request_acknowledged
print('OK — both notify functions importable')
"
```

**Step 4: Commit**

```bash
git add notifications/service.py
git commit -m "feat(notifications): add notify_support_request_created and notify_support_request_acknowledged"
```

---

## Task 4 — Wire signal handler for support request Record events

**Files:**
- Modify: `notifications/signals.py` — add `post_save` handler for `Record(record_type='support_request')`

**Context:** Django signals are the existing wiring pattern for notification dispatch. The handler fires on `post_save` of `Record`, checks `record_type`, and dispatches the correct notify function. Two events: (1) creation — `notify_support_request_created`, (2) status transition to `'active'` (acknowledged) — `notify_support_request_acknowledged`. The signal must not fire on non-support-request Records.

**Step 1: Read the existing signals.py to understand the pattern**

```bash
cat notifications/signals.py
```

Note: how existing handlers check `instance` fields, how they use `created` flag, how they are registered (likely via `@receiver` decorator or explicit `connect()` call). Match the pattern exactly.

**Step 2: Add the signal handler to notifications/signals.py**

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from records.models import Record
from .service import notify_support_request_created, notify_support_request_acknowledged


@receiver(post_save, sender=Record)
def handle_support_request_record(sender, instance, created, **kwargs):
    """
    Dispatch support request notifications on Record save.
    Only fires for record_type='support_request' — all other Records are ignored.
    """
    if instance.record_type != 'support_request':
        return

    if created:
        # New request — notify the assigned steward
        notify_support_request_created(instance)
        return

    # Status transition to 'active' (steward acknowledged)
    if instance.status == 'active':
        notify_support_request_acknowledged(instance)
```

**Important:** If `notifications/signals.py` already imports from `records.models`, do not add a duplicate import. If the file uses a different import style, match it. If `@receiver` is not the existing pattern, use `post_save.connect()` instead.

**Step 3: Verify the signal is registered**

```bash
python manage.py shell -c "
from django.db.models.signals import post_save
from records.models import Record
receivers = [r for r in post_save.receivers if 'support_request' in str(r) or 'handle_support' in str(r)]
# If empty, check that signals.py is imported in the app's AppConfig.ready()
print(f'Receivers registered: {len(post_save.receivers)} total')
# At minimum, verify no import errors:
from notifications import signals
print('OK — signals module loads without error')
"
```

**Step 4: Check AppConfig.ready() wires the signals module**

```bash
grep -n "signals\|ready" notifications/apps.py
```

If `ready()` does not import `notifications.signals`, add it:

```python
# notifications/apps.py
class NotificationsConfig(AppConfig):
    name = 'notifications'

    def ready(self):
        import notifications.signals  # noqa: F401
```

**Step 5: Commit**

```bash
git add notifications/signals.py notifications/apps.py
git commit -m "feat(notifications): wire post_save signal for support_request Record events"
```

---

## Task 5 — Add support request creation view (member-facing)

**Files:**
- Modify: `community/views.py` — add `htmx_support_request_new` view
- Modify: `community/urls.py` — add URL for new view
- Create: `templates/community/partials/support_request_form.html`

**Context:** Members raise a support request from a new HTMX form. On submission, a `Record` is created with the correct shape, `resolve_steward_for_tenant` is called, and the response redirects to the member's request list. The form is a simple two-field form: `title` (subject line) and `content` (request body). The `response_due_at` is set to `created_at + 72 hours` by default.

**Step 1: Read community/views.py to understand existing view patterns**

```bash
grep -n "def htmx_\|@login_required\|_require_level\|record_type\|record_family" community/views.py | head -30
```

Note the exact decorator pattern, how `_require_level` is called, and how Records are created in existing views (e.g. `htmx_create_gathering`). Match the pattern exactly.

**Step 2: Add the view to community/views.py**

Add after the last existing `htmx_` view function:

```python
@login_required
def htmx_support_request_new(request):
    """
    Member raises a new support request.
    GET: returns the form partial.
    POST: creates the Record, assigns steward, notifies.
    """
    from django.utils import timezone
    from datetime import timedelta
    import uuid

    from records.models import Record
    from community.services import resolve_steward_for_tenant

    # Resolve the member's active community tenant
    tenant = _get_active_community_tenant(request.user)
    if not tenant:
        return HttpResponseForbidden('No active community found.')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()

        if not title or not content:
            return render(request, 'community/partials/support_request_form.html', {
                'error': 'Subject and message are both required.',
                'title': title,
                'content': content,
            })

        steward = resolve_steward_for_tenant(tenant)
        response_due_at = timezone.now() + timedelta(hours=72)

        record = Record.objects.create(
            id=uuid.uuid4(),
            record_class='organizational',
            record_family='community',
            record_type='support_request',
            title=title,
            content=content,
            status='submitted',
            tenant=tenant,
            created_by=request.user,
            custom_fields={
                'response_due_at': response_due_at.isoformat(),
                'acknowledged_at': None,
                'resolved_at': None,
                'assigned_steward_id': str(steward.id) if steward else None,
            },
            permissions_data={'visibility': 'member_and_assigned_steward'},
        )

        # Signal fires automatically — notification dispatched via post_save

        return redirect('community:support_request_list')

    # GET — return empty form
    return render(request, 'community/partials/support_request_form.html', {
        'error': None,
        'title': '',
        'content': '',
    })
```

**Note on `_get_active_community_tenant`:** Check whether this helper already exists in `community/views.py`. If not, look for how other views resolve the user's tenant (e.g. via `UserPermission` or a `request.user.profile.tenant` pattern) and use the same approach. The key requirement: it must return the member's Sceptre Community tenant, not a global or agency tenant.

**Step 3: Add URL to community/urls.py**

```python
path('support/new/', views.htmx_support_request_new, name='support_request_new'),
```

**Step 4: Create the form template**

```html
<!-- templates/community/partials/support_request_form.html -->
<div class="support-request-form">
  {% if error %}
    <div class="form-error" role="alert">{{ error }}</div>
  {% endif %}

  <form method="post"
        hx-post="{% url 'community:support_request_new' %}"
        hx-target="#support-request-form-container"
        hx-swap="outerHTML">
    {% csrf_token %}

    <div class="field-group">
      <label for="id_title" class="field-label">Subject</label>
      <input
        type="text"
        id="id_title"
        name="title"
        value="{{ title }}"
        maxlength="255"
        required
        placeholder="Briefly describe your request"
        class="field-input"
      >
    </div>

    <div class="field-group">
      <label for="id_content" class="field-label">Message</label>
      <textarea
        id="id_content"
        name="content"
        required
        rows="5"
        placeholder="Describe what you need help with"
        class="field-input"
      >{{ content }}</textarea>
    </div>

    <div class="form-actions">
      <button type="submit" class="btn btn-primary">Submit Request</button>
    </div>
  </form>
</div>
```

**Step 5: Verify the URL resolves**

```bash
python manage.py shell -c "
from django.urls import reverse
url = reverse('community:support_request_new')
print(f'OK — URL resolves: {url}')
"
```

**Step 6: Commit**

```bash
git add community/views.py community/urls.py templates/community/partials/support_request_form.html
git commit -m "feat(community): add support request creation view and form partial"
```

---

## Task 6 — Add member support request list view

**Files:**
- Modify: `community/views.py` — add `support_request_list` view
- Modify: `community/urls.py` — add URL
- Create: `templates/community/support_request_list.html`

**Context:** Members view their own submitted requests and current status. Read-only. Shows title, status, submitted date, and whether the steward has acknowledged. Overdue requests (past `response_due_at` and not completed) are flagged visually. This is the surface the Support nav tile links to.

**Step 1: Add the view to community/views.py**

```python
@login_required
def support_request_list(request):
    """
    Member's own support request history and current status.
    Shows only records created by the requesting user.
    """
    from django.utils import timezone
    from records.models import Record

    now = timezone.now()

    requests = Record.objects.filter(
        record_family='community',
        record_type='support_request',
        created_by=request.user,
        deleted_at__isnull=True,
    ).order_by('-created_at')

    # Annotate overdue state at read-time
    request_items = []
    for req in requests:
        due_at_str = req.custom_fields.get('response_due_at')
        is_overdue = False
        if due_at_str and req.status != 'completed':
            from django.utils.dateparse import parse_datetime
            due_at = parse_datetime(due_at_str)
            if due_at and now > due_at:
                is_overdue = True
        request_items.append({
            'record': req,
            'is_overdue': is_overdue,
        })

    return render(request, 'community/support_request_list.html', {
        'request_items': request_items,
        'now': now,
    })
```

**Step 2: Add URL to community/urls.py**

```python
path('support/', views.support_request_list, name='support_request_list'),
```

**Step 3: Create the template**

```html
<!-- templates/community/support_request_list.html -->
{% extends "base.html" %}
{% block title %}My Support Requests{% endblock %}

{% block content %}
<div class="page-container">

  <div class="page-header">
    <span class="label-tag">&mdash;&mdash; COMMUNITY SUPPORT</span>
    <h1 class="page-title">My Requests</h1>
  </div>

  <div class="page-actions">
    <a href="{% url 'community:support_request_new' %}" class="btn btn-primary">
      Raise a Request
    </a>
  </div>

  {% if not request_items %}
    <div class="empty-state">
      <p>You have not submitted any support requests yet.</p>
    </div>
  {% else %}
    <div class="record-list">
      {% for item in request_items %}
        <div class="record-item {% if item.is_overdue %}record-item--overdue{% endif %}">
          <div class="record-item__left-rule"></div>
          <div class="record-item__body">
            <div class="record-item__title">{{ item.record.title }}</div>
            <div class="record-item__meta">
              <span class="status-badge status-badge--{{ item.record.status }}">
                {{ item.record.get_status_display }}
              </span>
              <span class="record-item__date">
                Submitted {{ item.record.created_at|date:"d M Y" }}
              </span>
              {% if item.is_overdue %}
                <span class="overdue-badge">Overdue</span>
              {% endif %}
            </div>
          </div>
        </div>
      {% endfor %}
    </div>
  {% endif %}

</div>
{% endblock %}
```

**Note on `{% extends "base.html" %}`:** Check the existing community templates to confirm the correct base template name and block names. Match them exactly — do not guess.

**Step 4: Verify**

```bash
python manage.py check
python manage.py shell -c "
from django.urls import reverse
print(reverse('community:support_request_list'))
print('OK')
"
```

**Step 5: Commit**

```bash
git add community/views.py community/urls.py templates/community/support_request_list.html
git commit -m "feat(community): add member support request list view"
```

---

## Task 7 — Add steward support queue view

**Files:**
- Modify: `community/views.py` — add `steward_support_queue` view
- Modify: `community/urls.py` — add URL
- Create: `templates/community/steward_support_queue.html`

**Context:** This is the accountability surface. Stewards see all open support requests across tenants they steward, sorted by `response_due_at` ascending (soonest-due first). Overdue requests are flagged visually. Higher-tier stewards see requests scoped to their tenant subtree via `tenant_path`. Gated at Level 3+ or `-steward` role.

**Step 1: Add the view to community/views.py**

```python
@login_required
def steward_support_queue(request):
    """
    Steward queue — all support requests across tenants this user stewards.
    Scoped via tenant_path for hierarchy visibility.
    Gated: competence_level >= 3 OR UserPermission.role endswith '-steward'.
    """
    from django.utils import timezone
    from django.utils.dateparse import parse_datetime
    from records.models import Record
    from tenants.models import UserPermission

    user = request.user

    # Gate: steward or Level 3+
    level_ok = getattr(user, 'competence_level', '0') in ['3', '4', '5']
    role_ok = UserPermission.objects.filter(
        user=user,
        role__endswith='-steward',
        is_active=True,
    ).exists()

    if not (level_ok or role_ok):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    # Collect tenant paths this steward oversees
    steward_permissions = UserPermission.objects.filter(
        user=user,
        role__endswith='-steward',
        is_active=True,
    ).values_list('tenant__tenant_path', flat=True)

    # Build tenant filter — include the steward's tenants and all sub-tenants
    from django.db.models import Q
    tenant_filter = Q()
    for path in steward_permissions:
        if path:
            tenant_filter |= Q(tenant__tenant_path__startswith=path)

    # Also include requests assigned directly to this steward
    tenant_filter |= Q(custom_fields__assigned_steward_id=str(user.id))

    now = timezone.now()
    status_filter = request.GET.get('status', 'open')

    qs = Record.objects.filter(
        record_family='community',
        record_type='support_request',
        deleted_at__isnull=True,
    ).filter(tenant_filter)

    # Apply status filter
    if status_filter == 'open':
        qs = qs.filter(status='submitted')
    elif status_filter == 'acknowledged':
        qs = qs.filter(status='active')
    elif status_filter == 'resolved':
        qs = qs.filter(status='completed')
    elif status_filter == 'needs_routing':
        qs = qs.filter(custom_fields__assigned_steward_id=None)
    # 'all' — no additional filter

    # Annotate overdue state and sort by response_due_at
    queue_items = []
    for req in qs.order_by('created_at'):
        due_at_str = req.custom_fields.get('response_due_at')
        is_overdue = False
        due_at = None
        if due_at_str and req.status != 'completed':
            due_at = parse_datetime(due_at_str)
            if due_at and now > due_at:
                is_overdue = True
        queue_items.append({
            'record': req,
            'is_overdue': is_overdue,
            'due_at': due_at,
        })

    # Sort: overdue first, then by due_at ascending, then by created_at
    queue_items.sort(key=lambda x: (
        not x['is_overdue'],
        x['due_at'] or now,
    ))

    return render(request, 'community/steward_support_queue.html', {
        'queue_items': queue_items,
        'status_filter': status_filter,
        'now': now,
    })
```

**Step 2: Add steward acknowledge view (status → active)**

```python
@login_required
def steward_acknowledge_support_request(request, record_id):
    """
    Steward acknowledges a support request — transitions status submitted → active.
    POST only.
    """
    from records.models import Record
    from tenants.models import UserPermission

    user = request.user
    level_ok = getattr(user, 'competence_level', '0') in ['3', '4', '5']
    role_ok = UserPermission.objects.filter(user=user, role__endswith='-steward', is_active=True).exists()
    if not (level_ok or role_ok):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    record = get_object_or_404(
        Record,
        id=record_id,
        record_family='community',
        record_type='support_request',
        status='submitted',
        deleted_at__isnull=True,
    )

    if request.method == 'POST':
        from django.utils import timezone
        custom = dict(record.custom_fields)
        custom['acknowledged_at'] = timezone.now().isoformat()
        custom['assigned_steward_id'] = str(user.id)
        record.custom_fields = custom
        record.status = 'active'
        record.save()
        # Signal fires — notify_support_request_acknowledged dispatched
        return redirect('community:steward_support_queue')

    return redirect('community:steward_support_queue')


@login_required
def steward_resolve_support_request(request, record_id):
    """
    Steward resolves a support request — transitions status active → completed.
    POST only.
    """
    from records.models import Record
    from tenants.models import UserPermission

    user = request.user
    level_ok = getattr(user, 'competence_level', '0') in ['3', '4', '5']
    role_ok = UserPermission.objects.filter(user=user, role__endswith='-steward', is_active=True).exists()
    if not (level_ok or role_ok):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    record = get_object_or_404(
        Record,
        id=record_id,
        record_family='community',
        record_type='support_request',
        deleted_at__isnull=True,
    )

    if request.method == 'POST':
        from django.utils import timezone
        custom = dict(record.custom_fields)
        custom['resolved_at'] = timezone.now().isoformat()
        record.custom_fields = custom
        record.status = 'completed'
        record.save()
        return redirect('community:steward_support_queue')

    return redirect('community:steward_support_queue')
```

**Step 3: Add URLs to community/urls.py**

```python
path('support/queue/', views.steward_support_queue, name='steward_support_queue'),
path('support/<uuid:record_id>/acknowledge/', views.steward_acknowledge_support_request, name='steward_acknowledge_support_request'),
path('support/<uuid:record_id>/resolve/', views.steward_resolve_support_request, name='steward_resolve_support_request'),
```

**Step 4: Create the steward queue template**

```html
<!-- templates/community/steward_support_queue.html -->
{% extends "base.html" %}
{% block title %}Support Queue{% endblock %}

{% block content %}
<div class="page-container">

  <div class="page-header">
    <span class="label-tag">&mdash;&mdash; COMMUNITY MANAGEMENT</span>
    <h1 class="page-title">Support Queue</h1>
  </div>

  <div class="queue-filters">
    <a href="?status=open"
       class="filter-tab {% if status_filter == 'open' %}filter-tab--active{% endif %}">
      Open
    </a>
    <a href="?status=acknowledged"
       class="filter-tab {% if status_filter == 'acknowledged' %}filter-tab--active{% endif %}">
      Acknowledged
    </a>
    <a href="?status=resolved"
       class="filter-tab {% if status_filter == 'resolved' %}filter-tab--active{% endif %}">
      Resolved
    </a>
    <a href="?status=needs_routing"
       class="filter-tab {% if status_filter == 'needs_routing' %}filter-tab--active{% endif %}">
      Needs Routing
    </a>
    <a href="?status=all"
       class="filter-tab {% if status_filter == 'all' %}filter-tab--active{% endif %}">
      All
    </a>
  </div>

  {% if not queue_items %}
    <div class="empty-state">
      <p>No support requests in this view.</p>
    </div>
  {% else %}
    <div class="record-list">
      {% for item in queue_items %}
        <div class="record-item {% if item.is_overdue %}record-item--overdue{% endif %}">
          <div class="record-item__left-rule"></div>
          <div class="record-item__body">
            <div class="record-item__title">{{ item.record.title }}</div>
            <div class="record-item__meta">
              <span class="status-badge status-badge--{{ item.record.status }}">
                {{ item.record.get_status_display }}
              </span>
              <span class="record-item__date">
                Submitted {{ item.record.created_at|date:"d M Y" }}
                by {{ item.record.created_by.get_full_name|default:item.record.created_by.username }}
              </span>
              {% if item.due_at %}
                <span class="record-item__due {% if item.is_overdue %}record-item__due--overdue{% endif %}">
                  Due {{ item.due_at|date:"d M Y H:i" }}
                </span>
              {% endif %}
              {% if item.is_overdue %}
                <span class="overdue-badge">Overdue</span>
              {% endif %}
            </div>
            <div class="record-item__content">
              {{ item.record.content|truncatewords:30 }}
            </div>
            <div class="record-item__actions">
              {% if item.record.status == 'submitted' %}
                <form method="post"
                      action="{% url 'community:steward_acknowledge_support_request' item.record.id %}">
                  {% csrf_token %}
                  <button type="submit" class="btn btn-sm btn-secondary">
                    Acknowledge
                  </button>
                </form>
              {% endif %}
              {% if item.record.status == 'active' %}
                <form method="post"
                      action="{% url 'community:steward_resolve_support_request' item.record.id %}">
                  {% csrf_token %}
                  <button type="submit" class="btn btn-sm btn-primary">
                    Mark Resolved
                  </button>
                </form>
              {% endif %}
            </div>
          </div>
        </div>
      {% endfor %}
    </div>
  {% endif %}

</div>
{% endblock %}
```

**Step 5: Verify**

```bash
python manage.py check
python manage.py shell -c "
from django.urls import reverse
print(reverse('community:steward_support_queue'))
print(reverse('community:steward_acknowledge_support_request', args=['00000000-0000-0000-0000-000000000000']))
print(reverse('community:steward_resolve_support_request', args=['00000000-0000-0000-0000-000000000000']))
print('OK — all URLs resolve')
"
```

**Step 6: Commit**

```bash
git add community/views.py community/urls.py templates/community/steward_support_queue.html
git commit -m "feat(community): add steward support queue view with acknowledge and resolve actions"
```

---

## Task 8 — Write tests

**Files:**
- Create: `community/tests/test_support_requests.py`

**Context:** The H.3 plan specifies the following exit criteria as tests. Write them all before running them. Tests use Django's `TestCase` with a test database — no live data required.

**Step 1: Create the test file**

```python
# community/tests/test_support_requests.py
"""
Tests for Phase H.3 — Community Support Request flow.
Covers: steward routing, record creation, status transitions,
notification dispatch, steward queue scoping, overdue flagging.
"""
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from records.models import Record
from tenants.models import Tenant, UserPermission
from community.services import resolve_steward_for_tenant

User = get_user_model()


def make_tenant(name='Test Community', path='/global/test/'):
    return Tenant.objects.create(
        name=name,
        tenant_path=path,
    )


def make_user(username, competence_level='1', tenant=None, role=None):
    user = User.objects.create_user(
        username=username,
        password='testpass123',
        email=f'{username}@test.com',
    )
    user.competence_level = competence_level
    user.save()
    if tenant and role:
        UserPermission.objects.create(
            user=user,
            tenant=tenant,
            role=role,
            is_active=True,
            tenant_path=tenant.tenant_path,
        )
    return user


class TestResolveStew(TestCase):
    """resolve_steward_for_tenant routing logic."""

    def test_resolves_steward_role(self):
        tenant = make_tenant()
        steward = make_user('steward1', role='branch-steward', tenant=tenant)
        result = resolve_steward_for_tenant(tenant)
        self.assertEqual(result, steward)

    def test_falls_back_to_coordinator_user(self):
        tenant = make_tenant()
        coordinator = make_user('coordinator1')
        tenant.coordinator_user = coordinator
        tenant.save()
        result = resolve_steward_for_tenant(tenant)
        self.assertEqual(result, coordinator)

    def test_returns_none_when_no_steward_or_coordinator(self):
        tenant = make_tenant()
        result = resolve_steward_for_tenant(tenant)
        self.assertIsNone(result)

    def test_steward_role_takes_priority_over_coordinator(self):
        tenant = make_tenant()
        coordinator = make_user('coordinator2')
        steward = make_user('steward2', role='branch-steward', tenant=tenant)
        tenant.coordinator_user = coordinator
        tenant.save()
        result = resolve_steward_for_tenant(tenant)
        self.assertEqual(result, steward)


class TestSupportRequestCreation(TestCase):
    """Member creates a support request via the form view."""

    def setUp(self):
        self.tenant = make_tenant()
        self.member = make_user('member1', competence_level='1', tenant=self.tenant, role='member')
        self.steward = make_user('steward3', competence_level='3', tenant=self.tenant, role='branch-steward')
        self.client = Client()
        self.client.login(username='member1', password='testpass123')

    def test_get_form_returns_200(self):
        url = reverse('community:support_request_new')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_post_creates_record(self):
        url = reverse('community:support_request_new')
        response = self.client.post(url, {
            'title': 'I need help with my induction',
            'content': 'I am stuck on lesson 3 and cannot proceed.',
        })
        self.assertRedirects(response, reverse('community:support_request_list'))
        record = Record.objects.get(
            record_family='community',
            record_type='support_request',
            created_by=self.member,
        )
        self.assertEqual(record.status, 'submitted')
        self.assertEqual(record.custom_fields['assigned_steward_id'], str(self.steward.id))
        self.assertIsNotNone(record.custom_fields['response_due_at'])

    def test_post_empty_title_returns_error(self):
        url = reverse('community:support_request_new')
        response = self.client.post(url, {'title': '', 'content': 'Some content'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'required')

    def test_needs_routing_when_no_steward(self):
        # Remove steward
        UserPermission.objects.filter(user=self.steward).delete()
        self.tenant.coordinator_user = None
        self.tenant.save()

        url = reverse('community:support_request_new')
        self.client.post(url, {
            'title': 'Unrouted request',
            'content': 'This should have no steward assigned.',
        })
        record = Record.objects.get(
            record_family='community',
            record_type='support_request',
            title='Unrouted request',
        )
        self.assertIsNone(record.custom_fields['assigned_steward_id'])


class TestSupportRequestStatusTransitions(TestCase):
    """Steward acknowledges and resolves support requests."""

    def setUp(self):
        self.tenant = make_tenant()
        self.member = make_user('member2', competence_level='1', tenant=self.tenant, role='member')
        self.steward = make_user('steward4', competence_level='3', tenant=self.tenant, role='branch-steward')
        self.record = Record.objects.create(
            record_family='community',
            record_type='support_request',
            record_class='organizational',
            title='Test request',
            content='Test content',
            status='submitted',
            tenant=self.tenant,
            created_by=self.member,
            custom_fields={
                'response_due_at': (timezone.now() + timedelta(hours=72)).isoformat(),
                'acknowledged_at': None,
                'resolved_at': None,
                'assigned_steward_id': str(self.steward.id),
            },
            permissions_data={'visibility': 'member_and_assigned_steward'},
        )
        self.client = Client()
        self.client.login(username='steward4', password='testpass123')

    def test_acknowledge_transitions_to_active(self):
        url = reverse('community:steward_acknowledge_support_request', args=[self.record.id])
        self.client.post(url)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, 'active')
        self.assertIsNotNone(self.record.custom_fields.get('acknowledged_at'))

    def test_resolve_transitions_to_completed(self):
        self.record.status = 'active'
        self.record.save()
        url = reverse('community:steward_resolve_support_request', args=[self.record.id])
        self.client.post(url)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, 'completed')
        self.assertIsNotNone(self.record.custom_fields.get('resolved_at'))

    def test_participant_cannot_acknowledge(self):
        participant = make_user('participant1', competence_level='1')
        c = Client()
        c.login(username='participant1', password='testpass123')
        url = reverse('community:steward_acknowledge_support_request', args=[self.record.id])
        response = c.post(url)
        self.assertEqual(response.status_code, 403)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, 'submitted')


class TestStewardQueue(TestCase):
    """Steward queue view — scoping, filtering, overdue flagging."""

    def setUp(self):
        self.tenant = make_tenant(path='/global/africa/test/')
        self.member = make_user('member3', competence_level='1', tenant=self.tenant, role='member')
        self.steward = make_user('steward5', competence_level='3', tenant=self.tenant, role='branch-steward')
        self.client = Client()
        self.client.login(username='steward5', password='testpass123')

    def _make_request(self, title='Request', status='submitted', due_hours=72):
        return Record.objects.create(
            record_family='community',
            record_type='support_request',
            record_class='organizational',
            title=title,
            content='Content',
            status=status,
            tenant=self.tenant,
            created_by=self.member,
            custom_fields={
                'response_due_at': (timezone.now() + timedelta(hours=due_hours)).isoformat(),
                'acknowledged_at': None,
                'resolved_at': None,
                'assigned_steward_id': str(self.steward.id),
            },
            permissions_data={'visibility': 'member_and_assigned_steward'},
        )

    def test_queue_returns_200(self):
        url = reverse('community:steward_support_queue')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_queue_shows_open_requests(self):
        req = self._make_request(title='Open request')
        url = reverse('community:steward_support_queue')
        response = self.client.get(url + '?status=open')
        self.assertContains(response, 'Open request')

    def test_overdue_request_flagged(self):
        self._make_request(title='Overdue request', due_hours=-1)
        url = reverse('community:steward_support_queue')
        response = self.client.get(url + '?status=open')
        self.assertContains(response, 'Overdue')

    def test_participant_cannot_access_queue(self):
        participant = make_user('participant2', competence_level='1')
        c = Client()
        c.login(username='participant2', password='testpass123')
        url = reverse('community:steward_support_queue')
        response = c.get(url)
        self.assertEqual(response.status_code, 403)
```

**Step 2: Run the tests**

```bash
python manage.py test community.tests.test_support_requests -v 2
```

**Expected:** All tests pass. If any fail, fix the issue in the relevant view or service before proceeding. Do not skip failures.

**Step 3: Run the full check**

```bash
python manage.py check
python manage.py test community notifications -v 1
```

**Expected:** 0 errors, 0 failures.

**Step 4: Commit**

```bash
git add community/tests/test_support_requests.py
git commit -m "test(community): H.3 support request flow — full test suite"
```

---

## Task 9 — Final verification and system check

**Step 1: Run full system check**

```bash
python manage.py check --deploy 2>&1 | grep -v "WARNINGS"
# Expected: System check identified no issues
```

**Step 2: Run all migrations cleanly**

```bash
python manage.py showmigrations | grep "\[ \]"
# Expected: no unapplied migrations
```

**Step 3: Run the full test suite**

```bash
python manage.py test --verbosity=1 2>&1 | tail -5
# Expected: OK (N tests)
```

**Step 4: Confirm no new migrations to Tenant, UserPermission, or Activity**

```bash
git diff main -- tenants/migrations/ activity/migrations/
# Expected: no output — these models were not touched
```

**Step 5: Final commit and merge prep**

```bash
git log --oneline main..HEAD
# Should show exactly these commits (in order):
# feat(notifications): add support_request_created and support_request_acknowledged types
# feat(community): add resolve_steward_for_tenant service helper
# feat(notifications): add notify_support_request_created and notify_support_request_acknowledged
# feat(notifications): wire post_save signal for support_request Record events
# feat(community): add support request creation view and form partial
# feat(community): add member support request list view
# feat(community): add steward support queue view with acknowledge and resolve actions
# test(community): H.3 support request flow — full test suite
```

**Step 6: Merge commit**

```bash
git checkout main
git merge --no-ff v3-h3-community-support \
  -m "feat(community): H.3 — support request flow, member-to-steward with SLA tracking"
git push origin main
```

---

## Exit Criteria Checklist

- [ ] Member can raise a support request from `/community/support/new/`
- [ ] Request is routed to a steward via `UserPermission` role lookup, falling back to `Tenant.coordinator_user`, or flagged "needs routing" if neither resolves
- [ ] Steward receives a notification on request creation
- [ ] Member receives a notification when steward acknowledges (status → active)
- [ ] `/community/support/queue/` renders, scoped to tenants the viewing user stewards (including sub-tenants via `tenant_path`)
- [ ] Overdue requests (past `response_due_at`, not resolved) are visually flagged in the queue
- [ ] Member can view their own request history and current status at `/community/support/`
- [ ] `python manage.py check` — 0 issues
- [ ] No new migrations to `Tenant`, `UserPermission`, or `Activity`
- [ ] All tests in `community/tests/test_support_requests.py` pass
