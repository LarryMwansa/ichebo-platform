# VERSION 2 PLANNING: Revision Summary
## What Changed & Why

---

## The Five Strategic Shifts

### 1. **Induction is a Distinct Formation Stage (NOT Onboarding)**

**Original Plan:**
```
Sign → Formation Contract → Auto Level 1 (immediate)
```

**Revised Plan:**
```
Sign → Profile Setup → Induction Tenant (12 weeks) → Assessment → Level 1 → Assigned Tenant
```

**Why:** The original plan bypassed the Kingdom Governance System's most critical function: preparing people to participate effectively. Induction isn't paperwork; it's the foundational stage where users learn how the system works, discover their giftings, and get properly placed. Without this, people scatter across communities unprepared.

**Impact:** Phase 1.0 now includes 12-week induction pathway as core (not optional). This is the **entry gate** to everything else.

---

### 2. **Learning Programmes Drive Competence Advancement**

**Original Plan:**
```
Formation contract → Level 1 → "Steward Application" needed for Level 2→3
(Learning is separate, optional)
```

**Revised Plan:**
```
Induction (Level 0→1) → Certificate Programme (Level 1→2) → Diploma (Level 2→3+)
Signal handlers auto-advance when thresholds met.
```

**Why:** Learning wasn't treated as the **engine** of formation. By tying programmes to advancement, users have measurable milestones. Signal handlers (Activity listeners) auto-detect completion and promote without manual intervention (except Level 3 steward approval). This creates repeatable, scalable pathways.

**Impact:** Phase 1.1 moves from optional to **core**. Learning is now structural, not supplementary. Five programmes (Certificate → Doctorate) are now the **backbone** of user progression.

---

### 3. **Multi-Tenancy from Day One, with Induction Tenant as System Entry**

**Original Plan:**
```
Users start at Level 0 (nowhere)
Multi-tenant content filtering added later (Phase 2)
```

**Revised Plan:**
```
Users start in Induction Tenant (special system-wide tenant)
After induction: auto-move to permanent tenant (geographic or functional)
Multi-tenant filtering from Phase 1.1 onwards
Content visibility rules:
  - Level 0: Induction modules only
  - Level 1+: Your assigned tenant(s) + collaborating networks
  - Level 4+: Handbook visible across all tenants
```

**Why:** Tenants aren't just scope containers; they're **communities**. Induction Tenant is where everyone starts. Permanent tenants are where they belong (local church, learning network, etc.). This follows the Sceptre Community model exactly: nodes form collectives, which scale through tiers.

**Impact:** Tenants are now **governance architecture**, not just a database feature. Phase 1.1 includes tenant scoping rules.

---

### 4. **Steward Role Becomes "Community Coordinator"**

**Original Plan:**
```
Level 2 users apply for Steward Role
Stewards are manually reviewed (Level 3+ only)
No clear connection to actual community responsibility
```

**Revised Plan:**
```
Level 2 users apply for Steward Role (same as before)
Stewards approved → become Level 3 + **Community Coordinator**
Coordinator sees dashboard for their Sceptre Community:
  - Member roster + roles (Shepherd, Net Caster, Net Mender)
  - Formation progress of community members
  - Recent activities, gatherings, linked records
Community Coordinator is tied to a specific Tenant
```

**Why:** The original plan treated stewards as abstract governance figures. But the Sceptre Community Programme shows stewards must be **coordinators of actual communities**. Giving them a community dashboard with member formation tracking ties governance to real pastoral work.

**Impact:** Phase 1.2 adds Community Coordinator dashboard. Stewards now have concrete responsibility to see their community's formation.

---

### 5. **App Drawer Gating Becomes Clear Progression Path**

**Original Plan:**
```
Apps are gated by level (abstract)
Users don't know how to unlock
```

**Revised Plan:**
```
Apps show:
  ✓ Available (you have access)
  🔒 Locked (you need Level X)

Locked app shows modal:
  "Governance requires Level 2.
   You're Level 1.
   Complete Certificate Programme (10 courses, 8 weeks) to advance."

This becomes visible **at every level**, creating a clear progression ladder.
```

**Why:** Users need to see the **path forward**, not just the gate. By showing what's required to unlock each app, we give users agency to pursue their own advancement.

**Impact:** Phase 1.2 adds this UI, making the formation journey transparent.

---

## The Three Phases Mapped to Governance

