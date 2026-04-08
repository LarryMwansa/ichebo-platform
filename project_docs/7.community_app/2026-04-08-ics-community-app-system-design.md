# ICS Community App — System Design & Build Roadmap

> **UI Architecture:** Django templates + HTMX throughout.
> All UI is server-rendered. HTMX handles form submissions, member list updates,
> and partial refreshes. `storage.js` is retained for UI state (theme, session token) only.

> **Data Contract reference:** `2026-04-08-ics-platform-data-contract_v8.md` —
> all schemas and patterns in this document originate from Parts 2, 3, 4, 11, and 14
> of that contract. Read the contract before implementing.

**Goal:** Build the ICS Community App — the digital expression of KGS Pillar 6
(Communities & Networks) — enabling members to see and experience their community,
and stewards to manage membership, gatherings, and announcements within their tenant scope.

**Architecture:** Django + DRF backend with a dedicated `community` Django app (to be
scaffolded). The Community App adds Django template views and HTMX interactions on top
of the existing Records, Activity, and Identity engines. It owns **no models** of its
own in MVP — it is a UI and transaction coordination layer. One model is stubbed
(`MembershipRequest`) but not wired to UI until Phase 2.

**Tech Stack:** Python/Django 4.2, DRF, PostgreSQL, Django templates, HTMX,
`community.css` (mobile-first, CSS variables).

---

## System Overview

### The Community Stack

```
KGS Layer          Pillar 6 — Communities & Networks
                   ↓ expressed as
Structural Layer   Sceptre Community (church_node Tenant)
                   ↓ populated by
Identity Layer     UserPermission (membership rows with metadata)
                   ↓ governed through
Content Layer      community/announcement Record — broadcasts to members
                   community/gathering Record — scheduled events
                   ↓ gathering also writes
Execution Layer    activity/event Activity (source_app:'community')
                   ↓ feeds into
Calendar App       GET /api/calendar/events/?source_app=community
                   ↓ and eventually
Dashboard          Upcoming gatherings widget, community pulse
```

### Two-surface model

```
Community App
  │
  ├── "My Community"  (member surface — Level 1+)
  │     Scope:  UserPermission rows where user_id = request.user, is_active = True
  │     Shows:  Active tenant(s), formation stage, service order, shepherd,
  │             upcoming gatherings (30 days), latest announcements, gifts summary
  │
  └── "Community Management"  (steward surface — Level 3+)
        Scope:  UserPermission.tenant_path LIKE '{steward.scope_path}%'
        Shows:  Member directory, formation pipeline, member profile,
                announcement management, gathering management,
                pastoral assignments, service order placement
```

### User roles in the Community App

| Role | What they can do |
|---|---|
| Seeker (0b) | No access — no tenant membership |
| Member (Level 1) | My Community: own tenant(s), gatherings, announcements |
| Disciple (Level 2) | My Community + limited directory (names and orders only) |
| Branch-Steward (Level 3) | Full My Community + full Management for their branch |
| Senior Steward (Level 4+) | All above + multi-branch directory across their scope |
| Architect (Level 5) | All above + cross-tenant visibility |

---

## Feature List (All Features — Unphased)

### F1 — My Community Surface

- Community header: tenant name, tier badge, description, logo
- Formation stage card:
  - Competence level label ("Foundational Disciple", "Active Contributor", etc.)
  - KGS Participation stage ("Formation", "Alignment", "Service", etc.)
  - Visual progress indicator (level 1–5 steps)
- Shepherd card: display_name of shepherd (if `UserPermission.metadata.shepherd_id` is set)
- Service order card: current service order placement (if `metadata.service_order` is set)
- Upcoming gatherings list (next 30 days via Calendar endpoint, source_app:'community')
  - Format badge: in_person / digital / hybrid
  - Stream link (if `custom_fields.stream_url` present)
  - Location (if `custom_fields.location` present)
- Latest announcements (most recent 5, record_type:'announcement', visibility:'tenant')
- Gifts register summary: count of active gifts with link to Activity App gifts register

### F2 — Member Directory (Level 3+ Management Surface)

- Searchable list: all active members within steward's scope_path
  - Search by display_name (HTMX typeahead)
  - Filter by: service order (dropdown), formation level (radio), shepherd (dropdown)
- Member card: avatar, display_name, competence level badge, service order label,
  tenant name (for multi-branch stewards)
- Tap/click → Member Profile detail
- Export: deferred (post-MVP)

### F3 — Formation Pipeline (Level 3+ Management Surface)

- Visual pipeline: members grouped by competence level
  - Columns: Seeker (0b) | Member (L1) | Disciple (L2) | Steward (L3) | Senior (L4) | Architect (L5)
  - Count per stage, member thumbnails/names within each column
- Pipeline shows who is "stuck" at each stage (no recent Learn activity or certification)
- Link to member profile for direct pastoral action

### F4 — Member Profile (Level 3+ Management Surface)

- Full member detail: avatar, display_name, email (Level 3+), competence level,
  join date, service order, shepherd assignment
- Formation history: competence level progression (read from Learn certifications
  via `GET /api/records/?record_family=learning&record_type=certification&created_by={id}`)
- Gifts summary: active gifts from Activity App gifts register
- Actions:
  - Assign/change shepherd (HTMX — PATCH UserPermission.metadata.shepherd_id)
  - Set/change service order (HTMX — PATCH UserPermission.metadata.service_order)
  - Deactivate membership (HTMX — PATCH UserPermission.is_active = false, with confirmation)

### F5 — Announcement Management (Level 3+)

- Announcement list: all active announcements for the steward's tenant
  - Sorted by created_at descending
  - Status badges: active / archived
- Create announcement: HTMX form
  - Fields: title, content (markdown textarea), tenant selector (if multi-branch steward)
  - Visibility is always 'tenant' (no choice — all member announcements are tenant-scoped)
  - On submit: POST /api/records/ with record_family:'community', record_type:'announcement'
- Archive announcement: HTMX toggle (PATCH status:'archived')
- Announcements appear on My Community surface for Level 1+ members

### F6 — Gathering Management (Level 3+)

- Gathering list: all active and upcoming gatherings for the steward's tenant
  - Sorted by custom_fields.scheduled_at ascending
  - Format badge: in_person / digital / hybrid
  - Status: upcoming / past / cancelled
- Create gathering: HTMX form (dual-write — see Part 14.4 of data contract)
  - Fields: title, description, format (in_person | digital | hybrid),
    scheduled_at (datetime picker), location (shown if format != digital),
    stream_url (shown if format != in_person), capacity (optional)
  - On submit: dual-write transaction (gathering Record + event Activity + Relationship)
  - On success: HTMX swaps gathering list with new card included
- Cancel gathering: HTMX confirmation → PATCH Record status:'cancelled' +
  PATCH Activity status:'cancelled' (transaction.atomic)
- Gatherings feed the Calendar App automatically via the event Activity

### F7 — Pastoral Assignment (Level 3+)

- Set shepherd on a member's profile: HTMX typeahead to select from Level 3+
  users within scope → PATCH UserPermission.metadata.shepherd_id
- Unset shepherd: clear button → PATCH shepherd_id: null
- Shepherd's flock view (optional — deferred if time): filtered member directory
  showing all members whose shepherd_id = request.user.id

### F8 — Service Order Placement (Level 3+)

- Set service order on a member's profile: dropdown of the 24 KGS Service Orders
  (hardcoded list — not a DB table in MVP) → PATCH UserPermission.metadata.service_order
- Clear placement: clear button → PATCH service_order: null
- The 24 Service Orders list is defined in community/constants.py and rendered
  as a select widget — consistent with the same free-text label used in the
  Activity App gifts register

### F9 — Gifts Register Cross-View (Level 3+)

- On the member profile, display a read-only summary of the member's gifts:
  `GET /api/activities/?activity_type=skill&created_by={member_id}&tenant_id={tenant_id}`
- Shows: gift title, KGS pathway, self-assessed competence %, service order label
- Link to Activity App team gifts register for full view
- No write access from Community App — gifts are owned by the Activity App

### F10 — Paraclete Integration Endpoint (Backend)

Community data available to Paraclete at Phase 6:

```
GET /api/calendar/events/?source_app=community&tenant_id={id}
    &from={today}&to={+7days}
    → upcoming gatherings for digest
```

Paraclete uses this to surface "Upcoming gathering: Sunday Service — in 2 days"
in the daily digest. No new endpoint required — Calendar endpoint already supports
this filter.

---

## Build Phases

### Phase A — Community App Scaffold + Health Check

*Entry requirement: Phases 0–4 of main roadmap complete. Records, Activity, and
Identity engines all have working DRF endpoints.*

#### Task A.1 — Django app scaffold

```bash
cd ~/ics
python manage.py startapp community
```

Register in `INSTALLED_APPS`:
```python
# ics_project/settings/base.py
INSTALLED_APPS = [
    ...
    'community',
]
```

