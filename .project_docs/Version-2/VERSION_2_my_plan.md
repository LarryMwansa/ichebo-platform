# Version 2 Building Plan — Post-MVP Features

## Strategic Context

**MVP Status:** Complete (6c43ce9)  
**Target:** Version 2 with enhanced UX, user onboarding, and competence workflows  
**Timeline:** Phased rollout based on user feedback from MVP  

---

## Phase 1 (Version 2.0): User Onboarding & Formation

### Why This First?
- MVP users currently start with no level (0). They can't access anything meaningful.
- Users need a clear entry point: Seeker → Level 1+ progression
- Formation/level advancement is the core value proposition (users do things to get certified)

### What Gets Built

#### G1: Seeker Entry & Formation Contract
**Goal:** New users enter as Seeker (Level 0), sign formation contract, get Level 1

**Features:**
- Seeker profile (email verified, basic profile data)
- Formation contract presentation (PDF or web view)
- Signature/acceptance flow (toggle + submit)
- Automatic Level 1 grant on acceptance
- Email notification to local steward (Level 3)

**Views:**
- `/accounts/join/` — Formation contract presentation
- `/accounts/join/accept/` — POST to accept contract
- Dashboard: Show "Formation Status" card (Seeker → Level 1)

**Data Model:**
- Add `formation_accepted_at` to User model
- Add `formation_signature_date` (when signed)
- Log to Activity: "Formation contract accepted"

**Files to Create/Modify:**
- `accounts/models.py` — add formation fields
- `accounts/views.py` — new join/accept views
- `templates/accounts/formation_contract.html` — contract presentation
- `accounts/management/commands/grant_initial_level.py` — auto-grant Level 1
- Database migration: add fields to User model

**Acceptance Criteria:**
- New user sees formation contract on first login
- User can accept contract
- User automatically becomes Level 1 after acceptance
- Steward notified of new Level 1 member

---

#### G2: Competence Level UI
**Goal:** Show user's current level, next level requirements, progress toward advancement

**Features:**
- Level badge in navbar (current level)
- Formation card on dashboard showing:
  - Current level (visual: colored badge 1-5)
  - Requirements for next level
  - Progress tracker (activities completed, etc.)
- Level advancement history (timeline of level changes)

**Views:**
- Dashboard card: "Your Formation Journey"
- `/accounts/formation/` — detailed formation history
- Modal: "Level up requirements" (onclick level badge)

**Data Model:**
- Query Activity records filtered by user
- Calculate progress toward next level based on:
  - Completed lessons (✓ if total >= threshold)
  - Certifications earned (✓ if count >= threshold)
  - Community participation (✓ if roles assigned)

**Files to Create/Modify:**
- `templates/accounts/_formation_card.html` — dashboard card (HTMX)
- `accounts/views.py` — formation_detail view
- `templates/accounts/formation_history.html` — timeline

**Acceptance Criteria:**
- User sees current level + next level requirements
- Dashboard shows progress toward advancement
- Formation history accessible

---

#### G3: Steward Onboarding (Level 2 → 3)
**Goal:** Users can apply for steward (Level 3) role; stewards review and grant

**Features:**
- "Apply for Steward Role" button (for Level 2+)
- Application form:
  - Why you want to serve
  - Time commitment
  - Experience summary
- Steward review queue at `/accounts/steward-approvals/` (Level 3+ only)
- Approve/reject with feedback

**Views:**
- `/accounts/steward-apply/` — form + POST
- `/accounts/steward-approvals/` — review queue
- `/accounts/htmx/approve-steward/<user_id>/` — HTMX action

**Data Model:**
- New `StewardApplication` model:
  - user, status (pending/approved/rejected)
  - motivation, experience, submitted_at
  - reviewed_by, reviewed_at, review_feedback
- New `CompetenceAdvancement` model:
  - user, from_level, to_level, granted_by
  - reason (formation_accepted, steward_approved, etc.)
  - granted_at

