# ICS Learn App — System Design & Build Roadmap

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

> **UI Architecture amendment — 2026-04-07:**
> The original design specified vanilla JS (IIFE modules + `learn.service.js`) for the UI layer.
> This has been superseded by the platform-wide decision to build all app UIs in
> **Django templates + HTMX**. The backend (Django `learn` app, DRF endpoints, signals,
> models) is unchanged. Phases A and B are unchanged. Phases C–G are amended:
> all `learn-app.js`, `learn.service.js`, and `learn.html` references are replaced
> by Django views, URL patterns, and templates. `learn.css` is unchanged — the
> design system carries forward identically. Vanilla JS is retained only for
> theme/UI state (`storage.js`) and minor interactions HTMX cannot handle.

**Goal:** Build the ICS Learn App — the digital expression of the Sceptre Qualification Programmes Framework — enabling learners to browse courses, enrol in programmes, track progress, and earn certifications that advance their competence level within the Kingdom Governance System.

**Architecture:** Django + DRF backend with a dedicated `learn` app. UI rendered via Django templates with HTMX for dynamic interactions (progress updates, enrolment, lesson completion, queue refreshes). All learning content is Record objects (`record_family: "learning"`). All learner progress is Activity objects. The two are linked via the Relationship engine. No new tables beyond the existing data contract — the Learning Engine is a pattern layer over Records + Activities.

**Tech Stack:** Python/Django 4.2, DRF, PostgreSQL, Django templates, HTMX, `learn.css` (mobile-first, existing CSS variables).

**Data Contract reference:** `2026-04-07-ics-platform-data-contract_v4.md` — all schemas and patterns in this document originate from Part 9 of that contract.

---

## System Overview

### The Learning Stack

```
KGS Layer          Apostles Programme (7-year mission container)
                   ↓ contextualises
Content Layer      Qualification Programmes (Certificate → Doctorate)
                   ↓ contains
                   Courses → Lessons → Assignments / Quizzes
                   (all Record objects, record_family: "learning")
                   ↓ structured by
                   Relationships (part_of — curriculum graph)

Learner Layer      Enrolment Activity (activity_type: "programme")
                   ↓ nests
                   Course Activity (activity_type: "project")
                   ↓ nests
                   Lesson/Assessment Activities (activity_type: "task")
                   ↓ completes to produce
                   Certification Record (record_type: "certification")
                   ↓ confirmed by steward via
                   POST /api/learn/certifications/{id}/confirm/
                   ↓ advances
                   user.competence_level
```

### User roles in the Learn App

| Role | What they do |
|---|---|
| Seeker (0b) | Browse published programmes. Cannot enrol. |
| Member (Level 1+) | Enrol, track progress, complete lessons |
| Disciple/Operator (Level 2+) | All above + submit assignments |
| Branch-Steward (Level 3+) | Confirm certifications for their tenant's learners |
| District-Steward / Senior Steward (Level 4+) | Author and submit Programmes and Courses for review |
| Architect (Level 5) | Review submitted content, approve (status → active), lock |

---

## The Five Qualification Programmes

These are the five content containers of the Apostles Programme. Each is a
Record (`record_class: "organizational"`, `record_family: "learning"`,
`record_type: "programme"`). Courses are authored within them.

| Programme | Competence Level | Duration | KGS Pathways | Prerequisites |
|---|---|---|---|---|
| Certificate | Level 1 | 1 year | New Life; Community Life; Learning | None |
| Diploma | Level 2 | 3 years | Spiritual Formation; Service; Mission; Learning | Certificate |
| Degree | Level 3 | 4 years | Leadership; Learning | Diploma + Certificate |
| Masters | Level 4 | 4–5 years | Leadership; Apostolic Stewardship | Degree + prior |
| Doctorate | Level 5 | 7 years total | Leadership; Apostolic Stewardship | Masters + all prior |

---

## Feature List (All Features — Unphased)

This is the complete Learn App feature inventory. Phasing follows below.

### F1 — Programme Catalogue
- Browse all published Qualification Programmes
- Pathway View: grouped by KGS pathway (default for enrolled learners)
- Catalogue View: flat list filtered by competence level
- Locked indicator for programmes above learner's current level
- Programme detail: title, description, pathways, duration, prerequisites, course list

### F2 — Course Browser
- Browse courses within a programme
- Course detail: title, description, lesson list, assignments, quizzes
- Competence gate: courses requiring a higher level show locked state

### F3 — Enrolment
- Enrol in a programme (creates enrolment Activity of type "programme")
- Prerequisite check before enrolment is permitted
- One active enrolment per programme per user
- Enrolment confirmation screen

### F4 — Progress Tracking
- Lesson completion (marks task Activity as completed)
- Course progress bar (% lessons/assessments completed)
- Programme progress bar (% courses completed)
- Progress persists via ActivityLog
- Resume where left off (last incomplete lesson)

### F5 — Lesson Viewer
- Read lesson content (Record.content rendered as rich text / markdown)
- Mark lesson complete button
- Navigate previous / next lesson
- Back to course breadcrumb

### F6 — Assessments (Assignments & Quizzes)
- Quiz: inline multiple-choice or short answer (stored in Record.custom_fields)
- Assignment: text submission by learner (stored as child Record linked to assignment)
- Submission marks assessment Activity as completed
- Steward can view submitted assignments within their tenant scope

### F7 — Certification & Competence Advancement
- Auto-create draft Certification Record when programme Activity hits 100%
- Learner sees "Awaiting certification" status
- Steward review queue: list of draft certifications for their tenant's learners
- Steward confirms → certification status → active → competence_level incremented
- Learner notification on certification confirmed (via Notifications app stub)

### F8 — Content Authorship (Level 4+)
- Create Programme record (draft)
- Create Course record (linked to programme via part_of Relationship)
- Create Lesson record (linked to course via part_of Relationship)
- Create Assignment / Quiz record (linked to course or lesson via part_of)
- Rich text / markdown content editor for lesson body
- Submit Programme or Course for Handbook review (status → submitted)