#### Task A.2 — MembershipRequest model (stub — not wired to UI)

```python
# community/models.py
import uuid
from django.conf import settings
from django.db import models


class MembershipRequest(models.Model):
    """
    Deferred — Phase 2 of Community App.
    Stubbed here so migration exists and Phase 2 requires no schema change.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id   = models.UUIDField()
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='membership_requests_created'
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='membership_requests_made'
    )
    tenant      = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    status      = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('denied', 'Denied')],
        default='pending'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='membership_requests_reviewed'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    note        = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'community_membership_request'
        ordering = ['-created_at']

    def __str__(self):
        return f"MembershipRequest({self.user_id} → {self.tenant_id}, {self.status})"
```

```bash
python manage.py makemigrations community
python manage.py migrate
```

#### Task A.3 — Service order constants

```python
# community/constants.py
KGS_SERVICE_ORDERS = [
    # A — Apostolic & Spiritual Ministry
    ("Order of Apostolic Service",     "Apostolic & Spiritual Ministry"),
    ("Order of Prophetic Ministry",    "Apostolic & Spiritual Ministry"),
    ("Order of Teaching and Doctrine", "Apostolic & Spiritual Ministry"),
    ("Order of Prayer and Intercession","Apostolic & Spiritual Ministry"),
    # B — Leadership & Governance Support
    ("Order of Governance Support",    "Leadership & Governance Support"),
    ("Order of Strategic Coordination","Leadership & Governance Support"),
    ("Order of Leadership Assistance", "Leadership & Governance Support"),
    ("Order of Communication and Alignment","Leadership & Governance Support"),
    # C — Formation & Teaching
    ("Order of Discipleship Facilitation","Formation & Teaching"),
    ("Order of Training and Instruction",  "Formation & Teaching"),
    ("Order of Mentorship and Coaching",   "Formation & Teaching"),
    ("Order of Curriculum Development",    "Formation & Teaching"),
    # D — Mission & Outreach
    ("Order of Evangelism",            "Mission & Outreach"),
    ("Order of Mission Teams",         "Mission & Outreach"),
    ("Order of Community Outreach",    "Mission & Outreach"),
    ("Order of Expansion and Planting","Mission & Outreach"),
    # E — Community Life & Care
    ("Order of Pastoral Care",         "Community Life & Care"),
    ("Order of Community Building",    "Community Life & Care"),
    ("Order of Hospitality and Welcome","Community Life & Care"),
    ("Order of Welfare and Support",   "Community Life & Care"),
    # F — Operations & Stewardship
    ("Order of Administration",        "Operations & Stewardship"),
    ("Order of Resource Management",   "Operations & Stewardship"),
    ("Order of Logistics and Events",  "Operations & Stewardship"),
    ("Order of Media and Communication","Operations & Stewardship"),
]

KGS_SERVICE_ORDER_CHOICES = [(o[0], o[0]) for o in KGS_SERVICE_ORDERS]

KGS_PARTICIPATION_STAGES = {
    0: ("Seeker",      "Connection"),
    1: ("Member",      "Formation"),
    2: ("Disciple",    "Alignment"),
    3: ("Steward",     "Service"),
    4: ("Senior Steward", "Leadership"),
    5: ("Architect",   "Apostolic Stewardship"),
}

KGS_COMPETENCE_LABELS = {
    0: "Seeker",
    1: "Foundational Disciple",
    2: "Active Contributor",
    3: "Functional Minister",
    4: "Leader",
    5: "Apostolic Steward",
}
```

#### Task A.4 — URL structure and health endpoint

```python
# community/urls.py
from django.urls import path
from . import views, api_views

urlpatterns = [
    # Health
    path('api/community/health/', api_views.community_health, name='community-health'),

    # Template views — My Community surface
    path('community/', views.my_community, name='community-home'),

    # Template views — Management surface (Level 3+)
    path('community/management/', views.management_home, name='community-management'),
    path('community/management/members/', views.member_directory, name='community-members'),
    path('community/management/members/<uuid:member_id>/', views.member_profile, name='community-member-profile'),
    path('community/management/pipeline/', views.formation_pipeline, name='community-pipeline'),

    # HTMX partials
    path('community/htmx/announcement/create/', views.htmx_create_announcement, name='htmx-create-announcement'),
    path('community/htmx/announcement/<uuid:record_id>/archive/', views.htmx_archive_announcement, name='htmx-archive-announcement'),
    path('community/htmx/gathering/create/', views.htmx_create_gathering, name='htmx-create-gathering'),
    path('community/htmx/gathering/<uuid:record_id>/cancel/', views.htmx_cancel_gathering, name='htmx-cancel-gathering'),
    path('community/htmx/member/<uuid:permission_id>/shepherd/', views.htmx_set_shepherd, name='htmx-set-shepherd'),
    path('community/htmx/member/<uuid:permission_id>/order/', views.htmx_set_order, name='htmx-set-order'),
    path('community/htmx/member/<uuid:permission_id>/deactivate/', views.htmx_deactivate_member, name='htmx-deactivate-member'),
    path('community/htmx/members/search/', views.htmx_member_search, name='htmx-member-search'),
    path('community/htmx/announcements/', views.htmx_announcement_list, name='htmx-announcement-list'),
]
```

Wire into root URLs:

```python
# ics_project/urls.py
urlpatterns = [
    ...
    path('', include('community.urls')),
]
```

```python
# community/api_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def community_health(request):
    return Response({'status': 'ok', 'app': 'community'})
```

```bash
git add . && git commit -m "feat: community app scaffold — model stub, constants, URLs, health check"
```

---

### Phase B — Django Views + Base Template + CSS

*Entry requirement: Phase A complete.*

#### Task B.1 — community.css

```css
/* frontend/assets/css/community.css */

/* ── Community surface layout ─────────────────────────────────── */
.community-surface {
  padding: 16px;
  max-width: 600px;
  margin: 0 auto;
}

/* ── Community header card ────────────────────────────────────── */
.community-header {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.community-logo {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  background: var(--primary-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}
.community-name { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.community-tier { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }

/* ── Formation stage card ─────────────────────────────────────── */
.formation-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}
.formation-stage-label {
  font-size: 13px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}
.formation-level-name {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
}
.formation-participation {
  font-size: 13px;
  color: var(--primary);
  margin-top: 2px;
}
.formation-steps {
  display: flex;
  gap: 6px;
  margin-top: 12px;
}
.formation-step {
  height: 6px;
  flex: 1;
  border-radius: 3px;
  background: var(--border);
}
.formation-step.active { background: var(--primary); }

/* ── Info card (shepherd, service order) ──────────────────────── */
.info-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.info-card-icon { font-size: 20px; flex-shrink: 0; }
.info-card-label { font-size: 12px; color: var(--text-secondary); }
.info-card-value { font-size: 14px; font-weight: 500; color: var(--text-primary); }

/* ── Section heading ──────────────────────────────────────────── */
.section-heading {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 16px 0 8px;
}

/* ── Gathering card ───────────────────────────────────────────── */
.gathering-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 10px;
}
.gathering-title { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.gathering-meta { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
.gathering-format {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
  margin-top: 6px;
}
.format-in_person  { background: var(--success-light); color: var(--success); }
.format-digital    { background: var(--primary-light); color: var(--primary); }
.format-hybrid     { background: var(--warning-light); color: var(--warning); }
.gathering-stream-link {
  display: block;
  margin-top: 8px;
  font-size: 13px;
  color: var(--primary);
  text-decoration: none;
  font-weight: 500;
}

/* ── Announcement card ────────────────────────────────────────── */
.announcement-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 10px;
}
.announcement-title { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.announcement-content { font-size: 13px; color: var(--text-secondary); margin-top: 4px; line-height: 1.5; }
.announcement-date { font-size: 11px; color: var(--text-tertiary); margin-top: 6px; }

/* ── Member card (directory) ──────────────────────────────────── */
.member-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
}
.member-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--primary-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
  color: var(--primary);
  flex-shrink: 0;
}
.member-name  { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.member-meta  { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }

/* ── Formation pipeline ───────────────────────────────────────── */
.pipeline-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.pipeline-col {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px;
}
.pipeline-col-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.pipeline-count {
  font-size: 24px;
  font-weight: 700;
  color: var(--primary);
  line-height: 1;
}
.pipeline-names {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 6px;
  line-height: 1.5;
}

/* ── Form cards ───────────────────────────────────────────────── */
.community-form {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 16px;
  margin-bottom: 16px;
}
.form-field { margin-bottom: 14px; }
.form-field label { font-size: 13px; font-weight: 600; color: var(--text-secondary); display: block; margin-bottom: 4px; }
.form-field input,
.form-field textarea,
.form-field select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--background);
  color: var(--text-primary);
  font-size: 14px;
}
.format-conditional { display: none; }
.format-conditional.visible { display: block; }

/* ── Gifts summary (read-only cross-app) ──────────────────────── */
.gifts-summary {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 12px;
}
.gifts-count { font-size: 22px; font-weight: 700; color: var(--primary); }
.gifts-label { font-size: 12px; color: var(--text-secondary); }

/* ── Buttons ──────────────────────────────────────────────────── */
.btn-primary {
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 10px 18px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  width: 100%;
}
.btn-secondary {
  background: transparent;
  color: var(--primary);
  border: 1.5px solid var(--primary);
  border-radius: 8px;
  padding: 9px 18px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  width: 100%;
}
.btn-danger {
  background: var(--error-light);
  color: var(--error);
  border: none;
  border-radius: 8px;
  padding: 9px 18px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
.btn-sm { padding: 6px 12px; font-size: 12px; width: auto; }

/* ── Empty state ──────────────────────────────────────────────── */
.empty-state {
  text-align: center;
  padding: 40px 16px;
  color: var(--text-secondary);
  font-size: 14px;
}

/* ── HTMX indicator ───────────────────────────────────────────── */
.htmx-indicator { opacity: 0; transition: opacity 0.2s; }
.htmx-request .htmx-indicator { opacity: 1; }

/* ── Desktop breakpoint ───────────────────────────────────────── */
@media (min-width: 768px) {
  .community-surface { padding: 24px; }
  .pipeline-grid { grid-template-columns: repeat(6, 1fr); }
}
```

