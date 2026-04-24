# Version 2 Building Plan — Post-MVP (Revised)
# Integrating Induction, Learning Pathways, and Sceptre Community Governance

## Strategic Context

**MVP Status:** Complete (commit 6c43ce9)  
**Vision:** Scale from MVP to a multi-tenant, decentralized Kingdom movement infrastructure  
**Scope:** User onboarding, formation pathways, learning structure, competence advancement, and Sceptre Community digital twin  
**Timeline:** 3 phases, ~10-12 weeks total, phased rollout based on live feedback  

---

## Core Strategic Principles

This roadmap is grounded in three foundational documents:
1. **Kingdom Governance System** — Apostolic structure, 7 governance pillars, 12 administrative offices, 24 service orders
2. **Sceptre Community Programme** — Decentralized community-based model, collective person principle, Acts 6 protocol
3. **Eight Kingdom Pathways + Qualification Framework** — Formation tiers from Induction (Level 0) through Level 5, linked to learning programmes

### Key Insight: Induction ≠ Onboarding

**Induction** is a 12-week **formation stage** (Level 0) where users:
- Understand the Kingdom mandate and governance model
- Complete foundational orientation and assessment
- Identify giftings, skills, and placement
- Transition to permanent community assignment

**Onboarding** is the signup/registration flow that precedes induction.

This distinction reshapes the v2.0 roadmap entirely.

---

## Phase 1.0 (v2.0): User Onboarding, Induction Entry & Formation Foundation
**Timeline:** 3 weeks | **Effort:** 45-50% of v2 velocity

### G1: User Onboarding & Induction Tenant Entry

**Goal:** Users sign up → register profile → enrol in Induction Tenant → begin 12-week formation  

**Features:**
- Sign-up flow (email verified, basic auth)
- Profile registration (name, gifting areas, availability, location)
- Auto-enrol in "Induction Tenant" (system-wide tenant)
- Induction orientation dashboard showing 12-week pathway
- Week-by-week formation milestones

**Views:**
- `/accounts/signup/` — Registration form
- `/accounts/profile/setup/` — Profile completion
- `/induction/dashboard/` — Formation roadmap (12 weeks)
- `/induction/modules/` — Orientation content (video, docs, activities)
- `/induction/assessments/` — Gifting survey, readiness checks

**Data Model:**
- User: add `level=0` (Seeker), `induction_started_at`, `induction_tenant_id`
- New `InductionRecord` model:
  - user, tenant (Induction), started_at, completed_at, status
  - gifting_assessment (JSONField), placement_recommendation
- Extend `UserPermission`: add `induction_status` (active/completed/paused)

**Backend Integration:**
- Add Induction Tenant (tenant_id = system-wide, not geographic)
- Create "Induction Coordinator" role (Level 4+ stewards manage induction cohorts)
- Activity logging: track each induction milestone

**Files to Create/Modify:**
- `accounts/models.py` — add level=0, induction fields
- `accounts/views.py` — signup, profile setup views
- `induction/models.py` (new app) — InductionRecord
- `induction/views.py` — dashboard, modules, assessments
- `templates/accounts/signup.html` — registration
- `templates/induction/dashboard.html` — 12-week roadmap
- `templates/induction/modules/` — orientation content
- Database migrations

**Acceptance Criteria:**
- New user completes signup → auto at Level 0, Seeker role
- User sees 12-week induction dashboard with milestones
- Gifting assessment completed + placement recommendation generated
- Induction Coordinator notified of new cohort

---

### G2: Competence Level UI & Progress Dashboard

**Goal:** Users see their current level, next level requirements, formation progress

**Features:**
- Dashboard card: "Your Formation Journey"
  - Current level (badge: Seeker/Level 1-5)
  - Induction progress bar (for Level 0)
  - Next level requirements
  - Pathways available at current level
- Formation history view (timeline of level changes)
- Level requirements modal (onclick level badge)
  - "Level 1: Complete Induction (8/12 weeks)" → "Enrol in Certificate Programme"
  - "Level 2: Certificate + 3 months in Certificate → Diploma Programme"

**Views:**
- Dashboard card: "Your Formation Journey" (HTMX partial)
- `/accounts/formation/` — Detailed formation view
- `/accounts/formation/history/` — Timeline of advancements