### F9 — Handbook Review Queue (Level 5)
- List submitted learning records (status: "submitted", record_family: "learning")
- Review programme / course detail
- Approve (status → active) or return to draft with a note
- Lock approved content (status → locked)

### F10 — Pathway View (Dashboard integration)
- "You are enrolled in [Programme] — [Primary Pathway]" banner
- Active enrolment widget surfaced on Learn App home
- Paraclete integration: "Continue your lesson: [lesson title]" (Phase 6)

### F11 — My Learning Dashboard (Learn App home)
- Active enrolments with progress
- Completed programmes and certifications
- Recommended next programme (based on competence level)
- Quick-access: resume last lesson

---

## Build Phases

### Phase A — Django Learn App (backend foundation)
*Entry requirement: Phases 0–4 of main roadmap complete (Django project, Records, Activity, Identity engines all live).*

### Phase B — Content Engine (read-only)
*Entry requirement: Phase A complete.*

### Phase C — Enrolment + Progress Tracking
*Entry requirement: Phase B complete.*

### Phase D — Assessments
*Entry requirement: Phase C complete.*

### Phase E — Certification + Competence Advancement
*Entry requirement: Phase D complete.*

### Phase F — Content Authorship + Handbook Review
*Entry requirement: Phase E complete.*

### Phase G — UI Polish + Pathway View + My Learning Dashboard
*Entry requirement: Phase F complete.*

---

## Phase A — Django Learn App (Backend Foundation)

**Exit criteria:** `GET /api/learn/health/` returns `{"status": "ok"}`. Django `learn` app exists with models, serializers, basic endpoints. No UI yet.

### Task A.1 — Create Django `learn` app

**Files:**
- Create: `~/ics/learn/__init__.py`
- Create: `~/ics/learn/apps.py`
- Create: `~/ics/learn/models.py`
- Create: `~/ics/learn/serializers.py`
- Create: `~/ics/learn/views.py`
- Create: `~/ics/learn/urls.py`
- Modify: `~/ics/ics_project/settings/base.py` (add `learn` to INSTALLED_APPS)
- Modify: `~/ics/ics_project/urls.py` (include learn.urls)

**Step 1:** Create the app scaffold

```bash
cd ~/ics && python manage.py startapp learn
```

**Step 2:** Add to INSTALLED_APPS in `base.py`

```python
INSTALLED_APPS = [
    ...
    'learn',
]
```

**Step 3:** Create `learn/models.py`

The Learn App does not define its own content models — all content is stored
in `records.Record`. The only Learn-specific model is `CertificationConfirmation`
which records the steward action (audit trail separate from the Record status change).

```python
# learn/models.py
import uuid
from django.db import models
from django.conf import settings


class CertificationConfirmation(models.Model):
    """
    Audit record of a steward confirming a learner's certification.
    The certification itself is a records.Record with record_type='certification'.
    This model records WHO confirmed it and WHEN, separately from the Record.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    certification_record_id = models.UUIDField(db_index=True)  # FK → records.Record
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='certifications_confirmed'
    )
    learner_id = models.UUIDField(db_index=True)               # FK → User (the learner)
    previous_competence_level = models.IntegerField()
    new_competence_level = models.IntegerField()
    confirmed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-confirmed_at']
        indexes = [
            models.Index(fields=['certification_record_id']),
            models.Index(fields=['learner_id']),
            models.Index(fields=['confirmed_by']),
        ]
```

**Step 4:** Run migrations

```bash
python manage.py makemigrations learn
python manage.py migrate
```

**Step 5:** Create health endpoint in `learn/views.py`

```python
# learn/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok", "app": "learn"})
```

**Step 6:** Create `learn/urls.py`

```python
# learn/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health, name='learn-health'),
]
```

**Step 7:** Include in main `urls.py`

```python
path('api/learn/', include('learn.urls')),
```

**Step 8:** Test

```bash
curl https://your-domain.com/api/learn/health/
# Expected: {"status": "ok", "app": "learn"}
```

Commit: `git add . && git commit -m "feat: learn app scaffold + health endpoint"`

---

### Task A.2 — Certification confirmation endpoint

**Files:**
- Modify: `~/ics/learn/views.py`
- Modify: `~/ics/learn/urls.py`
- Modify: `~/ics/learn/serializers.py`
- Modify: `~/ics/accounts/serializers.py` (competence_level write rule)

This is the most critical backend endpoint in the Learn App. It is the ONLY
place in the system that may increment `user.competence_level`.

**Step 1:** Add `CertificationConfirmSerializer` to `learn/serializers.py`

```python
# learn/serializers.py
from rest_framework import serializers
from .models import CertificationConfirmation


class CertificationConfirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificationConfirmation
        fields = [
            'id', 'certification_record_id', 'confirmed_by',
            'learner_id', 'previous_competence_level',
            'new_competence_level', 'confirmed_at', 'notes'
        ]
        read_only_fields = [
            'id', 'confirmed_by', 'previous_competence_level',
            'new_competence_level', 'confirmed_at'
        ]
```

**Step 2:** Add the confirm view to `learn/views.py`

