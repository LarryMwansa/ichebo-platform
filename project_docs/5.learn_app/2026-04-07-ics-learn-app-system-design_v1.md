# ICS Learn App — System Design & Build Roadmap

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the ICS Learn App — the digital expression of the Sceptre Qualification Programmes Framework — enabling learners to browse courses, enrol in programmes, track progress, and earn certifications that advance their competence level within the Kingdom Governance System.

**Architecture:** Django + DRF backend with a dedicated `learn` app. Vanilla JS `learn-app.js` and `learn.service.js` consume DRF endpoints. All learning content is Record objects (`record_family: "learning"`). All learner progress is Activity objects. The two are linked via the Relationship engine. No new tables beyond the existing data contract — the Learning Engine is a pattern layer over Records + Activities.

**Tech Stack:** Python/Django 4.2, DRF, PostgreSQL, Vanilla JS (IIFE modules), HTML/CSS mobile-first.

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

**Exit criteria:** Published programmes, courses, lessons are retrievable via DRF. `learn.service.js` exists and calls these endpoints. Competence gating works.

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

### Task B.3 — `learn.service.js` (frontend engine)

**Files:**
- Create: `~/ics/frontend/assets/js/engines/learn.service.js`
- Modify: `~/ics/frontend/index.html` (script load order)

```js
// learn.service.js
// ICS Learn Engine — IIFE module
// Depends on: identity.service.js, records.service.js, activity.service.js
// Called by: learn-app.js only. Never called directly from storage.

const ICSLearn = (() => {

  function authHeaders() {
    const token = localStorage.getItem('ics_token')
    return { 'Authorization': `Token ${token}`, 'Content-Type': 'application/json' }
  }

  // --- Content reads ---

  async function getProgrammes(filters = {}) {
    const params = new URLSearchParams({
      record_family: 'learning',
      record_type: 'programme',
      status: 'active',
      ...filters
    })
    const res = await fetch(`/api/records/?${params}`, { headers: authHeaders() })
    if (!res.ok) throw new Error(`getProgrammes failed: ${res.status}`)
    return res.json()
  }

  async function getProgramme(programmeId) {
    const res = await fetch(`/api/records/${programmeId}/`, { headers: authHeaders() })
    if (!res.ok) throw new Error(`getProgramme failed: ${res.status}`)
    return res.json()
  }

  async function getCurriculum(programmeId) {
    const res = await fetch(`/api/learn/programmes/${programmeId}/curriculum/`, { headers: authHeaders() })
    if (!res.ok) throw new Error(`getCurriculum failed: ${res.status}`)
    return res.json()
  }

  async function getLesson(lessonId) {
    const res = await fetch(`/api/records/${lessonId}/`, { headers: authHeaders() })
    if (!res.ok) throw new Error(`getLesson failed: ${res.status}`)
    return res.json()
  }

  // --- Enrolment ---

  async function enrol(programmeId, userId) {
    // Enrolment = create an Activity of type 'programme'
    const activity = {
      activity_type: 'programme',
      title: `Programme Enrolment`,
      assigned_to: userId,
      status: 'in_progress',
      progress: 0,
      kgs_pathway: 'learning',
      metadata: {
        source_app: 'learn',
        programme_record_id: programmeId
      }
    }
    const res = await fetch('/api/activities/', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(activity)
    })
    if (!res.ok) throw new Error(`enrol failed: ${res.status}`)
    const enrolmentActivity = await res.json()

    // Create Relationship: enrolment_activity → tracks → programme_record
    await fetch('/api/relationships/', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        from_record_id: enrolmentActivity.id,
        to_record_id: programmeId,
        relationship_type: 'tracks',
        direction: 'directed'
      })
    })

    return enrolmentActivity
  }

  async function getMyEnrolments(userId) {
    const params = new URLSearchParams({
      activity_type: 'programme',
      assigned_to: userId,
      status: 'in_progress',
      source_app: 'learn'
    })
    const res = await fetch(`/api/activities/?${params}`, { headers: authHeaders() })
    if (!res.ok) throw new Error(`getMyEnrolments failed: ${res.status}`)
    return res.json()
  }

  // --- Progress ---

  async function completeLesson(lessonActivityId) {
    const res = await fetch(`/api/activities/${lessonActivityId}/`, {
      method: 'PATCH',
      headers: authHeaders(),
      body: JSON.stringify({ status: 'completed', progress: 100 })
    })
    if (!res.ok) throw new Error(`completeLesson failed: ${res.status}`)
    return res.json()
  }

  async function updateCourseProgress(courseActivityId, completedTasks, totalTasks) {
    const progress = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0
    const payload = { progress }
    if (progress === 100) payload.status = 'completed'
    const res = await fetch(`/api/activities/${courseActivityId}/`, {
      method: 'PATCH',
      headers: authHeaders(),
      body: JSON.stringify(payload)
    })
    if (!res.ok) throw new Error(`updateCourseProgress failed: ${res.status}`)
    return res.json()
  }

  // --- Certification ---

  async function getCertificationQueue() {
    const res = await fetch('/api/learn/certifications/queue/', { headers: authHeaders() })
    if (!res.ok) throw new Error(`getCertificationQueue failed: ${res.status}`)
    return res.json()
  }

  async function confirmCertification(certificationId, notes = '') {
    const res = await fetch(`/api/learn/certifications/${certificationId}/confirm/`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ notes })
    })
    if (!res.ok) throw new Error(`confirmCertification failed: ${res.status}`)
    return res.json()
  }

  // --- Handbook review (Level 5) ---

  async function getReviewQueue() {
    const params = new URLSearchParams({
      record_family: 'learning',
      status: 'submitted'
    })
    const res = await fetch(`/api/records/?${params}`, { headers: authHeaders() })
    if (!res.ok) throw new Error(`getReviewQueue failed: ${res.status}`)
    return res.json()
  }

  async function approveContent(recordId) {
    const res = await fetch(`/api/records/${recordId}/`, {
      method: 'PATCH',
      headers: authHeaders(),
      body: JSON.stringify({ status: 'active' })
    })
    if (!res.ok) throw new Error(`approveContent failed: ${res.status}`)
    return res.json()
  }

  async function submitForReview(recordId) {
    const res = await fetch(`/api/records/${recordId}/`, {
      method: 'PATCH',
      headers: authHeaders(),
      body: JSON.stringify({ status: 'submitted' })
    })
    if (!res.ok) throw new Error(`submitForReview failed: ${res.status}`)
    return res.json()
  }

  return {
    getProgrammes,
    getProgramme,
    getCurriculum,
    getLesson,
    enrol,
    getMyEnrolments,
    completeLesson,
    updateCourseProgress,
    getCertificationQueue,
    confirmCertification,
    getReviewQueue,
    approveContent,
    submitForReview
  }
})()
```