#### Task B.2 — Base community template

```html
<!-- community/templates/community/base_community.html -->
{% extends "base.html" %}
{% load static %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'assets/css/community.css' %}">
{% endblock %}

{% block content %}
<div class="community-surface">
  {% block community_content %}{% endblock %}
</div>
{% endblock %}
```

#### Task B.3 — Stub views file

```python
# community/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db import transaction
import requests

from .constants import (
    KGS_SERVICE_ORDERS, KGS_SERVICE_ORDER_CHOICES,
    KGS_PARTICIPATION_STAGES, KGS_COMPETENCE_LABELS
)


def _require_level(request, min_level):
    """Return True if the user meets the minimum competence level."""
    return request.user.userprofile.competence_level >= min_level


@login_required
def my_community(request):
    """My Community — member surface."""
    return render(request, 'community/my_community.html', {})


@login_required
def management_home(request):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html',
                      {'min_level': 3}, status=403)
    return render(request, 'community/management.html', {})


@login_required
def member_directory(request):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html',
                      {'min_level': 3}, status=403)
    return render(request, 'community/member_directory.html', {})


@login_required
def member_profile(request, member_id):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html',
                      {'min_level': 3}, status=403)
    return render(request, 'community/member_profile.html',
                  {'member_id': member_id})


@login_required
def formation_pipeline(request):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html',
                      {'min_level': 3}, status=403)
    return render(request, 'community/formation_pipeline.html', {})
```

```bash
git add . && git commit -m "feat: community app — base template, CSS, stub views, URL routing"
```

---

### Phase C — My Community Surface (UI)

*Entry requirement: Phase B complete.*

#### Task C.1 — My Community view (full implementation)

```python
# community/views.py — replace my_community stub

from django.utils import timezone
from datetime import timedelta


@login_required
def my_community(request):
    """My Community — member surface. Level 1+ only."""
    user = request.user
    level = user.userprofile.competence_level

    if level < 1:
        # Seekers have no tenant membership
        return render(request, 'community/seeker_gate.html')

    # 1 — Get all active UserPermission rows for this user
    base_url = request.build_absolute_uri('/')[:-1]
    perms_resp = requests.get(
        f'{base_url}/api/permissions/',
        params={'user_id': str(user.id), 'is_active': 'true'},
        headers={'Authorization': request.META.get('HTTP_AUTHORIZATION', '')},
    )
    permissions = perms_resp.json().get('results', []) if perms_resp.ok else []

    # 2 — For the primary tenant (first active permission), load context
    primary_perm = permissions[0] if permissions else None
    shepherd = None
    service_order = None
    announcements = []
    upcoming_gatherings = []
    gifts_count = 0

    if primary_perm:
        tenant_id = primary_perm['tenant_id']
        meta = primary_perm.get('metadata', {})
        service_order = meta.get('service_order')

        # Shepherd
        shepherd_id = meta.get('shepherd_id')
        if shepherd_id:
            sh_resp = requests.get(
                f'{base_url}/api/auth/users/{shepherd_id}/',
                headers={'Authorization': request.META.get('HTTP_AUTHORIZATION', '')},
            )
            shepherd = sh_resp.json() if sh_resp.ok else None

        # Announcements (latest 5)
        ann_resp = requests.get(
            f'{base_url}/api/records/',
            params={
                'record_family': 'community',
                'record_type': 'announcement',
                'tenant_id': tenant_id,
                'status': 'active',
                'ordering': '-created_at',
                'page_size': 5,
            },
            headers={'Authorization': request.META.get('HTTP_AUTHORIZATION', '')},
        )
        announcements = ann_resp.json().get('results', []) if ann_resp.ok else []

        # Upcoming gatherings (next 30 days via Calendar endpoint)
        now = timezone.now()
        cal_resp = requests.get(
            f'{base_url}/api/calendar/events/',
            params={
                'source_app': 'community',
                'tenant_id': tenant_id,
                'from': now.date().isoformat(),
                'to': (now + timedelta(days=30)).date().isoformat(),
            },
            headers={'Authorization': request.META.get('HTTP_AUTHORIZATION', '')},
        )
        upcoming_gatherings = cal_resp.json() if cal_resp.ok else []

        # Gifts count (Activity App cross-read)
        gifts_resp = requests.get(
            f'{base_url}/api/activities/',
            params={
                'activity_type': 'skill',
                'created_by': str(user.id),
                'tenant_id': tenant_id,
                'status': 'active',
            },
            headers={'Authorization': request.META.get('HTTP_AUTHORIZATION', '')},
        )
        gifts_count = gifts_resp.json().get('count', 0) if gifts_resp.ok else 0

    stage_info = KGS_PARTICIPATION_STAGES.get(level, ('Member', 'Formation'))
    level_label = KGS_COMPETENCE_LABELS.get(level, 'Member')

    return render(request, 'community/my_community.html', {
        'permissions':          permissions,
        'primary_perm':         primary_perm,
        'shepherd':             shepherd,
        'service_order':        service_order,
        'announcements':        announcements,
        'upcoming_gatherings':  upcoming_gatherings,
        'gifts_count':          gifts_count,
        'level':                level,
        'level_label':          level_label,
        'stage_name':           stage_info[0],
        'participation_stage':  stage_info[1],
        'participation_steps':  range(1, 6),  # levels 1–5
    })
```

#### Task C.2 — My Community template

```html
<!-- community/templates/community/my_community.html -->
{% extends "community/base_community.html" %}

{% block community_content %}

{% if not primary_perm %}
<div class="empty-state">
  <p>You are not yet part of a community.</p>
  <p style="margin-top:8px;font-size:12px">
    Contact a steward to be added to your local Sceptre Community.
  </p>
</div>
{% else %}

<!-- Community header -->
{% with tenant=primary_perm.tenant %}
<div class="community-header">
  <div class="community-logo">🏛</div>
  <div>
    <div class="community-name">{{ primary_perm.tenant_name|default:"My Community" }}</div>
    <div class="community-tier">{{ primary_perm.tenant_tier|default:"Church Node"|title }}</div>
  </div>
</div>
{% endwith %}

<!-- Formation stage -->
<div class="formation-card">
  <div class="formation-stage-label">Formation Stage</div>
  <div class="formation-level-name">{{ level_label }}</div>
  <div class="formation-participation">{{ participation_stage }}</div>
  <div class="formation-steps">
    {% for step in participation_steps %}
    <div class="formation-step {% if step <= level %}active{% endif %}"></div>
    {% endfor %}
  </div>
</div>

<!-- Shepherd -->
{% if shepherd %}
<div class="info-card">
  <div class="info-card-icon">🤝</div>
  <div>
    <div class="info-card-label">Your Shepherd</div>
    <div class="info-card-value">{{ shepherd.display_name }}</div>
  </div>
</div>
{% endif %}

<!-- Service order -->
{% if service_order %}
<div class="info-card">
  <div class="info-card-icon">⚙️</div>
  <div>
    <div class="info-card-label">Service Placement</div>
    <div class="info-card-value">{{ service_order }}</div>
  </div>
</div>
{% endif %}

<!-- Gifts summary -->
<div class="gifts-summary">
  <div class="gifts-count">{{ gifts_count }}</div>
  <div class="gifts-label">
    Active gift{{ gifts_count|pluralize }} registered
    — <a href="/activity/gifts/" style="color:var(--primary)">View in Activity App</a>
  </div>
</div>

<!-- Upcoming gatherings -->
<div class="section-heading">Upcoming Gatherings</div>
{% if upcoming_gatherings %}
{% for gathering in upcoming_gatherings %}
<div class="gathering-card">
  <div class="gathering-title">{{ gathering.title }}</div>
  <div class="gathering-meta">{{ gathering.scheduled_at|slice:":16"|replace:"T":" " }}</div>
  {% with fmt=gathering.custom_fields.format|default:"in_person" %}
  <span class="gathering-format format-{{ fmt }}">
    {{ fmt|replace:"_":" "|title }}
  </span>
  {% endwith %}
  {% if gathering.custom_fields.location %}
  <div class="gathering-meta" style="margin-top:6px">📍 {{ gathering.custom_fields.location }}</div>
  {% endif %}
  {% if gathering.custom_fields.stream_url %}
  <a class="gathering-stream-link"
     href="{{ gathering.custom_fields.stream_url }}"
     target="_blank" rel="noopener">
    🔗 Join Online
  </a>
  {% endif %}
</div>
{% endfor %}
{% else %}
<div class="empty-state" style="padding:20px 0">No gatherings scheduled in the next 30 days.</div>
{% endif %}

<!-- Announcements -->
<div class="section-heading">Announcements</div>
{% if announcements %}
{% for ann in announcements %}
<div class="announcement-card">
  <div class="announcement-title">{{ ann.title }}</div>
  <div class="announcement-content">{{ ann.content|truncatechars:180 }}</div>
  <div class="announcement-date">{{ ann.created_at|slice:":10" }}</div>
</div>
{% endfor %}
{% else %}
<div class="empty-state" style="padding:20px 0">No announcements yet.</div>
{% endif %}

{% endif %}
{% endblock %}
```