```python
# learn/views.py (additions)
import uuid
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from records.models import Record          # adjust import path to your project
from django.contrib.auth import get_user_model
from .models import CertificationConfirmation
from .serializers import CertificationConfirmSerializer

User = get_user_model()


def is_level_3_or_above(user):
    """Check if user has competence_level >= 3 (branch-steward or above)."""
    return hasattr(user, 'userprofile') and user.userprofile.competence_level >= 3


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_certification(request, certification_id):
    """
    Steward confirms a learner's certification.
    - Gated to competence_level >= 3
    - Sets certification Record status to 'active'
    - Increments learner's competence_level by 1 (up to target_level)
    - Creates CertificationConfirmation audit record
    - This endpoint is the SOLE authorised writer of competence_level
    """
    if not is_level_3_or_above(request.user):
        return Response(
            {"detail": "Certification confirmation requires Level 3 or above."},
            status=status.HTTP_403_FORBIDDEN
        )

    certification_record = get_object_or_404(
        Record,
        id=certification_id,
        record_type='certification',
        status='draft'
    )

    # Retrieve metadata from the certification record
    metadata = certification_record.metadata or {}
    learner_id = metadata.get('learner_id') or str(certification_record.created_by_id)
    target_level = metadata.get('target_level', 1)

    learner = get_object_or_404(User, id=learner_id)
    learner_profile = learner.userprofile
    previous_level = learner_profile.competence_level

    # Only advance if not already at or above target level
    if previous_level >= target_level:
        return Response(
            {"detail": "Learner is already at or above the target competence level."},
            status=status.HTTP_400_BAD_REQUEST
        )

    new_level = min(previous_level + 1, target_level)

    # Update certification record status
    certification_record.status = 'active'
    certification_record.save(update_fields=['status', 'updated_at'])

    # Advance learner competence level — only write path in the system
    learner_profile.competence_level = new_level
    learner_profile.save(update_fields=['competence_level'])

    # Create audit record
    confirmation = CertificationConfirmation.objects.create(
        certification_record_id=certification_record.id,
        confirmed_by=request.user,
        learner_id=learner.id,
        previous_competence_level=previous_level,
        new_competence_level=new_level,
        notes=request.data.get('notes', '')
    )

    serializer = CertificationConfirmSerializer(confirmation)
    return Response(serializer.data, status=status.HTTP_200_OK)
```

**Step 3:** Add to `learn/urls.py`

```python
path('certifications/<uuid:certification_id>/confirm/', views.confirm_certification, name='certification-confirm'),
```

**Step 4:** Verify `competence_level` is read-only in `accounts/serializers.py`
everywhere EXCEPT this endpoint. Add a comment:

```python
# accounts/serializers.py — UserProfileSerializer
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['competence_level', 'status', ...]
        read_only_fields = ['competence_level']
        # NOTE: competence_level is intentionally read-only here.
        # The ONLY authorised write path is POST /api/learn/certifications/{id}/confirm/
        # See learn/views.py::confirm_certification
```

Commit: `git add . && git commit -m "feat: certification confirm endpoint — sole writer of competence_level"`

---

### Task A.3 — Certification review queue endpoint

**Files:**
- Modify: `~/ics/learn/views.py`
- Modify: `~/ics/learn/urls.py`

Stewards need a list of draft certifications pending their review.

```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def certification_queue(request):
    """
    Returns draft certification records visible to the requesting steward.
    Filtered to certifications created by learners within the steward's tenant scope.
    Requires competence_level >= 3.
    """
    if not is_level_3_or_above(request.user):
        return Response(
            {"detail": "Certification queue requires Level 3 or above."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Fetch draft certifications scoped to steward's tenant path
    # The steward's tenant_path comes from their active UserPermission row
    steward_tenant_path = request.user.userprofile.active_tenant_path  # adjust to your model

    certifications = Record.objects.filter(
        record_type='certification',
        status='draft',
        tenant__path__startswith=steward_tenant_path  # adjust to your tenant FK structure
    ).order_by('created_at')

    # Use existing RecordSerializer from records app
    from records.serializers import RecordSerializer
    serializer = RecordSerializer(certifications, many=True)
    return Response(serializer.data)
```

Add to `learn/urls.py`:

```python
path('certifications/queue/', views.certification_queue, name='certification-queue'),
```

Commit: `git add . && git commit -m "feat: certification queue endpoint for stewards"`

---

## Phase B — Content Engine (Read-Only)

**Exit criteria:** Published programmes, courses, lessons are retrievable via DRF. Django learn views call the ORM directly (not via a JS service layer). Competence gating works server-side.

### Task B.1 — Verify Records engine serves learning content

The Records engine (`GET /api/records/`) already exists from Phase 2 of the main roadmap. This task confirms the filtering params needed by the Learn App work correctly.

**Required queries — verify each returns correct results:**

```bash
# All published programmes
GET /api/records/?record_family=learning&record_type=programme&status=active

# Programmes visible to a specific learner level
GET /api/records/?record_family=learning&record_type=programme&status=active&required_level_lte=2

# Courses in a programme (via relationship traversal — see Task B.2)
GET /api/records/?record_family=learning&record_type=course&status=active

# Submitted content (Level 5 review queue)
GET /api/records/?record_family=learning&status=submitted

# Lessons in a course
GET /api/records/?record_family=learning&record_type=lesson&status=active
```

If the Records DRF view does not support `required_level_lte` filtering, add it:

```python
# records/views.py — add to filter_queryset or filterset_fields
required_level_lte = request.query_params.get('required_level_lte')
if required_level_lte:
    queryset = queryset.filter(permissions__required_level__lte=required_level_lte)
```

Commit: `git add . && git commit -m "feat: records endpoint — required_level_lte filter for learn app"`

---

### Task B.2 — Curriculum endpoint (course list for a programme)

The curriculum is the set of `part_of` Relationships from courses to a programme.
Rather than forcing the JS client to traverse relationships manually, expose a
dedicated curriculum endpoint.

**Files:**
- Modify: `~/ics/learn/views.py`
- Modify: `~/ics/learn/urls.py`

```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def programme_curriculum(request, programme_id):
    """
    Returns the ordered list of courses (and their lessons) for a programme.
    Traverses part_of Relationships: course → part_of → programme.
    Then for each course: lesson → part_of → course.
    """
    from records.models import Record, Relationship

    programme = get_object_or_404(
        Record,
        id=programme_id,
        record_family='learning',
        record_type='programme',
        status__in=['active', 'locked']
    )

    # Check learner competence gate
    required_level = programme.permissions.get('required_level', 1)
    user_level = request.user.userprofile.competence_level
    if user_level < required_level:
        return Response(
            {"detail": "Insufficient competence level to access this programme."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Get all courses part_of this programme
    course_ids = Relationship.objects.filter(
        to_record_id=programme_id,
        relationship_type='part_of'
    ).values_list('from_record_id', flat=True)

    courses = Record.objects.filter(
        id__in=course_ids,
        record_type='course',
        status__in=['active', 'locked']
    ).order_by('created_at')

    curriculum = []
    for course in courses:
        lesson_ids = Relationship.objects.filter(
            to_record_id=course.id,
            relationship_type='part_of'
        ).values_list('from_record_id', flat=True)

        lessons = Record.objects.filter(
            id__in=lesson_ids,
            record_type__in=['lesson', 'assignment', 'quiz'],
            status__in=['active', 'locked']
        ).order_by('created_at')

        from records.serializers import RecordSerializer
        curriculum.append({
            'course': RecordSerializer(course).data,
            'lessons': RecordSerializer(lessons, many=True).data
        })

    return Response({
        'programme': RecordSerializer(programme).data,
        'curriculum': curriculum
    })
```

