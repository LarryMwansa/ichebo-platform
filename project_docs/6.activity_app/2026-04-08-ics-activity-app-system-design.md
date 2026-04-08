# ICS Activity App — System Design & Build Roadmap

> **UI Architecture:** Django templates + HTMX throughout. No `activity-app.js`.
> All UI is server-rendered. HTMX handles status updates, form submissions, and
> partial refreshes. `storage.js` is retained for UI state (theme, session token) only.

> **Data Contract reference:** `2026-04-08-ics-platform-data-contract_v5.md` —
> all schemas and patterns in this document originate from Parts 4, 10, and 11
> of that contract. Read the contract before implementing.

**Goal:** Build the ICS Activity App — the operational execution layer of the Kingdom
Governance System — enabling members to manage personal disciplines, stewards to
coordinate team campaigns, and the platform to feed Paraclete and the Dashboard with
rich activity data.

**Architecture:** Django + DRF backend with a dedicated `activity` Django app (already
scaffolded from Phase 3 of the main roadmap). The Activity App adds Django template
views, HTMX interactions, and the Calendar aggregation service on top of the existing
Activity Engine. No new models beyond the existing data contract — the Activity App is a
pattern and UI layer over the Activity Engine.

**Tech Stack:** Python/Django 4.2, DRF, PostgreSQL, Django templates, HTMX,
`activity.css` (mobile-first, CSS variables).

---

## System Overview

### The Activity Stack

```
KGS Layer          Great Calendar → Seven-Year Programme → Harvest Campaign Cycle
                   ↓ generates
Operational Layer  Campaign (activity_type: "campaign")
                   ↓ contains
                   Project (activity_type: "project")
                   ↓ contains
                   Task (activity_type: "task") — assigned to a user
                   ↓ also parallel to
Personal Layer     Habit / Goal / Reminder (personal, tenant_id: null)
                   ↓ alongside
Gifts Layer        Skill register (activity_type: "skill") — gifts & competence
                   ↓ all feed into
Aggregation        Calendar App (GET /api/calendar/events/) — reads Activity table
                   ↓ consumed by
Intelligence       Paraclete digest — pending activities, habits, reminders
                   ↓ surfaces on
Dashboard          Pending activities widget, today's focus, habit streaks
```

### Two-surface model

```
Activity App
  │
  ├── "My Activities"  (personal surface)
  │     Scope:  tenant_id: null, created_by = request.user
  │     Types:  task, habit, goal, skill, reminder
  │     Also:   read-only programme cards (Learn enrolments)
  │     Nesting: flat only
  │
  └── "Ministry"  (organisational surface)
        Scope:  tenant_id in user's tenants
        Types:  task, habit, event, campaign, project, reminder
        Includes: "Assigned to me" queue — first-class tab
        Nesting: two-level (campaign/project → task)
        Create: campaign/project = Level 3+; task = Level 1+
```

### User roles in the Activity App

| Role | What they can do |
|---|---|
| Seeker (0b) | Personal tasks and habits only (limited) |
| Member (Level 1) | Full personal activities; see assigned ministry tasks |
| Disciple (Level 2) | All personal + team tasks; instantiate templates |
| Branch-Steward (Level 3+) | Create campaigns, projects, events; assign tasks to team members; view team gifts register |
| Senior Steward (Level 4+) | All above + create activity templates |
| Architect (Level 5) | All above + cross-tenant visibility |

---

## Feature List (All Features — Unphased)

### F1 — My Activities (Personal Surface)

- Personal task list: create, edit, complete, defer, cancel
- Habit tracker: create recurring disciplines (daily/weekly/monthly)
- Goal register: personal goals with progress tracking (0–100%)
- Gifts register: skills/gifts inventory (`activity_type: "skill"`)
  - Add a gift: title, description, self-assessed competence, KGS pathway, service order
  - View gifts list; update competence level; archive
- Reminder: create time-based reminders (Paraclete surfaces these; no dedicated view)
- Read-only Learn programme cards: active enrolments with progress bar
- Empty state for new members

### F2 — Ministry Surface

- Ministry activity list: all team activities visible to the user
  - Grouped view: campaign/project headers with nested tasks
  - Flat assigned-tasks view (no campaign parent)
- "Assigned to me" queue: primary tab — tasks where `assigned_to = request.user`
  - Grouped by parent campaign/project
  - Due today / overdue highlighted
  - HTMX status toggle (pending → in_progress → completed)
- Ministry events list: upcoming events with `scheduled_at` as dated list

### F3 — Create / Edit Activity

- Unified create form for all user-accessible types
- Fields: title, description, type selector (filtered by competence level),
  KGS pillar selector, KGS pathway selector, due_at, scheduled_at,
  recurrence (daily/weekly/monthly radio — custom RRULE deferred),
  assigned_to (steward only, scoped to their tenant), tenant selector
- "Start from template" affordance: HTMX-powered typeahead to select a template
  and pre-fill the form
- "Link to record" affordance: HTMX typeahead calls `GET /api/records/?search={q}`
  and creates a Relationship on save (per Part 3.3 rules in v5 contract)
- Edit: same form, pre-filled; access controlled by `created_by` or Level 3+ steward

### F4 — Campaign / Project Management (Level 3+)

- Create campaign: title, description, KGS pillar, pathway, date range, assigned team
- Create project nested under a campaign
- Create task nested under a campaign or project, with `assigned_to` selection
- Campaign detail view: progress overview (% tasks completed), task list, team members
- Task status managed by either the assigned user or the creating steward

### F5 — Template Management (Level 4+)

- Create activity template (`metadata.is_template: true`): any activity type
- Template list view (separate from main activity list)
- Template detail: view/edit template fields
- Instantiate template: creates a new activity with fields pre-filled from template
  (`metadata.template_id` set to source); all Level 2+ users can instantiate

### F6 — Gifts Register (Personal + Team View)

- Personal: add, edit, archive skill/gift entries
- Team view (steward, Level 3+): read-only list of team gifts within their tenant scope
  - Grouped by KGS service order
  - Competence distribution at a glance

### F7 — Dated Activity List (Events)

- Ministry surface events tab: activities with `scheduled_at` or `due_at` set
- Grouped by date (today, tomorrow, this week, later)
- Event cards: title, type badge, time, tenant context
- No calendar grid in MVP — dated grouped list only

### F8 — Paraclete Filter Endpoints (Backend)

All six Paraclete-required filters on `GET /api/activities/`:

```
?assigned_to={user_id}
?due_today=true
?overdue=true
?activity_type=habit&status=in_progress
?tenant_id={id}&status=pending
?parent_activity_id={id}
?metadata__source_app=learn
```

These are built as part of the Activity App work and consumed by Paraclete in Phase 6.

### F9 — Calendar App Backend

- `GET /api/calendar/events/?from=&to=&tenant_id=` aggregation endpoint
- Queries Activity table for activities with `scheduled_at` or `due_at` in range
- Returns `CalendarEvent[]` sorted chronologically
- Scope: requesting user's tenant membership + personal activities
- No calendar UI in this phase — backend only

### F10 — ActivityLog Signals

- Every status change writes an `ActivityLog` entry
- Every `assigned_to` change writes an `ActivityLog` entry (`event_type: "assigned"`)
- Every record link creation writes an `ActivityLog` entry (`event_type: "linked"`)
- Signals wired in `activity/signals.py`

---

## Build Phases

### Phase A — Activity App Backend (Filters + Signals)
*Entry requirement: Phases 0–4 of main roadmap complete. `activity` Django app exists with basic CRUD.*

### Phase B — Django Views + URL Routing
*Entry requirement: Phase A complete.*

### Phase C — My Activities Surface (UI)
*Entry requirement: Phase B complete.*

### Phase D — Ministry Surface + Assigned-to-Me Queue (UI)
*Entry requirement: Phase C complete.*

### Phase E — Campaign / Project Management + Record Linking (UI)
*Entry requirement: Phase D complete.*

### Phase F — Templates + Gifts Register + Calendar Backend
*Entry requirement: Phase E complete.*

---

## Phase A — Activity App Backend

**Exit criteria:** `GET /api/activities/health/` returns `{"status": "ok"}`. All
six Paraclete filter parameters work on `GET /api/activities/`. `ActivityLog` signal
fires on status change. Calendar app scaffolded with aggregation endpoint returning
valid JSON.

---

### Task A.1 — Verify and extend ActivityViewSet filters

**Files:**
- Modify: `~/ics/activity/views.py` (or `api_views.py` if already split)
- Modify: `~/ics/activity/urls.py`

The `activity` Django app was scaffolded in Phase 3 of the main roadmap. This task
verifies its DRF `ActivityViewSet` exists and adds all required filter backends.

**Step 1:** Confirm `activity/models.py` matches the v5 data contract schema.
The `Activity` model must include all fields from Part 4.1 of the contract.
Key fields to verify:

```python
# activity/models.py — confirm these exist
class Activity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenants.Tenant', null=True, blank=True,
                               on_delete=models.SET_NULL, related_name='activities')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.PROTECT,
                                   related_name='created_activities')
    created_at = models.DateTimeField(auto_now_add=True)

    ACTIVITY_TYPES = [
        ('task', 'Task'), ('habit', 'Habit'), ('goal', 'Goal'),
        ('event', 'Event'), ('campaign', 'Campaign'), ('project', 'Project'),
        ('programme', 'Programme'), ('reminder', 'Reminder'), ('skill', 'Skill'),
    ]
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    scheduled_at = models.DateTimeField(null=True, blank=True, db_index=True)
    due_at = models.DateTimeField(null=True, blank=True, db_index=True)
    recurrence = models.CharField(
        max_length=10,
        choices=[('none','None'),('daily','Daily'),('weekly','Weekly'),
                 ('monthly','Monthly'),('custom','Custom')],
        default='none'
    )
    recurrence_rule = models.CharField(max_length=500, blank=True, null=True)

    parent_activity = models.ForeignKey('self', null=True, blank=True,
                                        on_delete=models.SET_NULL,
                                        related_name='child_activities',
                                        db_index=True)

    STATUS_CHOICES = [
        ('pending','Pending'), ('in_progress','In Progress'),
        ('completed','Completed'), ('cancelled','Cancelled'), ('deferred','Deferred'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.IntegerField(default=0)

    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name='assigned_activities',
                                    db_index=True)

    KGS_PILLARS = [
        ('apostolic','Apostolic'), ('strategy','Strategy'),
        ('formation','Formation'), ('programmes','Programmes'),
        ('mission','Mission'), ('communities','Communities'),
        ('stewardship','Stewardship'),
    ]
    KGS_PATHWAYS = [
        ('new_life','New Life'), ('spiritual_formation','Spiritual Formation'),
        ('community_life','Community Life'), ('service','Service'),
        ('leadership','Leadership'), ('learning','Learning'),
        ('mission','Mission'), ('apostolic_stewardship','Apostolic Stewardship'),
    ]
    kgs_pillar = models.CharField(max_length=30, choices=KGS_PILLARS,
                                  blank=True, null=True)
    kgs_pathway = models.CharField(max_length=30, choices=KGS_PATHWAYS,
                                   blank=True, null=True)

    metadata = models.JSONField(default=dict, blank=True)
    # metadata keys: source_app, icon, color, is_template, template_id, service_order

    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant']),
            models.Index(fields=['activity_type']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['status']),
            models.Index(fields=['due_at']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['parent_activity']),
            models.Index(fields=['created_by']),
            models.Index(fields=['tenant', 'activity_type']),
            models.Index(fields=['tenant', 'assigned_to']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['assigned_to', 'due_at']),
        ]
```