**Update script load order in `index.html`:**

```html
<script src="/assets/js/engines/activity.service.js"></script>
<script src="/assets/js/engines/activity.store.js"></script>
<script src="/assets/js/engines/learn.service.js"></script>   <!-- NEW — after activity -->
<script src="/assets/js/engines/paraclete.service.js"></script>
```

Commit: `git add . && git commit -m "feat: learn.service.js — content, enrolment, progress, certification"`

---

## Phase C — Enrolment + Progress Tracking (UI)

**Exit criteria:** A learner can browse programmes, enrol, view their curriculum, mark lessons complete, and see progress bars update.

### Task C.1 — Learn App HTML shell

**Files:**
- Create: `~/ics/frontend/learn.html`

Mobile-first page shell. Sections shown/hidden by JS based on current view state.

```html
<!DOCTYPE html>
<html lang="en" data-theme="system">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Learn — ICS</title>
  <link rel="stylesheet" href="/assets/css/main.css">
  <link rel="stylesheet" href="/assets/css/learn.css">
</head>
<body>
  <!-- Top navbar (injected by navbar.js) -->
  <div id="navbar-container"></div>

  <!-- Learn App views — one visible at a time -->
  <main id="learn-root" class="app-root">

    <!-- View: My Learning (home) -->
    <section id="view-my-learning" class="learn-view" data-view="my-learning">
      <div class="learn-header">
        <h1>Learn</h1>
        <button id="btn-browse" class="btn-secondary">Browse Programmes</button>
      </div>
      <div id="active-enrolments" class="enrolment-list"></div>
      <div id="completed-certifications" class="certification-list"></div>
    </section>

    <!-- View: Programme Catalogue -->
    <section id="view-catalogue" class="learn-view hidden" data-view="catalogue">
      <div class="learn-header">
        <button id="btn-back-home" class="btn-back">← My Learning</button>
        <h2>Programmes</h2>
      </div>
      <div id="pathway-tabs" class="tab-row"></div>
      <div id="programme-list" class="programme-grid"></div>
    </section>

    <!-- View: Programme Detail -->
    <section id="view-programme" class="learn-view hidden" data-view="programme">
      <div id="programme-detail-container"></div>
    </section>

    <!-- View: Lesson Viewer -->
    <section id="view-lesson" class="learn-view hidden" data-view="lesson">
      <div id="lesson-viewer-container"></div>
    </section>

    <!-- View: Steward — Certification Queue -->
    <section id="view-cert-queue" class="learn-view hidden" data-view="cert-queue">
      <div class="learn-header">
        <h2>Certifications Pending</h2>
      </div>
      <div id="cert-queue-list"></div>
    </section>

    <!-- View: Level 4 — Content Authorship -->
    <section id="view-authorship" class="learn-view hidden" data-view="authorship">
      <div class="learn-header">
        <h2>Course Authorship</h2>
      </div>
      <div id="authorship-container"></div>
    </section>

    <!-- View: Level 5 — Handbook Review Queue -->
    <section id="view-review-queue" class="learn-view hidden" data-view="review-queue">
      <div class="learn-header">
        <h2>Review Queue</h2>
      </div>
      <div id="review-queue-list"></div>
    </section>

  </main>

  <!-- Bottom nav (injected by bottom-nav.js) -->
  <div id="bottom-nav-container"></div>

  <!-- Engine scripts -->
  <script src="/assets/js/core/storage.js"></script>
  <script src="/assets/js/engines/identity.service.js"></script>
  <script src="/assets/js/engines/records.service.js"></script>
  <script src="/assets/js/engines/relationships.service.js"></script>
  <script src="/assets/js/engines/activity.service.js"></script>
  <script src="/assets/js/engines/activity.store.js"></script>
  <script src="/assets/js/engines/learn.service.js"></script>
  <script src="/assets/js/core/auth.js"></script>
  <script src="/assets/js/core/router.js"></script>
  <script src="/assets/js/components/navbar.js"></script>
  <script src="/assets/js/components/bottom-nav.js"></script>
  <script src="/assets/js/apps/learn-app.js"></script>
</body>
</html>
```