Add to `learn/urls.py`:

```python
path('programmes/<uuid:programme_id>/curriculum/', views.programme_curriculum, name='programme-curriculum'),
```

Commit: `git add . && git commit -m "feat: curriculum endpoint — traverses part_of relationships"`

---

### Task B.3 — Django learn views + URL routing

**Files:**
- Modify: `~/ics/learn/views.py`
- Modify: `~/ics/learn/urls.py`
- Create: `~/ics/learn/templates/learn/` (template directory)

The Learn App UI is served by Django views that query the ORM directly and
pass context to templates. HTMX handles partial updates. No JS service layer.

**URL structure:**

```python
# learn/urls.py
from django.urls import path
from . import views, api_views

urlpatterns = [
    # API endpoints (DRF — consumed by HTMX and future mobile clients)
    path('health/', api_views.health, name='learn-health'),
    path('programmes/<uuid:programme_id>/curriculum/', api_views.programme_curriculum, name='programme-curriculum'),
    path('certifications/queue/', api_views.certification_queue, name='certification-queue'),
    path('certifications/<uuid:certification_id>/confirm/', api_views.confirm_certification, name='certification-confirm'),

    # Django template views (UI)
    path('', views.my_learning, name='learn-home'),
    path('programmes/', views.catalogue, name='learn-catalogue'),
    path('programmes/<uuid:programme_id>/', views.programme_detail, name='learn-programme'),
    path('lessons/<uuid:lesson_id>/', views.lesson_viewer, name='learn-lesson'),
    path('certifications/', views.certification_queue_view, name='learn-cert-queue'),
    path('author/', views.authorship, name='learn-author'),
    path('review/', views.review_queue, name='learn-review'),

    # HTMX partial endpoints (return HTML fragments, not full pages)
    path('htmx/enrol/<uuid:programme_id>/', views.htmx_enrol, name='htmx-enrol'),
    path('htmx/complete-lesson/<uuid:lesson_id>/', views.htmx_complete_lesson, name='htmx-complete-lesson'),
    path('htmx/confirm-cert/<uuid:cert_id>/', views.htmx_confirm_cert, name='htmx-confirm-cert'),
    path('htmx/approve-content/<uuid:record_id>/', views.htmx_approve_content, name='htmx-approve-content'),
]
```

**Rename existing DRF views file for clarity:**
- Rename: `learn/views.py` → `learn/api_views.py` (holds all DRF `@api_view` functions)
- Create: `learn/views.py` (holds all Django template views)

This keeps the API layer and the template layer cleanly separated in the same app.

Commit: `git add . && git commit -m "feat: learn app — Django URL structure, views/api_views split"`

---

## Phase C — Enrolment + Progress Tracking (UI)

**Exit criteria:** A learner can browse programmes, enrol, view their curriculum, mark lessons complete, and see progress bars update — all via Django templates and HTMX. No JS app file required.

### Task C.1 — Django template views (My Learning + Catalogue)

**Files:**
- Create: `~/ics/learn/views.py`
- Create: `~/ics/learn/templates/learn/base_learn.html`
- Create: `~/ics/learn/templates/learn/my_learning.html`
- Create: `~/ics/learn/templates/learn/catalogue.html`
- Create: `~/ics/learn/templates/learn/programme_detail.html`

**`learn/views.py` — core template views:**

```python
# learn/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from records.models import Record, Relationship
from activity.models import Activity


@login_required
def my_learning(request):
    """My Learning home — active enrolments and completed certifications."""
    user = request.user
    enrolments = Activity.objects.filter(
        activity_type='programme',
        assigned_to=user,
        status='in_progress',
        metadata__source_app='learn'
    ).order_by('-created_at')

    certifications = Record.objects.filter(
        record_type='certification',
        created_by=user,
        status='active'
    ).order_by('-updated_at')

    return render(request, 'learn/my_learning.html', {
        'enrolments': enrolments,
        'certifications': certifications,
    })


@login_required
def catalogue(request):
    """Programme catalogue — filtered by user competence level."""
    user_level = request.user.userprofile.competence_level
    programmes = Record.objects.filter(
        record_family='learning',
        record_type='programme',
        status='active'
    ).order_by('created_at')

    # Annotate each programme with locked status for the template
    for p in programmes:
        p.is_locked = user_level < (p.permissions.get('required_level', 1))

    return render(request, 'learn/catalogue.html', {
        'programmes': programmes,
        'user_level': user_level,
    })


@login_required
def programme_detail(request, programme_id):
    """Programme detail with curriculum and enrolment status."""
    user = request.user
    user_level = user.userprofile.competence_level

    programme = get_object_or_404(
        Record, id=programme_id,
        record_family='learning', record_type='programme',
        status__in=['active', 'locked']
    )

    required_level = programme.permissions.get('required_level', 1)
    if user_level < required_level:
        return render(request, 'learn/locked.html', {'programme': programme})

    # Build curriculum via part_of relationships
    course_ids = Relationship.objects.filter(
        to_record_id=programme_id,
        relationship_type='part_of'
    ).values_list('from_record_id', flat=True)

    courses = Record.objects.filter(
        id__in=course_ids, record_type='course',
        status__in=['active', 'locked']
    ).order_by('created_at')

    curriculum = []
    for course in courses:
        lesson_ids = Relationship.objects.filter(
            to_record_id=course.id, relationship_type='part_of'
        ).values_list('from_record_id', flat=True)
        lessons = Record.objects.filter(
            id__in=lesson_ids,
            record_type__in=['lesson', 'assignment', 'quiz'],
            status__in=['active', 'locked']
        ).order_by('created_at')
        curriculum.append({'course': course, 'lessons': lessons})

    already_enrolled = Activity.objects.filter(
        activity_type='programme',
        assigned_to=user,
        metadata__programme_record_id=str(programme_id)
    ).exists()

    return render(request, 'learn/programme_detail.html', {
        'programme': programme,
        'curriculum': curriculum,
        'already_enrolled': already_enrolled,
    })


@login_required
def lesson_viewer(request, lesson_id):
    """Lesson viewer — renders lesson content with prev/next navigation."""
    lesson = get_object_or_404(
        Record, id=lesson_id,
        record_type__in=['lesson', 'assignment', 'quiz'],
        status__in=['active', 'locked']
    )

    # Find parent course via part_of relationship
    parent_rel = Relationship.objects.filter(
        from_record_id=lesson_id, relationship_type='part_of'
    ).first()
    course = None
    siblings = []
    if parent_rel:
        course = Record.objects.filter(id=parent_rel.to_record_id).first()
        if course:
            sibling_ids = Relationship.objects.filter(
                to_record_id=course.id, relationship_type='part_of'
            ).values_list('from_record_id', flat=True)
            siblings = list(Record.objects.filter(
                id__in=sibling_ids, status__in=['active', 'locked']
            ).order_by('created_at'))

    current_index = next((i for i, s in enumerate(siblings) if s.id == lesson.id), 0)
    prev_lesson = siblings[current_index - 1] if current_index > 0 else None
    next_lesson = siblings[current_index + 1] if current_index < len(siblings) - 1 else None

    return render(request, 'learn/lesson_viewer.html', {
        'lesson': lesson,
        'course': course,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
    })
```