**Step 2:** Add `django-filter` to requirements if not present:

```bash
pip install django-filter
pip freeze > requirements.txt
```

Add to `INSTALLED_APPS` in `base.py`:
```python
'django_filters',
```

Add to `REST_FRAMEWORK` in `base.py`:
```python
'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
```

**Step 3:** Create `activity/filters.py`:

```python
# activity/filters.py
import django_filters
from django.utils import timezone
from .models import Activity


class ActivityFilter(django_filters.FilterSet):
    # Standard field filters
    activity_type = django_filters.CharFilter(field_name='activity_type')
    status = django_filters.CharFilter(field_name='status')
    assigned_to = django_filters.UUIDFilter(field_name='assigned_to__id')
    tenant_id = django_filters.UUIDFilter(field_name='tenant__id')
    parent_activity_id = django_filters.UUIDFilter(field_name='parent_activity__id')
    source_app = django_filters.CharFilter(
        field_name='metadata__source_app', lookup_expr='exact'
    )

    # Surface filter: personal (tenant null, created_by=user) or
    # ministry (tenant in user's tenants) — handled in ViewSet, not here

    # Computed filters
    due_today = django_filters.BooleanFilter(method='filter_due_today')
    overdue = django_filters.BooleanFilter(method='filter_overdue')

    def filter_due_today(self, queryset, name, value):
        if value:
            today = timezone.now().date()
            return queryset.filter(
                due_at__date=today,
                status__in=['pending', 'in_progress']
            )
        return queryset

    def filter_overdue(self, queryset, name, value):
        if value:
            now = timezone.now()
            return queryset.filter(
                due_at__lt=now,
                status__in=['pending', 'in_progress']
            )
        return queryset

    class Meta:
        model = Activity
        fields = ['activity_type', 'status', 'assigned_to', 'tenant_id',
                  'parent_activity_id', 'due_today', 'overdue', 'source_app']
```

**Step 4:** Create or update `activity/api_views.py`:

```python
# activity/api_views.py
import uuid
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Activity, ActivityLog
from .serializers import ActivitySerializer, ActivityLogSerializer
from .filters import ActivityFilter


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok", "app": "activity"})


class ActivityViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for Activity objects.
    Scoping: results filtered to activities the requesting user may see.
    Filters: see ActivityFilter for all supported query parameters.
    """
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ActivityFilter

    def get_queryset(self):
        user = self.request.user
        surface = self.request.query_params.get('surface')

        # Soft-delete: never return deleted activities
        qs = Activity.objects.filter(deleted_at__isnull=True)

        if surface == 'personal':
            # Personal: created by this user, no tenant
            return qs.filter(
                created_by=user,
                tenant__isnull=True
            )

        if surface == 'ministry':
            # Ministry: any activity in a tenant the user belongs to
            user_tenant_ids = user.userpermission_set.filter(
                is_active=True
            ).values_list('tenant_id', flat=True)
            return qs.filter(
                tenant_id__in=user_tenant_ids
            )

        # Default: personal + assigned-to-user ministry activities
        user_tenant_ids = user.userpermission_set.filter(
            is_active=True
        ).values_list('tenant_id', flat=True)

        personal = qs.filter(created_by=user, tenant__isnull=True)
        assigned = qs.filter(assigned_to=user, tenant_id__in=user_tenant_ids)

        return (personal | assigned).distinct()

    def perform_create(self, serializer):
        """
        Assignment permission gate: only Level 3+ may set assigned_to to another user.
        Template creation: only Level 4+ may set is_template: true.
        """
        user = self.request.user
        user_level = getattr(getattr(user, 'userprofile', None), 'competence_level', 0)

        assigned_to = serializer.validated_data.get('assigned_to')
        if assigned_to and assigned_to != user and user_level < 3:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "Only stewards (Level 3+) may assign activities to other users."
            )

        metadata = serializer.validated_data.get('metadata', {})
        if metadata.get('is_template') and user_level < 4:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "Only Senior Stewards (Level 4+) may create activity templates."
            )

        serializer.save(created_by=user)

    def perform_update(self, serializer):
        """Log status changes via ActivityLog."""
        instance = self.get_object()
        old_status = instance.status
        old_assigned = instance.assigned_to_id

        updated = serializer.save()

        # Log status change
        if updated.status != old_status:
            ActivityLog.objects.create(
                activity=updated,
                tenant=updated.tenant,
                created_by=self.request.user,
                event_type='status_changed',
                previous_value=old_status,
                new_value=updated.status
            )

        # Log assignment change
        if updated.assigned_to_id != old_assigned:
            ActivityLog.objects.create(
                activity=updated,
                tenant=updated.tenant,
                created_by=self.request.user,
                event_type='assigned',
                previous_value=str(old_assigned),
                new_value=str(updated.assigned_to_id)
            )

    def perform_destroy(self, instance):
        """Soft delete — never hard delete."""
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['deleted_at'])

    @action(detail=True, methods=['post'], url_path='instantiate')
    def instantiate(self, request, pk=None):
        """
        Create a new Activity from a template.
        Requires: activity.metadata.is_template = true
        Level 2+ may instantiate.
        """
        user = request.user
        user_level = getattr(getattr(user, 'userprofile', None), 'competence_level', 0)
        if user_level < 2:
            return Response(
                {"detail": "Level 2 or above required to instantiate templates."},
                status=status.HTTP_403_FORBIDDEN
            )

        template = self.get_object()
        if not template.metadata.get('is_template'):
            return Response(
                {"detail": "This activity is not a template."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Copy template fields; override per instantiation rules
        new_activity = Activity.objects.create(
            tenant=template.tenant,
            created_by=user,
            activity_type=template.activity_type,
            title=template.title,
            description=template.description,
            recurrence=template.recurrence,
            recurrence_rule=template.recurrence_rule,
            kgs_pillar=template.kgs_pillar,
            kgs_pathway=template.kgs_pathway,
            status='pending',
            progress=0,
            assigned_to=user,
            metadata={
                **template.metadata,
                'is_template': False,
                'template_id': str(template.id),
                'source_app': 'activity',
            }
        )

        ActivityLog.objects.create(
            activity=new_activity,
            tenant=new_activity.tenant,
            created_by=user,
            event_type='created',
            new_value=f'Instantiated from template {template.id}'
        )

        serializer = self.get_serializer(new_activity)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
```

**Step 5:** Create `activity/serializers.py` if not already complete:

```python
# activity/serializers.py
from rest_framework import serializers
from .models import Activity, ActivityLog


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
```

**Step 6:** Update `activity/urls.py`:

```python
# activity/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'activities', api_views.ActivityViewSet, basename='activity')

urlpatterns = [
    path('', include(router.urls)),
    path('health/', api_views.health, name='activity-health'),
]
```

**Step 7:** Include in main `urls.py`:

```python
path('api/', include('activity.urls')),
```

**Step 8:** Run migrations and verify:

```bash
python manage.py makemigrations activity
python manage.py migrate
curl https://your-domain.com/api/activity/health/
# Expected: {"status": "ok", "app": "activity"}

# Test filters
curl "https://your-domain.com/api/activities/?activity_type=task" -H "Authorization: Token {token}"
curl "https://your-domain.com/api/activities/?due_today=true&assigned_to={uuid}" -H "Authorization: Token {token}"
curl "https://your-domain.com/api/activities/?overdue=true" -H "Authorization: Token {token}"
```

Commit: `git add . && git commit -m "feat: activity app — ViewSet, filters, soft delete, instantiate endpoint"`

---

### Task A.2 — ActivityLog signal

**Files:**
- Create/modify: `~/ics/activity/signals.py`
- Modify: `~/ics/activity/apps.py`

```python
# activity/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Activity, ActivityLog


@receiver(post_save, sender=Activity)
def log_activity_creation(sender, instance, created, **kwargs):
    """Log Activity creation event."""
    if created:
        ActivityLog.objects.create(
            activity=instance,
            tenant=instance.tenant,
            created_by=instance.created_by,
            event_type='created',
            new_value=instance.title
        )
```

```python
# activity/apps.py
from django.apps import AppConfig


class ActivityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'activity'

    def ready(self):
        import activity.signals  # noqa: F401
```

Commit: `git add . && git commit -m "feat: activity signals — log creation on save"`

---

### Task A.3 — Calendar app scaffold + aggregation endpoint