Commit: `git add . && git commit -m "feat: learn.html shell — all view sections"`

---

### Task C.2 — `learn-app.js` — My Learning + Catalogue views

**Files:**
- Create: `~/ics/frontend/assets/js/apps/learn-app.js`

```js
// learn-app.js
// ICS Learn App — IIFE module
// Depends on: ICSLearn, ICSIdentity

const ICSLearnApp = (() => {

  let currentUser = null

  // --- View router ---
  function showView(viewName) {
    document.querySelectorAll('.learn-view').forEach(v => v.classList.add('hidden'))
    const target = document.querySelector(`[data-view="${viewName}"]`)
    if (target) target.classList.remove('hidden')
  }

  // --- My Learning (home) ---
  async function renderMyLearning() {
    showView('my-learning')
    const enrolments = await ICSLearn.getMyEnrolments(currentUser.id)
    const container = document.getElementById('active-enrolments')

    if (!enrolments.results || enrolments.results.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <p>You are not enrolled in any programme yet.</p>
          <button onclick="ICSLearnApp.renderCatalogue()" class="btn-primary">
            Browse Programmes
          </button>
        </div>`
      return
    }

    container.innerHTML = enrolments.results.map(enrolment => `
      <div class="enrolment-card" data-id="${enrolment.id}">
        <div class="enrolment-title">${enrolment.title}</div>
        <div class="progress-bar-wrap">
          <div class="progress-bar" style="width:${enrolment.progress}%"></div>
        </div>
        <span class="progress-label">${enrolment.progress}% complete</span>
        <button class="btn-primary" onclick="ICSLearnApp.resumeEnrolment('${enrolment.id}', '${enrolment.metadata?.programme_record_id}')">
          Continue
        </button>
      </div>
    `).join('')
  }

  // --- Programme Catalogue ---
  async function renderCatalogue() {
    showView('catalogue')
    const programmes = await ICSLearn.getProgrammes()
    const list = document.getElementById('programme-list')

    if (!programmes.results || programmes.results.length === 0) {
      list.innerHTML = '<p class="empty-state">No programmes available.</p>'
      return
    }

    list.innerHTML = programmes.results.map(p => {
      const userLevel = currentUser.competence_level || 0
      const requiredLevel = p.permissions?.required_level || 1
      const locked = userLevel < requiredLevel
      return `
        <div class="programme-card ${locked ? 'locked' : ''}" data-id="${p.id}">
          <div class="programme-badge">${p.metadata?.qualification || 'Programme'}</div>
          <h3 class="programme-title">${p.title}</h3>
          <p class="programme-meta">${p.metadata?.duration_years || '?'} year${p.metadata?.duration_years !== 1 ? 's' : ''}</p>
          ${locked
            ? `<span class="lock-indicator">Level ${requiredLevel} required</span>`
            : `<button class="btn-primary" onclick="ICSLearnApp.renderProgramme('${p.id}')">View</button>`
          }
        </div>
      `
    }).join('')
  }

  // --- Programme Detail + Enrolment ---
  async function renderProgramme(programmeId) {
    showView('programme')
    const { programme, curriculum } = await ICSLearn.getCurriculum(programmeId)
    const container = document.getElementById('programme-detail-container')

    const enrolments = await ICSLearn.getMyEnrolments(currentUser.id)
    const alreadyEnrolled = (enrolments.results || []).some(
      e => e.metadata?.programme_record_id === programmeId
    )

    container.innerHTML = `
      <div class="programme-detail">
        <button class="btn-back" onclick="ICSLearnApp.renderCatalogue()">← Programmes</button>
        <div class="programme-badge">${programme.metadata?.qualification || 'Programme'}</div>
        <h2>${programme.title}</h2>
        <p class="programme-description">${programme.content || programme.summary || ''}</p>
        <div class="programme-meta-row">
          <span>${programme.metadata?.duration_years || '?'} years</span>
          <span>Level ${programme.permissions?.required_level || 1}</span>
        </div>
        ${!alreadyEnrolled
          ? `<button class="btn-primary enrol-btn" onclick="ICSLearnApp.enrol('${programmeId}')">
               Enrol in this Programme
             </button>`
          : `<span class="enrolled-badge">Enrolled</span>`
        }
        <div class="curriculum-list">
          <h3>Curriculum</h3>
          ${curriculum.map((item, i) => `
            <div class="course-block">
              <h4>${i + 1}. ${item.course.title}</h4>
              <ul class="lesson-list">
                ${item.lessons.map(l => `
                  <li class="lesson-item" data-id="${l.id}">
                    <span class="lesson-type-tag">${l.record_type}</span>
                    ${l.title}
                  </li>
                `).join('')}
              </ul>
            </div>
          `).join('')}
        </div>
      </div>
    `
  }

  async function enrol(programmeId) {
    try {
      await ICSLearn.enrol(programmeId, currentUser.id)
      await renderProgramme(programmeId)
    } catch (err) {
      alert('Enrolment failed. Please try again.')
      console.error(err)
    }
  }

  async function resumeEnrolment(enrolmentActivityId, programmeId) {
    await renderProgramme(programmeId)
  }

  // --- Boot ---
  async function init() {
    currentUser = await ICSIdentity.getCurrentUser()
    if (!currentUser) {
      window.location.href = '/login.html'
      return
    }
    renderMyLearning()

    document.getElementById('btn-browse')?.addEventListener('click', renderCatalogue)
    document.getElementById('btn-back-home')?.addEventListener('click', renderMyLearning)
  }

  document.addEventListener('DOMContentLoaded', init)

  return { renderMyLearning, renderCatalogue, renderProgramme, enrol, resumeEnrolment }
})()
```

Commit: `git add . && git commit -m "feat: learn-app.js — my learning, catalogue, programme detail, enrolment"`

---

### Task C.3 — Lesson Viewer UI

**Files:**
- Modify: `~/ics/frontend/assets/js/apps/learn-app.js`

Add the `renderLesson` function and wire up lesson clicks.

```js
// Add to ICSLearnApp IIFE