Commit: `git add . && git commit -m "feat: learn views — my_learning, catalogue, programme_detail, lesson_viewer"`

---

### Task C.2 — Base learn template + CSS

**Files:**
- Create: `~/ics/learn/templates/learn/base_learn.html`
- Create: `~/ics/frontend/assets/css/learn.css`

**`base_learn.html`** — extends the platform base template, adds HTMX and learn-specific structure:

```html
{% extends "base.html" %}
{% load static %}

{% block extra_css %}
  <link rel="stylesheet" href="{% static 'css/learn.css' %}">
{% endblock %}

{% block extra_scripts %}
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
{% endblock %}
```

**`learn.css`** — identical to the original design. No changes to the design system. All CSS variables, mobile-first breakpoints, programme cards, progress bars, lesson viewer styles, and certification styles carry forward unchanged.

Commit: `git add . && git commit -m "feat: learn base template + learn.css"`

---

### Task C.3 — My Learning template

**Files:**
- Create: `~/ics/learn/templates/learn/my_learning.html`

```html
{% extends "learn/base_learn.html" %}

{% block content %}
<div class="learn-header">
  <h1>Learn</h1>
  <a href="{% url 'learn-catalogue' %}" class="btn-secondary">Browse Programmes</a>
</div>

{% if enrolments %}
  {% for enrolment in enrolments %}
  <div class="enrolment-card">
    <div class="enrolment-title">{{ enrolment.title }}</div>
    <div class="progress-bar-wrap">
      <div class="progress-bar" style="width:{{ enrolment.progress }}%"></div>
    </div>
    <span class="progress-label">{{ enrolment.progress }}% complete</span>
    <a href="{% url 'learn-programme' enrolment.metadata.programme_record_id %}"
       class="btn-primary">Continue</a>
  </div>
  {% endfor %}
{% else %}
  <div class="empty-state">
    <p>You are not enrolled in any programme yet.</p>
    <a href="{% url 'learn-catalogue' %}" class="btn-primary">Browse Programmes</a>
  </div>
{% endif %}

{% if certifications %}
  <h2>Completed</h2>
  {% for cert in certifications %}
  <div class="enrolment-card">
    <div class="enrolment-title">{{ cert.title }}</div>
    <span class="enrolled-badge">Certified</span>
  </div>
  {% endfor %}
{% endif %}
{% endblock %}
```

Commit: `git add . && git commit -m "feat: my_learning.html template"`

---

### Task C.4 — Catalogue + Programme detail templates

**Files:**
- Create: `~/ics/learn/templates/learn/catalogue.html`
- Create: `~/ics/learn/templates/learn/programme_detail.html`
- Create: `~/ics/learn/templates/learn/locked.html`

**`catalogue.html`:**

```html
{% extends "learn/base_learn.html" %}

{% block content %}
<div class="learn-header">
  <a href="{% url 'learn-home' %}" class="btn-back">← My Learning</a>
  <h2>Programmes</h2>
</div>

<div class="programme-grid">
  {% for programme in programmes %}
  <div class="programme-card {% if programme.is_locked %}locked{% endif %}">
    <div class="programme-badge">
      {{ programme.metadata.qualification|default:"Programme" }}
    </div>
    <h3 class="programme-title">{{ programme.title }}</h3>
    <p class="programme-meta">
      {{ programme.metadata.duration_years|default:"?" }} year{{ programme.metadata.duration_years|pluralize }}
    </p>
    {% if programme.is_locked %}
      <span class="lock-indicator">
        Level {{ programme.permissions.required_level }} required
      </span>
    {% else %}
      <a href="{% url 'learn-programme' programme.id %}" class="btn-primary">View</a>
    {% endif %}
  </div>
  {% endfor %}
</div>
{% endblock %}
```

**`programme_detail.html`:**

