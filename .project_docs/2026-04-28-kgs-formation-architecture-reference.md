# KGS Formation Architecture — Platform Reference

**Date:** 2026-04-28
**Status:** Canonical — governs all seed data, labels, and structural decisions
**Author:** Chizola (domain); Claude (technical mapping)
**Sources:** `Pathways Competence Levels Qualification Programmes, and Roles.md`;
`Oveview_Main Learning Programmes.md`; `kingdom-governance-system_v1.md`

> This document captures the full structure of the Kingdom Governance System (KGS)
> as it maps to the Ichebo platform. It is the source of truth for formation
> architecture decisions. Planning documents and ADRs draw from this — not the
> other way around.

---

## Why This Document Exists

The KGS defines a complete formation architecture: Pathways, Competence Levels,
Qualification Programmes, Service Orders, Administrative Offices, and Service
Domains. During Version 2 planning, these were worked out incrementally across
several sessions. This document consolidates the full picture in one place so
that:

- No layer of the KGS is misrepresented or missed in the platform
- Seed data is built to the correct structure from the start
- Future builders can understand the KGS intent without re-deriving it

---

## Full KGS Formation Layer Map

| KGS Layer                 | KGS Term                                                       | Count | Platform Concept                                     |
| ------------------------- | -------------------------------------------------------------- | ----- | ---------------------------------------------------- |
| Pathways                  | Eight Kingdom Pathways                                         | 8     | `kgs_pathways` tag array on programme Records        |
| Competence Levels         | Levels 0–5                                                     | 6     | `competence_level` on User                           |
| Qualification Programmes  | Certificate (×2) → Diploma → Degree → Masters → Doctorate      | 6     | Records (`learning/programme`)                       |
| Service Domains           | 6 Domains                                                      | 6     | Grouping label for Administrative Offices            |
| Administrative Offices    | 12 Offices                                                     | 12    | Agency-level tenants under `/global/agency/` (V2.5+) |
| Orders of Kingdom Service | 24 Orders                                                      | 24    | `service_order` on `UserPermission.metadata`         |

---

## Layer 1 — Eight Kingdom Pathways

Pathways describe the dimension of formation a programme develops. They are
not linear stages — a member may be on several pathways simultaneously depending
on which programmes they are enrolled in.

| Pathway                  | Programmes it appears in                             |
| ------------------------ | ---------------------------------------------------- |
| New Life                 | New Life Programme                                   |
| Community Life           | New Life Programme                                   |
| Learning & Qualification | New Life, Foundation, Leaders, Builders, Architect's |
| Spiritual Formation      | Foundation Programme                                 |
| Service                  | Foundation Programme, Leaders Programme              |
| Mission                  | Foundation Programme                                 |
| Leadership               | Leaders Programme, Builders Programme, Architect's Programme |
| Apostolic Stewardship    | Builders Programme, Architect's Programme            |

**Platform implementation:** Each programme Record carries
`custom_fields.kgs_pathways` (array). No separate Pathway model is required.

---

## Layer 2 — Six Competence Levels

Competence levels mark a member's stage of formation in the Kingdom. They
advance only through steward-confirmed programme completion — never automatically.

| Level | KGS Status           | Entry Point                        |
| ----- | -------------------- | ---------------------------------- |
| 0     | Entrant / Seeker     | Registration → Induction Tenant    |
| 1     | Member               | Induction Training completed + steward confirmed |
| 2     | Disciple / Worker    | New Life Programme completed       |
| 3     | Team Leader          | Foundation Programme completed     |
| 4     | System Manager       | Leaders Programme completed        |
| 5     | System Architect     | Builders Programme completed       |

**Platform implementation:** `User.competence_level` (integer 0–5). Single write
path: `POST /api/learn/certifications/{id}/confirm/`. No other write path exists
or will be created.

---

## Layer 3 — Six Qualification Programmes

Six programmes map to the six competence levels. Level 0 is served by
Induction Training — a `course` record nested inside the New Life Programme,
not a standalone programme.