async function renderLesson(lessonId, courseActivityId, courseItems) {
  showView('lesson')
  const lesson = await ICSLearn.getLesson(lessonId)
  const container = document.getElementById('lesson-viewer-container')

  const currentIndex = courseItems.findIndex(l => l.id === lessonId)
  const prevLesson = currentIndex > 0 ? courseItems[currentIndex - 1] : null
  const nextLesson = currentIndex < courseItems.length - 1 ? courseItems[currentIndex + 1] : null

  container.innerHTML = `
    <div class="lesson-viewer">
      <button class="btn-back" id="lesson-back-btn">← Back to Course</button>
      <span class="lesson-type-tag">${lesson.record_type}</span>
      <h2 class="lesson-title">${lesson.title}</h2>
      <div class="lesson-content">${renderMarkdown(lesson.content || '')}</div>
      <div class="lesson-nav">
        ${prevLesson
          ? `<button class="btn-secondary" onclick="ICSLearnApp.renderLesson('${prevLesson.id}', '${courseActivityId}', courseItems)">← Previous</button>`
          : '<span></span>'
        }
        <button class="btn-primary complete-btn" id="btn-complete-lesson" data-lesson-id="${lessonId}">
          Mark Complete
        </button>
        ${nextLesson
          ? `<button class="btn-secondary" onclick="ICSLearnApp.renderLesson('${nextLesson.id}', '${courseActivityId}', courseItems)">Next →</button>`
          : '<span></span>'
        }
      </div>
    </div>
  `

  document.getElementById('btn-complete-lesson').addEventListener('click', async (e) => {
    const btn = e.currentTarget
    btn.disabled = true
    btn.textContent = 'Completing...'
    await ICSLearn.completeLesson(lessonId)
    btn.textContent = '✓ Completed'
    btn.classList.add('completed')
  })
}