```html
{% extends "learn/base_learn.html" %}

{% block content %}
<div class="programme-detail">
  <a href="{% url 'learn-catalogue' %}" class="btn-back">← Programmes</a>
  <div class="programme-badge">{{ programme.metadata.qualification|default:"Programme" }}</div>
  <h2>{{ programme.title }}</h2>
  <p class="programme-description">{{ programme.content|default:programme.summary }}</p>
  <div class="programme-meta-row">
    <span>{{ programme.metadata.duration_years|default:"?" }} years</span>
    <span>Level {{ programme.permissions.required_level|default:1 }}</span>
  </div>

  {% if already_enrolled %}
    <span class="enrolled-badge">Enrolled</span>
  {% else %}
    <!-- HTMX enrolment — swaps button with confirmation in-place -->
    <button class="btn-primary enrol-btn"
            hx-post="{% url 'htmx-enrol' programme.id %}"
            hx-target="#enrol-section"
            hx-swap="outerHTML">
      Enrol in this Programme
    </button>
    <div id="enrol-section"></div>
  {% endif %}

  <div class="curriculum-list">
    <h3>Curriculum</h3>
    {% for item in curriculum %}
    <div class="course-block">
      <h4>{{ forloop.counter }}. {{ item.course.title }}</h4>
      <ul class="lesson-list">
        {% for lesson in item.lessons %}
        <li class="lesson-item">
          <span class="lesson-type-tag">{{ lesson.record_type }}</span>
          <a href="{% url 'learn-lesson' lesson.id %}">{{ lesson.title }}</a>
        </li>
        {% endfor %}
      </ul>
    </div>
    {% endfor %}
  </div>
</div>
{% endblock %}
```

Commit: `git add . && git commit -m "feat: catalogue.html + programme_detail.html templates"`

---

### Task C.5 — Lesson viewer template + HTMX complete button

**Files:**
- Create: `~/ics/learn/templates/learn/lesson_viewer.html`
- Create: `~/ics/learn/templates/learn/partials/lesson_complete_btn.html`
- Add HTMX view to `learn/views.py`

**`lesson_viewer.html`:**

```html
{% extends "learn/base_learn.html" %}

{% block content %}
<div class="lesson-viewer">
  {% if course %}
    <a href="{% url 'learn-programme' course.id %}" class="btn-back">← Back to Course</a>
  {% endif %}
  <span class="lesson-type-tag">{{ lesson.record_type }}</span>
  <h2 class="lesson-title">{{ lesson.title }}</h2>

  <div class="lesson-content">
    {{ lesson.content|linebreaks }}
  </div>

  <div class="lesson-nav">
    {% if prev_lesson %}
      <a href="{% url 'learn-lesson' prev_lesson.id %}" class="btn-secondary">← Previous</a>
    {% else %}
      <span></span>
    {% endif %}

    <!-- HTMX complete button — replaces itself with a ✓ confirmation -->
    <div id="complete-section">
      {% include "learn/partials/lesson_complete_btn.html" %}
    </div>

    {% if next_lesson %}
      <a href="{% url 'learn-lesson' next_lesson.id %}" class="btn-secondary">Next →</a>
    {% else %}
      <span></span>
    {% endif %}
  </div>
</div>
{% endblock %}
```

**`partials/lesson_complete_btn.html`:**

```html
<button class="btn-primary complete-btn"
        hx-post="{% url 'htmx-complete-lesson' lesson.id %}"
        hx-target="#complete-section"
        hx-swap="outerHTML">
  Mark Complete
</button>
```

**HTMX views — add to `learn/views.py`:**

```python
@login_required
def htmx_enrol(request, programme_id):
    """HTMX: creates enrolment Activity, returns confirmation fragment."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    user = request.user
    programme = get_object_or_404(Record, id=programme_id, record_type='programme')

    Activity.objects.create(
        activity_type='programme',
        title=f'Enrolment — {programme.title}',
        assigned_to=user,
        status='in_progress',
        progress=0,
        kgs_pathway='learning',
        metadata={
            'source_app': 'learn',
            'programme_record_id': str(programme_id)
        }
    )

    # Return a small HTML fragment — HTMX swaps it in place of the button
    return HttpResponse('<span class="enrolled-badge">Enrolled ✓</span>')


@login_required
def htmx_complete_lesson(request, lesson_id):
    """HTMX: marks lesson Activity complete, returns updated button fragment."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    Activity.objects.filter(
        metadata__lesson_record_id=str(lesson_id),
        assigned_to=request.user
    ).update(status='completed', progress=100)

    # Return completed state fragment
    return HttpResponse(
        '<button class="btn-primary complete-btn completed" disabled>✓ Completed</button>'
    )
```

Commit: `git add . && git commit -m "feat: lesson_viewer.html + HTMX complete lesson + enrol views"`

---

## Phase D — Assessments

**Exit criteria:** Quiz and Assignment records render correctly in the lesson viewer. Submission marks the assessment activity complete via HTMX.

### Task D.1 — Quiz template + HTMX submission

Quiz questions live in `Record.custom_fields`. The lesson viewer template detects
`lesson.record_type == 'quiz'` and renders a form. Submission is an HTMX POST.

**Files:**
- Create: `~/ics/learn/templates/learn/partials/quiz.html`
- Add HTMX quiz submit view to `learn/views.py`

**`partials/quiz.html`:**

```html
<form hx-post="{% url 'htmx-submit-quiz' lesson.id %}"
      hx-target="#complete-section"
      hx-swap="outerHTML">
  {% csrf_token %}
  {% for q in lesson.custom_fields.questions %}
  <div class="quiz-question">
    <p>{{ q.text }}</p>
    {% if q.type == 'multiple_choice' %}
      {% for option in q.options %}
      <label class="quiz-option">
        <input type="radio" name="q_{{ q.id }}" value="{{ forloop.counter0 }}">
        {{ option }}
      </label>
      {% endfor %}
    {% else %}
      <textarea name="q_{{ q.id }}" class="quiz-text-answer" rows="3"></textarea>
    {% endif %}
  </div>
  {% endfor %}
  <button type="submit" class="btn-primary">Submit Quiz</button>
</form>
```

Add `htmx-submit-quiz` view to `learn/views.py` — marks assessment Activity
as completed and returns the completed state fragment.

### Task D.2 — Assignment submission template

Same HTMX pattern. Assignment form submits text via POST. The view creates a
child Record (`record_type: "note"`) linked to the assignment via a `references`
Relationship, then marks the task Activity complete.

Commit: `git add . && git commit -m "feat: learn app — quiz + assignment templates with HTMX submission"`

---

## Phase E — Certification + Competence Advancement (UI)

**Exit criteria:** Learner sees "Awaiting certification" when programme is 100% complete. Steward sees certification queue as a Django-rendered page. Steward confirms via HTMX. Learner's competence level advances.

