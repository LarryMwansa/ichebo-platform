# VERSION 2 PLANNING — QUICK REFERENCE

## 8 Questions to Answer Now (Before Phase 1 Starts)

```
1. INDUCTION DURATION
   □ Always 12 weeks (hard deadline)
   □ Flexible per cohort (4-16 weeks)

2. LEVEL 0→1 ADVANCEMENT
   □ Auto on completion (induction coordinator confirms)
   □ Manual approval required

3. TENANT ASSIGNMENT
   □ Induction Coordinator assigns (based on assessment)
   □ User chooses from recommendations
   □ Steward assigns after review

4. CERTIFICATE PROGRAMME CONTENT
   □ All 10 courses exist, ready to use
   □ Need to create 5-10 courses in Phase 1.1
   □ Start with 5 courses, add more later

5. DIPLOMA/DEGREE/MASTERS CONTENT
   □ Available at v2.0 launch (all programs)
   □ Available at v2.1 launch (phased)
   □ Staged delivery: Certificate first, others later

6. HANDBOOK ACCESS (Level 4+)
   □ See Handbook across all tenants (system-wide)
   □ See only their own tenant's handbook
   □ Handbook is not tenant-scoped (everyone sees same content)

7. COMMUNITY THEME
   □ Pre-defined list: (Education, Healthcare, Business, Ministry, etc.)
   □ Free-text entry (community defines their own)
   □ Both (predefined + custom)

8. RECONDITIONING PROGRAMME
   □ Include as 4-week alternative path for existing believers
   □ Not in v2.0; defer to v2.1
   □ Combine with Induction (one path for all)
```

---

## The 3 Phases at a Glance

```
PHASE 1.0 (3 weeks) — INDUCTION & COMPETENCE
├─ G1: User signup → Induction Tenant → 12 weeks → Level 1
├─ G2: Dashboard shows level, progress, next steps
└─ G3: Steward application (L2→L3) + Community Coordinator role

PHASE 1.1 (3 weeks) — LEARNING & MULTI-TENANT
├─ H1: 5 Programmes (Certificate → Doctorate) + Enrolment system
├─ H2: Tenant-scoped content filtering + Induction Tenant rules
└─ H3: Signal handlers auto-advance on programme completion

PHASE 1.2 (2 weeks) — GATING & COMMUNITY
├─ I1: App drawer shows locked/unlocked + unlock paths
└─ I2: Community Coordinator dashboard (member roster, progress)
```

---

## Data Models You'll Need

```
PHASE 1.0
├─ InductionRecord (user, tenant, status, gifting_assessment, placement_recommendation)
├─ CompetenceAdvancement (user, from_level, to_level, reason, granted_at)
├─ StewardApplication (user, status, motivation, experience, reviewed_by, feedback)
└─ Extend User: add level=0, induction_started_at

PHASE 1.1
├─ Enrolment (user, programme, tenant, pathway, enrolled_at, status)
├─ Extend Record: add competence_level, pathway (varchar)
└─ Signal handlers: listen for Activity("programme_completed")

PHASE 1.2
├─ AppAccess (app_name, required_level, unlock_pathway)
└─ Extend Tenant: add coordinator_user_id, community_theme, area_of_operation
```

---

## User Progression (The Golden Flow)

```
SIGNUP
  ↓ (profile setup)
INDUCTION TENANT (Level 0)
  ├─ Week 1-4: Orientation modules
  ├─ Week 5-8: Gifting assessment
  ├─ Week 9-12: Placement assessment
  └─ Advance to Level 1 ✓
  ↓
PERMANENT TENANT (assigned after assessment)
  ├─ Enrol in CERTIFICATE (Level 1)
  ├─ Complete 10 courses
  ├─ Signal handler: "Certificate 100%" → Level 1→2 ✓
  ↓
ENROL IN DIPLOMA (Level 2)
  ├─ (3 years of courses)
  ├─ After X courses + demonstrated skills...
  ├─ Apply for Steward Role
  └─ Steward approved → Level 2→3 + Community Coordinator ✓
  ↓
COMMUNITY COORDINATOR (Level 3)
  ├─ Manage their Sceptre Community
  ├─ See member formation progress
  ├─ Assign roles (Shepherd, Net Caster, Net Mender)
  ↓
CONTINUE TO LEVEL 4-5 (future phases)
```

---

## Files to Create/Modify (Phase 1.0 Summary)

```
NEW MODELS
├─ induction/models.py → InductionRecord
├─ accounts/models.py → CompetenceAdvancement, StewardApplication
└─ Extend User, UserPermission

NEW VIEWS/TEMPLATES
├─ accounts/views.py → signup, profile_setup, steward_apply, steward_approvals
├─ induction/views.py → dashboard, modules, assessments
├─ accounts/views.py → htmx_approve_steward
└─ Templates: signup.html, induction/dashboard.html, steward_apply.html, steward_approvals.html

DATABASE MIGRATIONS
└─ accounts: add level=0, induction fields
└─ induction: new InductionRecord table
└─ Seed data: Induction Tenant
```