**Data Model:**
- New `CompetenceAdvancement` model:
  - user, from_level, to_level, reason (induction_completed, certificate_earned, etc.)
  - triggered_by (ForeignKey to learning Record, if applicable)
  - granted_at, granted_by
- Extend Activity: track "induction_milestone_reached", "level_advanced"

**Files to Create/Modify:**
- `templates/dashboard/_formation_card.html` — progress card
- `accounts/views.py` — formation_detail view
- `accounts/models.py` — CompetenceAdvancement
- `accounts/serializers.py` — expose formation data
- `templates/accounts/formation_history.html` — timeline
- Database migrations

**Acceptance Criteria:**
- Level 0 users see "8/12 weeks of induction complete"
- Level 1 users see "Certificate Programme available"
- Formation history shows when user advanced

---

### G3: Steward Application & Approval Workflow

**Goal:** Level 2 users can apply for steward role; Level 3+ stewards review and approve

**Features:**
- "Apply for Steward Role" button (visible only to Level 2+)
- Application form:
  - Why do you want to serve? (text)
  - Time commitment (hours/week)
  - Experience summary (text)
  - Community/gifting focus (dropdown)
- Steward review queue at `/accounts/steward-approvals/` (Level 3+ only)
  - Card layout: applicant info, application, approval/reject buttons
- Approve action:
  - User advances to Level 3
  - CompetenceAdvancement record created (reason: steward_approved)
  - User notified via Activity + email
  - Can access "Community Coordinator" role now

**Views:**
- `/accounts/steward-apply/` — Application form
- `/accounts/steward-approvals/` — Review queue (Level 3+ only)
- `/accounts/htmx/approve-steward/<user_id>/` — HTMX action

**Data Model:**
- New `StewardApplication` model:
  - user, status (pending/approved/rejected)
  - motivation, experience, time_commitment
  - submitted_at, reviewed_by, reviewed_at, review_feedback

**Files to Create/Modify:**
- `accounts/models.py` — StewardApplication
- `accounts/views.py` — steward_apply, steward_approvals, htmx_approve_steward
- `templates/accounts/steward_apply.html` — form
- `templates/accounts/steward_approvals.html` — review queue
- Database migrations

**Acceptance Criteria:**
- Level 2+ can apply for steward
- Level 3+ see and can approve/reject applications
- Approved users become Level 3 and can coordinate communities

---

### Summary: Phase 1.0 (G1-G3)

| Item | Details |
|------|---------|
| **Features** | Induction entry + 12-week formation, competence UI, steward application |
| **Models** | InductionRecord, CompetenceAdvancement, StewardApplication |
| **Views** | ~8-10 new templates, ~5 view functions, HTMX partials |
| **Commits** | 3 (induction entry, competence UI, steward workflow) |
| **Effort** | 45-50% of v2 velocity (~2.5 weeks, 1 dev) |
| **Dependencies** | Builds cleanly on MVP; no external dependencies |
| **Key Outcome** | Users have clear entry point (Induction) and see formation path |

---

## Phase 1.1 (v2.1): Learning Pathways & Qualification Structure
**Timeline:** 3 weeks | **Effort:** 35-40% of v2 velocity

### H1: Learning Programmes & Enrolment System

**Goal:** Expose 5 qualification programmes (Certificate → Doctorate) with level gating and pathway filtering

**Features:**
- Programme catalogue:
  - **Certificate Programme** (Level 1) — 1 year, entry foundation
  - **Diploma Programme** (Level 2) — 3 years, operator/worker training
  - **Degree Programme** (Level 3) — 4 years, team leader preparation
  - **Masters Programme** (Level 4) — 4-5 years, system builder
  - **Doctorate Programme** (Level 5) — 7 years, system architect
- Each programme links to 5-10 courses (existing Learn app)
- Enrolment system:
  - Users can enrol in available programmes (level-gated)
  - Enrolment dashboard shows progress (% courses completed)
  - Completion triggers Activity listener → competence advancement check
- Pathway filtering:
  - Dashboard shows "You are on the Service Pathway" (dynamic based on courses enrolled)
  - Learn catalogue filters by available pathways for user's level