### Task E.1 — Awaiting certification view

The Django signal (Task E.1 backend — unchanged) auto-creates the draft
Certification Record. The learner's My Learning page detects a draft certification
linked to their completed enrolment and shows an "Awaiting certification" banner.

Add to `my_learning.html`:

```html
{% if pending_certifications %}
  {% for cert in pending_certifications %}
  <div class="enrolment-card awaiting-cert">
    <div class="enrolment-title">{{ cert.title }}</div>
    <span class="cert-pending-badge">Awaiting Steward Confirmation</span>
  </div>
  {% endfor %}
{% endif %}
```

Update `my_learning` view to pass `pending_certifications` (draft certification
Records created by the current user).

### Task E.2 — Steward certification queue template + HTMX confirm

**Files:**
- Create: `~/ics/learn/templates/learn/certification_queue.html`
- Add `htmx_confirm_cert` view to `learn/views.py`

**`certification_queue.html`:**

```html
{% extends "learn/base_learn.html" %}
{% block content %}
<div class="learn-header"><h2>Certifications Pending</h2></div>

{% if certifications %}
  {% for cert in certifications %}
  <div class="cert-card" id="cert-{{ cert.id }}">
    <h4>{{ cert.title }}</h4>
    <p class="cert-meta">Submitted: {{ cert.created_at|date:"d M Y" }}</p>
    <textarea name="notes" placeholder="Notes (optional)"
              id="notes-{{ cert.id }}"></textarea>
    <button class="btn-primary"
            hx-post="{% url 'htmx-confirm-cert' cert.id %}"
            hx-target="#cert-{{ cert.id }}"
            hx-swap="outerHTML"
            hx-include="#notes-{{ cert.id }}">
      Confirm &amp; Advance Level
    </button>
  </div>
  {% endfor %}
{% else %}
  <p class="empty-state">No certifications pending.</p>
{% endif %}
{% endblock %}
```

**`htmx_confirm_cert` view** calls the existing `confirm_certification` logic
from `api_views.py` and returns a small HTML fragment confirming the action:

```python
@login_required
def htmx_confirm_cert(request, cert_id):
    if request.method != 'POST':
        return HttpResponse(status=405)
    # Reuse confirm_certification logic (extracted to a service function)
    # Returns fragment replacing the cert card with a confirmed state
    return HttpResponse(
        f'<div class="cert-card confirmed">'
        f'<span class="enrolled-badge">✓ Certification Confirmed</span>'
        f'</div>'
    )
```

Commit: `git add . && git commit -m "feat: learn app — certification queue template + HTMX confirm"`

---

## Phase F — Content Authorship + Handbook Review (UI)

**Exit criteria:** Level 4+ users can create and submit Programmes, Courses, and Lessons via Django forms. Level 5 users see a review queue and can approve content via HTMX.

### Task F.1 — Authorship views + templates (Level 4+)

**Files:**
- Create: `~/ics/learn/templates/learn/authorship.html`
- Create: `~/ics/learn/templates/learn/author_programme_form.html`
- Create: `~/ics/learn/templates/learn/author_course_form.html`
- Create: `~/ics/learn/templates/learn/author_lesson_form.html`
- Add authorship views to `learn/views.py`