#### Task C.3 — Seeker gate and locked templates

```html
<!-- community/templates/community/seeker_gate.html -->
{% extends "community/base_community.html" %}
{% block community_content %}
<div class="empty-state">
  <p style="font-size:32px;margin-bottom:12px">🌱</p>
  <p style="font-weight:600;color:var(--text-primary)">Community access requires membership.</p>
  <p style="margin-top:8px">
    Community features are available to Level 1 Members and above.
    Complete your formation journey to join a Sceptre Community.
  </p>
</div>
{% endblock %}
```

```html
<!-- community/templates/community/locked.html -->
{% extends "community/base_community.html" %}
{% block community_content %}
<div class="empty-state">
  <p style="font-size:32px;margin-bottom:12px">🔒</p>
  <p style="font-weight:600;color:var(--text-primary)">Level {{ min_level }}+ required.</p>
  <p style="margin-top:8px">This section is available to stewards and above.</p>
</div>
{% endblock %}
```

```bash
git add . && git commit -m "feat: community — My Community surface complete"
```

---

### Phase D — Member Directory + Formation Pipeline (Management Surface)

*Entry requirement: Phase C complete.*

#### Task D.1 — Management home view

```python
# community/views.py — replace management_home stub

@login_required
def management_home(request):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html', {'min_level': 3}, status=403)

    user = request.user
    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    # Get steward's scope_path from their highest-level UserPermission
    perms_resp = requests.get(
        f'{base_url}/api/permissions/',
        params={'user_id': str(user.id), 'is_active': 'true', 'ordering': '-level'},
        headers=auth_header,
    )
    permissions = perms_resp.json().get('results', []) if perms_resp.ok else []
    primary_perm = permissions[0] if permissions else None
    scope_path = primary_perm['tenant_path'] if primary_perm else None

    # Member count
    member_count = 0
    if scope_path:
        mc_resp = requests.get(
            f'{base_url}/api/permissions/',
            params={'tenant_path__startswith': scope_path, 'is_active': 'true', 'page_size': 1},
            headers=auth_header,
        )
        member_count = mc_resp.json().get('count', 0) if mc_resp.ok else 0

    # Recent announcements (last 3)
    announcements = []
    if primary_perm:
        ann_resp = requests.get(
            f'{base_url}/api/records/',
            params={
                'record_family': 'community', 'record_type': 'announcement',
                'tenant_id': primary_perm['tenant_id'],
                'ordering': '-created_at', 'page_size': 3,
            },
            headers=auth_header,
        )
        announcements = ann_resp.json().get('results', []) if ann_resp.ok else []

    # Upcoming gatherings (next 7 days)
    now = timezone.now()
    gatherings = []
    if primary_perm:
        cal_resp = requests.get(
            f'{base_url}/api/calendar/events/',
            params={
                'source_app': 'community',
                'tenant_id': primary_perm['tenant_id'],
                'from': now.date().isoformat(),
                'to': (now + timedelta(days=7)).date().isoformat(),
            },
            headers=auth_header,
        )
        gatherings = cal_resp.json() if cal_resp.ok else []

    return render(request, 'community/management.html', {
        'primary_perm':  primary_perm,
        'scope_path':    scope_path,
        'member_count':  member_count,
        'announcements': announcements,
        'gatherings':    gatherings,
    })
```

#### Task D.2 — Member directory view

```python
# community/views.py — replace member_directory stub

@login_required
def member_directory(request):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html', {'min_level': 3}, status=403)

    user = request.user
    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    perms_resp = requests.get(
        f'{base_url}/api/permissions/',
        params={'user_id': str(user.id), 'is_active': 'true', 'ordering': '-level'},
        headers=auth_header,
    )
    my_perms = perms_resp.json().get('results', []) if perms_resp.ok else []
    primary_perm = my_perms[0] if my_perms else None
    scope_path = primary_perm['tenant_path'] if primary_perm else None

    # Filters from GET params
    filter_order = request.GET.get('order', '')
    filter_level = request.GET.get('level', '')
    search_q     = request.GET.get('q', '')

    params = {
        'tenant_path__startswith': scope_path,
        'is_active': 'true',
        'ordering': 'user__display_name',
        'page_size': 50,
    }
    if filter_order:
        params['metadata__service_order'] = filter_order
    if filter_level:
        params['level'] = filter_level
    if search_q:
        params['search'] = search_q

    members_resp = requests.get(
        f'{base_url}/api/permissions/',
        params=params,
        headers=auth_header,
    )
    members = members_resp.json().get('results', []) if members_resp.ok else []

    return render(request, 'community/member_directory.html', {
        'members':       members,
        'scope_path':    scope_path,
        'filter_order':  filter_order,
        'filter_level':  filter_level,
        'search_q':      search_q,
        'order_choices': KGS_SERVICE_ORDER_CHOICES,
        'level_choices': [(0,'Seeker'),(1,'Member'),(2,'Disciple'),(3,'Steward'),(4,'Senior Steward'),(5,'Architect')],
    })
```

#### Task D.3 — Formation pipeline view

```python
# community/views.py — replace formation_pipeline stub

@login_required
def formation_pipeline(request):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html', {'min_level': 3}, status=403)

    user = request.user
    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    perms_resp = requests.get(
        f'{base_url}/api/permissions/',
        params={'user_id': str(user.id), 'is_active': 'true', 'ordering': '-level'},
        headers=auth_header,
    )
    my_perms = perms_resp.json().get('results', []) if perms_resp.ok else []
    primary_perm = my_perms[0] if my_perms else None
    scope_path = primary_perm['tenant_path'] if primary_perm else None

    members_resp = requests.get(
        f'{base_url}/api/permissions/',
        params={'tenant_path__startswith': scope_path, 'is_active': 'true', 'page_size': 200},
        headers=auth_header,
    )
    all_members = members_resp.json().get('results', []) if members_resp.ok else []

    # Group by competence level
    pipeline = {lvl: [] for lvl in range(6)}
    for m in all_members:
        lvl = m.get('level', 0)
        pipeline[lvl].append(m)

    pipeline_display = [
        {
            'level': lvl,
            'label': KGS_COMPETENCE_LABELS.get(lvl, f'Level {lvl}'),
            'stage': KGS_PARTICIPATION_STAGES.get(lvl, ('',''))[1],
            'members': pipeline[lvl],
            'count': len(pipeline[lvl]),
        }
        for lvl in range(6)
    ]

    return render(request, 'community/formation_pipeline.html', {
        'pipeline_display': pipeline_display,
        'total': len(all_members),
    })
```

#### Task D.4 — Management, directory, and pipeline templates