| Level | Programme Name        | KGS Qualification   | Duration    | Prerequisites         |
| ----- | --------------------- | ------------------- | ----------- | --------------------- |
| 0     | *(Induction Training course)* | Certificate (Entrant) | 12 weeks | None              |
| 1     | New Life Programme    | Certificate         | 1 year      | Induction Training    |
| 2     | Foundation Programme  | Diploma             | 3 years     | New Life Programme    |
| 3     | Leaders Programme     | Degree              | 6–12 months | Foundation Programme  |
| 4     | Builders Programme    | Masters             | 6–12 months | Leaders Programme     |
| 5     | Architect's Programme | Doctorate           | 2 years     | Builders Programme    |

### Programme Pathway Assignments

Each programme carries multiple pathways. These are stored as an array, not a
single value, because formation is multi-dimensional at every level.

| Programme             | `kgs_pathways`                                                   |
| --------------------- | ---------------------------------------------------------------- |
| New Life Programme    | `["new_life", "community_life", "learning"]`                     |
| Foundation Programme  | `["spiritual_formation", "service", "mission", "learning"]`      |
| Leaders Programme     | `["leadership", "service", "learning"]`                          |
| Builders Programme    | `["leadership", "apostolic_stewardship"]`                        |
| Architect's Programme | `["leadership", "apostolic_stewardship"]`                        |

### Induction Training — Course Structure

Induction Training is seeded as `record_type: "course"` linked to New Life
Programme via a `part_of` Relationship. It is not a standalone programme.

All four lessons are required for all entrant types. `induction_pathway`
on the User model records the entrant's background for context only — it does
not gate individual lessons.

| Lesson                                                | Covers                        |
| ----------------------------------------------------- | ----------------------------- |
| Keys To the Kingdom                                   | Beginners pathway foundation  |
| Repentance & Reformation                              | Reconditioning pathway        |
| Community Programme                                   | Sceptre Community life        |
| The Secret of Living a Fulfilled Life (HAL Beginners) | Practical formation           |

**Platform implementation:** 5 seeded programme Records (Levels 1–5) via
`seed_programmes`. 1 seeded course Record + 4 lesson Records via
`seed_induction_course`. All carry `origin: "system"`, `status: "active"`.

---

## Layer 4 — 24 Orders of Kingdom Service

The 24 Orders define how members serve within the Kingdom structure. They are
the controlled vocabulary for `UserPermission.metadata.service_order`. No model
change is needed — the field already accepts a string. In V2.3+, this becomes a
dropdown; until then, stewards enter it as free text from the list below.

| Service Domain                  | Administrative Office                   | Orders of Kingdom Service                     |
| ------------------------------- | --------------------------------------- | --------------------------------------------- |
| Apostolic & Spiritual Ministry  | Office of Apostolic Stewardship         | 1. Order of Apostolic Service                 |
|                                 | Office of Prophetic Discernment         | 2. Order of Prophetic Ministry                |
|                                 |                                         | 3. Order of Teaching and Doctrine             |
|                                 |                                         | 4. Order of Prayer and Intercession           |
| Leadership & Governance Support | Office of Governance and Policy         | 5. Order of Governance Support                |
|                                 | Office of Strategic Development         | 6. Order of Strategic Coordination            |
|                                 |                                         | 7. Order of Leadership Assistance             |
|                                 |                                         | 8. Order of Communication and Alignment       |
| Formation & Teaching            | Office of Discipleship Formation        | 9. Order of Discipleship Facilitation         |
|                                 | Office of Leadership Development        | 10. Order of Training and Instruction         |
|                                 |                                         | 11. Order of Mentorship and Coaching          |
|                                 |                                         | 12. Order of Curriculum Development           |
| Mission & Outreach              | Office of Learning and Qualifications   | 13. Order of Evangelism                       |
|                                 | Office of Ministry Programmes           | 14. Order of Mission Teams                    |
|                                 |                                         | 15. Order of Community Outreach               |
|                                 |                                         | 16. Order of Expansion and Planting           |
| Community Life & Care           | Office of Mission Mobilisation          | 17. Order of Pastoral Care                    |
|                                 | Office of Community Networks            | 18. Order of Community Building               |
|                                 |                                         | 19. Order of Hospitality and Welcome          |
|                                 |                                         | 20. Order of Welfare and Support              |
| Operations & Stewardship        | Office of Operations and Administration | 21. Order of Administration                   |
|                                 | Office of Resource Stewardship          | 22. Order of Resource Management              |
|                                 |                                         | 23. Order of Logistics and Events             |
|                                 |                                         | 24. Order of Media and Communication          |