function renderMarkdown(text) {
  // Minimal markdown: bold, italic, paragraphs, line breaks
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
    .replace(/^/, '<p>')
    .replace(/$/, '</p>')
}
```

Commit: `git add . && git commit -m "feat: learn app — lesson viewer with complete button + nav"`

---

### Task C.4 — `learn.css`

**Files:**
- Create: `~/ics/frontend/assets/css/learn.css`

Mobile-first styles using the platform's existing CSS variables.

```css
/* learn.css — ICS Learn App styles */

/* Views */
.learn-view { padding: var(--space-4); }
.learn-view.hidden { display: none; }

.learn-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}
.learn-header h1, .learn-header h2 { margin: 0; }

/* Programme grid */
.programme-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-3);
}
@media (min-width: 768px) {
  .programme-grid { grid-template-columns: repeat(2, 1fr); }
}

/* Programme card */
.programme-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  background: var(--color-surface);
}
.programme-card.locked { opacity: 0.6; }
.programme-badge {
  display: inline-block;
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-primary);
  margin-bottom: var(--space-2);
}
.lock-indicator {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

/* Enrolment card */
.enrolment-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  background: var(--color-surface);
  margin-bottom: var(--space-3);
}
.enrolment-title { font-weight: 600; margin-bottom: var(--space-2); }
.progress-bar-wrap {
  height: 6px;
  background: var(--color-border);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: var(--space-1);
}
.progress-bar {
  height: 100%;
  background: var(--color-primary);
  border-radius: 3px;
  transition: width 0.3s ease;
}
.progress-label { font-size: var(--text-sm); color: var(--color-text-muted); }

