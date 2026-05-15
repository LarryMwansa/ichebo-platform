# Version 2 Building Plan — Post-MVP Features

> **Version:** v2.0 — April 2026
> **Previous version:** v1.0 (original post-MVP draft — superseded)
> **Status:** Revised — grounded in KGS framework, Sceptre Community Programme concept note, and Chizola's onboarding direction
>
> **v2.0 Changes from v1.0:**
>
> - Induction system redesigned to reflect the 12-week Level 0 Induction Tenant model
> - Learn App (F1–F11 qualification framework) moved into Version 2 as a foundational dependency
> - Competence advancement changed from automated lesson counting to steward-governed programme completion
> - Two entrant pathways (existing believers / Reconditioning; kingdom-curious / Beginners) formalised
> - Tenant placement pipeline added as an explicit post-induction stage
> - Phase structure reordered to reflect correct build dependencies

---

## Strategic Context

**MVP Status:** Complete (6c43ce9)
**Target:** Version 2 — The Formation & Learning Platform
**Core conviction:** MVP gives users accounts and apps. Version 2 gives them a home, a journey, and a qualification. Without this, the platform is a set of tools with no formation system beneath them.

---

## Formation Architecture (Foundation for all of Version 2)

Before reading the phases, this architecture must be understood. Every feature in Version 2 is in service of this structure.

> **ADR-011 governs all programme names, induction structure, and curriculum decisions.** Read it before coding anything in this section.

### KGS Programme Stack (canonical — ADR-011)

| Level | Programme Name        | KGS Qualification | Pathways                                           | Duration    |
| ----- | --------------------- | ----------------- | -------------------------------------------------- | ----------- |
| 0     | (Induction Training)  | Certificate entry | New Life; Community Life                           | 12 weeks    |
| 1     | New Life Programme    | Certificate       | New Life; Community Life; Learning & Qualification | 1 year      |
| 2     | Foundation Programme  | Diploma           | Spiritual Formation; Service; Mission; Learning    | 3 years     |
| 3     | Leaders Programme     | Degree            | Leadership; Service; Learning & Qualification      | 6–12 months |
| 4     | Builders Programme    | Masters           | Leadership; Apostolic Stewardship                  | 6–12 months |
| 5     | Architect's Programme | Doctorate         | Leadership; Apostolic Stewardship                  | 2 years     |

**Induction Training** is a `record_type: "course"` inside New Life Programme — not a standalone programme. All four lessons are required for all entrant types:

- Keys To the Kingdom *(Beginners foundation)*
- Repentance & Reformation *(Reconditioning pathway)*
- Community Programme *(Sceptre Community life)*
- The Secret of Living a Fulfilled Life — HAL Beginners *(Practical formation)*

`induction_pathway` on the User model records background (`"reconditioning"` / `"beginners"`) for context only — it does not gate individual lessons.

```text
Platform Layer
  └── Induction Tenant (Level 0 — 12 weeks)
        └── New Life Programme → Induction Training course (all 4 lessons)
              └── ✓ Complete + Steward confirms → Geographic tenant placement → Level 1

  └── Home Tenant (Level 1+)
        └── New Life Programme (Certificate — 1 year)
              └── ✓ Complete + Steward confirms → Level 2
        └── Foundation Programme (Diploma — 3 years)
              └── ✓ Complete + Steward confirms → Level 3
        └── Leaders / Builders / Architect's continue the pattern → Levels 4, 5
```

**Curriculum is open.** Seeded programme and course records are `status: "active"` but not locked. Level 4+ authors add courses and lessons post-seed. The seed establishes structure — it does not freeze it.

**The 24 Service Orders** (from KGS Service Domains) are the controlled vocabulary for `UserPermission.metadata.service_order`. No model change needed — stored as free text now, dropdown UI in V2.3+.

**The 12 Administrative Offices** are deferred to V2.5+, modelled as Agency-level tenants under `/global/agency/`.

---

## Phase 1 (Version 2.0) — Learn App Foundation

### Why first?

Induction requires course delivery. The 12-week Induction Tenant cannot run without the Learn App's ability to serve programmes, courses, and lessons. This is the foundational infrastructure. All other phases sit on it.

The Learn App was designed with the full qualification framework (F1–F11) in the existing system design document. Version 2 builds it in full, not as a subset.

---

### L1: Learn App — Data & Backend

**Goal:** Bring the Learn App's qualification framework to life. Programmes, courses, lessons, assessments, and certifications fully operational.

**What gets built:**