**Files to Create/Modify:**
- `accounts/models.py` — StewardApplication, CompetenceAdvancement
- `accounts/views.py` — steward_apply, steward_approvals, htmx_approve_steward
- `templates/accounts/steward_apply.html` — application form
- `templates/accounts/steward_approvals.html` — review queue
- Database migration

**Acceptance Criteria:**
- Level 2+ users can apply for steward
- Level 3+ stewards can review applications
- Approved applicants automatically become Level 3
- Rejection includes feedback for user

---

### Summary: Phase 1 (G1-G3)
- **Files Changed:** ~8 templates, 2 models, 3 views
- **Commits:** 3 (formation contract, level UI, steward onboarding)
- **Effort:** 40-50% of version-2 velocity
- **Dependencies:** None (builds cleanly on MVP)

---

## Phase 2 (Version 2.1): Tenant Self-Service & Hierarchy

### Why This Second?
- MVP has only one tenant (Handbook). Real use needs multi-tenant support.
- Users want to create and join local communities (tenants)
- Hierarchy enables decentralized governance

### What Gets Built

#### H1: Tenant Creation & Management
**Goal:** Users can create new tenants (local communities), assign stewards, set hierarchy

**Features:**
- `/tenants/create/` form (Level 3+ only)
  - Name, slug, tier, parent tenant, description, location
  - Logo upload
- Tenant dashboard at `/tenants/<slug>/` (for tenant members)
- Settings panel: name, description, logo, visibility
- Member management: invite users, assign roles

**Views:**
- `tenants:create` — form + creation
- `tenants:detail` — tenant dashboard
- `tenants:settings` — admin panel
- `tenants:members` — list + invite form
- `tenants:htmx-invite-user` — HTMX invite
- `tenants:htmx-change-role` — role assignment

**Data Model:**
- Extend `Tenant` model (already has parent, path, tier)
- New `TenantInvitation` model:
  - tenant, email, invited_by, accepted_at, status
- Extend `UserPermission` (already exists):
  - Add invitation workflow (invite → pending → accepted)

**Files to Create/Modify:**
- `tenants/views.py` — all views listed above
- `tenants/forms.py` — TenantForm, InviteForm
- `templates/tenants/create.html`
- `templates/tenants/detail.html`
- `templates/tenants/settings.html`
- `templates/tenants/members.html`
- Database migration (TenantInvitation, extend Tenant)

**Acceptance Criteria:**
- Level 3+ can create tenants
- Stewards can invite users
- Users can join via invitation
- Tenant hierarchy properly reflected in path field

---

#### H2: Multi-Tenant Content Visibility
**Goal:** Governance and Learn content respects tenant boundaries; users see only their tenant's content

**Features:**
- Filter governance records by user's tenant(s)
- Filter learning content by user's tenant(s)
- Users with access to multiple tenants see content from all
- Handbook content visible to Level 4+ across all tenants

**Views Affected:**
- `governance:records-list` — add tenant filter
- `learn:catalogue` — add tenant filter
- `learn:review` — add tenant filter (already Handbook only, but check)

**Data Model:**
- Already have `Record.tenant_id` (add if missing)
- Already have `Activity.metadata['tenant_id']` (for tracking which tenant context)

**Files to Create/Modify:**
- `governance/views.py` — add tenant filtering
- `learn/views.py` — add tenant filtering
- `templates/governance/*.html` — show tenant context
- `templates/learn/*.html` — show tenant context

**Acceptance Criteria:**
- Users only see content from their tenant(s)
- Level 5+ can see across all tenants (or Handbook only?)
- Filters work correctly in all surfaces

---

### Summary: Phase 2 (H1-H2)
- **Files Changed:** ~12 templates, 1 model, 8+ views
- **Commits:** 2 (tenant management, multi-tenant content)
- **Effort:** 30-40% of version-2 velocity
- **Dependencies:** Requires Phase 1 (users need levels for tenant creation)