```
KINGDOM MANDATE (Level 1)
  ↓
APOSTOLIC GOVERNANCE / THE AGENCY (Level 2)
  ↓
[PHASE 1.0] Pillar 3: Formation & Discipleship
  - Induction entry (L0→L1)
  - Steward application (L2→L3)
  - Formation UI + progression dashboard
  ↓
[PHASE 1.1] Pillar 3 + 4: Formation & Programmes
  - 5 qualification programmes (Certificate→Doctorate)
  - Multi-tenant content visibility
  - Auto-advancement via signal handlers
  ↓
[PHASE 1.2] Pillar 6: Communities & Networks
  - Community Coordinator dashboard
  - App drawer gating (visible progression path)
  ↓
NETWORK OF COMMUNITIES (Sceptre Communities as Church Nodes)
  ↓
DISCIPLES (users operating within communities)
```

This now aligns with the **Kingdom Governance System's actual pillars**, not abstract features.

---

## What Stays the Same

✓ MVP is frozen (mvp branch)  
✓ version-2 branch is active  
✓ Tenant model with hierarchy (already exists)  
✓ User levels 0-5 (already exists)  
✓ Activity logging (can extend)  
✓ Learn app with authorship + review (Phase F complete)  
✓ Record types: programme, course, lesson, quiz, assignment  

---

## What's New

| Item | Phase | Notes |
|------|-------|-------|
| Induction Tenant (system-wide) | 1.0 | All new users start here |
| InductionRecord model | 1.0 | Tracks 12-week formation |
| CompetenceAdvancement model | 1.0 | Records each level transition |
| StewardApplication model | 1.0 | L2→L3 approval workflow |
| Enrolment model | 1.1 | Tracks programme enrolment |
| Multi-tenant content filtering | 1.1 | What users see by tenant + level |
| Signal handlers for advancement | 1.1 | Auto-promote on threshold met |
| AppAccess model | 1.2 | What apps require what level |
| Community Coordinator dashboard | 1.2 | Stewards see their community's progress |

---

## Data Flow Changes

**OLD:**
```
User signup → Level 1 → Dashboard
           (no formation)
```

**NEW:**
```
User signup
  ↓
Profile setup + Induction Tenant enrol
  ↓
12-week induction pathway
  - Week 1-4: Orientation (video + modules)
  - Week 5-8: Foundations + gifting assessment
  - Week 9-12: Placement assessment
  ↓
Gifting assessment output → Placement recommendation
  ↓
Induction complete → Level 0→1 auto-advance
  ↓
Move to assigned Tenant (geographic or functional)
  ↓
Enrol in Certificate programme
  ↓
Complete courses → Activity logged
  ↓
Signal handler: "Certificate 100% complete" → Auto Level 1→2
  ↓
Enrol in Diploma programme
  ↓
Apply for Steward role (if Level 2)
  ↓
Steward approval (manual) → Level 2→3 + Community Coordinator
  ↓
Continue progression...
```

---

## Why This Matters

The original VERSION_2_PLANNING.md treated each feature as independent:
- G1 = Formation Contract (checkbox)
- G2 = UI showing progress (cosmetic)
- G3 = Steward approval (governance theater)

**The revised plan treats them as integrated.**

Induction isn't optional signup flow; it's where the **Kingdom Governance System** comes alive. Learning programmes aren't content; they're the **metric of advancement**. Tenants aren't technical scoping; they're **communities of practice**. Stewards aren't titles; they're **community coordinators** with pastoral responsibility.

This aligns the digital infrastructure (**Ichebo Platform**) with the theology (**Sceptre Community Programme**) and the governance framework (**Kingdom Governance System**).

---

## The Core Question This Revision Answers

**Original:** "How do we add features to the MVP?"  
**Revised:** "How do we implement the Kingdom Governance System digitally, with the Sceptre Community Programme as the operational model and learning pathways as the advancement engine?"

The answer shapes everything.

---

## Next Steps

1. **Lock in the 8 questions** (see VERSION_2_PLANNING_REVISED.md)
2. **Prepare Induction Content** (parallel with dev)
3. **Start Phase 1.0** (induction entry + competence UI + steward application)
4. **Test with power users** (end of week 3)
5. **Adjust based on feedback** (if needed)
6. **Start Phase 1.1** (programmes + multi-tenant + advancement)

---

**Revised By:** Claude Code  
**Date:** 24 April 2026  
**Based On:** Kingdom Governance System v1, Sceptre Community Programme v2, Onboarding Stage concept, Prompt for Learning App