The learning stack as defined in the Learn App system design:

- `record_family: "learning"` types: `programme`, `course`, `lesson`, `assignment`, `quiz`, `certification`
- `activity_type: "programme"` (enrolment container)
- `activity_type: "project"` (course progress tracker)
- `activity_type: "task"` (lesson and assessment completion)
- `CertificationConfirmation` model in `learn/` app
- `part_of` Relationship graph: lesson → course → programme
- `Relationship.type: "tracks"` linking progress Activities to content Records

**Five Qualification Programmes (seeded as system records via `seed_programmes`):**

| Level | Programme Name        | KGS Qualification | Duration    | Prerequisites        |
| ----- | --------------------- | ----------------- | ----------- | -------------------- |
| 1     | New Life Programme    | Certificate       | 1 year      | Induction Training   |
| 2     | Foundation Programme  | Diploma           | 3 years     | New Life Programme   |
| 3     | Leaders Programme     | Degree            | 6–12 months | Foundation Programme |
| 4     | Builders Programme    | Masters           | 6–12 months | Leaders Programme    |
| 5     | Architect's Programme | Doctorate         | 2 years     | Builders Programme   |

Each programme record carries `custom_fields.kgs_pathways` (array) and `custom_fields.kgs_qualification` (display label).

**Eight KGS Pathways surfaced per programme:**

| Pathway                  | Programmes                                                       |
| ------------------------ | ---------------------------------------------------------------- |
| New Life                 | New Life Programme                                               |
| Community Life           | New Life Programme                                               |
| Learning & Qualification | New Life, Foundation, Leaders, Builders, Architect's             |
| Spiritual Formation      | Foundation Programme                                             |
| Service                  | Foundation Programme, Leaders Programme                          |
| Mission                  | Foundation Programme                                             |
| Leadership               | Leaders Programme, Builders Programme, Architect's Programme     |
| Apostolic Stewardship    | Builders Programme, Architect's Programme                        |

**Induction Training course (seeded via `seed_induction_course`, inside New Life Programme):**

| Lesson                                                | Covers                        |
| ----------------------------------------------------- | ----------------------------- |
| Keys To the Kingdom                                   | Beginners pathway foundation  |
| Repentance & Reformation                              | Reconditioning pathway        |
| Community Programme                                   | Sceptre Community life        |
| The Secret of Living a Fulfilled Life (HAL Beginners) | Practical formation           |

All four lessons required for all entrant types. `induction_pathway` on User is background metadata only.

**Files to create / modify:**

- `learn/models.py` — `CertificationConfirmation` model
- `learn/serializers.py` — full DRF serializers for all learning record types
- `learn/views.py` — DRF ViewSets: Programme, Course, Lesson, Assessment, Certification
- `learn/urls.py` — API routing
- `learn/service.py` — enrolment logic, prerequisite checks, certification trigger
- `learn/signals.py` — programme completion → draft certification creation
- Database migration: `CertificationConfirmation` table

**Acceptance criteria:**

- All five qualification programmes can be seeded and retrieved via API
- Courses and lessons can be authored and linked via `part_of` Relationships
- Enrolment creates a programme Activity with nested course and lesson Activities
- Lesson completion marks the task Activity as completed and updates programme progress
- Programme reaching 100% triggers a draft `certification` Record automatically

---

### L2: Learn App — UI (Django templates + HTMX)

**Goal:** Learners can browse programmes, enrol, track progress, complete lessons, and earn certifications. Stewards can confirm certifications.

**Features (from system design F1–F11):**

- **F1 — Programme Catalogue:** Pathway view (default) + flat catalogue view filtered by competence level. Locked state for above-level programmes.
- **F2 — Course Browser:** Course detail with lesson list, assessments, competence gate.
- **F3 — Enrolment:** Prerequisite check, one enrolment per programme, confirmation screen.
- **F4 — Progress Tracking:** Lesson completion, course and programme progress bars, resume from last incomplete.
- **F5 — Lesson Viewer:** Rendered lesson content, mark complete, previous/next navigation.
- **F6 — Assessments:** Inline quiz (multiple choice / short answer), assignment text submission.
- **F7 — Certification:** "Awaiting certification" state, steward review queue, confirm → competence_level increment.
- **F8 — Content Authorship (Level 4+):** Draft and submit programmes, courses, lessons, assessments.
- **F9 — Handbook Review Queue (Level 5):** Review submitted content, approve or return, lock.
- **F10 — Pathway Banner:** "You are on the Service Pathway — here are your available courses."
- **F11 — My Learning Dashboard:** Active enrolments, certifications, formation summary.