**Files:**
- Create: `~/ics/calendar_app/` (Django app — named `calendar_app` to avoid
  collision with Python's built-in `calendar` module)
- Modify: `~/ics/ics_project/settings/base.py`
- Modify: `~/ics/ics_project/urls.py`

**Step 1:** Scaffold the app:

```bash
cd ~/ics && python manage.py startapp calendar_app
```

**Step 2:** Add to `INSTALLED_APPS`:

```python
'calendar_app',
```

**Step 3:** Create `calendar_app/service.py` — aggregation logic:

```python
# calendar_app/service.py
from django.utils.dateparse import parse_datetime
from activity.models import Activity


def get_calendar_events(user, from_date, to_date, tenant_id=None,
                        activity_type=None, source_app=None):
    """
    Aggregate Activity objects with scheduled_at or due_at in range.
    Scoped to the requesting user's tenant memberships + personal activities.
    Returns a list of CalendarEvent dicts sorted by scheduled_at / due_at.
    """
    user_tenant_ids = list(
        user.userpermission_set.filter(is_active=True).values_list('tenant_id', flat=True)
    )

    qs = Activity.objects.filter(deleted_at__isnull=True).filter(
        # Personal activities
        models_Q(created_by=user, tenant__isnull=True) |
        # Tenant activities the user can see
        models_Q(tenant_id__in=user_tenant_ids)
    )

    # Date range filter — match either scheduled_at OR due_at in range
    qs = qs.filter(
        models_Q(scheduled_at__date__gte=from_date, scheduled_at__date__lte=to_date) |
        models_Q(due_at__date__gte=from_date, due_at__date__lte=to_date)
    )

    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)
    if activity_type:
        qs = qs.filter(activity_type=activity_type)
    if source_app:
        qs = qs.filter(metadata__source_app=source_app)

    events = []
    for activity in qs.order_by('scheduled_at', 'due_at'):
        events.append({
            'id': str(activity.id),
            'source_type': 'activity',
            'source_app': activity.metadata.get('source_app', 'activity'),
            'title': activity.title,
            'scheduled_at': activity.scheduled_at.isoformat() if activity.scheduled_at else None,
            'due_at': activity.due_at.isoformat() if activity.due_at else None,
            'activity_type': activity.activity_type,
            'record_type': None,
            'tenant_id': str(activity.tenant_id) if activity.tenant_id else None,
            'status': activity.status,
            'kgs_pillar': activity.kgs_pillar,
            'kgs_pathway': activity.kgs_pathway,
        })

    return events


# Import Q here to avoid naming collision
from django.db.models import Q as models_Q
```

**Step 4:** Create `calendar_app/views.py`:

```python
# calendar_app/views.py
from datetime import date, timedelta
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as http_status
from .service import get_calendar_events


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def calendar_events(request):
    """
    GET /api/calendar/events/
    Query params:
      from        ISO date (default: today)
      to          ISO date (default: today + 30 days)
      tenant_id   UUID (optional)
      activity_type (optional)
      source_app  (optional)
    """
    from_str = request.query_params.get('from')
    to_str = request.query_params.get('to')
    tenant_id = request.query_params.get('tenant_id')
    activity_type = request.query_params.get('activity_type')
    source_app = request.query_params.get('source_app')

    from_date = parse_date(from_str) if from_str else date.today()
    to_date = parse_date(to_str) if to_str else from_date + timedelta(days=30)

    if from_date > to_date:
        return Response(
            {"detail": "'from' must be before or equal to 'to'."},
            status=http_status.HTTP_400_BAD_REQUEST
        )

    events = get_calendar_events(
        user=request.user,
        from_date=from_date,
        to_date=to_date,
        tenant_id=tenant_id,
        activity_type=activity_type,
        source_app=source_app,
    )

    return Response({'events': events, 'count': len(events)})
```

**Step 5:** Create `calendar_app/urls.py`:

```python
# calendar_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('events/', views.calendar_events, name='calendar-events'),
]
```

**Step 6:** Include in main `urls.py`:

```python
path('api/calendar/', include('calendar_app.urls')),
```

**Step 7:** Verify:

```bash
curl "https://your-domain.com/api/calendar/events/?from=2026-04-08&to=2026-04-30" \
  -H "Authorization: Token {token}"
# Expected: {"events": [...], "count": N}
```

Commit: `git add . && git commit -m "feat: calendar app — aggregation endpoint (Activity table, MVP scope)"`

---

## Phase B — Django Views + URL Routing

**Exit criteria:** All Activity App URL routes resolve. `views.py` and `api_views.py`
are split. `base_activity.html` loads HTMX and `activity.css`. No template content
yet — 200 responses with empty base template suffice.

---

### Task B.1 — URL structure + views/api_views split

**Files:**
- Create: `~/ics/activity/views.py` (Django template views)
- Rename existing DRF views to: `~/ics/activity/api_views.py`
- Modify: `~/ics/activity/urls.py`

```python
# activity/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views, views

router = DefaultRouter()
router.register(r'activities', api_views.ActivityViewSet, basename='activity')

urlpatterns = [
    # API (DRF — consumed by HTMX + Paraclete)
    path('api/', include(router.urls)),
    path('api/activity/health/', api_views.health, name='activity-health'),

    # Django template views (UI)
    path('activity/', views.my_activities, name='activity-home'),
    path('activity/ministry/', views.ministry, name='activity-ministry'),
    path('activity/ministry/assigned/', views.assigned_to_me, name='activity-assigned'),
    path('activity/ministry/events/', views.ministry_events, name='activity-events'),
    path('activity/create/', views.activity_create, name='activity-create'),
    path('activity/<uuid:activity_id>/', views.activity_detail, name='activity-detail'),
    path('activity/<uuid:activity_id>/edit/', views.activity_edit, name='activity-edit'),
    path('activity/templates/', views.template_list, name='activity-templates'),
    path('activity/gifts/', views.gifts_register, name='activity-gifts'),
    path('activity/team-gifts/', views.team_gifts, name='activity-team-gifts'),

    # HTMX partial endpoints (return HTML fragments)
    path('activity/htmx/status/<uuid:activity_id>/', views.htmx_status_update, name='htmx-activity-status'),
    path('activity/htmx/progress/<uuid:activity_id>/', views.htmx_progress_update, name='htmx-activity-progress'),
    path('activity/htmx/create/', views.htmx_create_activity, name='htmx-activity-create'),
    path('activity/htmx/link-record/<uuid:activity_id>/', views.htmx_link_record, name='htmx-link-record'),
    path('activity/htmx/record-search/', views.htmx_record_search, name='htmx-record-search'),
    path('activity/htmx/template-search/', views.htmx_template_search, name='htmx-template-search'),
    path('activity/htmx/instantiate/<uuid:template_id>/', views.htmx_instantiate_template, name='htmx-instantiate'),
    path('activity/htmx/gift/add/', views.htmx_add_gift, name='htmx-add-gift'),
    path('activity/htmx/gift/<uuid:gift_id>/archive/', views.htmx_archive_gift, name='htmx-archive-gift'),
]
```

**Step 2:** Create stub `activity/views.py` with all view functions returning a
simple render to confirm routing:

```python
# activity/views.py — stubs (content added in Phases C–F)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.http import require_POST


@login_required
def my_activities(request):
    return render(request, 'activity/my_activities.html', {})

@login_required
def ministry(request):
    return render(request, 'activity/ministry.html', {})

@login_required
def assigned_to_me(request):
    return render(request, 'activity/assigned_to_me.html', {})

@login_required
def ministry_events(request):
    return render(request, 'activity/ministry_events.html', {})

@login_required
def activity_create(request):
    return render(request, 'activity/activity_form.html', {})

@login_required
def activity_detail(request, activity_id):
    return render(request, 'activity/activity_detail.html', {})

@login_required
def activity_edit(request, activity_id):
    return render(request, 'activity/activity_form.html', {})

@login_required
def template_list(request):
    return render(request, 'activity/template_list.html', {})

@login_required
def gifts_register(request):
    return render(request, 'activity/gifts_register.html', {})

@login_required
def team_gifts(request):
    return render(request, 'activity/team_gifts.html', {})

# HTMX stubs
@login_required
def htmx_status_update(request, activity_id):
    return HttpResponse('')

@login_required
def htmx_progress_update(request, activity_id):
    return HttpResponse('')

@login_required
def htmx_create_activity(request):
    return HttpResponse('')

@login_required
def htmx_link_record(request, activity_id):
    return HttpResponse('')

@login_required
def htmx_record_search(request):
    return HttpResponse('')

@login_required
def htmx_template_search(request):
    return HttpResponse('')

@login_required
def htmx_instantiate_template(request, template_id):
    return HttpResponse('')

@login_required
def htmx_add_gift(request):
    return HttpResponse('')

@login_required
def htmx_archive_gift(request, gift_id):
    return HttpResponse('')
```

Commit: `git add . && git commit -m "feat: activity app — URL structure, views/api_views split, all routes resolve"`

---

### Task B.2 — Base activity template + CSS

**Files:**
- Create: `~/ics/activity/templates/activity/base_activity.html`
- Create: `~/ics/frontend/assets/css/activity.css`

```html
<!-- activity/templates/activity/base_activity.html -->
{% extends "base.html" %}
{% load static %}

{% block extra_css %}
  <link rel="stylesheet" href="{% static 'css/activity.css' %}">
{% endblock %}

{% block extra_scripts %}
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
{% endblock %}

{% block content %}
<div class="activity-shell">

  <!-- Surface tab row -->
  <nav class="activity-tab-row">
    <a href="{% url 'activity-home' %}"
       class="activity-tab {% if request.resolver_match.url_name == 'activity-home' %}active{% endif %}">
      My Activities
    </a>
    <a href="{% url 'activity-ministry' %}"
       class="activity-tab {% if 'ministry' in request.resolver_match.url_name %}active{% endif %}">
      Ministry
    </a>
  </nav>

  <!-- Page content injected here by child templates -->
  {% block activity_content %}{% endblock %}

</div>
{% endblock %}
```

**`activity.css`** — mobile-first styles using platform CSS variables:

```css
/* activity.css — Activity App styles */

/* ── Shell ──────────────────────────────────────────────── */
.activity-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--color-bg);
}

/* ── Tab row ─────────────────────────────────────────────── */
.activity-tab-row {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
  position: sticky;
  top: var(--navbar-height, 56px);
  z-index: 10;
}
.activity-tab {
  flex: 1;
  text-align: center;
  padding: 12px 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
  text-decoration: none;
  border-bottom: 2px solid transparent;
  transition: color 0.15s, border-color 0.15s;
}
.activity-tab.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

/* ── Activity cards ──────────────────────────────────────── */
.activity-card {
  background: var(--color-surface);
  border-radius: var(--radius-md, 12px);
  padding: 16px;
  margin: 12px 16px;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.activity-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.activity-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
}
.activity-meta {
  font-size: 12px;
  color: var(--color-text-secondary);
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

/* ── Type badge ───────────────────────────────────────────── */
.type-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 100px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.type-badge.task     { background: var(--color-blue-tint); color: var(--color-blue); }
.type-badge.habit    { background: var(--color-green-tint); color: var(--color-green); }
.type-badge.goal     { background: var(--color-purple-tint); color: var(--color-purple); }
.type-badge.event    { background: var(--color-orange-tint); color: var(--color-orange); }
.type-badge.campaign { background: var(--color-red-tint); color: var(--color-red); }
.type-badge.project  { background: var(--color-teal-tint); color: var(--color-teal); }
.type-badge.skill    { background: var(--color-yellow-tint); color: var(--color-yellow-dark); }

/* ── Status controls ─────────────────────────────────────── */
.status-controls {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  flex-wrap: wrap;
}
.btn-status {
  padding: 6px 14px;
  border-radius: 100px;
  border: 1px solid var(--color-border);
  background: transparent;
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background 0.1s, color 0.1s;
}
.btn-status:hover,
.btn-status.active {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}

/* ── Progress bar ────────────────────────────────────────── */
.progress-bar-wrap {
  background: var(--color-border);
  border-radius: 100px;
  height: 6px;
  overflow: hidden;
}
.progress-bar {
  height: 100%;
  background: var(--color-primary);
  border-radius: 100px;
  transition: width 0.3s ease;
}

/* ── Campaign / project group ────────────────────────────── */
.campaign-group {
  margin: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md, 12px);
  overflow: hidden;
}
.campaign-group-header {
  background: var(--color-surface-alt, var(--color-surface));
  padding: 14px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--color-border);
}
.campaign-group-header h3 {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}
.campaign-tasks {
  display: flex;
  flex-direction: column;
}
.campaign-tasks .activity-card {
  margin: 0;
  border-radius: 0;
  border-bottom: 1px solid var(--color-border);
  box-shadow: none;
}
.campaign-tasks .activity-card:last-child {
  border-bottom: none;
}

/* ── Due date indicators ─────────────────────────────────── */
.due-label {
  font-size: 12px;
  font-weight: 600;
}
.due-label.overdue  { color: var(--color-red, #d93025); }
.due-label.due-today { color: var(--color-orange, #f29900); }

/* ── Empty states ────────────────────────────────────────── */
.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: var(--color-text-secondary);
}
.empty-state p { font-size: 15px; margin-bottom: 16px; }

/* ── Activity form ───────────────────────────────────────── */
.activity-form {
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
}
.form-control {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm, 8px);
  padding: 10px 12px;
  font-size: 15px;
  background: var(--color-surface);
  color: var(--color-text);
  width: 100%;
  box-sizing: border-box;
}
.form-control:focus {
  border-color: var(--color-primary);
  outline: none;
}

/* ── Recurrence radio group ──────────────────────────────── */
.recurrence-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.recurrence-group label {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: 100px;
  cursor: pointer;
  font-size: 13px;
  color: var(--color-text);
}
.recurrence-group input[type="radio"]:checked + span,
.recurrence-group label:has(input:checked) {
  background: var(--color-primary-tint, #e8f0fe);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

/* ── Record link typeahead ───────────────────────────────── */
.record-search-wrap {
  position: relative;
}
.record-search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-top: none;
  border-radius: 0 0 var(--radius-sm, 8px) var(--radius-sm, 8px);
  max-height: 200px;
  overflow-y: auto;
  z-index: 50;
}
.record-search-results .record-option {
  padding: 10px 12px;
  cursor: pointer;
  font-size: 14px;
  border-bottom: 1px solid var(--color-border);
}
.record-search-results .record-option:last-child { border-bottom: none; }
.record-search-results .record-option:hover {
  background: var(--color-bg);
}

/* ── Gifts register ──────────────────────────────────────── */
.gift-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md, 12px);
  padding: 14px 16px;
  margin: 8px 16px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}
.gift-card-body { flex: 1; }
.gift-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
}
.gift-meta {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 3px;
}
.gift-competence {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-primary);
}

/* ── Desktop breakpoint ──────────────────────────────────── */
@media (min-width: 768px) {
  .activity-card { margin: 12px 24px; }
  .campaign-group { margin: 16px 24px; }
  .activity-form { max-width: 640px; margin: 0 auto; padding: 32px 24px; }
}
```

Commit: `git add . && git commit -m "feat: activity base template + activity.css"`

---

## Phase C — My Activities Surface (UI)

**Exit criteria:** A member can view their personal activities (tasks, habits, goals),
create new ones, mark complete via HTMX, and see their Learn enrolments as read-only
progress cards.

---

### Task C.1 — My Activities view + template

**Files:**
- Modify: `~/ics/activity/views.py`
- Create: `~/ics/activity/templates/activity/my_activities.html`

```python
# activity/views.py — my_activities
from django.utils import timezone

@login_required
def my_activities(request):
    user = request.user
    now = timezone.now()

    # Personal activities (no tenant) — exclude templates and programme types
    personal_qs = Activity.objects.filter(
        created_by=user,
        tenant__isnull=True,
        deleted_at__isnull=True,
        metadata__is_template=False,
    ).exclude(activity_type='programme').order_by('due_at', '-created_at')

    tasks  = personal_qs.filter(activity_type='task',
                                status__in=['pending', 'in_progress'])
    habits = personal_qs.filter(activity_type='habit',
                                status__in=['pending', 'in_progress'])
    goals  = personal_qs.filter(activity_type='goal',
                                status__in=['pending', 'in_progress'])

    # Learn enrolments — read-only programme activities
    learn_enrolments = Activity.objects.filter(
        assigned_to=user,
        activity_type='programme',
        status='in_progress',
        metadata__source_app='learn',
        deleted_at__isnull=True,
    ).order_by('-created_at')

    completed = personal_qs.filter(status='completed').order_by('-updated_at')[:5]

    return render(request, 'activity/my_activities.html', {
        'tasks': tasks,
        'habits': habits,
        'goals': goals,
        'learn_enrolments': learn_enrolments,
        'completed': completed,
        'now': now,
    })
```

```html
<!-- activity/templates/activity/my_activities.html -->
{% extends "activity/base_activity.html" %}

{% block activity_content %}
<div class="activity-page-header">
  <h1>My Activities</h1>
  <a href="{% url 'activity-create' %}" class="btn-primary">+ New</a>
</div>

<!-- Learn enrolments (read-only) -->
{% if learn_enrolments %}
<section class="activity-section">
  <h2 class="section-title">Learning</h2>
  {% for enrolment in learn_enrolments %}
  <div class="activity-card">
    <div class="activity-card-header">
      <span class="activity-title">{{ enrolment.title }}</span>
      <span class="type-badge" style="background:var(--color-blue-tint);color:var(--color-blue)">
        Programme
      </span>
    </div>
    <div class="progress-bar-wrap">
      <div class="progress-bar" style="width:{{ enrolment.progress }}%"></div>
    </div>
    <span class="activity-meta">{{ enrolment.progress }}% complete</span>
  </div>
  {% endfor %}
</section>
{% endif %}

<!-- Tasks -->
{% if tasks %}
<section class="activity-section">
  <h2 class="section-title">Tasks</h2>
  {% for activity in tasks %}
    {% include "activity/partials/activity_card.html" with activity=activity %}
  {% endfor %}
</section>
{% endif %}

<!-- Habits -->
{% if habits %}
<section class="activity-section">
  <h2 class="section-title">Habits</h2>
  {% for activity in habits %}
    {% include "activity/partials/activity_card.html" with activity=activity show_recurrence=True %}
  {% endfor %}
</section>
{% endif %}

<!-- Goals -->
{% if goals %}
<section class="activity-section">
  <h2 class="section-title">Goals</h2>
  {% for activity in goals %}
    {% include "activity/partials/activity_card.html" with activity=activity show_progress=True %}
  {% endfor %}
</section>
{% endif %}

<!-- Gifts register link -->
<div style="margin: 8px 16px 24px;">
  <a href="{% url 'activity-gifts' %}" class="btn-secondary" style="width:100%;display:block;text-align:center;">
    My Gifts & Skills Register
  </a>
</div>

{% if not tasks and not habits and not goals and not learn_enrolments %}
<div class="empty-state">
  <p>Nothing here yet. Start by adding a task, habit, or goal.</p>
  <a href="{% url 'activity-create' %}" class="btn-primary">Add your first activity</a>
</div>
{% endif %}

{% endblock %}
```

---

### Task C.2 — Activity card partial + HTMX status update

**Files:**
- Create: `~/ics/activity/templates/activity/partials/activity_card.html`
- Modify: `~/ics/activity/views.py` (htmx_status_update)

```html
<!-- activity/templates/activity/partials/activity_card.html -->
<div class="activity-card" id="activity-{{ activity.id }}">
  <div class="activity-card-header">
    <span class="activity-title">{{ activity.title }}</span>
    <span class="type-badge {{ activity.activity_type }}">{{ activity.activity_type }}</span>
  </div>

  {% if activity.description %}
  <p class="activity-meta">{{ activity.description|truncatechars:100 }}</p>
  {% endif %}

  <div class="activity-meta">
    {% if activity.due_at %}
      {% if activity.due_at < now %}
        <span class="due-label overdue">Overdue · {{ activity.due_at|date:"d M" }}</span>
      {% elif activity.due_at|date:"Y-m-d" == now|date:"Y-m-d" %}
        <span class="due-label due-today">Due today</span>
      {% else %}
        <span>Due {{ activity.due_at|date:"d M" }}</span>
      {% endif %}
    {% endif %}
    {% if show_recurrence and activity.recurrence != 'none' %}
      <span>{{ activity.get_recurrence_display }}</span>
    {% endif %}
    {% if activity.kgs_pathway %}
      <span>{{ activity.get_kgs_pathway_display }}</span>
    {% endif %}
  </div>

  {% if show_progress %}
  <div class="progress-bar-wrap" style="margin-top:4px">
    <div class="progress-bar" style="width:{{ activity.progress }}%"></div>
  </div>
  <span class="activity-meta">{{ activity.progress }}%</span>
  {% endif %}

  <!-- HTMX status controls -->
  <div class="status-controls"
       hx-target="#activity-{{ activity.id }}"
       hx-swap="outerHTML">
    {% if activity.status == 'pending' %}
      <button class="btn-status"
              hx-post="{% url 'htmx-activity-status' activity.id %}"
              hx-vals='{"status": "in_progress"}'>
        Start
      </button>
      <button class="btn-status"
              hx-post="{% url 'htmx-activity-status' activity.id %}"
              hx-vals='{"status": "deferred"}'>
        Defer
      </button>
    {% elif activity.status == 'in_progress' %}
      <button class="btn-status active"
              hx-post="{% url 'htmx-activity-status' activity.id %}"
              hx-vals='{"status": "completed"}'>
        ✓ Mark Complete
      </button>
      <button class="btn-status"
              hx-post="{% url 'htmx-activity-status' activity.id %}"
              hx-vals='{"status": "deferred"}'>
        Defer
      </button>
    {% elif activity.status == 'deferred' %}
      <button class="btn-status"
              hx-post="{% url 'htmx-activity-status' activity.id %}"
              hx-vals='{"status": "pending"}'>
        Restore
      </button>
    {% endif %}
    <a href="{% url 'activity-detail' activity.id %}" class="btn-status">View</a>
  </div>
</div>
```

```python
# activity/views.py — htmx_status_update
from django.views.decorators.http import require_POST
from django.utils import timezone

@login_required
@require_POST
def htmx_status_update(request, activity_id):
    """
    HTMX endpoint: update activity status.
    Returns updated activity card HTML fragment.
    """
    activity = get_object_or_404(
        Activity,
        id=activity_id,
        deleted_at__isnull=True
    )

    # Permission: owner or Level 3+ steward in the same tenant
    user = request.user
    user_level = getattr(getattr(user, 'userprofile', None), 'competence_level', 0)
    is_owner = activity.created_by == user
    is_assignee = activity.assigned_to == user
    is_steward = user_level >= 3

    if not (is_owner or is_assignee or is_steward):
        return HttpResponse(status=403)

    new_status = request.POST.get('status')
    allowed = ['pending', 'in_progress', 'completed', 'deferred', 'cancelled']
    if new_status not in allowed:
        return HttpResponse(status=400)

    old_status = activity.status
    activity.status = new_status
    if new_status == 'completed':
        activity.progress = 100
    activity.save(update_fields=['status', 'progress', 'updated_at'])

    ActivityLog.objects.create(
        activity=activity,
        tenant=activity.tenant,
        created_by=user,
        event_type='status_changed',
        previous_value=old_status,
        new_value=new_status
    )

    now = timezone.now()
    return render(request, 'activity/partials/activity_card.html', {
        'activity': activity,
        'now': now,
    })
```

Commit: `git add . && git commit -m "feat: my activities view — personal tasks, habits, goals, learn cards, HTMX status"`

---

### Task C.3 — Activity create form

**Files:**
- Modify: `~/ics/activity/views.py`
- Create: `~/ics/activity/templates/activity/activity_form.html`
- Create: `~/ics/activity/templates/activity/partials/record_search_results.html`
- Create: `~/ics/activity/templates/activity/partials/template_search_results.html`

```python
# activity/views.py — activity_create
@login_required
def activity_create(request):
    user = request.user
    user_level = getattr(getattr(user, 'userprofile', None), 'competence_level', 0)

    if request.method == 'POST':
        title        = request.POST.get('title', '').strip()
        description  = request.POST.get('description', '').strip()
        activity_type = request.POST.get('activity_type', 'task')
        kgs_pillar   = request.POST.get('kgs_pillar') or None
        kgs_pathway  = request.POST.get('kgs_pathway') or None
        due_at_str   = request.POST.get('due_at') or None
        scheduled_at_str = request.POST.get('scheduled_at') or None
        recurrence   = request.POST.get('recurrence', 'none')
        assigned_to_id = request.POST.get('assigned_to') or None
        tenant_id    = request.POST.get('tenant_id') or None
        linked_record_id = request.POST.get('linked_record_id') or None

        if not title:
            return render(request, 'activity/activity_form.html', {
                'error': 'Title is required.',
                'user_level': user_level,
                'post': request.POST,
            })

        # Resolve tenant
        tenant = None
        if tenant_id:
            from tenants.models import Tenant
            tenant = Tenant.objects.filter(id=tenant_id).first()

        # Resolve assigned_to
        from django.contrib.auth import get_user_model
        User = get_user_model()
        assigned_to = None
        if assigned_to_id:
            if user_level < 3:
                return render(request, 'activity/activity_form.html', {
                    'error': 'Only stewards (Level 3+) may assign activities.',
                    'user_level': user_level,
                    'post': request.POST,
                })
            assigned_to = User.objects.filter(id=assigned_to_id).first()

        # Parse dates
        from django.utils.dateparse import parse_datetime, parse_date
        due_at = parse_datetime(due_at_str) if due_at_str else None
        scheduled_at = parse_datetime(scheduled_at_str) if scheduled_at_str else None

        activity = Activity.objects.create(
            created_by=user,
            tenant=tenant,
            activity_type=activity_type,
            title=title,
            description=description or None,
            kgs_pillar=kgs_pillar,
            kgs_pathway=kgs_pathway,
            due_at=due_at,
            scheduled_at=scheduled_at,
            recurrence=recurrence,
            assigned_to=assigned_to,
            status='pending',
            metadata={'source_app': 'activity', 'is_template': False},
        )

        # Create record link if provided
        if linked_record_id:
            _create_activity_record_link(activity, linked_record_id, user)

        return redirect('activity-detail', activity_id=activity.id)

    # GET — determine available type options by level
    available_types = ['task', 'habit', 'goal', 'reminder']
    if user_level >= 1:
        available_types.append('skill')
    if user_level >= 3:
        available_types.extend(['event', 'campaign', 'project'])

    # User's tenants for tenant selector
    user_tenants = user.userpermission_set.filter(
        is_active=True
    ).select_related('tenant')

    return render(request, 'activity/activity_form.html', {
        'available_types': available_types,
        'user_tenants': user_tenants,
        'user_level': user_level,
    })


def _create_activity_record_link(activity, record_id, user):
    """
    Create a Relationship between this Activity (via its Record representation)
    and the target Record, per Part 3.3 of v5 data contract.
    """
    from records.models import Relationship, Record
    import uuid

    # Determine relationship_type by activity_type (v5 Part 3.3 rules)
    tracks_types = {'task', 'habit', 'goal', 'reminder'}
    aligns_types = {'campaign', 'event', 'project', 'skill'}

    rel_type = 'tracks' if activity.activity_type in tracks_types else 'aligns_with'

    target_record = Record.objects.filter(id=record_id).first()
    if not target_record:
        return

    # Find or create a Record representation for this Activity
    # (using activity family, matching activity_type)
    activity_record = Record.objects.filter(
        metadata__activity_id=str(activity.id)
    ).first()

    if not activity_record:
        activity_record = Record.objects.create(
            tenant=activity.tenant,
            created_by=user,
            record_class='personal' if not activity.tenant else 'organizational',
            record_family='activity',
            record_type=activity.activity_type,
            title=activity.title,
            status='active',
            origin='user',
            metadata={
                'source_app': 'activity',
                'activity_id': str(activity.id),
            },
        )

    Relationship.objects.create(
        tenant=activity.tenant,
        created_by=user,
        from_record_id=activity_record.id,
        to_record_id=target_record.id,
        relationship_type=rel_type,
        direction='directed',
    )
```

```html
<!-- activity/templates/activity/activity_form.html -->
{% extends "activity/base_activity.html" %}

{% block activity_content %}
<div class="activity-form">
  <h1 style="font-size:20px;font-weight:700;margin-bottom:4px;">
    {% if activity %}Edit Activity{% else %}New Activity{% endif %}
  </h1>

  {% if error %}
  <div class="form-error" style="color:var(--color-red);font-size:14px;padding:10px;
    border:1px solid var(--color-red);border-radius:8px;background:var(--color-red-tint)">
    {{ error }}
  </div>
  {% endif %}

  <form method="post" action="{% if activity %}{% url 'activity-edit' activity.id %}{% else %}{% url 'activity-create' %}{% endif %}">
    {% csrf_token %}

    <!-- Start from template -->
    <div class="form-group">
      <label>Start from a template (optional)</label>
      <input type="text" id="template-search-input" class="form-control"
             placeholder="Search templates…"
             hx-get="{% url 'htmx-template-search' %}"
             hx-trigger="keyup changed delay:300ms"
             hx-target="#template-search-results"
             hx-include="[name='template_q']"
             name="template_q"
             autocomplete="off">
      <div id="template-search-results" class="record-search-results" style="display:none"></div>
      <input type="hidden" name="template_id" id="template-id-input">
    </div>

    <!-- Title -->
    <div class="form-group">
      <label for="title">Title <span style="color:var(--color-red)">*</span></label>
      <input type="text" name="title" id="title" class="form-control"
             value="{{ post.title|default:activity.title|default:'' }}"
             placeholder="What do you need to do?" required>
    </div>

    <!-- Description -->
    <div class="form-group">
      <label for="description">Description</label>
      <textarea name="description" id="description" class="form-control"
                rows="3" placeholder="Optional details…">{{ post.description|default:activity.description|default:'' }}</textarea>
    </div>

    <!-- Type -->
    <div class="form-group">
      <label for="activity_type">Type</label>
      <select name="activity_type" id="activity_type" class="form-control">
        {% for t in available_types %}
        <option value="{{ t }}"
          {% if post.activity_type == t or activity.activity_type == t %}selected{% endif %}>
          {{ t|capfirst }}
        </option>
        {% endfor %}
      </select>
    </div>

    <!-- Recurrence -->
    <div class="form-group">
      <label>Recurrence</label>
      <div class="recurrence-group">
        {% for val, label in recurrence_options %}
        <label>
          <input type="radio" name="recurrence" value="{{ val }}"
            {% if post.recurrence == val or activity.recurrence == val %}checked{% endif %}
            {% if not post and not activity and val == 'none' %}checked{% endif %}>
          <span>{{ label }}</span>
        </label>
        {% endfor %}
      </div>
    </div>

    <!-- KGS alignment -->
    <div class="form-group">
      <label for="kgs_pathway">KGS Pathway</label>
      <select name="kgs_pathway" id="kgs_pathway" class="form-control">
        <option value="">— None —</option>
        <option value="new_life">New Life</option>
        <option value="spiritual_formation">Spiritual Formation</option>
        <option value="community_life">Community Life</option>
        <option value="service">Service</option>
        <option value="leadership">Leadership</option>
        <option value="learning">Learning</option>
        <option value="mission">Mission</option>
        <option value="apostolic_stewardship">Apostolic Stewardship</option>
      </select>
    </div>

    <!-- Due date -->
    <div class="form-group">
      <label for="due_at">Due date</label>
      <input type="datetime-local" name="due_at" id="due_at" class="form-control"
             value="{{ post.due_at|default:'' }}">
    </div>

    <!-- Scheduled at (for events) -->
    <div class="form-group" id="scheduled-at-group" style="display:none">
      <label for="scheduled_at">Scheduled date &amp; time</label>
      <input type="datetime-local" name="scheduled_at" id="scheduled_at" class="form-control"
             value="{{ post.scheduled_at|default:'' }}">
    </div>

    <!-- Tenant (ministry activities) -->
    {% if user_tenants %}
    <div class="form-group">
      <label for="tenant_id">Ministry context (optional)</label>
      <select name="tenant_id" id="tenant_id" class="form-control">
        <option value="">Personal (no team)</option>
        {% for up in user_tenants %}
        <option value="{{ up.tenant.id }}"
          {% if post.tenant_id == up.tenant.id|stringformat:"s" %}selected{% endif %}>
          {{ up.tenant.name }}
        </option>
        {% endfor %}
      </select>
    </div>
    {% endif %}

    <!-- Assign to (Level 3+ only) -->
    {% if user_level >= 3 %}
    <div class="form-group">
      <label for="assigned_to">Assign to</label>
      <input type="text" class="form-control" placeholder="Search team members…"
             autocomplete="off">
      <input type="hidden" name="assigned_to" id="assigned_to_input"
             value="{{ post.assigned_to|default:'' }}">
      <small style="color:var(--color-text-secondary);font-size:12px">
        Leave blank to assign to yourself or leave unassigned (team-visible)
      </small>
    </div>
    {% endif %}

    <!-- Link to Record -->
    <div class="form-group">
      <label>Link to a record (optional)</label>
      <div class="record-search-wrap">
        <input type="text" class="form-control" id="record-search-input"
               placeholder="Search records…"
               hx-get="{% url 'htmx-record-search' %}"
               hx-trigger="keyup changed delay:300ms"
               hx-target="#record-search-results"
               hx-include="[name='record_q']"
               name="record_q"
               autocomplete="off">
        <div id="record-search-results" class="record-search-results"></div>
      </div>
      <input type="hidden" name="linked_record_id" id="linked-record-id">
      <div id="linked-record-display" style="font-size:13px;color:var(--color-primary);margin-top:4px"></div>
    </div>

    <button type="submit" class="btn-primary" style="width:100%">
      {% if activity %}Save Changes{% else %}Create Activity{% endif %}
    </button>
  </form>
</div>

<script>
// Show scheduled_at field for event type
document.getElementById('activity_type').addEventListener('change', function() {
  const group = document.getElementById('scheduled-at-group');
  group.style.display = this.value === 'event' ? 'block' : 'none';
});
</script>
{% endblock %}
```

```python
# activity/views.py — add to create view's GET context
# (pass recurrence options)
'recurrence_options': [
    ('none', 'Once'), ('daily', 'Daily'),
    ('weekly', 'Weekly'), ('monthly', 'Monthly')
],
```

```python
# activity/views.py — htmx_record_search
@login_required
def htmx_record_search(request):
    """HTMX typeahead: search records for linking."""
    from records.models import Record
    query = request.GET.get('record_q', '').strip()
    if len(query) < 2:
        return HttpResponse('')

    user = request.user
    user_tenant_ids = user.userpermission_set.filter(
        is_active=True
    ).values_list('tenant_id', flat=True)

    records = Record.objects.filter(
        deleted_at__isnull=True,
        status='active',
    ).filter(
        models_Q(created_by=user) |
        models_Q(tenant_id__in=user_tenant_ids)
    ).filter(
        title__icontains=query
    )[:8]

    return render(request, 'activity/partials/record_search_results.html', {
        'records': records
    })
```

```python
# Import needed
from django.db.models import Q as models_Q
```

```html
<!-- activity/templates/activity/partials/record_search_results.html -->
{% if records %}
<div class="record-search-results" style="display:block">
  {% for record in records %}
  <div class="record-option"
       onclick="selectRecord('{{ record.id }}', '{{ record.title|escapejs }}')">
    {{ record.title }}
    <span style="color:var(--color-text-secondary);font-size:11px;margin-left:6px">
      {{ record.record_type }}
    </span>
  </div>
  {% endfor %}
</div>
<script>
function selectRecord(id, title) {
  document.getElementById('linked-record-id').value = id;
  document.getElementById('record-search-input').value = title;
  document.getElementById('linked-record-display').textContent = '✓ Linked: ' + title;
  document.getElementById('record-search-results').innerHTML = '';
}
</script>
{% endif %}
```

Commit: `git add . && git commit -m "feat: activity create form — all types, recurrence, record link typeahead"`

---

## Phase D — Ministry Surface + Assigned-to-Me Queue (UI)

**Exit criteria:** A disciple can see all tasks assigned to them. A steward can see
their team's campaign/project/task hierarchy. HTMX status updates work on the Ministry
surface identically to My Activities.

---

### Task D.1 — Ministry view + Assigned-to-me queue

**Files:**
- Modify: `~/ics/activity/views.py`
- Create: `~/ics/activity/templates/activity/ministry.html`
- Create: `~/ics/activity/templates/activity/assigned_to_me.html`
- Create: `~/ics/activity/templates/activity/ministry_events.html`

```python
# activity/views.py — ministry
@login_required
def ministry(request):
    user = request.user
    user_level = getattr(getattr(user, 'userprofile', None), 'competence_level', 0)
    now = timezone.now()

    user_tenant_ids = user.userpermission_set.filter(
        is_active=True
    ).values_list('tenant_id', flat=True)

    # Top-level campaigns and projects (no parent)
    campaigns = Activity.objects.filter(
        tenant_id__in=user_tenant_ids,
        activity_type__in=['campaign', 'project'],
        parent_activity__isnull=True,
        deleted_at__isnull=True,
        metadata__is_template=False,
        status__in=['pending', 'in_progress'],
    ).order_by('due_at', '-created_at')

    # Annotate child tasks on each campaign
    campaign_data = []
    for campaign in campaigns:
        tasks = Activity.objects.filter(
            parent_activity=campaign,
            activity_type='task',
            deleted_at__isnull=True,
            status__in=['pending', 'in_progress'],
        ).order_by('due_at')
        campaign_data.append({'campaign': campaign, 'tasks': tasks})

    # Unparented team tasks (no campaign/project parent)
    loose_tasks = Activity.objects.filter(
        tenant_id__in=user_tenant_ids,
        activity_type='task',
        parent_activity__isnull=True,
        deleted_at__isnull=True,
        status__in=['pending', 'in_progress'],
    ).order_by('due_at', '-created_at')

    return render(request, 'activity/ministry.html', {
        'campaign_data': campaign_data,
        'loose_tasks': loose_tasks,
        'user_level': user_level,
        'now': now,
    })


@login_required
def assigned_to_me(request):
    user = request.user
    now = timezone.now()

    assigned = Activity.objects.filter(
        assigned_to=user,
        tenant__isnull=False,
        deleted_at__isnull=True,
        status__in=['pending', 'in_progress'],
    ).select_related('parent_activity').order_by('due_at', '-created_at')

    # Group by parent (campaign/project) or no parent
    grouped = {}
    ungrouped = []
    for task in assigned:
        if task.parent_activity_id:
            key = task.parent_activity_id
            if key not in grouped:
                grouped[key] = {
                    'parent': task.parent_activity,
                    'tasks': []
                }
            grouped[key]['tasks'].append(task)
        else:
            ungrouped.append(task)

    return render(request, 'activity/assigned_to_me.html', {
        'grouped': grouped.values(),
        'ungrouped': ungrouped,
        'now': now,
    })


@login_required
def ministry_events(request):
    user = request.user
    now = timezone.now()

    user_tenant_ids = user.userpermission_set.filter(
        is_active=True
    ).values_list('tenant_id', flat=True)

    events = Activity.objects.filter(
        tenant_id__in=user_tenant_ids,
        activity_type='event',
        deleted_at__isnull=True,
        scheduled_at__gte=now,
    ).order_by('scheduled_at')

    return render(request, 'activity/ministry_events.html', {
        'events': events,
        'now': now,
    })
```

```html
<!-- activity/templates/activity/ministry.html -->
{% extends "activity/base_activity.html" %}

{% block activity_content %}
<div class="activity-page-header">
  <h1>Ministry</h1>
  {% if user_level >= 3 %}
  <a href="{% url 'activity-create' %}?type=campaign" class="btn-primary">+ Campaign</a>
  {% endif %}
</div>

<!-- Ministry sub-tabs -->
<div class="ministry-subtabs">
  <a href="{% url 'activity-assigned' %}"
     class="subtab">Assigned to Me</a>
  <a href="{% url 'activity-ministry' %}"
     class="subtab active">Team</a>
  <a href="{% url 'activity-events' %}"
     class="subtab">Events</a>
</div>

<!-- Campaign / project groups -->
{% for group in campaign_data %}
<div class="campaign-group">
  <div class="campaign-group-header">
    <h3>{{ group.campaign.title }}</h3>
    <div style="display:flex;align-items:center;gap:8px">
      <span class="type-badge {{ group.campaign.activity_type }}">
        {{ group.campaign.activity_type }}
      </span>
      {% if group.campaign.due_at %}
      <span class="due-label {% if group.campaign.due_at < now %}overdue{% endif %}">
        {{ group.campaign.due_at|date:"d M" }}
      </span>
      {% endif %}
    </div>
  </div>
  <div class="campaign-tasks">
    {% for task in group.tasks %}
      {% include "activity/partials/activity_card.html" with activity=task %}
    {% empty %}
    <div style="padding:14px 16px;color:var(--color-text-secondary);font-size:14px">
      No tasks yet.
      {% if user_level >= 3 %}
      <a href="{% url 'activity-create' %}?parent={{ group.campaign.id }}&type=task"
         style="color:var(--color-primary)">Add task</a>
      {% endif %}
    </div>
    {% endfor %}
  </div>
</div>
{% endfor %}

<!-- Loose tasks -->
{% if loose_tasks %}
<section class="activity-section" style="margin-top:8px">
  <h2 class="section-title">Unassigned Tasks</h2>
  {% for task in loose_tasks %}
    {% include "activity/partials/activity_card.html" with activity=task %}
  {% endfor %}
</section>
{% endif %}

{% if not campaign_data and not loose_tasks %}
<div class="empty-state">
  <p>No team activities yet.</p>
  {% if user_level >= 3 %}
  <a href="{% url 'activity-create' %}" class="btn-primary">Create a campaign</a>
  {% endif %}
</div>
{% endif %}
{% endblock %}
```

```html
<!-- activity/templates/activity/assigned_to_me.html -->
{% extends "activity/base_activity.html" %}

{% block activity_content %}
<div class="activity-page-header">
  <h1>Assigned to Me</h1>
</div>

<div class="ministry-subtabs">
  <a href="{% url 'activity-assigned' %}" class="subtab active">Assigned to Me</a>
  <a href="{% url 'activity-ministry' %}" class="subtab">Team</a>
  <a href="{% url 'activity-events' %}" class="subtab">Events</a>
</div>

{% for group in grouped %}
<div class="campaign-group">
  <div class="campaign-group-header">
    <h3>{{ group.parent.title }}</h3>
    <span class="type-badge {{ group.parent.activity_type }}">
      {{ group.parent.activity_type }}
    </span>
  </div>
  <div class="campaign-tasks">
    {% for task in group.tasks %}
      {% include "activity/partials/activity_card.html" with activity=task %}
    {% endfor %}
  </div>
</div>
{% endfor %}

{% if ungrouped %}
<section class="activity-section">
  <h2 class="section-title">Direct Assignments</h2>
  {% for task in ungrouped %}
    {% include "activity/partials/activity_card.html" with activity=task %}
  {% endfor %}
</section>
{% endif %}

{% if not grouped and not ungrouped %}
<div class="empty-state">
  <p>Nothing assigned to you right now.</p>
</div>
{% endif %}
{% endblock %}
```

```html
<!-- activity/templates/activity/ministry_events.html -->
{% extends "activity/base_activity.html" %}
{% load tz %}

{% block activity_content %}
<div class="activity-page-header">
  <h1>Events</h1>
  {% if user_level >= 3 %}
  <a href="{% url 'activity-create' %}?type=event" class="btn-primary">+ Event</a>
  {% endif %}
</div>

<div class="ministry-subtabs">
  <a href="{% url 'activity-assigned' %}" class="subtab">Assigned to Me</a>
  <a href="{% url 'activity-ministry' %}" class="subtab">Team</a>
  <a href="{% url 'activity-events' %}" class="subtab active">Events</a>
</div>

{% if events %}
  {% regroup events by scheduled_at|date:"Y-m-d" as events_by_date %}
  {% for date_group in events_by_date %}
  <div class="date-group-header">{{ date_group.grouper|date:"l, d F Y" }}</div>
  {% for event in date_group.list %}
  <div class="activity-card">
    <div class="activity-card-header">
      <span class="activity-title">{{ event.title }}</span>
      <span class="activity-meta">{{ event.scheduled_at|time:"H:i" }}</span>
    </div>
    {% if event.description %}
    <p class="activity-meta">{{ event.description|truncatechars:120 }}</p>
    {% endif %}
    {% if event.kgs_pathway %}
    <span class="activity-meta">{{ event.get_kgs_pathway_display }}</span>
    {% endif %}
    <div class="status-controls">
      <a href="{% url 'activity-detail' event.id %}" class="btn-status">View</a>
    </div>
  </div>
  {% endfor %}
  {% endfor %}
{% else %}
<div class="empty-state">
  <p>No upcoming events.</p>
  {% if user_level >= 3 %}
  <a href="{% url 'activity-create' %}" class="btn-primary">Create an event</a>
  {% endif %}
</div>
{% endif %}
{% endblock %}
```

Commit: `git add . && git commit -m "feat: ministry surface — team view, assigned-to-me queue, events dated list"`

---

## Phase E — Campaign Management + Activity Detail

**Exit criteria:** A steward can create a campaign, add nested tasks, assign to
team members. Any user can view an activity detail page. Completed activities
shown in a "Done" section.

---

### Task E.1 — Activity detail view

**Files:**
- Modify: `~/ics/activity/views.py`
- Create: `~/ics/activity/templates/activity/activity_detail.html`

```python
# activity/views.py — activity_detail
@login_required
def activity_detail(request, activity_id):
    user = request.user
    user_level = getattr(getattr(user, 'userprofile', None), 'competence_level', 0)

    activity = get_object_or_404(Activity, id=activity_id, deleted_at__isnull=True)

    # Permission check
    user_tenant_ids = list(user.userpermission_set.filter(
        is_active=True
    ).values_list('tenant_id', flat=True))

    is_owner = activity.created_by == user
    is_assignee = activity.assigned_to == user
    is_team_member = activity.tenant_id in user_tenant_ids if activity.tenant_id else False
    is_personal_visible = not activity.tenant_id and is_owner

    if not (is_owner or is_assignee or is_team_member or is_personal_visible):
        return render(request, 'activity/locked.html', status=403)

    # Child tasks
    child_tasks = Activity.objects.filter(
        parent_activity=activity,
        deleted_at__isnull=True,
    ).order_by('due_at', '-created_at')

    # Activity log
    logs = ActivityLog.objects.filter(
        activity=activity
    ).order_by('-created_at')[:10]

    # Linked records
    from records.models import Relationship, Record
    linked_relationships = Relationship.objects.filter(
        from_record__metadata__activity_id=str(activity_id),
        deleted_at__isnull=True,
    ).select_related('to_record')

    can_edit = is_owner or user_level >= 3

    return render(request, 'activity/activity_detail.html', {
        'activity': activity,
        'child_tasks': child_tasks,
        'logs': logs,
        'linked_relationships': linked_relationships,
        'can_edit': can_edit,
        'user_level': user_level,
        'now': timezone.now(),
    })
```

```html
<!-- activity/templates/activity/activity_detail.html -->
{% extends "activity/base_activity.html" %}

{% block activity_content %}
<div style="padding:16px">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
    <div>
      <span class="type-badge {{ activity.activity_type }}">{{ activity.activity_type }}</span>
      <h1 style="font-size:20px;font-weight:700;margin-top:6px">{{ activity.title }}</h1>
    </div>
    {% if can_edit %}
    <a href="{% url 'activity-edit' activity.id %}" class="btn-secondary" style="white-space:nowrap">
      Edit
    </a>
    {% endif %}
  </div>

  {% if activity.description %}
  <p style="font-size:15px;color:var(--color-text);margin-bottom:12px">
    {{ activity.description }}
  </p>
  {% endif %}

  <!-- Meta row -->
  <div class="activity-meta" style="margin-bottom:16px">
    <span>Status: <strong>{{ activity.get_status_display }}</strong></span>
    {% if activity.due_at %}
      <span>Due: {{ activity.due_at|date:"d M Y" }}</span>
    {% endif %}
    {% if activity.scheduled_at %}
      <span>Scheduled: {{ activity.scheduled_at|date:"d M Y, H:i" }}</span>
    {% endif %}
    {% if activity.assigned_to %}
      <span>Assigned to: {{ activity.assigned_to.get_full_name|default:activity.assigned_to.email }}</span>
    {% endif %}
    {% if activity.kgs_pathway %}
      <span>Pathway: {{ activity.get_kgs_pathway_display }}</span>
    {% endif %}
    {% if activity.recurrence != 'none' %}
      <span>Repeats: {{ activity.get_recurrence_display }}</span>
    {% endif %}
  </div>

  <!-- Progress bar (goals and programmes) -->
  {% if activity.activity_type in 'goal,programme' %}
  <div class="progress-bar-wrap" style="margin-bottom:12px">
    <div class="progress-bar" style="width:{{ activity.progress }}%"></div>
  </div>
  <span class="activity-meta">{{ activity.progress }}% complete</span>
  {% endif %}

  <!-- HTMX status controls -->
  <div class="status-controls"
       id="activity-status-{{ activity.id }}"
       hx-target="#activity-status-{{ activity.id }}"
       hx-swap="outerHTML">
    {% if activity.status == 'pending' %}
    <button class="btn-status"
            hx-post="{% url 'htmx-activity-status' activity.id %}"
            hx-vals='{"status":"in_progress"}'>
      Start
    </button>
    {% elif activity.status == 'in_progress' %}
    <button class="btn-status active"
            hx-post="{% url 'htmx-activity-status' activity.id %}"
            hx-vals='{"status":"completed"}'>
      ✓ Mark Complete
    </button>
    {% endif %}
  </div>

  <!-- Linked records -->
  {% if linked_relationships %}
  <section style="margin-top:24px">
    <h2 style="font-size:15px;font-weight:700;margin-bottom:8px">Linked Records</h2>
    {% for rel in linked_relationships %}
    <div style="padding:10px 12px;border:1px solid var(--color-border);border-radius:8px;
         margin-bottom:8px;font-size:14px">
      <span style="font-weight:600">{{ rel.to_record.title }}</span>
      <span style="color:var(--color-text-secondary);margin-left:8px;font-size:12px">
        {{ rel.to_record.record_type }} · {{ rel.relationship_type }}
      </span>
    </div>
    {% endfor %}
  </section>
  {% endif %}

  <!-- Child tasks -->
  {% if child_tasks %}
  <section style="margin-top:24px">
    <h2 style="font-size:15px;font-weight:700;margin-bottom:8px">Tasks</h2>
    {% for task in child_tasks %}
      {% include "activity/partials/activity_card.html" with activity=task %}
    {% endfor %}
  </section>
  {% endif %}
  {% if can_edit and activity.activity_type in 'campaign,project' %}
  <div style="margin-top:8px">
    <a href="{% url 'activity-create' %}?parent={{ activity.id }}&type=task"
       class="btn-secondary" style="width:100%;display:block;text-align:center">
      + Add Task
    </a>
  </div>
  {% endif %}

  <!-- Activity log -->
  {% if logs %}
  <section style="margin-top:24px">
    <h2 style="font-size:15px;font-weight:700;margin-bottom:8px">History</h2>
    {% for log in logs %}
    <div style="display:flex;gap:10px;padding:8px 0;border-bottom:1px solid var(--color-border);
         font-size:13px;color:var(--color-text-secondary)">
      <span style="white-space:nowrap">{{ log.created_at|date:"d M, H:i" }}</span>
      <span>{{ log.event_type|capfirst }}
        {% if log.previous_value and log.new_value %}
          · {{ log.previous_value }} → {{ log.new_value }}
        {% elif log.new_value %}
          · {{ log.new_value }}
        {% endif %}
      </span>
    </div>
    {% endfor %}
  </section>
  {% endif %}
</div>
{% endblock %}
```

Commit: `git add . && git commit -m "feat: activity detail — meta, status HTMX, child tasks, linked records, log"`

---

## Phase F — Templates + Gifts Register + Calendar UI Stub

**Exit criteria:** Level 4+ can create activity templates. Level 2+ can instantiate
them. Personal gifts register is functional. Team gifts view works for stewards.
Calendar backend passes smoke test.

---

### Task F.1 — Template list + HTMX instantiate

**Files:**
- Modify: `~/ics/activity/views.py`
- Create: `~/ics/activity/templates/activity/template_list.html`
- Create: `~/ics/activity/templates/activity/partials/template_search_results.html`

```python
# activity/views.py — template_list
@login_required
def template_list(request):
    user = request.user
    user_level = getattr(getattr(user, 'userprofile', None), 'competence_level', 0)

    user_tenant_ids = user.userpermission_set.filter(
        is_active=True
    ).values_list('tenant_id', flat=True)

    templates = Activity.objects.filter(
        tenant_id__in=user_tenant_ids,
        metadata__is_template=True,
        deleted_at__isnull=True,
    ).order_by('activity_type', 'title')

    return render(request, 'activity/template_list.html', {
        'templates': templates,
        'user_level': user_level,
    })


@login_required
def htmx_template_search(request):
    """HTMX: search templates for 'start from template' affordance."""
    query = request.GET.get('template_q', '').strip()
    if len(query) < 2:
        return HttpResponse('')

    user_tenant_ids = request.user.userpermission_set.filter(
        is_active=True
    ).values_list('tenant_id', flat=True)

    templates = Activity.objects.filter(
        tenant_id__in=user_tenant_ids,
        metadata__is_template=True,
        title__icontains=query,
        deleted_at__isnull=True,
    )[:6]

    return render(request, 'activity/partials/template_search_results.html', {
        'templates': templates,
    })


@login_required
@require_POST
def htmx_instantiate_template(request, template_id):
    """HTMX: instantiate a template and redirect to the new activity's edit form."""
    user = request.user
    user_level = getattr(getattr(user, 'userprofile', None), 'competence_level', 0)

    if user_level < 2:
        return HttpResponse('Level 2 required to use templates.', status=403)

    template = get_object_or_404(
        Activity,
        id=template_id,
        deleted_at__isnull=True,
    )
    if not template.metadata.get('is_template'):
        return HttpResponse('Not a template.', status=400)

    new_activity = Activity.objects.create(
        tenant=template.tenant,
        created_by=user,
        activity_type=template.activity_type,
        title=template.title,
        description=template.description,
        recurrence=template.recurrence,
        kgs_pillar=template.kgs_pillar,
        kgs_pathway=template.kgs_pathway,
        status='pending',
        progress=0,
        assigned_to=user,
        metadata={
            **template.metadata,
            'is_template': False,
            'template_id': str(template.id),
            'source_app': 'activity',
        },
    )

    from django.http import HttpResponseRedirect
    return HttpResponseRedirect(f'/activity/{new_activity.id}/edit/')
```

```html
<!-- activity/templates/activity/partials/template_search_results.html -->
{% if templates %}
<div style="display:block">
  {% for t in templates %}
  <div class="record-option"
       hx-post="{% url 'htmx-instantiate' t.id %}"
       hx-target="body"
       hx-push-url="true"
       style="cursor:pointer">
    {{ t.title }}
    <span style="color:var(--color-text-secondary);font-size:11px;margin-left:6px">
      {{ t.activity_type }}
    </span>
  </div>
  {% endfor %}
</div>
{% endif %}
```

---

### Task F.2 — Gifts register (personal + team)

**Files:**
- Modify: `~/ics/activity/views.py`
- Create: `~/ics/activity/templates/activity/gifts_register.html`
- Create: `~/ics/activity/templates/activity/team_gifts.html`
- Create: `~/ics/activity/templates/activity/partials/gift_card.html`

```python
# activity/views.py — gifts_register + team_gifts
@login_required
def gifts_register(request):
    user = request.user
    gifts = Activity.objects.filter(
        created_by=user,
        activity_type='skill',
        tenant__isnull=True,
        deleted_at__isnull=True,
    ).order_by('status', '-created_at')

    return render(request, 'activity/gifts_register.html', {'gifts': gifts})


@login_required
def team_gifts(request):
    user = request.user
    user_level = getattr(getattr(user, 'userprofile', None), 'competence_level', 0)

    if user_level < 3:
        return render(request, 'activity/locked.html', {
            'message': 'The team gifts register requires Steward level (Level 3+).'
        })

    user_tenant_ids = user.userpermission_set.filter(
        is_active=True
    ).values_list('tenant_id', flat=True)

    # Tenant-scoped skill activities
    team_gifts_qs = Activity.objects.filter(
        activity_type='skill',
        tenant_id__in=user_tenant_ids,
        deleted_at__isnull=True,
        status='active',
    ).select_related('created_by').order_by('metadata__service_order', 'title')

    return render(request, 'activity/team_gifts.html', {
        'team_gifts': team_gifts_qs,
    })


@login_required
@require_POST
def htmx_add_gift(request):
    """HTMX: add a new skill/gift entry. Returns updated gift list fragment."""
    user = request.user
    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '').strip()
    kgs_pathway = request.POST.get('kgs_pathway') or None
    service_order = request.POST.get('service_order', '').strip()
    competence = int(request.POST.get('competence', 20))

    if not title:
        return HttpResponse('<p style="color:red">Title is required.</p>')

    Activity.objects.create(
        created_by=user,
        tenant=None,
        activity_type='skill',
        title=title,
        description=description or None,
        kgs_pathway=kgs_pathway,
        progress=competence,
        status='active',
        metadata={
            'source_app': 'activity',
            'is_template': False,
            'service_order': service_order or None,
        },
    )

    gifts = Activity.objects.filter(
        created_by=user,
        activity_type='skill',
        tenant__isnull=True,
        deleted_at__isnull=True,
    ).order_by('status', '-created_at')

    return render(request, 'activity/partials/gifts_list.html', {'gifts': gifts})


@login_required
@require_POST
def htmx_archive_gift(request, gift_id):
    """HTMX: archive a skill/gift entry."""
    user = request.user
    gift = get_object_or_404(Activity, id=gift_id, created_by=user, activity_type='skill')
    gift.status = 'cancelled'
    gift.save(update_fields=['status', 'updated_at'])

    return HttpResponse(status=200)
```

```html
<!-- activity/templates/activity/gifts_register.html -->
{% extends "activity/base_activity.html" %}

{% block activity_content %}
<div class="activity-page-header">
  <h1>Gifts & Skills</h1>
</div>

<!-- Add gift form -->
<div style="padding:16px;background:var(--color-surface);border-bottom:1px solid var(--color-border)">
  <form hx-post="{% url 'htmx-add-gift' %}"
        hx-target="#gifts-list"
        hx-swap="innerHTML"
        hx-on::after-request="this.reset()">
    {% csrf_token %}
    <div class="form-group">
      <input type="text" name="title" class="form-control"
             placeholder="Gift or skill name (e.g. Teaching, Administration)" required>
    </div>
    <div class="form-group">
      <textarea name="description" class="form-control" rows="2"
                placeholder="How does this gift manifest in your life?"></textarea>
    </div>
    <div style="display:flex;gap:12px;flex-wrap:wrap">
      <div class="form-group" style="flex:1;min-width:140px">
        <label style="font-size:12px;font-weight:600;color:var(--color-text-secondary)">
          KGS Pathway
        </label>
        <select name="kgs_pathway" class="form-control" style="font-size:14px">
          <option value="">— None —</option>
          <option value="service">Service</option>
          <option value="leadership">Leadership</option>
          <option value="mission">Mission</option>
          <option value="spiritual_formation">Spiritual Formation</option>
          <option value="community_life">Community Life</option>
          <option value="learning">Learning</option>
          <option value="apostolic_stewardship">Apostolic Stewardship</option>
        </select>
      </div>
      <div class="form-group" style="flex:1;min-width:140px">
        <label style="font-size:12px;font-weight:600;color:var(--color-text-secondary)">
          Competence (1–100)
        </label>
        <input type="number" name="competence" class="form-control"
               min="1" max="100" value="20" style="font-size:14px">
      </div>
    </div>
    <div class="form-group">
      <input type="text" name="service_order" class="form-control"
             placeholder="Service order (optional, e.g. Order of Teaching and Doctrine)">
    </div>
    <button type="submit" class="btn-primary" style="width:100%">Add Gift</button>
  </form>
</div>

<!-- Gifts list -->
<div id="gifts-list" style="padding:8px 0">
  {% include "activity/partials/gifts_list.html" %}
</div>

{% if request.user.userprofile.competence_level >= 3 %}
<div style="margin:8px 16px 24px">
  <a href="{% url 'activity-team-gifts' %}" class="btn-secondary"
     style="width:100%;display:block;text-align:center">
    View Team Gifts Register
  </a>
</div>
{% endif %}
{% endblock %}
```

```html
<!-- activity/templates/activity/partials/gifts_list.html -->
{% for gift in gifts %}
{% if gift.status != 'cancelled' %}
<div class="gift-card" id="gift-{{ gift.id }}">
  <div class="gift-card-body">
    <div class="gift-title">{{ gift.title }}</div>
    {% if gift.description %}
    <div class="gift-meta">{{ gift.description|truncatechars:100 }}</div>
    {% endif %}
    <div class="gift-meta" style="margin-top:4px">
      {% if gift.kgs_pathway %}<span>{{ gift.get_kgs_pathway_display }}</span>{% endif %}
      {% if gift.metadata.service_order %}<span>{{ gift.metadata.service_order }}</span>{% endif %}
    </div>
  </div>
  <div style="display:flex;flex-direction:column;align-items:flex-end;gap:8px">
    <span class="gift-competence">{{ gift.progress }}%</span>
    <button class="btn-status"
            hx-post="{% url 'htmx-archive-gift' gift.id %}"
            hx-target="#gift-{{ gift.id }}"
            hx-swap="outerHTML"
            style="font-size:11px">
      Archive
    </button>
  </div>
</div>
{% endif %}
{% empty %}
<div class="empty-state">
  <p>No gifts or skills recorded yet.</p>
</div>
{% endfor %}
```

Commit: `git add . && git commit -m "feat: gifts register — add, view, archive; team gifts view for stewards"`

---

### Task F.3 — Smoke test checklist

Before closing Phase F, verify manually on mobile:

- [ ] Member creates a personal task; marks complete via HTMX — card updates without page reload
- [ ] Member creates a habit (weekly); sees recurrence label on card
- [ ] Member creates a goal; sees progress bar
- [ ] Member adds a gift to gifts register; archives one
- [ ] Member views their Learn enrolment as a read-only card on My Activities
- [ ] Disciple sees "Assigned to me" tab; HTMX status update works
- [ ] Steward creates a campaign with two nested tasks; both appear in campaign group
- [ ] Steward assigns a task to another team member; task appears in their "Assigned to me" queue
- [ ] Steward views team gifts register; sees correct tenant scope
- [ ] Level 4 user creates an activity template; Level 2 user instantiates it and gets pre-filled form
- [ ] Record link typeahead returns results; linking creates a Relationship (verify in Django admin)
- [ ] `GET /api/calendar/events/?from=2026-04-08&to=2026-04-30` returns events JSON
- [ ] `GET /api/activities/?due_today=true` returns today's due activities
- [ ] `GET /api/activities/?overdue=true` returns overdue activities
- [ ] `GET /api/activities/?metadata__source_app=learn` returns learn enrolments
- [ ] `ActivityLog` entries exist in Django admin after status changes

Commit: `git add . && git commit -m "feat: activity app — smoke test pass, all phases complete"`

---

## Django Endpoint Summary

```
# Activity CRUD (core engine)
GET    /api/activities/                  list with all filters
POST   /api/activities/                  create
GET    /api/activities/{id}/             retrieve
PATCH  /api/activities/{id}/             update
DELETE /api/activities/{id}/             soft delete

# Activity template
POST   /api/activities/{id}/instantiate/ create Activity from template

# Paraclete-required filters (all on GET /api/activities/)
?assigned_to={user_id}
?due_today=true
?overdue=true
?activity_type={type}
?status={status}
?tenant_id={tenant_id}
?parent_activity_id={id}
?metadata__source_app={app}
?surface=personal
?surface=ministry

# Calendar aggregation
GET    /api/calendar/events/             date-range event feed

# Activity App health
GET    /api/activity/health/
```

---

## File Map (Activity App additions)

```
~/ics/
  activity/
    __init__.py
    apps.py                    ← MODIFIED: ready() imports signals
    models.py                  ← VERIFIED: all v5 fields present + indexes
    filters.py                 ← NEW: ActivityFilter (django-filter)
    serializers.py             ← VERIFIED: ActivitySerializer, ActivityLogSerializer
    api_views.py               ← NEW/MODIFIED: ActivityViewSet, health, instantiate action
    views.py                   ← NEW: all Django template views + HTMX partials
    signals.py                 ← NEW: log creation on save
    urls.py                    ← MODIFIED: full URL structure
    templates/
      activity/
        base_activity.html     ← NEW
        my_activities.html     ← NEW
        ministry.html          ← NEW
        assigned_to_me.html    ← NEW
        ministry_events.html   ← NEW
        activity_form.html     ← NEW (create + edit)
        activity_detail.html   ← NEW
        template_list.html     ← NEW
        gifts_register.html    ← NEW
        team_gifts.html        ← NEW
        locked.html            ← NEW (competence gate + 403)
        partials/
          activity_card.html   ← NEW (HTMX status controls)
          gifts_list.html      ← NEW (HTMX target for add/archive)
          record_search_results.html  ← NEW
          template_search_results.html ← NEW

  calendar_app/
    __init__.py
    apps.py
    service.py                 ← NEW: aggregation logic
    views.py                   ← NEW: calendar_events DRF view
    urls.py                    ← NEW
    templates/
      calendar/
        (empty — Phase 2 adds grid view)

  frontend/assets/css/
    activity.css               ← NEW
```

**Note:** There is no `activity-app.js`. The UI is entirely served by Django views
and templates. HTMX replaces the JS interaction layer. `storage.js` is retained
for theme/UI state only.

---

## Phase Summary

| Phase | What it builds | Entry requirement | Exit criteria |
|-------|----------------|-------------------|---------------|
| A | ActivityViewSet filters, soft delete, instantiate endpoint, ActivityLog signal, Calendar app scaffold + endpoint | Phases 0–4 done; `activity` app exists | All filters work; health 200; calendar endpoint returns JSON |
| B | Django URL structure, views/api_views split, base template, `activity.css` | Phase A done | All URLs resolve; base template loads HTMX and CSS |
| C | My Activities surface: tasks, habits, goals, Learn cards, HTMX status, create form, record link typeahead | Phase B done | Member can create, view, and complete personal activities via HTMX |
| D | Ministry surface: team view, assigned-to-me queue, events dated list | Phase C done | Disciple sees assigned queue; steward sees team hierarchy |
| E | Activity detail, campaign/project management, activity edit | Phase D done | Steward creates campaign with nested tasks; detail page shows log |
| F | Templates (Level 4+ create, Level 2+ instantiate), gifts register, team gifts, smoke test | Phase E done | Full smoke test checklist passes |

---

## Deferred (Post-MVP)

- Full RRULE custom recurrence builder (UI for `recurrence: 'custom'`)
- Activity analytics dashboard (completion rates, habit streaks, team performance)
- Bulk task assignment (multiple tasks → multiple users in one action)
- Cross-tenant campaign templates (visible across Church Collective network)
- `assigned_to_tenant_id` field (collective/network-level assignment — see v5 contract note)
- Calendar App Phase 2: full month/week grid UI in Django templates + HTMX
- Calendar App Phase 2: Records engine events (programme milestones, governance calendars)
- Progress update HTMX widget (slider or input for goals — currently manual via edit form)
- iCal export from Calendar app
- Notifications on task assignment (wired to Notifications app stub in Phase 5.7)
- Paraclete "next suggested activity" integration (Phase 6 of main roadmap)