/* Lesson list */
.curriculum-list { margin-top: var(--space-5); }
.course-block { margin-bottom: var(--space-4); }
.lesson-list { list-style: none; padding: 0; margin: var(--space-2) 0 0 0; }
.lesson-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  cursor: pointer;
}
.lesson-item:hover { background: var(--color-hover); }
.lesson-type-tag {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  color: var(--color-text-muted);
  min-width: 60px;
}

/* Lesson viewer */
.lesson-viewer { max-width: 680px; margin: 0 auto; }
.lesson-title { margin: var(--space-3) 0; }
.lesson-content {
  line-height: 1.7;
  color: var(--color-text);
  margin-bottom: var(--space-5);
}
.lesson-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

/* Certification */
.enrolled-badge {
  display: inline-block;
  padding: var(--space-1) var(--space-3);
  background: var(--color-success-bg);
  color: var(--color-success);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-weight: 600;
}
.complete-btn.completed {
  background: var(--color-success);
  cursor: default;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: var(--space-8) var(--space-4);
  color: var(--color-text-muted);
}
```

Commit: `git add . && git commit -m "feat: learn.css — mobile-first styles for all learn views"`

---

## Phase D — Assessments

**Exit criteria:** Quiz and Assignment records render correctly in the lesson viewer. Submission marks the assessment activity complete.

### Task D.1 — Quiz renderer

**Files:**
- Modify: `~/ics/frontend/assets/js/apps/learn-app.js`

Quiz questions are stored in `Record.custom_fields` as a JSON structure:

```js
// custom_fields structure for record_type: "quiz"
{
  questions: [
    {
      id: "q1",
      text: "What is the primary focus of the New Life Pathway?",
      type: "multiple_choice",  // or "short_answer"
      options: ["Salvation and identity", "Leadership skills", "Mission strategy"],
      correct_index: 0
    }
  ]
}
```

The `renderLesson` function detects `lesson.record_type === 'quiz'` and renders a quiz form instead of markdown content. On all questions answered, marks the activity complete.

### Task D.2 — Assignment submission

Assignment submission creates a child Record linked to the assignment:

```js
// In learn.service.js — add:
async function submitAssignment(assignmentId, submissionText, userId) {
  // Create a child Record for the submission
  const submission = await ICSRecords.create({
    record_class: 'personal',
    record_family: 'learning',
    record_type: 'note',         // submission is a personal note-type record
    title: `Assignment Submission`,
    content: submissionText,
    created_by: userId,
    metadata: { source_app: 'learn', assignment_record_id: assignmentId }
  })

  // Link submission → references → assignment
  await ICSRelationships.create({
    from_record_id: submission.id,
    to_record_id: assignmentId,
    relationship_type: 'references',
    direction: 'directed'
  })

  return submission
}
```

Commit: `git add . && git commit -m "feat: learn app — quiz renderer + assignment submission"`

---

## Phase E — Certification + Competence Advancement (UI)

**Exit criteria:** Learner sees "Awaiting certification" when programme is 100% complete. Steward sees certification queue. Steward can confirm. Learner's competence level advances.

### Task E.1 — Auto-certification on programme completion

Add to `learn-app.js` — called after every lesson completion that might complete a course or programme:

```js
async function checkProgrammeCompletion(enrolmentActivityId) {
  const activity = await ICSActivity.get(enrolmentActivityId)
  if (activity.progress === 100 && activity.status === 'completed') {
    // Programme complete — show awaiting certification UI
    renderAwaitingCertification(activity)
  }
}
```

The backend auto-creates the draft Certification Record via a Django signal on
`Activity` save when `progress == 100 AND activity_type == 'programme'`.

**Add to `activity/signals.py`:**

```python
# activity/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Activity
import uuid