**Views:**

- `GET /learn/` — My Learning Dashboard
- `GET /learn/catalogue/` — Programme catalogue
- `GET /learn/programme/{id}/` — Programme detail
- `GET /learn/course/{id}/` — Course detail
- `GET /learn/lesson/{id}/` — Lesson viewer
- `POST /learn/htmx/enrol/{programme_id}/` — Enrolment
- `POST /learn/htmx/lesson/{id}/complete/` — Mark lesson complete
- `POST /learn/htmx/assessment/{id}/submit/` — Submit assessment
- `GET /learn/certifications/` — Steward certification queue (Level 3+)
- `POST /learn/htmx/certification/{id}/confirm/` — Confirm certification

**Files to create:**

- `templates/learn/dashboard.html`
- `templates/learn/catalogue.html`
- `templates/learn/programme_detail.html`
- `templates/learn/course_detail.html`
- `templates/learn/lesson_viewer.html`
- `templates/learn/_progress_bar.html` (HTMX partial)
- `templates/learn/_enrol_button.html` (HTMX partial)
- `templates/learn/certification_queue.html`
- `templates/learn/authorship/programme_form.html` (Level 4+)
- `templates/learn/authorship/course_form.html` (Level 4+)
- `templates/learn/authorship/lesson_form.html` (Level 4+)
- `templates/learn/handbook_review.html` (Level 5)

**Acceptance criteria:**

- Seeker (Level 0b) can browse catalogue but cannot enrol
- Member (Level 1+) can enrol and track progress
- Level 4+ can author content
- Level 5 can review and approve submitted content
- Steward (Level 3+) can confirm certifications, triggering competence_level increment
- Pathway banner surfaces correctly per programme enrolment

---

### L3: Learn App — Carry-Forward Items from MVP

These two items were identified during the Phase 5.2 audit as incomplete in MVP. They are deferred here rather than patched now because assessment submission design may shift once the full five-programme qualification framework is built in L1–L2.

**Item 1 — Register `CertificationConfirmation` in Django admin**

The model exists and is migrated. It is not registered in `learn/admin.py`. The roadmap exit criteria requires "Verifiable in Django admin."

- File: `learn/admin.py`
- Change: register `CertificationConfirmation` with `list_display` showing `certification_record_id`, `learner_id`, `confirmed_by`, `previous_competence_level`, `new_competence_level`, `confirmed_at`

**Item 2 — Assessment submission backend (`POST /learn/htmx/assessment/{id}/submit/`)**

The quiz and assignment templates (`partials/quiz.html`, `partials/assignment_form.html`) exist and render correctly. There is no view or URL to receive the submission. The form posts to nowhere.

This is deferred to Version 2 (not patched in MVP) because:

- Quiz and assignment types are likely to be extended when real induction programme content is authored
- The submission model (what gets persisted, how it relates to progress) should be decided alongside the full assessment design in L1
- The correct pattern is: submission creates an `Activity (activity_type: "task")` with `metadata.lesson_record_id` and `metadata.submission_text`, which is then counted by `_recalculate_programme_progress()`

When building:

- Add `htmx_submit_assessment(request, lesson_id)` to `learn/views.py`
- Add URL: `POST /learn/htmx/assessment/<uuid:lesson_id>/submit/`
- Wire both quiz and assignment form templates to this endpoint
- Ensure the created Activity is counted correctly by the existing progress recalculation logic

**Acceptance criteria for L3:**

- `CertificationConfirmation` visible and filterable in Django admin
- Submitting a quiz or assignment creates an Activity record and triggers progress recalculation
- Progress reaches 100% correctly when all lessons and assessments are completed

---

### L4: Settings and Activity UI — Carry-Forward Items from MVP

Two small gaps identified across Phase 5.3 (Activity) and Phase 5.6 (Profile + Settings). Deferred to Version 2 because both touch areas that will expand in v2 anyway.

**Item 1 — Bible translation preference save (`accounts`)**

The settings page renders a Bible translation selector (`_settings_bible.html`) and the available translations are passed in context from `SettingsView`. There is no view or URL to receive and persist the selection.

When building:

- Add `htmx_settings_bible(request)` to `accounts/views.py`
- Persist to `User.preferences['bible_translation']` (same pattern as theme and region handlers)
- Add URL: `POST /accounts/htmx/settings/bible/`
- Wire the `_settings_bible.html` template form to this endpoint
- The `UserProfile.preferred_bible_translation` FK field may also need updating — confirm which field is the authoritative store when building the induction profile in V2.2