**Data Model:**
- New `Enrolment` model:
  - user, programme (ForeignKey to Record), tenant_id
  - pathway (varchar: "Service Pathway", "Spiritual Formation Pathway", etc.)
  - enrolled_at, completed_at, status (active/paused/completed)
- Extend Record (learning):
  - Add `competence_level` (1-5), `programme_type` (certificate/diploma/etc.)
  - Add `pathway` (CharField, e.g., "Service", "Spiritual Formation", "Mission")
- Extend Activity:
  - Track "programme_enrolled", "programme_completed"

**Backend Integration:**
- Learn app already has Programme, Course, Lesson, Quiz, Assignment records
- Add programme catalogue view (filter by level, show available next programmes)
- Add enrolment endpoints: POST /api/enrolments/, GET /api/enrolments/?user_id=X
- Signal handler: on Activity("lesson_completed"), check if user can advance

**Views:**
- Dashboard card: "Your Programmes"
  - Certificate: 6/10 courses complete (60% progress)
  - Next: Diploma Programme (locked: complete Certificate first)
- Learn catalogue: filter by pathway ("Service Pathway", "Spiritual Formation Pathway", etc.)
- `/learn/programmes/` — Catalogue of all programmes (level-gated)
- `/learn/programmes/<id>/` — Programme detail + "Enrol" button
- `/learn/my-programmes/` — User's enrolments + progress

**Files to Create/Modify:**
- `records/models.py` — extend Record: add competence_level, pathway
- `learn/models.py` (or records) — new Enrolment model
- `learn/views.py` — programme_catalogue, programme_detail, my_programmes
- `learn/serializers.py` — EnrolmentSerializer
- `templates/learn/programmes.html` — catalogue
- `templates/learn/programme_detail.html` — detail + enrol
- `templates/learn/my_programmes.html` — user's enrolments
- Database migrations

**Acceptance Criteria:**
- Level 1 user sees Certificate Programme available to enrol
- User enrols in Certificate → appears in "My Programmes" with 0% progress
- User completes first course → Activity logged, enrolment progress updates to 10%
- Learn catalogue filters by pathways available at user's level

---

### H2: Multi-Tenant Content Visibility & Induction Tenant Scoping

**Goal:** Users see only content from their assigned tenants; Induction Tenant has special scoping rules

**Features:**
- Induction Tenant (Level 0):
  - Users see only orientation content (induction modules)
  - After induction completion, users auto-transfer to geographic/functional tenant
- Permanent Tenant (Level 1+):
  - Users see governance, learn, bible, community content scoped to their tenant(s)
  - Handbook accessible to Level 4+ across all tenants
  - Can belong to multiple tenants (e.g., local church + global learning network)
- Content filtering:
  - Governance records filtered by tenant
  - Learn programmes filtered by tenant (unless Handbook/global)
  - Bible reader shows tenant-context annotations

**Data Model:**
- Extend UserPermission:
  - Add `tenant_hierarchy` (JSONField: list of tenant IDs user can see)
  - Add `induction_completed_at` (when transitioned from Induction Tenant)
- Activity: add `tenant_context_id` (which tenant this activity happened in)

**Backend Integration:**
- Update get_queryset() in all viewsets:
  - Filter Record, Activity, Annotation by user's tenant_ids
  - Exception: Handbook records visible to Level 4+
- Special case: Induction Tenant
  - Only shows induction modules + assessment records
  - On induction completion, auto-assign to next tenant (from placement recommendation)

**Views Affected:**
- `governance:records-list` — add tenant filter, show current tenant context
- `learn:catalogue` — add tenant filter
- `learn:my-programmes` — show tenant-scoped programmes
- `bible:annotations` — show tenant-context
- `dashboard:index` — show "You are in: <Tenant Name>" header

**Files to Create/Modify:**
- `accounts/models.py` — extend UserPermission
- `governance/views.py` — add tenant filtering
- `learn/views.py` — add tenant filtering + pathway filtering
- `records/views.py` — add tenant filtering for all Record queries
- `activity/views.py` — add tenant context
- Template headers: show current tenant context
- Database migrations