**Platform note:** The 24 Order names above are the complete controlled
vocabulary. No additional values should be added without a KGS governance
decision.

---

## Layer 5 — 12 Administrative Offices and 6 Service Domains

The 12 Administrative Offices are large institutional structures that govern
the Kingdom's service work. They are grouped under 6 Service Domains.

| Service Domain                  | Administrative Offices                                            |
| ------------------------------- | ----------------------------------------------------------------- |
| Apostolic & Spiritual Ministry  | Office of Apostolic Stewardship; Office of Prophetic Discernment  |
| Leadership & Governance Support | Office of Governance and Policy; Office of Strategic Development  |
| Formation & Teaching            | Office of Discipleship Formation; Office of Leadership Development |
| Mission & Outreach              | Office of Learning and Qualifications; Office of Ministry Programmes |
| Community Life & Care           | Office of Mission Mobilisation; Office of Community Networks      |
| Operations & Stewardship        | Office of Operations and Administration; Office of Resource Stewardship |

### Platform Implementation (Deferred to V2.5+)

Each of the 12 Offices maps to an Agency-level tenant in the platform hierarchy:

```text
/global/agency/office-apostolic-stewardship/
/global/agency/office-prophetic-discernment/
/global/agency/office-governance-policy/
/global/agency/office-strategic-development/
/global/agency/office-discipleship-formation/
/global/agency/office-leadership-development/
/global/agency/office-learning-qualifications/
/global/agency/office-ministry-programmes/
/global/agency/office-mission-mobilisation/
/global/agency/office-community-networks/
/global/agency/office-operations-administration/
/global/agency/office-resource-stewardship/
```

Each Office-tenant carries its own stewards, Records, programmes, and community.
This requires zero model changes — the existing tenant hierarchy and materialized
path system supports it fully.

**Why deferred:** The platform must first establish the formation stack (Levels
0–5, induction, qualification programmes) before the service and governance
structures that operate at Level 3+ can be meaningfully populated. Offices are
built when there are enough Level 3+ stewards to staff them.

---

## What the Platform Must Get Right from the Start

The following are not deferred. They must be correct in seed data and labels
from the first Version 2 build:

1. **Six programmes seeded, not five.** Level 0 entry via Induction Training
   course is the sixth. `seed_programmes` seeds Levels 1–5 as named programme
   Records. `seed_induction_course` seeds the Induction Training course + 4
   lessons inside New Life Programme.

2. **KGS programme names used everywhere.** Not academic placeholders.
   "New Life Programme", "Foundation Programme", "Leaders Programme",
   "Builders Programme", "Architect's Programme" — in UI display, seed data,
   and all documentation.

3. **Pathway arrays, not single values.** `custom_fields.kgs_pathways` is an
   array on every programme Record. Formation is multi-dimensional.

4. **24 Service Orders are the only valid values** for
   `UserPermission.metadata.service_order`. Stewards must select from this
   list. Document it clearly in the steward UI when the field is built (V2.3+).

5. **Competence level 0 is a real level.** It is not a null state. A Level 0
   user is an Entrant actively in formation in the Induction Tenant. The
   platform treats it as a full formation stage.

---

## Relationship to Other Documents

| Document | Relationship |
| -------- | ------------ |
| `2026-04-25-ichebo-adr-version-2.md` | ADR-011 formally amends programme names and induction structure — this document is the source it draws from |
| `master-roadmap-canonical-2026-04-27.md` | V2.1 section references this structure for seed command design |
| `VERSION_2_PLANNING.md` | Formation Architecture section summarises this; build assignments reference the seed commands defined here |
| `data-contract-v10-canonical-2026-04-27.md` | v10 amendment must reflect the 6 programmes, induction fields, and `"induction"` tier from this document |