**Item 2 — Distinct ministry and calendar URL routes (`activity`)**

All data and HTMX actions for ministry types (campaign, project, event) exist in the current `my_activities()` view via type filter. There is no distinct `GET /activity/ministry/` or `GET /activity/calendar/` URL as specified in the roadmap.

This is low priority — the functionality is present, just not split into dedicated surfaces. Deferred to Version 2 because the Activity app UI is scheduled to expand with assigned-to-me queues and richer calendar views anyway.

When building:

- Add `ministry()` view to `activity/views.py` — filters to ministry types (`campaign`, `project`, `task`, `event`), adds assigned-to-me tab
- Add `calendar_view()` view — dated list of all activities with `due_at` set, ordered chronologically
- Add URLs to `activity/template_urls.py`: `GET /activity/ministry/` and `GET /activity/calendar/`
- Update app drawer / nav links to point to the new routes

**Acceptance criteria for L4:**

- Selecting and saving a Bible translation in Settings persists to the database and is respected by the Bible app on next load
- `/activity/ministry/` renders ministry-type activities distinct from personal activities
- `/activity/calendar/` renders a dated list of all activities with due dates

---

### Summary: Phase 1 (L1–L2–L3–L4)

- **Commits:** 4 (backend, UI, Learn carry-forwards, Settings/Activity carry-forwards)
- **Effort:** ~40% of Version 2 velocity
- **Dependencies:** None (Learn App is the foundation)

---

## Phase 2 (Version 2.1) — Induction System

### Why second?

With the Learn App operational, the Induction Tenant can be built properly — as a real 12-week formation environment served by real courses, not a placeholder form flow. Induction is the true entry point of the platform.

---

### G1: Induction Tenant (System Tenant)

**Goal:** Establish the Induction Tenant as a permanent, system-managed tenant at a fixed path. All new users are placed here automatically on registration.

**What it is:**
The Induction Tenant is the "Outer Court of the Gentiles" — the preparatory space where every new entrant is received, oriented, and formed before being placed in their long-term community. It is not a community in the KGS sense; it is an onboarding environment.

**Tenant definition:**

```python
InductionTenant = {
  name: "Induction",
  slug: "induction",
  path: "/global/induction/",
  tier: "induction",        # New tier value — system-managed
  affiliation: "ichebo",
  status: "active",
  settings: {
    allow_public_records: False,
    require_approval: False,  # Auto-enrolment on registration
    max_members: None
  }
}
```

**Data model changes:**

- Add `"induction"` to `Tenant.tier` enum
- Add `induction_enrolled_at` to `User` model
- Add `induction_completed_at` to `User` model
- Add `induction_pathway` field to `User` or `UserProfile`: `"reconditioning" | "beginners" | null`

**Files to create / modify:**

- `tenants/models.py` — add `"induction"` to tier choices
- `accounts/models.py` — add induction fields
- `tenants/management/commands/seed_induction_tenant.py` — seed command
- Database migration

**Acceptance criteria:**

- Induction Tenant exists at `/global/induction/` with correct tier
- Cannot be deleted, renamed, or modified via normal UI flows
- All new users automatically placed here on first login (see G2)

---

### G2: Sign-up & Profile Registration

**Goal:** New users enter the platform, complete their profile, and are placed into the Induction Tenant automatically.

**Three-step flow:**

**Step 1 — Sign-up:**

- Email + password registration (standard Django auth)
- Email verification
- No competence level assigned
- User status: `"seeker"`

**Step 2 — Profile Registration:**

- Full profile: name, location (country/province/city), phone, date of birth
- Entrant type selection: "I am already part of a church or faith community" (Reconditioning) vs "I am new to this and exploring" (Beginners)
- Gifting, skills, occupation, capacity fields (initial self-assessment — used for eventual placement)
  - *Note: exact fields to be confirmed by Chizola before build*
- Saved to `UserProfile`

**Step 3 — Tenant Placement (Induction):**

- `UserPermission` row created: `tenant_path = "/global/induction/"`, `level = 0`, `role = "seeker"`, `is_active = True`
- `induction_enrolled_at` set on User
- `induction_pathway` set based on entrant type selection
- User redirected to Induction Dashboard

**Views:**

- `GET /accounts/register/` — sign-up form
- `POST /accounts/register/` — create user, send verification email
- `GET /accounts/verify-email/{token}/` — verify, redirect to profile
- `GET /accounts/profile-setup/` — profile registration form
- `POST /accounts/profile-setup/` — save profile + place in Induction Tenant
- `GET /accounts/welcome/` — induction welcome / orientation