**Acceptance Criteria:**
- Level 0 user in Induction Tenant sees only orientation modules
- After induction: auto-moved to assigned tenant
- Level 1 user sees only their tenant's governance + learn content
- Handbook visible to Level 4+ across all tenants
- Users can view activity filtered by their tenants

---

### H3: Automatic Competence Advancement (Signal Handlers)

**Goal:** System auto-advances users when thresholds met; no manual approval needed (except Level 3)

**Features:**
- Level advancement triggers:
  - **Level 0 → 1:** Complete induction (12 weeks) → auto-advance, move to assigned tenant
  - **Level 1 → 2:** Complete Certificate programme → auto-advance (if steward approves)
  - **Level 2 → 3:** Apply for steward + steward approval (manual review G3)
  - **Level 3 → 4:** Complete Diploma programme + Level 3 role for 1 year (auto-advance)
  - **Level 4 → 5:** System admin assignment (manual, future phase)
- Notifications:
  - User gets notification: "You've advanced to Level 2! Diploma Programme is now available."
  - Dashboard shows "New Level Unlocked" banner (auto-dismiss after 7 days)
- CompetenceAdvancement record created automatically

**Backend Integration:**
- Signal handler in `learn/signals.py`:
  - Listen for Activity("programme_completed")
  - Check user's current level + programme type
  - If threshold met, create CompetenceAdvancement, emit "user_advanced" signal
- Celery task (future): daily check for users eligible for Level 4 (1 year as Level 3)

**Files to Create/Modify:**
- `learn/signals.py` — new signal handlers for programme completion
- `accounts/signals.py` — auto-advancement logic
- `accounts/models.py` — add method `check_advancement_eligibility()`
- `accounts/tasks.py` — Celery task for batch advancement check
- `templates/dashboard.html` — "Level Up" banner

**Acceptance Criteria:**
- User completes Induction → Level 0 → 1 transition auto-triggered
- User completes Certificate → Activity logged, CompetenceAdvancement created
- User sees "Level 2 Unlocked!" notification
- Diploma Programme becomes available

---

### Summary: Phase 1.1 (H1-H3)

| Item | Details |
|------|---------|
| **Features** | Learning programmes (5 tiers), enrolment system, tenant scoping, auto-advancement |
| **Models** | Enrolment, extend Record + UserPermission |
| **Views** | ~6-8 new templates, ~4 view functions |
| **Commits** | 2 (learning structure, multi-tenant visibility) + 1 (advancement automation) |
| **Effort** | 35-40% of v2 velocity (~2 weeks) |
| **Key Outcome** | Learning pathways are now engine for competence advancement; induction → Level 1 → programmes |

---

## Phase 1.2 (v2.2): App Drawer Gating & Sceptre Community Visibility
**Timeline:** 2 weeks | **Effort:** 20-25% of v2 velocity

### I1: App Drawer Level Gating

**Goal:** Apps appear/lock in drawer based on user level; locked apps show what's required

**Features:**
- App access requirements:
  - **Bible** — Level 0+
  - **Learn** — Level 0+ (orientation only), Level 1+ (full)
  - **Community** — Level 1+
  - **Governance** — Level 2+
  - **Dashboard (admin)** — Level 4+
- Drawer shows:
  - ✓ Available apps (user level >= required_level)
  - 🔒 Locked apps with tooltip: "Requires Level 2. You're Level 1. Enrol in Certificate to advance."
- Locked app click → Modal: "To access Governance, advance to Level 2. Enrol in Certificate Programme (6 courses, 8 weeks)."

**Views:**
- App drawer with conditional rendering
- Lock modal with pathway to unlock

**Data Model:**
- New `AppAccess` model:
  - app_name (varchar: bible, learn, community, etc.)
  - required_level (integer: 0-5)
  - unlock_pathway (text: "Complete Certificate Programme")

**Files to Create/Modify:**
- `core/models.py` — AppAccess model
- `templates/components/_app_drawer.html` — conditional rendering
- `static/js/app_drawer.js` — lock/unlock logic
- `templates/_app_locked_modal.html` — unlock info
- Database migrations + seed data

**Acceptance Criteria:**
- Level 0 can access Bible, Learn (orientation)
- Level 1 can access Learn (full), Community
- Level 2 can access Governance
- Locked apps show clear unlock path

