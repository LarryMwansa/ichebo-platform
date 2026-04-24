# VERSION 2 PLANNING: Original vs. Revised — Side-by-Side Comparison

---

## Phase 1 Comparison

| Dimension | **ORIGINAL** | **REVISED** |
|-----------|-------------|-----------|
| **Entry Point** | Sign → Formation Contract → Level 1 | Sign → Profile → Induction Tenant → 12 weeks → Level 1 |
| **Level 0 Purpose** | Undefined (skipped) | **Induction Stage** — oriented, assessed, placed |
| **Time to Level 1** | Immediate (form submission) | 12 weeks (structured formation + assessment) |
| **Who Advances User to L1** | Automatic (no review) | Induction Coordinator confirmation |
| **Placement** | No community assignment | Steward assigns to permanent tenant |
| **Gifting Discovery** | Not done | Formal assessment (week 5-8) |
| **G2: Competence UI** | "Your Formation Journey" card | Same, but now shows induction progress bar |
| **G3: Steward Application** | L2→L3 approval (abstract) | L2→L3 + **becomes Community Coordinator** with dashboard |
| **Phase 1 Duration** | 2-3 weeks | 3 weeks (same effort, more substance) |

---

## Phase 2 Comparison

| Dimension | **ORIGINAL** | **REVISED** |
|-----------|-------------|-----------|
| **H1: Tenant Management** | Create tenants, invite members | **Moved to H2** |
| **Learning Programmes** | Deferred to v2.3 or later | **Core of Phase 1.1** — 5 programmes (Certificate → Doctorate) |
| **Enrolment System** | Not in original plan | New: Users enrol in programmes, track progress |
| **Level Advancement** | Manual (steward must approve each) | **Signal handlers auto-advance** when threshold met |
| **H2: Multi-Tenant Visibility** | Filter content by tenant | Same, plus: **Induction Tenant special rules** (orientation only) |
| **Tenant Scoping** | Basic (show only your tenant's content) | **Sophisticated:** Level 4+ see Handbook across all; Level 1-3 see assigned + collaborating tenants only |
| **H3: New Feature** | Auto-advancement (manual approval) | **Signal handlers + Celery** for automatic detection |
| **Learning as Engine** | Optional, separate | **Primary driver of competence advancement** |
| **Phase 2 Duration** | 2-3 weeks | 3 weeks (higher complexity) |

---

## Phase 3 Comparison

| Dimension | **ORIGINAL** | **REVISED** |
|-----------|-------------|-----------|
| **I1: App Drawer Gating** | "Locked" state shows tooltip | Same, plus: **Modal shows unlock path** ("Enrol in Certificate to access Governance") |
| **I2: Advancement Automation** | Background job, no UI | Same, plus: **Dashboard "Level Up" banner** notifies user |
| **New Feature: Community Coordinator** | Not in original | **Community dashboard** — see member formation, recent activities, gatherings |
| **Phase 3 Duration** | 1-2 weeks | 2 weeks (similar effort) |

---

## What Got Added

| Feature | Phase | Why |
|---------|-------|-----|
| **Induction Tenant (system-wide)** | 1.0 | Central entry point; all users start here |
| **InductionRecord model** | 1.0 | Track 12-week formation progress |
| **Gifting Assessment** | 1.0 | Part of induction; guides placement |
| **Community Coordinator Role** | 1.0 | Stewards now manage actual community |
| **5 Qualification Programmes** | 1.1 | Certificate, Diploma, Degree, Masters, Doctorate |
| **Enrolment System** | 1.1 | Track which programmes users are in |
| **Pathway Filtering** | 1.1 | "You are on Service Pathway" — learn catalogue filtered |
| **Signal Handlers** | 1.1 | Auto-detect programme completion → auto-advance |
| **Induction Tenant Special Scoping** | 1.1 | Level 0 sees orientation only; after induction, moves to permanent tenant |
| **Community Coordinator Dashboard** | 1.2 | Stewards see member roster, formation progress, activities |
| **App Drawer Lock Modals** | 1.2 | Shows unlock path, not just the lock |

---

## What Stayed the Same

| Feature | Status | Notes |
|---------|--------|-------|
| G1: Formation Contract Concept | ✓ Same | Now part of induction orientation, not standalone |
| G2: Competence UI | ✓ Same | Enhanced with induction progress tracking |
| G3: Steward Application | ✓ Same | Enhanced: now results in Community Coordinator role |
| H1: Tenant Hierarchy | ✓ Same | Already built; now explicitly called "Sceptre Community" |
| H2: Multi-Tenant Content Filtering | ✓ Same | Enhanced: special rules for Induction Tenant |
| I1: App Drawer Gating | ✓ Same | Enhanced: lock modals show unlock paths |
| I2: Auto-Advancement | ✓ Same | Enhanced: signal handlers + Celery |

---

## Architectural Alignment

### **ORIGINAL Plan**
```
MVP features → add onboarding (G1-G3) → add learning (H1-H2) → add gating (I1-I2)
(incremental; features feel disconnected)
```

### **REVISED Plan**
```
Kingdom Governance System (theology)
        ↓
Sceptre Community Programme (operational model)
        ↓
Ichebo Platform (digital infrastructure)
        ↓
Phases 1.0-1.2 (implement the above)
(cohesive; every feature serves a larger purpose)
```

---

## Timeline Impact

| Phase | **Original** | **Revised** | **Change** |
|-------|-------------|-----------|-----------|
| 1.0 | 2-3 weeks | 3 weeks | +1 week (induction is more substantial) |
| 1.1 | 2-3 weeks | 3 weeks | Same (learning programmes offset by multi-tenant clarity) |
| 1.2 | 1-2 weeks | 2 weeks | Same (community coordinator is well-scoped) |
| **Total v2.0-2.2** | **5-8 weeks** | **8 weeks** | **Stable; same effort, higher value** |

---

## Success Metrics Changes

### **ORIGINAL**
- ✓ All users can self-serve onboard
- ✓ Formation journey clear
- ✓ Stewards can evaluate applicants

### **REVISED** (same goal, more substance)
- ✓ All users enter through structured Induction
- ✓ Induction assessment guides permanent placement
- ✓ Learning programmes are measurable milestones
- ✓ Stewards see community formation progress
- ✓ Level advancement is transparent (app drawer shows unlock paths)
- ✓ Multi-tenant content filtering works correctly

---

## Key Decisions Locked In (Revised Plan)

| Question | **Original** Answer | **Revised** Answer |
|----------|------------------|------------------|
| What is Level 0? | Undefined | Induction stage (12 weeks) |
| How long to Level 1? | Instant | 12 weeks + assessment |
| How do users advance? | Steward approval | Signal handlers (auto) + steward approval (L3 only) |
| What drives advancement? | Vague (activities?) | **Learning programmes** (concrete, measurable) |
| How many programmes? | Not specified | **5** (Certificate → Doctorate, linked to levels 1-5) |
| Who assigns tenants? | Not specified | Induction Coordinator (based on assessment) |
| What do stewards do? | Review applications | Review L2→L3 applications + **manage community** |
| When is learning ready? | v2.3 (deferred) | **v2.1 (core)** |

---

## The One Question This Answers

**"Is the ICS platform implementing the Kingdom Governance System + Sceptre Community model digitally, or just adding features to MVP?"**

- **Original:** Just adding features
- **Revised:** Implementing the entire system coherently

---

## Recommendation

**Adopt the REVISED plan.** It's not more work (8 weeks either way), but it:

1. **Aligns digital architecture with theology** — every feature serves the Kingdom Governance System
2. **Makes progression transparent** — users see exactly what's required to advance
3. **Grounds stewards in pastoral reality** — Community Coordinator role ties governance to real community management
4. **Treats learning as foundational** — not optional, but the engine of advancement
5. **Implements Sceptre Community model** — tenants become governance architecture, not just database features

The ORIGINAL plan would work. The REVISED plan works *and* builds the right thing.