Django `CreateView` or function-based views gated to `competence_level >= 4`.
Each form creates a Record with the appropriate `record_family`, `record_type`,
and `status: "draft"`. A "Submit for Review" button PATCHes the record status
to `"submitted"` — this can be a standard Django form POST (no HTMX needed here
as it's a full-page action).

Core form fields per content type are unchanged from the original design spec
(Programme: title, qualification, description, duration, pathways; Course: title,
description, parent programme; Lesson: title, content textarea, type, parent course).

### Task F.2 — Handbook review queue template + HTMX approve (Level 5)

**Files:**
- Create: `~/ics/learn/templates/learn/review_queue.html`
- Add `htmx_approve_content` view to `learn/views.py`

**`review_queue.html`:**

```html
{% extends "learn/base_learn.html" %}
{% block content %}
<div class="learn-header"><h2>Review Queue</h2></div>

{% if items %}
  {% for item in items %}
  <div class="review-card" id="review-{{ item.id }}">
    <span class="lesson-type-tag">{{ item.record_type }}</span>
    <h4>{{ item.title }}</h4>
    <p class="cert-meta">Submitted: {{ item.updated_at|date:"d M Y" }}</p>
    <div class="review-actions">
      <button class="btn-primary"
              hx-post="{% url 'htmx-approve-content' item.id %}"
              hx-target="#review-{{ item.id }}"
              hx-swap="outerHTML">
        Approve
      </button>
      <button class="btn-secondary"
              hx-post="{% url 'htmx-return-content' item.id %}"
              hx-target="#review-{{ item.id }}"
              hx-swap="outerHTML">
        Return to Draft
      </button>
    </div>
  </div>
  {% endfor %}
{% else %}
  <p class="empty-state">No items pending review.</p>
{% endif %}
{% endblock %}
```

`htmx_approve_content` view sets `record.status = 'active'`, gated to Level 5.
Returns a small confirmation fragment replacing the review card.

Commit: `git add . && git commit -m "feat: learn app — authorship forms + handbook review queue templates"`

---

## Phase G — UI Polish + Role-Aware Navigation

**Exit criteria:** Learn App navigation adapts to user role server-side. Pathway banner shows for enrolled learners. Smoke test on mobile passes.

### Task G.1 — Role-aware navigation (server-side)

Role-aware tabs are rendered in `base_learn.html` using the Django request context.
No JS required — the template checks `request.user.userprofile.competence_level`
and shows the appropriate navigation items:

```html
<!-- In base_learn.html nav section -->
<nav class="learn-tab-row">
  <a href="{% url 'learn-home' %}">My Learning</a>
  <a href="{% url 'learn-catalogue' %}">Browse</a>
  {% if request.user.userprofile.competence_level >= 3 %}
    <a href="{% url 'learn-cert-queue' %}">Certifications</a>
  {% endif %}
  {% if request.user.userprofile.competence_level >= 4 %}
    <a href="{% url 'learn-author' %}">Author</a>
  {% endif %}
  {% if request.user.userprofile.competence_level >= 5 %}
    <a href="{% url 'learn-review' %}">Review Queue</a>
  {% endif %}
</nav>
```

| Level | Visible tabs |
|---|---|
| 0b (Seeker) | Browse only |
| 1–2 (Member/Disciple) | My Learning, Browse |
| 3 (Branch-Steward) | My Learning, Browse, Certifications |
| 4 (Senior Steward) | My Learning, Browse, Certifications, Author |
| 5 (Architect) | All above + Review Queue |

### Task G.2 — Pathway banner

Add to `my_learning.html` above the enrolment list, populated from the active
enrolment Activity's `kgs_pathway` and the linked Programme Record's metadata:

```html
{% if active_pathway %}
<div class="pathway-banner">
  <span class="pathway-label">{{ active_pathway }}</span>
  <span class="pathway-programme">{{ active_qualification }} · Year {{ active_year }}</span>
</div>
{% endif %}
```

The `my_learning` view resolves these values from the user's active enrolment
Activity before passing them to the template as context.

### Task G.3 — Smoke test checklist

Before closing Phase G, verify manually on mobile:

- [ ] Seeker can browse programmes, sees lock on locked programmes
- [ ] Member can enrol, see progress bar, mark a lesson complete
- [ ] Progress bar updates after lesson completion (HTMX swap visible)
- [ ] Programme at 100% shows "Awaiting certification" state on My Learning page
- [ ] Branch-Steward sees certification queue with pending item
- [ ] Steward confirms via HTMX → learner's competence level increments in DB
- [ ] Level 4 user can create a Programme and submit for review
- [ ] Level 5 user sees submitted Programme in review queue and can approve
- [ ] Approved Programme appears in public catalogue
- [ ] Role-aware nav tabs show/hide correctly for each level
- [ ] Pathway banner displays for enrolled learner

Commit: `git add . && git commit -m "feat: learn app — role-aware nav, pathway banner, smoke test pass"`

---

## Django Endpoint Summary

All endpoints required by the Learn App, in one place:

```
# Existing Records endpoints (already built — verify filters work)
GET  /api/records/?record_family=learning&record_type=programme&status=active
GET  /api/records/?record_family=learning&status=submitted
GET  /api/records/{id}/
PATCH /api/records/{id}/     (status changes — gated by role)

# Existing Activity endpoints (already built)
POST  /api/activities/
PATCH /api/activities/{id}/
GET   /api/activities/?activity_type=programme&assigned_to={id}

# New Learn endpoints (built in Phase A)
GET   /api/learn/health/
GET   /api/learn/programmes/{id}/curriculum/
GET   /api/learn/certifications/queue/
POST  /api/learn/certifications/{id}/confirm/
```

---

## File Map (Learn App additions)

```
/learn/                              ← NEW Django app
  __init__.py
  apps.py
  models.py                          ← CertificationConfirmation only
  serializers.py
  api_views.py                       ← DRF endpoints (health, curriculum, cert queue, cert confirm)
  views.py                           ← Django template views + HTMX partial views
  urls.py                            ← API routes + template view routes + HTMX routes
  signals.py                         ← auto-create certification on programme complete
  templates/
    learn/
      base_learn.html                ← extends base.html, loads HTMX, learn.css
      my_learning.html               ← My Learning home
      catalogue.html                 ← Programme catalogue
      programme_detail.html          ← Programme detail + curriculum
      lesson_viewer.html             ← Lesson content + nav
      certification_queue.html       ← Steward cert queue
      authorship.html                ← Level 4 authorship home
      author_programme_form.html     ← Create programme form
      author_course_form.html        ← Create course form
      author_lesson_form.html        ← Create lesson form
      review_queue.html              ← Level 5 Handbook review queue
      locked.html                    ← Competence gate placeholder
      partials/
        lesson_complete_btn.html     ← HTMX complete button fragment
        quiz.html                    ← Quiz form fragment

/activity/
  signals.py                         ← MODIFIED: add programme completion handler

/accounts/serializers.py             ← MODIFIED: competence_level read-only note

/frontend/assets/css/
  learn.css                          ← NEW — unchanged from original design spec
```

**Note:** `learn.html`, `learn-app.js`, and `learn.service.js` are **not created**.
The UI is fully served by Django views and templates. HTMX replaces the JS
interaction layer. `storage.js` is retained for theme/UI state only.

---

## Phase Summary

| Phase | What it builds | Entry requirement | Exit criteria |
|---|---|---|---|
| A | Django `learn` app, `CertificationConfirmation` model, DRF endpoints | Phases 0–4 done | `/api/learn/health/` 200. Confirm endpoint works. |
| B | Records endpoint filters verified, curriculum endpoint, URL structure, views/api_views split | Phase A done | All DRF queries return correct data. URL routing confirmed. |
| C | Django template views, base template, My Learning, Catalogue, Programme detail, Lesson viewer, `learn.css` | Phase B done | Learner can enrol (HTMX) and mark lessons complete (HTMX) |
| D | Quiz template + HTMX submission, Assignment submission template | Phase C done | Assessments render and submit via HTMX |
| E | Certification auto-creation signal, steward queue template, HTMX confirm | Phase D done | Steward confirms via HTMX; `competence_level` increments in DB |
| F | Authorship forms (Level 4+), Handbook review queue template, HTMX approve (Level 5) | Phase E done | Content can be authored, submitted, approved |
| G | Role-aware nav (server-side), pathway banner, mobile smoke test | Phase F done | Full smoke test checklist passes on mobile |

---

## Deferred (Post-MVP)

- Rich text editor (TipTap or similar) for lesson authorship — markdown textarea suffices for MVP
- Quiz auto-grading with score display
- Assignment peer review
- Paraclete "continue your lesson" integration (Phase 6 of main roadmap)
- Learning analytics dashboard (completion rates per programme)
- Offline lesson caching (service worker)
- Video lessons (`record_type: "video_lesson"` — deferred with Video/Live app)
- Programme ordering / sequencing UI (drag-and-drop curriculum builder)