---

### I2: Sceptre Community Visibility & Community Coordinator Role

**Goal:** Level 3+ users who are Community Coordinators see their Sceptre Community dashboard

**Features:**
- New "Community Coordinator" role (auto-assigned when Level 3 approved)
  - Can view `/community/<community_id>/dashboard/`
  - Can manage community members, gatherings, announcements
  - Can see linked verses, records, activities for their community
- Community dashboard shows:
  - Community info (name, theme, area of operation)
  - Member roster (with roles: Shepherd, Net Caster, Net Mender, etc.)
  - Recent activities (lessons completed, gatherings scheduled)
  - Community metrics (formation progress, engagement)

**Views:**
- `/community/<slug>/` — Community dashboard (Community Coordinator only)
- `/community/<slug>/members/` — Member roster + role assignment
- `/community/<slug>/gatherings/` — Schedule + attendance
- `/community/<slug>/reports/` — Community health metrics

**Data Model:**
- Extend Tenant:
  - Add `coordinator_user_id` (ForeignKey to User, Community Coordinator)
  - Add `community_theme` (CharField: "Education", "Healthcare", "Business", etc.)
  - Add `area_of_operation` (TextField: geographic/functional scope)
- Extend UserPermission:
  - Add `role_in_community` (CharField: Coordinator, Shepherd, Net Caster, Net Mender, Member)

**Files to Create/Modify:**
- `community/views.py` — community dashboard, members, gatherings
- `tenants/models.py` — extend Tenant
- `templates/community/dashboard.html` — coordinator dashboard
- `templates/community/members.html` — roster + role assignment

**Acceptance Criteria:**
- User approved as steward → becomes Level 3 + Community Coordinator
- Coordinator sees their community dashboard
- Can view + manage community members

---

### Summary: Phase 1.2 (I1-I2)

| Item | Details |
|------|---------|
| **Features** | App drawer gating, community coordinator view |
| **Models** | AppAccess, extend Tenant + UserPermission |
| **Views** | ~4-5 new templates |
| **Commits** | 2 (drawer gating, community visibility) |
| **Effort** | 20-25% of v2 velocity (~1.5 weeks) |
| **Key Outcome** | Users see clear level progression; Community Coordinators can manage their community |

---

## Phase 1.3 (v2.3): Advanced Features (TBD)
**Timeline:** 2+ weeks (future phases) | **Effort:** TBD

Deferred to v2.3 based on feedback. Candidates:
- Learning paths (curated sequences within programmes)
- Competence badges + portfolio
- Social features (follow users, comment on lessons)
- Community analytics (stewards see member formation progress)
- Notifications (email digests, daily activity summaries)
- Mobile app refinement (role-adaptive Flutter interface)

---

## Implementation Roadmap

```
MVP (COMPLETE)
  └─ Branch: mvp (commit 6c43ce9)

Version 2.0
  ├─ Branch: version-2
  └─ Phase 1: Induction & Competence Foundation (3 weeks)
     ├─ G1: User Onboarding → Induction Tenant Entry
     ├─ G2: Competence Level UI & Formation Dashboard
     └─ G3: Steward Application & Approval
     
Version 2.1
  └─ Phase 2: Learning Pathways & Multi-Tenant Scoping (3 weeks)
     ├─ H1: Learning Programmes (Certificate → Doctorate) & Enrolment
     ├─ H2: Tenant-Scoped Content Visibility & Induction Tenant Special Rules
     └─ H3: Automatic Competence Advancement via Signal Handlers
     
Version 2.2
  └─ Phase 3: App Drawer Gating & Community Coordinator View (2 weeks)
     ├─ I1: App Drawer Level Gating
     └─ I2: Sceptre Community Visibility & Coordinator Dashboard
     
Version 2.3 (TBD)
  └─ Phase 4: Advanced Features (pending feedback)
     └─ Learning paths, badges, social, analytics, integrations
```

---

## Effort & Timeline Estimation