```html
<!-- community/templates/community/management.html -->
{% extends "community/base_community.html" %}
{% block community_content %}

<div class="community-header">
  <div class="community-logo">⚙️</div>
  <div>
    <div class="community-name">Community Management</div>
    <div class="community-tier">{{ primary_perm.tenant_name|default:"Your Branch" }}</div>
  </div>
</div>

<!-- Nav tiles -->
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px">
  <a href="{% url 'community-members' %}" class="info-card" style="text-decoration:none">
    <div class="info-card-icon">👥</div>
    <div>
      <div class="info-card-label">Members</div>
      <div class="info-card-value">{{ member_count }}</div>
    </div>
  </a>
  <a href="{% url 'community-pipeline' %}" class="info-card" style="text-decoration:none">
    <div class="info-card-icon">📊</div>
    <div>
      <div class="info-card-label">Pipeline</div>
      <div class="info-card-value">Formation Stages</div>
    </div>
  </a>
</div>

<!-- Announcements -->
<div class="section-heading" style="display:flex;justify-content:space-between;align-items:center">
  <span>Announcements</span>
  <button class="btn-secondary btn-sm"
          hx-get="{% url 'htmx-create-announcement' %}"
          hx-target="#announcement-form-slot"
          hx-swap="innerHTML">+ New</button>
</div>
<div id="announcement-form-slot"></div>
<div id="announcement-list"
     hx-get="{% url 'htmx-announcement-list' %}"
     hx-trigger="load"
     hx-swap="innerHTML">
  <div class="htmx-indicator">Loading…</div>
</div>

<!-- Gatherings -->
<div class="section-heading" style="display:flex;justify-content:space-between;align-items:center;margin-top:8px">
  <span>Gatherings</span>
  <button class="btn-secondary btn-sm"
          hx-get="{% url 'htmx-create-gathering' %}"
          hx-target="#gathering-form-slot"
          hx-swap="innerHTML">+ Schedule</button>
</div>
<div id="gathering-form-slot"></div>
{% if gatherings %}
{% for g in gatherings %}
<div class="gathering-card" id="gathering-{{ g.id }}">
  <div class="gathering-title">{{ g.title }}</div>
  <div class="gathering-meta">{{ g.scheduled_at|slice:":16"|replace:"T":" " }}</div>
  {% with fmt=g.custom_fields.format|default:"in_person" %}
  <span class="gathering-format format-{{ fmt }}">{{ fmt|replace:"_":" "|title }}</span>
  {% endwith %}
</div>
{% endfor %}
{% else %}
<div class="empty-state" style="padding:20px 0">No gatherings in the next 7 days.</div>
{% endif %}

{% endblock %}
```

```html
<!-- community/templates/community/member_directory.html -->
{% extends "community/base_community.html" %}
{% block community_content %}

<div style="margin-bottom:16px">
  <input type="search" placeholder="Search members…"
         name="q" value="{{ search_q }}"
         hx-get="{% url 'htmx-member-search' %}"
         hx-trigger="keyup changed delay:400ms"
         hx-target="#member-list"
         hx-swap="innerHTML"
         style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:8px;
                background:var(--background);color:var(--text-primary);font-size:14px">
</div>

<!-- Filters -->
<div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap">
  <select name="level"
          hx-get="{% url 'htmx-member-search' %}"
          hx-trigger="change"
          hx-target="#member-list"
          hx-swap="innerHTML"
          hx-include="[name='q'],[name='order']"
          style="flex:1;padding:8px;border:1px solid var(--border);border-radius:8px;
                 background:var(--background);color:var(--text-primary);font-size:13px">
    <option value="">All levels</option>
    {% for val, label in level_choices %}
    <option value="{{ val }}" {% if filter_level == val|stringformat:"s" %}selected{% endif %}>{{ label }}</option>
    {% endfor %}
  </select>

  <select name="order"
          hx-get="{% url 'htmx-member-search' %}"
          hx-trigger="change"
          hx-target="#member-list"
          hx-swap="innerHTML"
          hx-include="[name='q'],[name='level']"
          style="flex:1;padding:8px;border:1px solid var(--border);border-radius:8px;
                 background:var(--background);color:var(--text-primary);font-size:13px">
    <option value="">All service orders</option>
    {% for val, label in order_choices %}
    <option value="{{ val }}" {% if filter_order == val %}selected{% endif %}>{{ val }}</option>
    {% endfor %}
  </select>
</div>

<div id="member-list">
  {% include "community/partials/member_list.html" %}
</div>
{% endblock %}
```

```html
<!-- community/templates/community/partials/member_list.html -->
{% for m in members %}
<a href="{% url 'community-member-profile' m.user_id %}" class="member-card">
  <div class="member-avatar">{{ m.display_name|first|upper }}</div>
  <div>
    <div class="member-name">{{ m.display_name }}</div>
    <div class="member-meta">
      Level {{ m.level }}
      {% if m.metadata.service_order %} · {{ m.metadata.service_order }}{% endif %}
    </div>
  </div>
</a>
{% empty %}
<div class="empty-state">No members found.</div>
{% endfor %}
```

```html
<!-- community/templates/community/formation_pipeline.html -->
{% extends "community/base_community.html" %}
{% block community_content %}

<div style="font-size:13px;color:var(--text-secondary);margin-bottom:12px">
  {{ total }} total active member{{ total|pluralize }}
</div>

<div class="pipeline-grid">
{% for col in pipeline_display %}
<div class="pipeline-col">
  <div class="pipeline-col-label">{{ col.label }}</div>
  <div class="pipeline-count">{{ col.count }}</div>
  <div class="pipeline-names">
    {% for m in col.members|slice:":5" %}{{ m.display_name }}{% if not forloop.last %}, {% endif %}{% endfor %}
    {% if col.count > 5 %} +{{ col.count|add:"-5" }} more{% endif %}
  </div>
</div>
{% endfor %}
</div>

{% endblock %}
```

```bash
git add . && git commit -m "feat: community — member directory, formation pipeline, management surface"
```

---

### Phase E — Announcement + Gathering Management (HTMX)

*Entry requirement: Phase D complete.*

#### Task E.1 — HTMX views: announcements

```python
# community/views.py — HTMX announcement handlers

@login_required
def htmx_announcement_list(request):
    if not _require_level(request, 3):
        return HttpResponse('')

    user = request.user
    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    perms_resp = requests.get(
        f'{base_url}/api/permissions/',
        params={'user_id': str(user.id), 'is_active': 'true', 'ordering': '-level'},
        headers=auth_header,
    )
    my_perms = perms_resp.json().get('results', []) if perms_resp.ok else []
    tenant_id = my_perms[0]['tenant_id'] if my_perms else None

    if not tenant_id:
        return HttpResponse('<div class="empty-state">No tenant context.</div>')

    ann_resp = requests.get(
        f'{base_url}/api/records/',
        params={
            'record_family': 'community', 'record_type': 'announcement',
            'tenant_id': tenant_id, 'ordering': '-created_at', 'page_size': 20,
        },
        headers=auth_header,
    )
    announcements = ann_resp.json().get('results', []) if ann_resp.ok else []
    return render(request, 'community/partials/announcement_list.html',
                  {'announcements': announcements})


@login_required
def htmx_create_announcement(request):
    if not _require_level(request, 3):
        return HttpResponse('')

    if request.method == 'POST':
        user = request.user
        base_url = request.build_absolute_uri('/')[:-1]
        auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

        perms_resp = requests.get(
            f'{base_url}/api/permissions/',
            params={'user_id': str(user.id), 'is_active': 'true', 'ordering': '-level'},
            headers=auth_header,
        )
        my_perms = perms_resp.json().get('results', []) if perms_resp.ok else []
        primary_perm = my_perms[0] if my_perms else None

        if not primary_perm:
            return HttpResponse('<p style="color:var(--error)">No tenant context.</p>')

        create_resp = requests.post(
            f'{base_url}/api/records/',
            json={
                'record_class':  'organizational',
                'record_family': 'community',
                'record_type':   'announcement',
                'title':         request.POST.get('title', '').strip(),
                'content':       request.POST.get('content', '').strip(),
                'tenant_id':     primary_perm['tenant_id'],
                'status':        'active',
                'metadata':      {'source_app': 'community'},
                'permissions':   {'visibility': 'tenant', 'required_level': 1},
            },
            headers=auth_header,
        )

        if create_resp.ok:
            # Refresh the announcement list
            return htmx_announcement_list(request)
        else:
            return HttpResponse(
                '<p style="color:var(--error)">Failed to create announcement. Please try again.</p>'
            )

    # GET — return the create form partial
    return render(request, 'community/partials/announcement_form.html')


@login_required
def htmx_archive_announcement(request, record_id):
    if not _require_level(request, 3):
        return HttpResponse('')

    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    requests.patch(
        f'{base_url}/api/records/{record_id}/',
        json={'status': 'archived'},
        headers=auth_header,
    )
    return htmx_announcement_list(request)
```

#### Task E.2 — HTMX views: gatherings (dual-write)