**Files to create / modify:**

- `accounts/views.py` — registration, profile setup views
- `accounts/forms.py` — RegistrationForm, ProfileSetupForm
- `templates/accounts/register.html`
- `templates/accounts/profile_setup.html`
- `templates/accounts/welcome.html`

**Acceptance criteria:**

- New user completes registration → profile → placed in Induction Tenant in one uninterrupted flow
- Entrant type drives which induction programme they are enrolled in (G3)
- User sees Induction Dashboard on first login thereafter

---

### G3: Induction Programme Enrolment

**Goal:** On placement into the Induction Tenant, users are automatically enrolled in the correct induction programme(s) via the Learn App.

**Enrolment logic (triggered by G2 placement):**

| Entrant type   | Outer Court programme    | Inner Court programme |
| -------------- | ------------------------ | --------------------- |
| Reconditioning | Reconditioning Programme | Community Programme   |
| Beginners      | Beginners Programme      | Community Programme   |

Both are enrolled in sequence. Community Programme enrolment is triggered on completion of their Outer Court programme.

**12-week structure:**

- Weeks 1–6: Outer Court (Reconditioning or Beginners Programme)
- Weeks 7–12: Inner Court (Community Programme)
- Final week: Gifting and placement readiness assessment

This is implemented entirely via the Learn App (L1–L2). The induction system calls the enrolment service with the appropriate programme IDs.

**Induction Dashboard (surface within the Learn App for induction-tenanted users):**

- Current programme with progress
- Weeks remaining estimate
- Orientation materials (static content or first lesson of Beginners/Reconditioning)
- Upcoming induction gatherings (Community App integration — later)

**Files to create / modify:**

- `learn/service.py` — `enrol_induction_programmes(user, pathway)` function
- `accounts/views.py` — call enrolment service on profile setup completion
- `templates/learn/induction_dashboard.html`

**Acceptance criteria:**

- Every new user is automatically enrolled in the correct Outer Court programme
- Completing Outer Court triggers Community Programme enrolment
- Induction Dashboard shows correct programme and progress

---

### G4: Induction Completion & Tenant Placement

**Goal:** Users who complete the 12-week induction programme are assessed, confirmed by a steward, and placed into their geographic home tenant.

**Completion flow:**

1. User completes Community Programme (Inner Court)
2. `CertificationConfirmation` draft created automatically (Learn App signal)
3. Induction steward (Level 3+ within Induction Tenant) reviews the user's profile:
   - Gifting / skills / occupation / capacity data from profile registration (G2)
   - Programme completion evidence
   - Assessment submission (from Community Programme)
4. Steward confirms completion
5. System:
   - Sets `induction_completed_at` on User
   - Sets `User.status = "active"`, `User.competence_level = 1`
   - Creates `UserPermission` in the user's geographic tenant (`level = 1`, `role = "disciple"`)
   - Deactivates the Induction Tenant `UserPermission`
   - Logs to ActivityLog: "Induction completed — placed in {tenant}"

**Placement assignment:**

- Steward selects the appropriate geographic tenant from the tenant directory during confirmation
- Matching logic: user's location (country/province/city from profile) narrows the tenant list
- Steward makes the final placement decision

**Views:**

- `GET /learn/induction/review/` — steward: list of users pending induction confirmation
- `GET /learn/induction/review/{user_id}/` — steward: individual review with profile + progress
- `POST /learn/htmx/induction/confirm/{user_id}/` — steward confirms, select placement tenant
- `GET /accounts/formation/` — user: post-placement welcome and Level 1 orientation

**Files to create / modify:**

- `learn/views.py` — induction review views
- `templates/learn/induction_review_queue.html`
- `templates/learn/induction_review_detail.html`
- `accounts/views.py` — post-placement landing
- `templates/accounts/formation.html`

**Acceptance criteria:**

- Steward can see all users pending induction confirmation
- Steward can review profile + programme completion data
- Confirming placement sets Level 1, deactivates Induction Tenant permission, creates home tenant permission
- User is notified and lands on their formation dashboard

---

### Summary: Phase 2 (G1–G4)

- **Commits:** 4 (Induction Tenant seed, sign-up + profile, programme enrolment, completion + placement)
- **Effort:** ~35% of Version 2 velocity
- **Dependencies:** Requires Phase 1 (Learn App must exist for induction programmes to run)