---

## Success Checklist

### Phase 1.0 (End of Week 3)
- [ ] New user sees signup → profile setup → induction dashboard
- [ ] Induction dashboard shows 12-week roadmap with milestone tracking
- [ ] Gifting assessment form collects data
- [ ] Steward can review and approve/reject steward applications
- [ ] Approved steward becomes Level 3 + Community Coordinator
- [ ] Level badge in navbar updates when level changes

### Phase 1.1 (End of Week 6)
- [ ] 5 programmes visible in catalogue (level-gated)
- [ ] User can enrol in programmes for their level
- [ ] Learn catalogue filters by available pathways
- [ ] Completing a programme triggers advancement signal
- [ ] User auto-advances (L0→1, L1→2, etc.)
- [ ] Induction Tenant users see only orientation modules (not other content)
- [ ] Level 1+ users see their tenant's content + collaborating networks

### Phase 1.2 (End of Week 8)
- [ ] App drawer shows locked/unlocked apps
- [ ] Locked app shows modal with unlock requirement
- [ ] Community Coordinator sees dashboard for their community
- [ ] Can view member roster, formation progress, recent activities

---

## Content You'll Need to Create (Parallel Work)

### Induction Orientation (by end of Week 1)
- [ ] Video: "Welcome to the Kingdom Governance System" (3 min)
- [ ] Module: "What is Induction?" (5 min read)
- [ ] Module: "Understanding the 7 Pillars" (10 min read)
- [ ] Gifting Assessment Form (15 min form)
- [ ] Module: "Your Placement" (5 min)
- Subtotal: ~40 minutes of total content

### Certificate Programme (by Phase 1.1)
- [ ] 10 courses (can reuse existing Learn content or create)
- [ ] Curriculum: foundation, disciplines, roles, Kingdom mandate, etc.
- [ ] Quizzes/assessments for each course

---

## Key Terminology Alignment

| Concept | ICS Platform | Kingdom Governance | Sceptre Community |
|---------|--------------|-------------------|------------------|
| **Entry Point** | Induction Tenant | Level 1 Connection | Outer Court |
| **Formation Stage** | Level 0 (12 weeks) | Formation Layer | Reconditioning + Inner Court |
| **Community Unit** | Tenant | Church Node | Sceptre Community |
| **Steward Role** | Community Coordinator | Office/Leadership | Shepherd/Coordinator |
| **Pathway** | Learning Programme | Kingdom Pathway | Training Pathway |
| **Progression** | Level 0→1→2→3→4→5 | Connection→Formation→Alignment→Service→Leadership | Induction → Formation → Service |

---

## Metrics to Track Post-Launch

- Induction completion rate (% of Level 0 users who reach Level 1)
- Induction drop-off by week (identify friction points)
- Average time to Level 2 (should be ~1 year)
- Steward application approval rate (% approved)
- Programme enrolment rate (% of Level 1+ enrolled in Certificate)
- Programme completion rate (% who finish Certificate)
- Community Coordinator activation (% of Level 3 users managing community)

---

## One-Page Summary for Stakeholders

```
VERSION 2: FROM MVP TO KINGDOM GOVERNANCE SYSTEM

The Ichebo Platform now implements three core frameworks:
1. Kingdom Governance System — 7 pillars of apostolic leadership
2. Sceptre Community Programme — Decentralized node-based communities
3. Learning Pathways — Formation from Induction through Doctorate

Users follow this journey:
INDUCTION (Level 0, 12 weeks)
  → CERTIFICATE (Level 1, 1 year)
    → DIPLOMA (Level 2, 3 years)
      → DEGREE (Level 3, 4 years)
        → MASTERS (Level 4, 4-5 years)
          → DOCTORATE (Level 5, 7 years)

At each level, users unlock new capabilities:
- Level 0: Learn governance basics
- Level 1: Join community, access core learning
- Level 2: Lead small groups, expand learning
- Level 3: Coordinate community (steward role)
- Level 4: Oversee multiple communities
- Level 5: System architecture

Timeline: 8 weeks to implement Phases 1.0-1.2
Impact: Transparent, repeatable formation system aligned to theology
```

---

## When to Ask for Help

- **During Phase 1.0:** If induction content isn't clear or timelines feel off
- **Before Phase 1.1:** If you need to add/modify learning programmes
- **Before Phase 1.2:** If community coordinator dashboard scope needs adjustment

---

**Last Updated:** 24 April 2026  
**Read First:** README_REVISED_PLAN.md  
**Full Details:** VERSION_2_PLANNING_REVISED.md