```python
# community/views.py — HTMX gathering handlers

@login_required
def htmx_create_gathering(request):
    if not _require_level(request, 3):
        return HttpResponse('')

    if request.method == 'POST':
        user = request.user
        base_url = request.build_absolute_uri('/')[:-1]
        auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

        perms_resp = requests.get(
            f'{base_url}/api/permissions/',
            params={'user_id': str(user.id), 'is_active': 'true', 'ordering': '-level'},
            headers=auth_header,
        )
        my_perms = perms_resp.json().get('results', []) if perms_resp.ok else []
        primary_perm = my_perms[0] if my_perms else None

        if not primary_perm:
            return HttpResponse('<p style="color:var(--error)">No tenant context.</p>')

        title        = request.POST.get('title', '').strip()
        description  = request.POST.get('description', '').strip()
        fmt          = request.POST.get('format', 'in_person')
        location     = request.POST.get('location', '').strip() or None
        stream_url   = request.POST.get('stream_url', '').strip() or None
        capacity     = request.POST.get('capacity', '').strip() or None
        scheduled_at = request.POST.get('scheduled_at', '').strip()
        tenant_id    = primary_perm['tenant_id']

        # Dual-write: atomic via try/except (both API calls in sequence)
        try:
            # Step 1 — create gathering Record
            rec_resp = requests.post(
                f'{base_url}/api/records/',
                json={
                    'record_class':  'organizational',
                    'record_family': 'community',
                    'record_type':   'gathering',
                    'title':         title,
                    'content':       description or None,
                    'tenant_id':     tenant_id,
                    'status':        'active',
                    'metadata':      {'source_app': 'community'},
                    'custom_fields': {
                        'format':       fmt,
                        'location':     location,
                        'stream_url':   stream_url,
                        'capacity':     int(capacity) if capacity else None,
                        'scheduled_at': scheduled_at,
                    },
                    'permissions': {'visibility': 'tenant', 'required_level': 1},
                },
                headers=auth_header,
            )
            rec_resp.raise_for_status()
            record_id = rec_resp.json()['id']

            # Step 2 — create event Activity
            act_resp = requests.post(
                f'{base_url}/api/activities/',
                json={
                    'activity_type': 'event',
                    'title':         title,
                    'description':   description or None,
                    'scheduled_at':  scheduled_at or None,
                    'tenant_id':     tenant_id,
                    'kgs_pillar':    'communities',
                    'kgs_pathway':   'community_life',
                    'status':        'pending',
                    'metadata':      {'source_app': 'community'},
                },
                headers=auth_header,
            )
            act_resp.raise_for_status()
            activity_id = act_resp.json()['id']

            # Step 3 — link Record → Activity
            rel_resp = requests.post(
                f'{base_url}/api/relationships/',
                json={
                    'from_record_id':    record_id,
                    'to_record_id':      activity_id,
                    'relationship_type': 'aligns_with',
                    'direction':         'directed',
                    'tenant_id':         tenant_id,
                },
                headers=auth_header,
            )
            rel_resp.raise_for_status()

        except Exception:
            return HttpResponse(
                '<p style="color:var(--error)">Failed to schedule gathering. Please try again.</p>'
            )

        # Success — return a success partial (the management page will refresh gatherings)
        return HttpResponse(
            '<div class="announcement-card" style="border-color:var(--success)">'
            f'<div class="announcement-title">✓ Gathering scheduled: {title}</div>'
            '</div>'
        )

    # GET — return the create form partial
    return render(request, 'community/partials/gathering_form.html')


@login_required
def htmx_cancel_gathering(request, record_id):
    if not _require_level(request, 3):
        return HttpResponse('')

    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    # Find the linked Activity via Relationship
    rel_resp = requests.get(
        f'{base_url}/api/relationships/',
        params={'from_record_id': str(record_id), 'relationship_type': 'aligns_with'},
        headers=auth_header,
    )
    relationships = rel_resp.json().get('results', []) if rel_resp.ok else []

    # Cancel Record
    requests.patch(
        f'{base_url}/api/records/{record_id}/',
        json={'status': 'cancelled'},
        headers=auth_header,
    )

    # Cancel linked Activity
    for rel in relationships:
        act_id = rel.get('to_record_id')
        if act_id:
            requests.patch(
                f'{base_url}/api/activities/{act_id}/',
                json={'status': 'cancelled'},
                headers=auth_header,
            )

    return HttpResponse(
        f'<div class="gathering-card" style="opacity:0.5">'
        f'<div class="gathering-title">Gathering cancelled</div></div>'
    )
```

#### Task E.3 — HTMX partials templates

```html
<!-- community/templates/community/partials/announcement_form.html -->
<div class="community-form" id="announcement-form">
  <div class="form-field">
    <label>Title</label>
    <input type="text" name="title" placeholder="Announcement title" required>
  </div>
  <div class="form-field">
    <label>Content</label>
    <textarea name="content" rows="4" placeholder="Announcement message…"></textarea>
  </div>
  <button class="btn-primary"
          hx-post="{% url 'htmx-create-announcement' %}"
          hx-target="#announcement-list"
          hx-swap="innerHTML"
          hx-include="#announcement-form">
    Publish Announcement
  </button>
</div>
```

```html
<!-- community/templates/community/partials/gathering_form.html -->
<div class="community-form" id="gathering-form">
  <div class="form-field">
    <label>Title</label>
    <input type="text" name="title" placeholder="e.g. Sunday Morning Service" required>
  </div>
  <div class="form-field">
    <label>Date & Time</label>
    <input type="datetime-local" name="scheduled_at" required>
  </div>
  <div class="form-field">
    <label>Format</label>
    <select name="format"
            hx-on:change="
              const fmt = this.value;
              document.getElementById('loc-field').classList.toggle('visible', fmt !== 'digital');
              document.getElementById('stream-field').classList.toggle('visible', fmt !== 'in_person');
            ">
      <option value="in_person">In Person</option>
      <option value="digital">Digital</option>
      <option value="hybrid">Hybrid</option>
    </select>
  </div>
  <div class="form-field format-conditional visible" id="loc-field">
    <label>Location</label>
    <input type="text" name="location" placeholder="Venue or address">
  </div>
  <div class="form-field format-conditional" id="stream-field">
    <label>Stream URL</label>
    <input type="url" name="stream_url" placeholder="https://youtube.com/live/…">
  </div>
  <div class="form-field">
    <label>Description (optional)</label>
    <textarea name="description" rows="3" placeholder="Agenda or notes…"></textarea>
  </div>
  <button class="btn-primary"
          hx-post="{% url 'htmx-create-gathering' %}"
          hx-target="#gathering-form-slot"
          hx-swap="innerHTML"
          hx-include="#gathering-form">
    Schedule Gathering
  </button>
</div>
```

```html
<!-- community/templates/community/partials/announcement_list.html -->
{% for ann in announcements %}
<div class="announcement-card" id="announcement-{{ ann.id }}">
  <div style="display:flex;justify-content:space-between;align-items:flex-start">
    <div>
      <div class="announcement-title">{{ ann.title }}</div>
      <div class="announcement-content">{{ ann.content|truncatechars:200 }}</div>
      <div class="announcement-date">{{ ann.created_at|slice:":10" }}
        {% if ann.status == 'archived' %}<span style="color:var(--text-tertiary)"> · Archived</span>{% endif %}
      </div>
    </div>
    {% if ann.status == 'active' %}
    <button class="btn-danger btn-sm"
            hx-post="{% url 'htmx-archive-announcement' ann.id %}"
            hx-target="#announcement-list"
            hx-swap="innerHTML"
            hx-confirm="Archive this announcement?">
      Archive
    </button>
    {% endif %}
  </div>
</div>
{% empty %}
<div class="empty-state" style="padding:16px 0">No announcements yet.</div>
{% endfor %}
```

```bash
git add . && git commit -m "feat: community — announcement + gathering HTMX management complete"
```

---

### Phase F — Member Profile + Pastoral Assignment + Service Order

*Entry requirement: Phase E complete.*

#### Task F.1 — Member profile view (full implementation)

```python
# community/views.py — replace member_profile stub

@login_required
def member_profile(request, member_id):
    if not _require_level(request, 3):
        return render(request, 'community/locked.html', {'min_level': 3}, status=403)

    user = request.user
    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    # Steward's scope
    perms_resp = requests.get(
        f'{base_url}/api/permissions/',
        params={'user_id': str(user.id), 'is_active': 'true', 'ordering': '-level'},
        headers=auth_header,
    )
    my_perms = perms_resp.json().get('results', []) if perms_resp.ok else []
    scope_path = my_perms[0]['tenant_path'] if my_perms else None

    # Member's permission row (within steward's scope)
    member_perm_resp = requests.get(
        f'{base_url}/api/permissions/',
        params={
            'user_id': str(member_id),
            'tenant_path__startswith': scope_path,
            'is_active': 'true',
        },
        headers=auth_header,
    )
    member_perms = member_perm_resp.json().get('results', []) if member_perm_resp.ok else []
    member_perm = member_perms[0] if member_perms else None

    if not member_perm:
        return render(request, 'community/locked.html',
                      {'min_level': 3, 'message': 'Member not found in your scope.'}, status=404)

    # Member user details
    member_resp = requests.get(
        f'{base_url}/api/auth/users/{member_id}/',
        headers=auth_header,
    )
    member_user = member_resp.json() if member_resp.ok else {}

    # Member's gifts
    gifts_resp = requests.get(
        f'{base_url}/api/activities/',
        params={
            'activity_type': 'skill',
            'created_by': str(member_id),
            'tenant_id': member_perm['tenant_id'],
            'status': 'active',
        },
        headers=auth_header,
    )
    gifts = gifts_resp.json().get('results', []) if gifts_resp.ok else []

    # Member's certifications (Learn App)
    certs_resp = requests.get(
        f'{base_url}/api/records/',
        params={
            'record_family': 'learning',
            'record_type': 'certification',
            'created_by': str(member_id),
            'status': 'active',
            'ordering': '-created_at',
        },
        headers=auth_header,
    )
    certifications = certs_resp.json().get('results', []) if certs_resp.ok else []

    # Potential shepherds (Level 3+ in this scope)
    shepherds_resp = requests.get(
        f'{base_url}/api/permissions/',
        params={
            'tenant_path__startswith': scope_path,
            'level__gte': 3,
            'is_active': 'true',
        },
        headers=auth_header,
    )
    shepherds = shepherds_resp.json().get('results', []) if shepherds_resp.ok else []

    level = member_user.get('competence_level', 0)
    level_label = KGS_COMPETENCE_LABELS.get(level, f'Level {level}')
    stage_info = KGS_PARTICIPATION_STAGES.get(level, ('Member', 'Formation'))

    return render(request, 'community/member_profile.html', {
        'member_perm':    member_perm,
        'member_user':    member_user,
        'gifts':          gifts,
        'certifications': certifications,
        'shepherds':      shepherds,
        'order_choices':  KGS_SERVICE_ORDER_CHOICES,
        'level_label':    level_label,
        'stage_info':     stage_info,
    })
```