---

## Phase 3 (Version 2.2): App Drawer Gating & Competence Workflows

### Why This Third?
- MVP lets all authenticated users see all apps. Drawer should gate by level/role.
- Competence advancement is core value (do → learn → advance)
- Users need clear path to unlock new apps

### What Gets Built

#### I1: App Drawer Level Gating
**Goal:** Apps appear in drawer only if user has access level; "locked" state shows requirement

**Features:**
- Each app has `required_level` setting (1-5)
- Drawer shows:
  - ✓ Available apps (user level >= required_level)
  - 🔒 Locked apps (user level < required_level) with "requires Level X" tooltip
- Locked app click shows info modal: "This app requires Level 3. You're currently Level 1. Complete X activities to advance."

**Views:**
- `partials/app_drawer_item.html` — conditional rendering (locked vs. available)
- Modal content: requirement explanation + next steps

**Data Model:**
- Add `required_level` field to app definitions (in settings or separate model)
- Option 1: Django settings `APP_REQUIREMENTS = {'governance': 3, 'learn': 1}`
- Option 2: New `AppAccess` model (more flexible)

**Files to Create/Modify:**
- `static/js/app_drawer.js` — conditional rendering logic
- `templates/app_drawer.html` — locked state UI
- `templates/_app_locked_modal.html` — info modal
- `settings.py` — add APP_REQUIREMENTS or create model

**Acceptance Criteria:**
- Locked apps show in drawer but are not clickable
- Tooltip/modal explains requirement
- User sees path to unlock ("complete 3 more lessons")

---

#### I2: Formation Advancement Automation
**Goal:** System automatically advances users based on completion thresholds

**Features:**
- Background job / signal handler that checks for level-up eligibility:
  - Level 1 → 2: Complete 1 lesson from 3 different courses
  - Level 2 → 3: Complete 1 full programme + 5 lessons
  - Level 3 → 4: Recommendation from steward (steward application)
  - Level 4 → 5: System admin (can also be earned via special achievement)
- Auto-create CompetenceAdvancement record
- User notification: "You've advanced to Level X!"
- Dashboard shows "New Level Unlocked" banner

**Views:**
- No new views (runs in background)
- Dashboard: show notification

**Data Model:**
- CompetenceAdvancement model (already planned in Phase 1)
- Define advancement rules in settings or database

**Files to Create/Modify:**
- `learn/signals.py` — listen for lesson completion, check eligibility
- `accounts/models.py` — add method `check_advancement_eligibility()`
- `accounts/management/commands/check_advancement.py` — batch job
- `templates/dashboard.html` — show advancement notifications

**Acceptance Criteria:**
- Users auto-advance when thresholds met
- Notifications sent
- History tracked in CompetenceAdvancement

---

### Summary: Phase 3 (I1-I2)
- **Files Changed:** ~5 templates, 1 signal, 1 management command
- **Commits:** 2 (drawer gating, advancement automation)
- **Effort:** 20-25% of version-2 velocity
- **Dependencies:** Requires Phase 1 (needs level system)

---

## Phase 4 (Version 2.3): Advanced Features

### What Could Go Here
- Learning paths (curated sequences: "Fast Track" vs. "Deep Dive")
- Competence badges + portfolio
- Social features (follow users, comment on lessons)
- Advanced analytics (stewards see member progress)
- Integrations (calendar sync, email digests)

### Decision Point
- Gather MVP feedback first
- Prioritize based on user requests
- May extend timeline or defer to version-3

---

## Implementation Roadmap