---

## Phase 3 (Version 2.2) — Competence Level UI & Formation Dashboard

### Why third?

Once users are being inducted and placed, the formation journey needs to be visible to them. This phase surfaces that journey in the UI and connects the Learn App's competence advancement to the user's profile and community.

---

### H1: Formation Dashboard (Level 1+ members)

**Goal:** Users see their current level, active programme, progress toward the next level, and their formation history.

**Features:**

- Level badge in navbar (current level — visual: coloured badge 1–5)
- "Your Formation Journey" card on dashboard:
  - Current competence level with KGS name (e.g. "Foundational Disciple")
  - Active qualification programme with progress bar
  - Next level: what programme must be completed
  - Pathway affiliation (e.g. "You are on the Service Pathway")
- Formation history: timeline of level advancements with dates and confirming steward
- "Level up requirements" modal (on level badge click)

**Data sources:**

- `User.competence_level` for current level
- `CertificationConfirmation` records for history
- Active `activity_type: "programme"` Activity for current enrolment

**Views:**

- `GET /accounts/formation/` — full formation history
- `GET /learn/htmx/formation-card/` — HTMX dashboard card partial

**Files to create / modify:**

- `templates/accounts/_formation_card.html` (HTMX partial)
- `templates/accounts/formation_history.html`
- `accounts/views.py` — formation_detail view

**Acceptance criteria:**

- Member sees current level, active programme progress, and next level requirement
- Dashboard card updates via HTMX without full page reload
- Formation history shows accurate timeline

---

### H2: App Drawer Level Gating

**Goal:** Apps in the drawer reflect the user's competence level. Apps above the user's access level are shown in a locked state with a path to unlock.

**Access levels per app:**

| App        | Minimum level | Notes                                            |
| ---------- | ------------- | ------------------------------------------------ |
| Bible      | 0b (Seeker)   | Always accessible                                |
| Learn      | 0b (Seeker)   | Browse only; enrol at Level 1                    |
| Activity   | 1             | Full access at Level 1                           |
| Community  | 1             | My Community at Level 1; Management at Level 3   |
| Governance | 3             | Reference Library at Level 3; Mandate at Level 4 |
| Paraclete  | 1             | Level 1+                                         |

**Drawer behaviour:**

- Available apps: rendered normally, clickable
- Locked apps: shown with lock icon and tooltip "Requires Level X"
- Click on locked app: modal explaining requirement + "Here is what you need to do"

**Files to create / modify:**

- `templates/partials/app_drawer.html` — conditional rendering
- `templates/partials/_app_locked_modal.html` — info modal
- `frontend/settings.py` — `APP_LEVEL_REQUIREMENTS` dict or equivalent
- `accounts/context_processors.py` — expose level to all templates

**Acceptance criteria:**

- Drawer correctly shows/hides apps by level for all 6 level states
- Locked state is clear and informative, not punishing
- User sees a path to unlock (points to Learn App)

---

### Summary: Phase 3 (H1–H2)

- **Commits:** 2 (formation dashboard, drawer gating)
- **Effort:** ~15% of Version 2 velocity
- **Dependencies:** Requires Phase 2 (users must have levels from induction)

---

## Phase 4 (Version 2.3) — Tenant Self-Service & Hierarchy

### Why fourth?

Once users are being inducted, placed, and progressing in their formation, the platform needs to support the growth of the network: new tenants being created, communities forming collectives, and members joining via invitation.

---

### I1: Tenant Creation & Management (Level 3+)

**Goal:** Stewards can create new Sceptre Community tenants, set their position in the hierarchy, and manage their members.

**Features:**

- `/tenants/create/` form (Level 3+ only): name, slug, tier, parent tenant, description, location, logo
- Tenant dashboard at `/tenants/{slug}/`
- Settings panel: name, description, logo, visibility
- Member management: invite users, assign roles, assign service orders, assign shepherds
- `TenantInvitation` model: tenant, email, invited_by, accepted_at, status

**Acceptance criteria:**

- Level 3+ can create tenants with correct tier and parent path
- Invitations work end-to-end (invite → email → accept → UserPermission created)
- Tenant hierarchy correctly reflected in materialized path

---

### I2: Multi-Tenant Content Visibility

**Goal:** Governance and Learn content respects tenant boundaries. Users see only content from their tenant(s).

**Features:**

- Governance records filtered by user's tenant(s)
- Learn content filtered by user's tenant(s) (Handbook-governed content visible to Level 4+ across all tenants)

**Acceptance criteria:**