#### Task F.2 — HTMX views: pastoral + service order

```python
# community/views.py — pastoral and service order HTMX handlers

@login_required
def htmx_set_shepherd(request, permission_id):
    if not _require_level(request, 3) or request.method != 'POST':
        return HttpResponse('')

    shepherd_id = request.POST.get('shepherd_id', '').strip() or None
    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    requests.patch(
        f'{base_url}/api/permissions/{permission_id}/',
        json={'metadata': {'shepherd_id': shepherd_id}},
        headers=auth_header,
    )

    label = 'No shepherd assigned'
    if shepherd_id:
        sh_resp = requests.get(f'{base_url}/api/auth/users/{shepherd_id}/', headers=auth_header)
        sh = sh_resp.json() if sh_resp.ok else {}
        label = sh.get('display_name', 'Shepherd assigned')

    return HttpResponse(
        f'<div class="info-card-value" id="shepherd-value">✓ {label}</div>'
    )


@login_required
def htmx_set_order(request, permission_id):
    if not _require_level(request, 3) or request.method != 'POST':
        return HttpResponse('')

    service_order = request.POST.get('service_order', '').strip() or None
    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    requests.patch(
        f'{base_url}/api/permissions/{permission_id}/',
        json={'metadata': {'service_order': service_order}},
        headers=auth_header,
    )

    label = service_order if service_order else 'No service order assigned'
    return HttpResponse(
        f'<div class="info-card-value" id="order-value">✓ {label}</div>'
    )


@login_required
def htmx_deactivate_member(request, permission_id):
    if not _require_level(request, 3) or request.method != 'POST':
        return HttpResponse('')

    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    requests.patch(
        f'{base_url}/api/permissions/{permission_id}/',
        json={'is_active': False},
        headers=auth_header,
    )

    return HttpResponse(
        '<div class="announcement-card" style="border-color:var(--error)">'
        '<div class="announcement-title" style="color:var(--error)">Membership deactivated.</div>'
        '</div>'
    )


@login_required
def htmx_member_search(request):
    if not _require_level(request, 2):
        return HttpResponse('')

    user = request.user
    base_url = request.build_absolute_uri('/')[:-1]
    auth_header = {'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}

    perms_resp = requests.get(
        f'{base_url}/api/permissions/',
        params={'user_id': str(user.id), 'is_active': 'true', 'ordering': '-level'},
        headers=auth_header,
    )
    my_perms = perms_resp.json().get('results', []) if perms_resp.ok else []
    scope_path = my_perms[0]['tenant_path'] if my_perms else None

    params = {
        'tenant_path__startswith': scope_path,
        'is_active': 'true',
        'ordering': 'user__display_name',
        'page_size': 50,
    }
    q = request.GET.get('q', '').strip()
    level = request.GET.get('level', '').strip()
    order = request.GET.get('order', '').strip()
    if q:
        params['search'] = q
    if level:
        params['level'] = level
    if order:
        params['metadata__service_order'] = order

    members_resp = requests.get(f'{base_url}/api/permissions/', params=params, headers=auth_header)
    members = members_resp.json().get('results', []) if members_resp.ok else []

    return render(request, 'community/partials/member_list.html', {'members': members})
```

#### Task F.3 — Member profile template

```html
<!-- community/templates/community/member_profile.html -->
{% extends "community/base_community.html" %}
{% block community_content %}

<!-- Header -->
<div class="community-header">
  <div class="member-avatar" style="width:56px;height:56px;font-size:22px">
    {{ member_user.display_name|first|upper }}
  </div>
  <div>
    <div class="community-name">{{ member_user.display_name }}</div>
    <div class="community-tier">{{ level_label }} · {{ stage_info.1 }}</div>
  </div>
</div>

<!-- Formation steps -->
<div class="formation-card">
  <div class="formation-stage-label">Formation</div>
  <div class="formation-level-name">{{ level_label }}</div>
  <div class="formation-participation">{{ stage_info.1 }}</div>
  <div class="formation-steps">
    {% for step in "12345" %}
    <div class="formation-step {% if forloop.counter <= member_user.competence_level %}active{% endif %}"></div>
    {% endfor %}
  </div>
</div>

<!-- Shepherd assignment -->
<div class="info-card" id="shepherd-card">
  <div class="info-card-icon">🤝</div>
  <div style="flex:1">
    <div class="info-card-label">Shepherd</div>
    <div class="info-card-value" id="shepherd-value">
      {% if member_perm.metadata.shepherd_id %}Assigned{% else %}Not assigned{% endif %}
    </div>
    <form style="margin-top:8px;display:flex;gap:8px;align-items:center">
      <select name="shepherd_id" style="flex:1;padding:6px;border:1px solid var(--border);
              border-radius:6px;background:var(--background);color:var(--text-primary);font-size:13px">
        <option value="">— Remove shepherd —</option>
        {% for s in shepherds %}
        <option value="{{ s.user_id }}"
                {% if s.user_id == member_perm.metadata.shepherd_id %}selected{% endif %}>
          {{ s.display_name }}
        </option>
        {% endfor %}
      </select>
      <button class="btn-secondary btn-sm"
              hx-post="{% url 'htmx-set-shepherd' member_perm.id %}"
              hx-target="#shepherd-value"
              hx-swap="outerHTML"
              hx-include="[name='shepherd_id']">
        Set
      </button>
    </form>
  </div>
</div>

<!-- Service order placement -->
<div class="info-card" id="order-card">
  <div class="info-card-icon">⚙️</div>
  <div style="flex:1">
    <div class="info-card-label">Service Order</div>
    <div class="info-card-value" id="order-value">
      {{ member_perm.metadata.service_order|default:"Not assigned" }}
    </div>
    <form style="margin-top:8px;display:flex;gap:8px;align-items:center">
      <select name="service_order" style="flex:1;padding:6px;border:1px solid var(--border);
              border-radius:6px;background:var(--background);color:var(--text-primary);font-size:13px">
        <option value="">— Remove placement —</option>
        {% for val, label in order_choices %}
        <option value="{{ val }}"
                {% if val == member_perm.metadata.service_order %}selected{% endif %}>
          {{ val }}
        </option>
        {% endfor %}
      </select>
      <button class="btn-secondary btn-sm"
              hx-post="{% url 'htmx-set-order' member_perm.id %}"
              hx-target="#order-value"
              hx-swap="outerHTML"
              hx-include="[name='service_order']">
        Set
      </button>
    </form>
  </div>
</div>

<!-- Gifts summary -->
{% if gifts %}
<div class="section-heading">Gifts Register</div>
{% for gift in gifts %}
<div class="announcement-card">
  <div class="announcement-title">{{ gift.title }}</div>
  <div class="announcement-content">
    Competence: {{ gift.progress }}%
    {% if gift.metadata.service_order %} · {{ gift.metadata.service_order }}{% endif %}
  </div>
</div>
{% endfor %}
{% endif %}

<!-- Certifications -->
{% if certifications %}
<div class="section-heading">Certifications</div>
{% for cert in certifications %}
<div class="announcement-card">
  <div class="announcement-title">{{ cert.title }}</div>
  <div class="announcement-date">{{ cert.created_at|slice:":10" }}</div>
</div>
{% endfor %}
{% endif %}

<!-- Deactivate membership -->
<div style="margin-top:24px;padding-top:16px;border-top:1px solid var(--border)">
  <button class="btn-danger"
          hx-post="{% url 'htmx-deactivate-member' member_perm.id %}"
          hx-target="#deactivate-slot"
          hx-swap="innerHTML"
          hx-confirm="Deactivate this member's community membership? This cannot be undone without steward action.">
    Deactivate Membership
  </button>
  <div id="deactivate-slot"></div>
</div>

{% endblock %}
```