```
MVP (COMPLETE)
  └─ Branch: mvp (6c43ce9)

Version 2.0
  └─ Phase 1: User Onboarding & Formation
     G1: Formation Contract (Seeker → Level 1)
     G2: Level UI & Progress Dashboard
     G3: Steward Application & Approval
     
Version 2.1
  └─ Phase 2: Multi-Tenant & Hierarchy
     H1: Tenant Creation & Management
     H2: Tenant-Scoped Content Visibility
     
Version 2.2
  └─ Phase 3: Gating & Competence Workflows
     I1: App Drawer Level Gating
     I2: Automated Level Advancement
     
Version 2.3 (TBD)
  └─ Phase 4: Advanced Features (pending feedback)
```

---

## Effort Estimation

| Phase | Features | Commits | Weeks* | Notes |
|-------|----------|---------|--------|-------|
| 1.0 | Formation (G1-G3) | 3 | 2-3 | Core user journey |
| 1.1 | Multi-tenant (H1-H2) | 2 | 2-3 | Foundation for scaling |
| 1.2 | Gating & Advancement (I1-I2) | 2 | 1-2 | Polish user experience |
| 1.3 | Advanced features | TBD | TBD | Post-feedback |

*Estimates assume 1 developer, daily testing, minimal QA

---

## Success Metrics

### After Phase 1 (Formation & Onboarding)
- ✓ All users can self-serve onboard (Seeker → Level 1)
- ✓ Formation journey clear and intuitive
- ✓ Users see path to Level 2/3
- ✓ Stewards can evaluate applicants

### After Phase 2 (Multi-Tenant)
- ✓ Local communities can be created and managed
- ✓ Users can join multiple communities
- ✓ Content properly scoped to tenants
- ✓ Hierarchy (global → district → church) works

### After Phase 3 (Gating & Workflows)
- ✓ App drawer shows only accessible apps
- ✓ Users understand level requirements
- ✓ Level advancement is transparent
- ✓ Auto-advancement rewards activity

---

## Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| MVP feedback requires pivot | High | Schedule feedback session week 1; adjust plan if needed |
| Tenant hierarchy complexity | Medium | Use materialized path pattern (already in code) |
| Performance with multi-tenant data | Medium | Add indexes on tenant_id; lazy-load content |
| User onboarding friction | Medium | A/B test formation contract presentation |
| Advancement rules unclear to users | Medium | Add in-app help + tooltip explanations |

---

## Branch Structure

```
main                    ← production (behind)
├─ mvp                  ← MVP complete (6c43ce9) [FREEZE for feedback]
└─ version-2            ← v2.0 phase 1 starts here
   ├─ version-2-g1      ← Formation contract work
   ├─ version-2-g2      ← Level UI work
   ├─ version-2-g3      ← Steward onboarding work
   └─ version-2.0       ← Merge point after G1-G3
      └─ version-2.1    ← Phase 2 starts
         └─ version-2.2 ← Phase 3 starts
```

Or simpler: Keep all work on `version-2` branch, tag releases.

---

## Next Immediate Steps

1. **Get MVP feedback** (this week)
   - Test with 2-3 power users
   - Collect feedback on:
     - Is onboarding clear?
     - Is content discovery intuitive?
     - What's missing?

2. **Adjust plan** (if needed)
   - Update roadmap based on feedback
   - Reprioritize features

3. **Start Phase 1** (week 2)
   - Begin G1 (formation contract)
   - Iterate based on learning

4. **Document learnings**
   - Keep post_MVP.md updated
   - Record decisions in commit messages

---

## Questions to Answer Now

- [ ] Should app drawer require different levels (e.g., governance needs Level 3)?
- [ ] What's the formation contract? (Document to present to users)
- [ ] What are level-up requirements? (E.g., Level 1 → 2 requires X lessons)
- [ ] Should users be able to create tenants immediately (Level 3) or after onboarding (Level 2)?
- [ ] Should MVP feedback period be 1 week or 2 weeks before starting v2.0?

---

**Status:** Ready to proceed  
**Branch:** version-2  
**Decision Point:** Gather MVP feedback before finalizing v2.0 roadmap