@receiver(post_save, sender=Activity)
def create_certification_on_programme_completion(sender, instance, **kwargs):
    """Auto-create a draft Certification Record when a programme Activity completes."""
    if (
        instance.activity_type == 'programme'
        and instance.status == 'completed'
        and instance.progress == 100
        and instance.metadata.get('source_app') == 'learn'
    ):
        from records.models import Record
        programme_record_id = instance.metadata.get('programme_record_id')

        # Avoid creating duplicate certifications
        already_exists = Record.objects.filter(
            record_type='certification',
            metadata__contains={'enrolment_activity_id': str(instance.id)}
        ).exists()

        if not already_exists:
            Record.objects.create(
                id=uuid.uuid4(),
                record_class='personal',
                record_family='learning',
                record_type='certification',
                status='draft',
                title=f'Certification Pending',
                created_by=instance.assigned_to,
                metadata={
                    'source_app': 'learn',
                    'programme_record_id': programme_record_id,
                    'enrolment_activity_id': str(instance.id),
                    'learner_id': str(instance.assigned_to_id),
                    'target_level': _get_target_level(programme_record_id)
                }
            )


def _get_target_level(programme_record_id):
    """Look up the target competence level from the programme Record's metadata."""
    from records.models import Record
    try:
        prog = Record.objects.get(id=programme_record_id)
        return prog.metadata.get('competence_level_target', 1)
    except Record.DoesNotExist:
        return 1
```

Register in `activity/apps.py`:

```python
def ready(self):
    import activity.signals  # noqa
```

### Task E.2 — Steward certification queue UI

Add `renderCertificationQueue` to `learn-app.js`:

```js
async function renderCertificationQueue() {
  showView('cert-queue')
  const certifications = await ICSLearn.getCertificationQueue()
  const list = document.getElementById('cert-queue-list')

  if (!certifications.length) {
    list.innerHTML = '<p class="empty-state">No certifications pending.</p>'
    return
  }

  list.innerHTML = certifications.map(cert => `
    <div class="cert-card" data-id="${cert.id}">
      <h4>${cert.title}</h4>
      <p class="cert-meta">Submitted: ${new Date(cert.created_at).toLocaleDateString()}</p>
      <textarea class="cert-notes" placeholder="Notes (optional)" id="notes-${cert.id}"></textarea>
      <button class="btn-primary" onclick="ICSLearnApp.confirmCert('${cert.id}')">
        Confirm & Advance Level
      </button>
    </div>
  `).join('')
}

async function confirmCert(certId) {
  const notes = document.getElementById(`notes-${certId}`)?.value || ''
  try {
    await ICSLearn.confirmCertification(certId, notes)
    renderCertificationQueue()
  } catch (err) {
    alert('Confirmation failed. Please try again.')
    console.error(err)
  }
}
```

Commit: `git add . && git commit -m "feat: learn app — certification queue UI + steward confirmation flow"`

---

## Phase F — Content Authorship + Handbook Review (UI)

**Exit criteria:** Level 4+ users can create and submit Programmes, Courses, and Lessons. Level 5 users see a review queue and can approve content.

### Task F.1 — Authorship UI (Level 4+)

**Files:**
- Modify: `~/ics/frontend/assets/js/apps/learn-app.js`

The authorship view shows a form to create a new Programme or Course.
Uses `ICSRecords.create()` directly for record creation.
After creation, shows a "Submit for Review" button that calls
`ICSLearn.submitForReview(recordId)`.

Core form fields for a Programme:
- Title
- Qualification level (select: Certificate | Diploma | Degree | Masters | Doctorate)
- Description
- Duration (years)
- KGS Pathways (multi-select from the eight pathways)

Core form fields for a Course:
- Title
- Description
- Parent Programme (select from user's authored programmes)

Core form fields for a Lesson:
- Title
- Content (markdown textarea)
- Type (lesson | assignment | quiz)
- Parent Course (select)

### Task F.2 — Handbook Review Queue UI (Level 5)

```js
async function renderReviewQueue() {
  showView('review-queue')
  const items = await ICSLearn.getReviewQueue()
  const list = document.getElementById('review-queue-list')

  list.innerHTML = items.results?.map(item => `
    <div class="review-card">
      <span class="lesson-type-tag">${item.record_type}</span>
      <h4>${item.title}</h4>
      <p class="cert-meta">Submitted: ${new Date(item.updated_at).toLocaleDateString()}</p>
      <div class="review-actions">
        <button class="btn-primary" onclick="ICSLearnApp.approveContent('${item.id}')">Approve</button>
        <button class="btn-secondary" onclick="ICSLearnApp.returnToDraft('${item.id}')">Return</button>
      </div>
    </div>
  `).join('') || '<p class="empty-state">No items pending review.</p>'
}