- Users only see content from their tenant scope
- Level 5 has cross-tenant visibility where appropriate
- Filters apply consistently across all content surfaces

---

### Summary: Phase 4 (I1–I2)

- **Commits:** 2 (tenant management, multi-tenant content)
- **Effort:** ~10% of Version 2 velocity
- **Dependencies:** Requires Phase 2 (users need levels and home tenants for tenant creation to be meaningful)

---

## Implementation Roadmap

```text
MVP (COMPLETE — 6c43ce9)

Version 2.0 — Learn App Foundation
  L1: Learn App Backend (models, DRF, qualification framework)
  L2: Learn App UI (catalogue, enrolment, lesson viewer, certification)

Version 2.1 — Induction System
  G1: Induction Tenant (system tenant, seed command)
  G2: Sign-up & Profile Registration (entrant type, skills/gifting)
  G3: Induction Programme Enrolment (auto-enrol on placement)
  G4: Induction Completion & Tenant Placement (steward confirms → Level 1)

Version 2.2 — Formation UI & Drawer Gating
  H1: Formation Dashboard (level badge, progress card, history)
  H2: App Drawer Level Gating (locked state, path to unlock)

Version 2.3 — Tenant Self-Service
  I1: Tenant Creation & Management
  I2: Multi-Tenant Content Visibility
```

---

## Effort Estimation

| Phase | Features             | Commits | Weeks* | Notes                                                |
| ----- | -------------------- | ------- | ------ | ---------------------------------------------------- |
| 2.0   | Learn App (L1–L2)    | 2       | 3–4    | Largest single build — full qualification framework  |
| 2.1   | Induction (G1–G4)    | 4       | 2–3    | Depends on Phase 2.0                                 |
| 2.2   | Formation UI (H1–H2) | 2       | 1      | Mostly template work                                 |
| 2.3   | Tenants (I1–I2)      | 2       | 2      | Model additions + UI                                 |

*Estimates assume 1 developer, daily testing, minimal QA

---

## Success Metrics

### After Phase 2.0 (Learn App)

- All five qualification programmes browsable and enrollable
- Lesson completion and progress tracking working end-to-end
- Steward can confirm certifications, advancing competence level
- Level 4+ can author content; Level 5 can approve it

### After Phase 2.1 (Induction)

- Every new user lands in the Induction Tenant automatically
- Reconditioning and Beginners pathways serve different programmes
- Steward can confirm induction completion and place users in their home tenant
- No user enters a community without completing induction

### After Phase 2.2 (Formation UI)

- Users can see their level, programme, and progress at a glance
- App drawer correctly reflects access by level
- Users understand the path to unlock new apps

### After Phase 2.3 (Tenants)

- New Sceptre Communities can be established digitally
- Tenant hierarchy grows through Level 3+ steward action
- Content scoping works correctly across tenants

---

## Risk & Mitigation

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Learn App is larger than expected | High | System design already locked (v2). Build against that spec. Do not scope-creep in this phase. |
| Induction programme content not ready when system is built | Medium | System must be built first. Content (lessons, assignments) is authored by Level 4+ after the app exists. Seed with placeholder content. |
| Profile registration fields unclear (gifting/skills) | Medium | Chizola to confirm exact fields before G2 build begins. Mark as decision required. |
| Placement logic is manual (steward assigns) — bottleneck risk | Medium | Steward queue is visible and manageable. Auto-suggest by geography reduces effort. Scale with the network. |
| Reconditioning vs Beginners pathway boundaries unclear | Low | Defined by the Sceptre Community Programme concept note. Steward can adjust pathway during induction review if initial self-selection was wrong. |

---

## Open Decisions (Required Before Build)