```bash
git add . && git commit -m "feat: community — member profile, pastoral assignment, service order HTMX complete"
```

---

### Phase G — Smoke Test Checklist

*Entry requirement: Phases A–F complete.*

Verify manually on mobile (and desktop for management surface):

**My Community surface:**
- [ ] Level 1 member sees community header with tenant name and tier
- [ ] Formation card shows correct level label and participation stage; progress steps reflect level
- [ ] Shepherd card appears when `shepherd_id` is set; hidden when null
- [ ] Service order card appears when `service_order` is set; hidden when null
- [ ] Gifts summary shows correct count; link to Activity App gifts register works
- [ ] Upcoming gatherings list shows events within 30 days with format badge and location/stream link
- [ ] Announcements list shows 5 most recent active announcements
- [ ] Seeker (Level 0b) sees seeker gate — no community content
- [ ] Level 0 member with no UserPermission rows sees "not yet part of a community" empty state

**Community Management surface:**
- [ ] Level 2 user sees locked.html with "Level 3+ required" message
- [ ] Level 3 steward sees management home with member count, announcement section, and gathering section
- [ ] Member directory loads and shows all active members in scope
- [ ] Search by name filters member list via HTMX without page reload
- [ ] Level and service order filter dropdowns work correctly via HTMX
- [ ] Formation pipeline shows correct member counts per level column
- [ ] Member profile loads: avatar, level, shepherd, service order, gifts, certifications

**Announcements:**
- [ ] Create announcement form appears via HTMX; submitting creates a Record and refreshes list
- [ ] Archive button archives the record (status:'archived'); refreshed list shows archived state
- [ ] Announcement appears on My Community surface for Level 1 members in same tenant

**Gatherings:**
- [ ] Create gathering form appears via HTMX
- [ ] Location field shows only when format is 'in_person' or 'hybrid'
- [ ] Stream URL field shows only when format is 'digital' or 'hybrid'
- [ ] Submitting creates: one gathering Record, one event Activity (source_app:'community'),
      one aligns_with Relationship — verify all three in Django admin
- [ ] `GET /api/calendar/events/?source_app=community&tenant_id={id}` returns the new gathering
- [ ] Gathering appears in My Community upcoming gatherings (within 30 days)
- [ ] Cancel gathering PATCHes both Record and Activity to status:'cancelled'
- [ ] Cancelled gathering disappears from Calendar endpoint results

**Pastoral assignment:**
- [ ] Set shepherd on member profile: HTMX select → PATCH → shepherd-value updates inline
- [ ] Shepherd name appears on member's My Community surface after assignment
- [ ] Clear shepherd: select "Remove shepherd" → shepherd-value shows "Not assigned"

**Service order:**
- [ ] Set service order on member profile: HTMX select → PATCH → order-value updates inline
- [ ] Service order appears on member directory card after assignment
- [ ] Service order filter in directory correctly filters by `metadata__service_order`

**Access control:**
- [ ] `GET /api/community/health/` returns `{"status": "ok", "app": "community"}`
- [ ] All management views return 403 / locked template for Level 2 and below
- [ ] Steward cannot see members outside their scope_path (verify with two tenants)

```bash
git add . && git commit -m "feat: community app — smoke test pass, all phases complete"
```

---

## Django Endpoint Summary

```
# Community App health
GET    /api/community/health/

# Template views
GET    /community/                          My Community (Level 1+)
GET    /community/management/              Management home (Level 3+)
GET    /community/management/members/      Member directory (Level 3+)
GET    /community/management/members/{id}/ Member profile (Level 3+)
GET    /community/management/pipeline/     Formation pipeline (Level 3+)

# HTMX partials
GET    /community/htmx/announcement/create/          announcement create form
POST   /community/htmx/announcement/create/          create announcement (Level 3+)
POST   /community/htmx/announcement/{id}/archive/    archive announcement (Level 3+)
GET    /community/htmx/gathering/create/             gathering create form
POST   /community/htmx/gathering/create/             create gathering — dual-write (Level 3+)
POST   /community/htmx/gathering/{id}/cancel/        cancel gathering (Level 3+)
POST   /community/htmx/member/{id}/shepherd/         set shepherd (Level 3+)
POST   /community/htmx/member/{id}/order/            set service order (Level 3+)
POST   /community/htmx/member/{id}/deactivate/       deactivate membership (Level 3+)
GET    /community/htmx/members/search/               HTMX member search (Level 2+)
GET    /community/htmx/announcements/                HTMX announcement list (Level 3+)

# Existing platform endpoints consumed by Community App (no changes)
GET    /api/permissions/?tenant_path__startswith={}&is_active=true
POST   /api/permissions/
PATCH  /api/permissions/{id}/
GET    /api/records/?record_family=community&record_type=announcement
GET    /api/records/?record_family=community&record_type=gathering
POST   /api/records/
PATCH  /api/records/{id}/
POST   /api/activities/
PATCH  /api/activities/{id}/
POST   /api/relationships/
GET    /api/relationships/?from_record_id={}&relationship_type=aligns_with
GET    /api/calendar/events/?source_app=community
GET    /api/activities/?activity_type=skill&created_by={}&tenant_id={}
GET    /api/records/?record_family=learning&record_type=certification&created_by={}
```

---

## File Map (Community App additions)

```
~/ics/
  community/
    __init__.py
    apps.py
    models.py                  ← NEW: MembershipRequest (stubbed, not wired to UI)
    constants.py               ← NEW: KGS_SERVICE_ORDERS, KGS_PARTICIPATION_STAGES, KGS_COMPETENCE_LABELS
    api_views.py               ← NEW: community_health endpoint
    views.py                   ← NEW: all Django template views + HTMX partials
    urls.py                    ← NEW: full URL structure
    templates/
      community/
        base_community.html    ← NEW
        my_community.html      ← NEW
        management.html        ← NEW
        member_directory.html  ← NEW
        member_profile.html    ← NEW
        formation_pipeline.html← NEW
        seeker_gate.html       ← NEW
        locked.html            ← NEW
        partials/
          member_list.html     ← NEW (HTMX target for search/filter)
          announcement_list.html ← NEW (HTMX target for create/archive)
          announcement_form.html ← NEW
          gathering_form.html    ← NEW

  frontend/assets/css/
    community.css              ← NEW
```

---

## Phase Summary

| Phase | What it builds | Entry requirement | Exit criteria |
|-------|----------------|-------------------|---------------|
| A | Django app scaffold, MembershipRequest model stub, service order constants, URL structure, health check | Phases 0–4 of main roadmap done | Health check returns 200; migration applied |
| B | Base template, community.css, stub views | Phase A done | All URLs resolve; base template loads with CSS |
| C | My Community surface: tenant header, formation stage, shepherd, service order, gatherings, announcements, gifts summary | Phase B done | Level 1 member sees full My Community page; seeker gate shown for Level 0b |
| D | Member directory, formation pipeline, management home | Phase C done | Steward sees member list with search/filter; pipeline shows correct counts |
| E | Announcement management (create/archive HTMX), gathering management (dual-write create/cancel HTMX) | Phase D done | Announcement creates Record; gathering creates Record + Activity + Relationship; Calendar endpoint returns gathering |
| F | Member profile, pastoral assignment (HTMX), service order placement (HTMX), deactivation | Phase E done | Steward sets shepherd and service order on member; values update inline; appear on member's My Community surface |
| G | Smoke test checklist | Phase F done | All checklist items pass; admin confirms dual-write objects; Calendar endpoint confirms community events |

---

## Deferred (Post-MVP)

- `MembershipRequest` flow — self-service join request, steward approval queue,
  induction training gate (Learn App integration)
- `report` record type — community health and activity reports
- `pastoral_note` record type — confidential steward notes on members (privacy design required)
- Attendance tracking — `AttendanceLog` model (privacy-sensitive; deferred)
- `PastoralAssignment` model — upgrade from `UserPermission.metadata.shepherd_id`
  when shepherd management needs versioning and history
- GinIndex on `UserPermission.metadata` — add if directory filter performance degrades
- Shepherd's flock view — filtered directory showing all members under a specific shepherd
- Community analytics dashboard — formation pipeline trends over time, service order coverage gaps
- Collective-level gathering visibility — gatherings visible across Church Collective network
- iCS Live Stream integration — gathering `stream_url` pointing to native Video App stream
  (no data contract change required — `stream_url` is already a string field)
- Notifications on new announcements — wired to Notifications App stub (Phase 5.7)
- Paraclete integration — "You have a gathering tomorrow" in daily digest
  (Calendar endpoint already supports this; Paraclete implementation is Phase 6)
- Calendar App Phase 2 — community gatherings appear in grid calendar UI