| Phase | Goal | Duration | Commits | Effort |
|-------|------|----------|---------|--------|
| **1.0** | Induction → Competence UI → Steward workflow | 3 weeks | 3 | 45-50% |
| **1.1** | 5 Learning programmes → Multi-tenant → Auto-advancement | 3 weeks | 3 | 35-40% |
| **1.2** | App drawer gating → Community coordinator | 2 weeks | 2 | 20-25% |
| **1.3** | Advanced features (TBD) | 2+ weeks | TBD | TBD |
| **TOTAL v2.0-2.2** | Full user formation loop + learning engine | **8 weeks** | **8** | **100%** |

*Assumes 1 developer, daily testing, live user feedback loop*

---

## Critical Data Flow: Level 0 → Level 5

```
SIGNUP
  ↓
CREATE USER (level=0, role=Seeker)
  ↓
ENROL IN INDUCTION TENANT
  ↓
[12 WEEKS INDUCTION]
  - Week 1-4: Orientation modules + gifting assessment
  - Week 5-8: Foundation teachings + skill survey
  - Week 9-12: Placement assessment + transition prep
  ↓
INDUCTION COMPLETE
  ↓
AUTO-ADVANCE TO LEVEL 1
  ↓
MOVE TO ASSIGNED TENANT (geographic or functional)
  ↓
ENROL IN CERTIFICATE PROGRAMME
  ↓
[CERTIFICATE PATHWAY: 1 year]
  - Complete 10 courses → Activity logged
  - Signal handler checks advancement threshold
  ↓
AUTO-ADVANCE TO LEVEL 2
  ↓
ENROL IN DIPLOMA PROGRAMME
  ↓
[DIPLOMA PATHWAY: 3 years]
  - Complete courses + demonstrate operator skills
  ↓
APPLY FOR STEWARD ROLE (or auto-eligible Level 3)
  ↓
STEWARD APPROVAL (manual review)
  ↓
ADVANCE TO LEVEL 3 + COMMUNITY COORDINATOR
  ↓
[Continue progression to Level 4-5...]
```

---

## Key Architectural Decisions

### 1. Induction Tenant is System-Wide
- Not geographic, not functional
- All new users start here
- Special content scoping (orientation only)
- On completion, auto-move to permanent tenant

### 2. Learning Programmes Drive Advancement
- Formation is not passive (no "accept contract" shortcut)
- Users must complete programme milestones to advance
- Signal handlers auto-detect threshold + promote
- Creates measurable, repeatable pathway

### 3. Tenant Hierarchy Mirrors Civic Demarcation
- Follows Sceptre Community model
- Each tenant has community theme + area of operation
- Multi-tenant membership allowed (user can belong to local church + learning network)
- Content filtering follows tenant boundaries

### 4. Community Coordinator is Steward+
- Level 3 users auto-become Community Coordinators
- Can see + manage their community's formation progress
- This drives "Shepherd" and "Net Caster" roles
- Acts 6 Protocol: split governance oversight from operational management

### 5. No Forced Tenant Assignment Until Post-Induction
- Prevents wrong placement
- Gifting assessment + steward recommendation inform placement
- Users see provisional placement → can confirm or request change

---

## Success Criteria

### After Phase 1.0 (Induction & Competence)
- ✓ All new users can self-serve onboard (Seeker → Level 1)
- ✓ Induction 12-week pathway is clear and visible
- ✓ Gifting assessment guides placement recommendation
- ✓ Users see formation progress on dashboard
- ✓ Stewards can review + approve Level 2→3 applications

### After Phase 1.1 (Learning Pathways)
- ✓ 5 qualification programmes available (Certificate → Doctorate)
- ✓ Users can enrol in programmes appropriate to their level
- ✓ Learn catalogue shows pathway filtering ("You are on Service Pathway")
- ✓ Completing programmes auto-triggers level advancement
- ✓ Tenant-scoped content filtering prevents cross-tenant leakage

### After Phase 1.2 (Gating & Community)
- ✓ App drawer shows locked/unlocked apps by level
- ✓ Users see clear unlock path (e.g., "Enrol in Certificate to access Governance")
- ✓ Level 3+ Community Coordinators can manage their community
- ✓ Community dashboard shows formation progress of members

---

## Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Induction 12-week timeline feels too long | High | Offer "accelerated" pathway for existing believers (Reconditioning Programme) |
| Users abandon during induction | High | Weekly check-ins from Induction Coordinator; milestone reminders |
| Tenant placement friction | Medium | Offer "temporary placement" first 2 weeks; allow change request |
| Learning programme content not ready | High | Start with Certificate only; add Diploma/Degree later (can still model structure) |
| Advancement too automatic (no human touch) | Medium | Keep Level 2→3 as manual approval; let others auto-advance |
| Performance: multi-tenant queries slow | Medium | Add indexes on `tenant_id`, `user_id`; lazy-load content |

---

## Questions to Lock In Now (Before Phase 1 Starts)

1. **Induction Duration:** Always 12 weeks, or configurable per tenant?
2. **Level 0 → 1 Automatic:** Does induction completion auto-advance, or does steward need to confirm?
3. **Tenant Assignment:** Who assigns placement after induction? (Steward recommendation? Coordinator? User choice?)
4. **Certificate Programme Content:** Do all 10 courses exist, or need to be created?
5. **Diploma/Degree/Masters Content:** Available at v2.0 launch, or staged per phase?
6. **Handbook Access:** Should Level 4+ see all Handbook across tenants, or only their tenure's Handbook?
7. **Community Theme:** Pre-defined list (Education, Healthcare, Business, etc.) or free-text?
8. **Reconditioning Programme:** Is this a separate 4-week path for existing believers, or part of Induction?

---

## Dependencies & Prerequisites

✓ MVP complete (records, activities, bible, learn authorship all in place)
✓ User roles model (levels 0-5 exist)
✓ Tenant model with hierarchy (already built)
✓ Learn app with Programme/Course/Lesson records (Phase F complete)
✓ Activity logging (exists, can extend)
✓ Email notifications (exists, can extend)

**New Dependencies (Phase 1.1+):**
- Celery + Redis (for signal handlers, batch jobs) — planned in Production Infrastructure Plan
- Email service (for advancement notifications) — already available

---

## Branch & Release Strategy

```
main (production)
  ← mvp (frozen MVP reference)
  ← mvp-production (demo prep)
  ← version-2 (active development)
     ├─ Tag: v2.0.0 (Phase 1.0 complete)
     ├─ Tag: v2.1.0 (Phase 1.1 complete)
     ├─ Tag: v2.2.0 (Phase 1.2 complete)
     └─ Tag: v2.3.0 (Phase 1.3 complete)
```

Deploy to staging after each phase; gather feedback before next phase.

---

## Next Immediate Steps

1. **Clarify the 8 questions above** (this week)
   - Lock in formation rules, timelines, content availability
   - Get design feedback on induction dashboard

2. **Prepare Induction Content** (Week 1)
   - Video: "Welcome to the Kingdom Governance System" (3 min)
   - Orientation module 1: "What is Induction?" (read, 5 min)
   - Gifting assessment form (15 min to complete)
   - This can happen in parallel with Phase 1 dev

3. **Start Phase 1.0 Development** (Week 1)
   - Signup + profile setup (3 days)
   - Induction dashboard + models (2 days)
   - Gifting assessment (1 day)
   - Steward application flow (2 days)
   - Testing + refinement (2 days)

4. **Gather Feedback** (End of Week 3)
   - Test with 2-3 power users (existing stewards)
   - Does induction feel right? Too long? Too short?
   - Placement recommendation working?
   - Adjust before Phase 1.1

5. **Start Phase 1.1** (Week 4)
   - Learning programmes + enrolment
   - Tenant scoping
   - Signal handlers

---

## Related Documents

- `Kingdom Governance System v1` — 7 pillars, 12 offices, 24 service orders
- `Sceptre Community Programme v2` — Decentralized model, Church Nodes, formation pathways
- `Production Infrastructure Plan: ICS Post-MVP` — Backend scaling (Redis, Celery, Docker, offline)
- `Onboarding Stage (Concept)` — 12-week induction vision
- `Prompt for Learning App` — 5 programmes, 8 pathways, qualification framework

---

**Status:** Ready to proceed  
**Branch:** version-2  
**Decision Point:** Lock in 8 questions above; confirm Induction content is being prepared  
**Target Launch:** v2.0 (Phase 1) within 3 weeks