- [ ] **G2 — Profile Registration fields:** What specific gifting, skills, occupation, and capacity fields should the profile registration form collect? (Chizola to confirm)
- [ ] **G1 — Induction Tenant tier:** Should `"induction"` be a new tier value in the Tenant model, or should the Induction Tenant use an existing tier with a `is_induction: true` flag? (Technical decision — recommend new tier value for clarity)
- [ ] **G4 — Placement geography:** Should geographic tenant matching be automated (suggest tenants by user's city/province) or fully manual (steward browses tenant directory)? (Recommend: suggest + steward confirms)
- [ ] **Data contract version:** Version 2 will require a v10 amendment to the data contract covering: Induction Tenant tier, `induction_enrolled_at`, `induction_completed_at`, `induction_pathway` on User. This amendment should be produced before Phase 2.1 build begins.

---

## Branch Structure

```text
main                      ← production
├─ mvp                    ← MVP complete (6c43ce9) [frozen]
└─ version-2              ← all v2 work branches from here
   ├─ version-2-l1        ← Learn App backend
   ├─ version-2-l2        ← Learn App UI
   ├─ version-2-g1        ← Induction Tenant
   ├─ version-2-g2        ← Sign-up & profile
   ├─ version-2-g3        ← Induction enrolment
   ├─ version-2-g4        ← Induction completion
   ├─ version-2-h1        ← Formation dashboard
   ├─ version-2-h2        ← Drawer gating
   ├─ version-2-i1        ← Tenant management
   └─ version-2-i2        ← Multi-tenant content
```

---

## Immediate Next Steps

1. **Confirm open decisions** (this week)
   - Profile registration fields (G2) — Chizola confirms
   - Induction Tenant tier strategy — technical decision
   - Placement geography logic

2. **Produce Data Contract v10 amendment** (before Phase 2.1)
   - New `"induction"` tier
   - Induction fields on User model
   - Confirm no breaking changes to existing schemas

3. **Begin Version 2.0 — Learn App build** (L1 first)
   - Build against the locked Learn App system design v2
   - Backend first, UI second

4. **Seed induction programmes** (in parallel with L2 UI or immediately after)
   - Reconditioning Programme: structure and placeholder lessons
   - Beginners Programme: structure and placeholder lessons
   - Community Programme: structure and placeholder lessons
   - *Full lesson content authored by Level 4+ users once platform is live*

---

## V2.1 Build Assignments

Concrete task checklist for the first build sprint. Branches and acceptance criteria are defined in L1–L4 and G1–G4 above.

### Phase 2.0 — Learn App (branch: `version-2-l1`, `version-2-l2`)

- [ ] Create `learn/` Django app with `CertificationConfirmation` model and migration
- [ ] Write `learn/serializers.py` — Programme, Course, Lesson, Assessment, Certification
- [ ] Write `learn/views.py` — DRF ViewSets for all learning record types
- [ ] Write `learn/urls.py` — API routing under `/api/learn/`
- [ ] Write `learn/service.py` — enrolment logic, prerequisite checks, certification trigger
- [ ] Write `learn/signals.py` — programme completion → draft certification Record
- [ ] Write `seed_programmes` management command — seeds 5 KGS-named programmes (Levels 1–5) with `kgs_pathways` and `kgs_qualification` in `custom_fields`
- [ ] Write `seed_induction_course` management command — seeds Induction Training course + 4 lessons inside New Life Programme
- [ ] Build Learn App UI (L2): catalogue, enrolment, lesson viewer, certification queue, authorship forms
- [ ] Build video embed utility (`core/utils/video.py`) + `templates/video/_player.html` partial
- [ ] Register `CertificationConfirmation` in `learn/admin.py` (L3 carry-forward)
- [ ] Add `htmx_submit_assessment` view + URL (L3 carry-forward)
- [ ] Add `htmx_settings_bible` view + URL in `accounts/` (L4 carry-forward)
- [ ] Add `ministry()` and `calendar_view()` views + URLs in `activity/` (L4 carry-forward)

### Phase 2.1 — Induction System (branch: `version-2-g1` … `version-2-g4`)

- [ ] Add `"induction"` to `Tenant.tier` choices + migration (G1)
- [ ] Add `induction_enrolled_at`, `induction_completed_at`, `induction_pathway` to `User` + migration (G1)
- [ ] Write `seed_induction_tenant` management command (G1)
- [ ] Build registration + email verification views (G2)
- [ ] Build profile setup form — entrant type, location, gifting/skills fields (G2, pending Chizola field confirmation)
- [ ] Wire G2 completion to auto-place user in Induction Tenant via `UserPermission` (G2)
- [ ] Write `enrol_induction_programmes(user, pathway)` in `learn/service.py` (G3)
- [ ] Build Induction Dashboard template (G3)
- [ ] Build steward induction review queue and detail views (G4)
- [ ] Extend `certifications/confirm/` endpoint for `context == "induction_completion"` placement logic (G4)

### Pre-build gates (before coding starts)

- [ ] Chizola confirms profile registration fields (G2 blocker)
- [ ] Data Contract v10 amendment produced and approved (covers Induction tier, User induction fields, `community_ref` relationship type, `Activity.linked_record` FK)

---

**Status:** Ready for Chizola review and open decision resolution
**Decision point before build:** Profile registration fields + Data Contract v10