async function approveContent(recordId) {
  await ICSLearn.approveContent(recordId)
  renderReviewQueue()
}

async function returnToDraft(recordId) {
  await fetch(`/api/records/${recordId}/`, {
    method: 'PATCH',
    headers: ICSLearn._authHeaders(),
    body: JSON.stringify({ status: 'draft' })
  })
  renderReviewQueue()
}
```

Commit: `git add . && git commit -m "feat: learn app — authorship UI + handbook review queue"`

---

## Phase G — UI Polish + Role-Aware Navigation

**Exit criteria:** Learn App home adapts to user role. Steward and Level 4+ users see their respective action tabs. Pathway banner shows for enrolled learners. Smoke test on mobile passes.

### Task G.1 — Role-aware navigation tabs

On boot, `init()` checks `currentUser.competence_level` and renders tabs accordingly:

| Level | Visible tabs |
|---|---|
| 0b (Seeker) | Browse only |
| 1–2 (Member/Disciple) | My Learning, Browse |
| 3 (Branch-Steward) | My Learning, Browse, Certifications |
| 4 (Senior Steward) | My Learning, Browse, Certifications, Author |
| 5 (Architect) | All above + Review Queue |

### Task G.2 — Pathway banner

For enrolled learners, show above the enrolment list:

```html
<div class="pathway-banner">
  <span class="pathway-label">New Life Pathway</span>
  <span class="pathway-programme">Certificate Programme · Year 1</span>
</div>
```

Populated from the active enrolment Activity's `kgs_pathway` field and the
linked Programme Record's `metadata.qualification`.

### Task G.3 — Smoke test checklist

Before closing Phase G, verify manually on mobile:

- [ ] Seeker can browse programmes, sees lock on locked programmes
- [ ] Member can enrol, see progress bar, mark a lesson complete
- [ ] Progress bar updates after lesson completion
- [ ] Programme at 100% shows "Awaiting certification" state
- [ ] Branch-Steward sees certification queue with pending item
- [ ] Steward confirms → learner's competence level increments in DB
- [ ] Level 4 user can create a Programme and submit for review
- [ ] Level 5 user sees submitted Programme in review queue and can approve
- [ ] Approved Programme appears in public catalogue

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
/learn/                          ← NEW Django app
  __init__.py
  apps.py
  models.py                      ← CertificationConfirmation only
  serializers.py
  views.py                       ← health, curriculum, cert queue, cert confirm
  urls.py
  signals.py                     ← auto-create certification on programme complete

/activity/
  signals.py                     ← MODIFIED: add programme completion handler

/accounts/serializers.py         ← MODIFIED: competence_level read-only note

/frontend/
  learn.html                     ← NEW page shell
  assets/
    css/
      learn.css                  ← NEW
    js/
      engines/
        learn.service.js         ← NEW (after activity.service.js in load order)
      apps/
        learn-app.js             ← NEW
```

---

## Phase Summary

| Phase | What it builds | Entry requirement | Exit criteria |
|---|---|---|---|
| A | Django learn app, certification endpoint, curriculum endpoint | Phases 0–4 done | `/api/learn/health/` 200. Confirm endpoint works. |
| B | Records endpoint filters verified, learn.service.js | Phase A done | JS service calls all endpoints successfully |
| C | My Learning, Catalogue, Programme detail, Enrolment, Lesson viewer | Phase B done | Learner can enrol and mark lessons complete |
| D | Quizzes, Assignment submission | Phase C done | Assessments render and submit |
| E | Certification auto-creation, steward queue, level advancement | Phase D done | Steward can confirm; competence_level increments |
| F | Content authorship (Level 4+), Handbook review queue (Level 5) | Phase E done | Content can be authored, submitted, approved |
| G | Role-aware UI, pathway banner, mobile smoke test | Phase F done | Full smoke test passes on mobile |

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
