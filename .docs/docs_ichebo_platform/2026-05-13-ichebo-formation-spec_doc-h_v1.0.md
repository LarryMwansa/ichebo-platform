**ICHEBO FORMATION**

**Product Specification**

_DOC H - Version 1.0 - May 2026_

| **Field**      | **Value**                                                             |
| -------------- | --------------------------------------------------------------------- |
| Document       | DOC H - Ichebo Formation Product Specification                        |
| Version        | 1.0 - May 2026                                                        |
| Status         | Approved - Canonical Reference                                        |
| KGS references | Part V (Formation Layer), Part VI (Leadership Layer), Sections 22-25  |
| Data contract  | data-contract-v11-canonical-2026-05-13.md Parts 2, 4, 12              |
| Depends on     | DOC A (Product Vision), DOC E (Engine Specs)                          |
| ADR references | ADR-006 (competence_level write constraint), ADR-011 (KGS programmes) |
| Authors        | Chizola (domain); Claude (technical)                                  |

**_People developed before deployed. Leadership formed before appointed. Service aligned with competence. Growth structured, measurable, and scalable._**

**-- FOUNDATION**

**What Formation Is**

The disciplined development of persons into mature disciples, equipped servants, and capable leaders - before they are deployed.

## **1.1 Formation in the KGS**

The KGS places formation at the centre of the governance system. The Formation Layer is not a training department - it is the mechanism by which the entire system reproduces itself with integrity. The KGS principle is explicit:

**The KGS Formation principle**

People are developed before deployed. Leadership is formed before appointed. Service is aligned with competence. Growth is structured, measurable, and scalable. Formation is not optional for participation - it is the pathway through which participation becomes possible.

## **1.2 What Ichebo Formation Is**

Ichebo Formation is the standalone product that implements the KGS Formation Layer digitally. It is distinct from the Learn App (which delivers content) in the same way that a pastoral office is distinct from a classroom - Formation tracks the person's journey, accountability relationships, and governance status. Learn delivers the material that informs that journey.

| **Ichebo Formation (this product)**                           | **Ichebo Learn / Academy (separate product)**               |
| ------------------------------------------------------------- | ----------------------------------------------------------- |
| Tracks the person's competence level and formation journey    | Delivers course content, lessons, and assessments           |
| Manages shepherd-to-disciple accountability relationships     | Manages programme enrolment and progress                    |
| Records advancement evidence and confirmation                 | Records lesson completion and certification                 |
| Manages the 24 Service Order assignments                      | Hosts the curriculum authored by Level 4+ architects        |
| Governs the advancement workflow - request, review, confirm   | Triggers the certification signal that Formation confirms   |
| The pastoral record - who is being formed, by whom, into what | The academic record - what was studied, completed, assessed |

## **1.3 Product Attributes**

| **Attribute**   | **Value**                                                                                             |
| --------------- | ----------------------------------------------------------------------------------------------------- |
| Product type    | Standalone - own service, integrated with Learn App and Activity Engine                               |
| Primary users   | Community stewards (Level 3+) managing formation pipelines; Level 5 architects confirming advancement |
| Secondary users | Individual members viewing their own formation journey                                                |
| Status          | Version 3+ - planned. Layer adjacent to Layer 7 in the roadmap.                                       |
| Depends on      | Sync Engine (DOC C), Activity Engine (DOC E), Learn App certification flow                            |

**-- COMPETENCE LEVELS**

**The KGS Roles and Competence Framework**

Six levels. Five qualification programmes. One write path. No exceptions.

## **2.1 The Six Competence Levels**

Competence levels in the KGS represent spiritual formation progress, governance authority, and service capacity simultaneously. They are not seniority grades or membership tiers. They are verified statements of formation and readiness.

| **L0a**<br><br>- | **Guest**<br><br>Unauthenticated \| -<br><br>Accesses public records and the tenant directory. No account required. No formation tracking. |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |

| **L0b**<br><br>- | **Seeker**<br><br>Registered - formation not yet begun \| -<br><br>Bible reader, personal records (limited to 10), induction programmes. No community membership. Formation journey not yet started. |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| **L1**<br><br>1 year | **Foundational Disciple**<br><br>Member / Disciple \| Certificate of Kingdom Studies<br><br>Full personal records. Community membership. Active in formation pathways. Initial service role within a Service Order. |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| **L2**<br><br>3 years | **Active Contributor**<br><br>Servant / Minister-in-Training \| Diploma in Kingdom Service<br><br>Organisational records. Small group leadership. Growing service competence. Active in ministry within a Service Domain. |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| **L3**<br><br>4 years | **Functional Minister**<br><br>Community Coordinator / Steward \| Degree in Kingdom Ministry<br><br>Governs a Sceptre Community. Confirms certifications for Level 1 and 2. Manages formation pipeline. Accesses Stage Mode (Apostolic Command Shell). |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

| **L4**<br><br>4-5 years | **Leader**<br><br>Senior Steward / District Level \| Masters in Kingdom Leadership<br><br>Creates governance records. Multi-community scope. Manages formation across a district. Confirms certifications for Level 3. |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| **L5**<br><br>7 years | **Apostolic Steward**<br><br>Architect / Global Leadership \| Doctorate in Apostolic Governance<br><br>Cross-tenant governance. Handbook authorship. Network-wide formation oversight. Confirms certifications for Level 4. |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

## **2.2 The competence_level Write Constraint - Absolute**

**Absolute constraint - ADR-006**

competence_level is the most protected field in the entire platform. It may only be written by one code path: POST /api/learn/certifications/{id}/confirm/. No engine, no endpoint, no signal, no management command, no migration may write to competence_level through any other path. This is not a convention - it is an architectural invariant enforced at the service layer.

The constraint exists because competence_level is not just a number. It determines:

- What apps and features the user can access (drawer gating)
- What records the user can create and read
- What governance functions the user can perform
- Whether the user can enter Stage Mode (Level 3+ only)
- Whether the user can confirm another person's certification
- The user's authority and accountability within the network

An incorrect competence_level creates incorrect permissions throughout the entire platform. The single write path is the safeguard.

## **2.3 Level Gating - What Each Level Unlocks**

| **Feature**                  | **Min level** | **Feature**                          | **Min level** |
| ---------------------------- | ------------- | ------------------------------------ | ------------- |
| Personal records (up to 10)  | 0b            | Stage Mode (Apostolic Command Shell) | 3             |
| Bible reader                 | 0b            | Confirm certifications (Level 1-2)   | 3             |
| Induction programmes         | 0b            | Create governance records            | 4             |
| Full personal records        | 1             | Confirm certifications (Level 3)     | 4             |
| Community membership         | 1             | Handbook read - Reference Library    | 3             |
| Learn App (enrol)            | 1             | Handbook read - Mandate Branch       | 4             |
| Announcements (read)         | 1             | Handbook write (all branches)        | 5             |
| Gatherings (attend)          | 1             | Confirm certifications (Level 4)     | 5             |
| Ministry activities (create) | 2             | Cross-tenant governance              | 5             |
| Manage community             | 3             | Network-wide formation oversight     | 5             |

**-- EIGHT PATHWAYS**

**The Eight Kingdom Pathways**

Interconnected dimensions of growth. Not sequential steps - integrated formation.

## **3.1 The Pathway Architecture**

The Eight Kingdom Pathways are the primary structure for human development within the KGS. They are not sequential steps - a person does not complete one pathway before beginning another. They are integrated dimensions of growth, each activated and developed simultaneously through different aspects of community life.

Every qualification programme aligns with specific pathways. Every Service Order is aligned with a primary pathway. Formation tracking in Ichebo Formation shows the member's progress across all eight pathways, not just the programme they are currently enrolled in.

**1\. New Life Pathway**

_Salvation, identity, and foundational faith. The entry point for all formation._

Service orders: Orders 1-4 (Apostolic and Spiritual Ministry)

**2\. Spiritual Formation Pathway**

_Inner transformation and spiritual maturity through prayer, Word, and spiritual disciplines._

Service orders: Orders 1-4 (Apostolic and Spiritual Ministry)

**3\. Community Life Pathway**

_Belonging, relational integration, accountability, and values alignment within the Sceptre Community._

Service orders: Orders 17-20 (Community Life and Care)

**4\. Service Pathway**

_Activation into Kingdom function through Service Domains and the discovery of gifts and calling._

Service orders: Orders 9-16 (Formation and Teaching, Mission and Outreach)

**5\. Leadership Pathway**

_Leadership readiness, responsibility, and governance alignment. Prerequisite for Level 3 advancement._

Service orders: Orders 5-8 (Leadership and Governance Support)

**6\. Learning and Qualification Pathway**

_Formal training, certification, and knowledge and skill acquisition through the five qualification programmes._

Service orders: Orders 9-12 (Formation and Teaching)

**7\. Mission Pathway**

_Outward expression through evangelism, outreach, and cultural and territorial engagement._

Service orders: Orders 13-16 (Mission and Outreach)

**8\. Apostolic Stewardship Pathway**

_Strategic leadership formation and stewardship of structures and people. Level 4-5 formation._

Service orders: Orders 5-8 (Leadership and Governance Support)

## **3.2 Pathway Tracking in Formation**

Ichebo Formation tracks a member's progress across all eight pathways. Each pathway has a set of indicators that the formation system monitors:

| **Pathway indicator**              | **How Formation tracks it**                                                     |
| ---------------------------------- | ------------------------------------------------------------------------------- |
| Programme enrolment and completion | Learn App certification records - which programme at which level                |
| Service order assignment           | UserPermission.metadata.service_order - active assignment confirmed by steward  |
| Gathering participation            | Activity Engine - attendance records for community gatherings                   |
| Ministry activity                  | Activity Engine - campaign and project participation within Service Domain      |
| Competence level                   | User.competence_level - the single authoritative indicator of formation status  |
| Shepherd relationship              | UserPermission.metadata.shepherd_id - active pastoral accountability            |
| Key record activity                | Records Engine - key records authored (personal spiritual discipline indicator) |
| Outreach participation             | Activity Engine - mission activities tagged with kgs_pathway: "mission"         |

**-- QUALIFICATION PROGRAMMES**

**Five Programmes. One Arc.**

From Certificate to Doctorate. Progressive formation aligned with governance capacity.

## **4.1 The Five Qualification Programmes**

The five qualification programmes are the formal educational structure of the Formation Layer. Each programme corresponds to a competence level and a qualification type. Completion of a programme is necessary but not sufficient for advancement - steward confirmation of demonstrated formation is also required.

| **Programme**                     | **Level** | **Duration - Focus**                                                                                                                                                         |
| --------------------------------- | --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Certificate of Kingdom Studies    | Level 1   | 1 year. Foundational formation. Identity in Christ, governance framework introduction, community participation, initial service roles. New Life and Community Life Pathways. |
| Diploma in Kingdom Service        | Level 2   | 3 years. Developing servant-leaders with practical ministry competence. Service and Learning/Qualification Pathways. Activation within 24 Service Orders.                    |
| Degree in Kingdom Ministry        | Level 3   | 4 years. Functional ministry leadership. Prepares leaders to govern Sceptre Communities and steward formation pipelines. Leadership Pathway primary.                         |
| Masters in Kingdom Leadership     | Level 4   | 4-5 years. Strategic leadership formation and governance oversight. District-level and collective governance. Mission and Apostolic Stewardship Pathways.                    |
| Doctorate in Apostolic Governance | Level 5   | 7 years. Apostolic stewardship and system-level oversight. Governance architecture, generational stewardship, KGS framework development. Full Apostolic Stewardship Pathway. |

## **4.2 The Induction - Before Any Programme**

Before any qualification programme begins, every new community member completes the Induction. The Induction is a structured entry process - not an orientation exercise.

| **Attribute**          | **Value**                                                                                                                                                   |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Duration               | 12 weeks structured - completion determined by programme completion, not time served                                                                        |
| Entry point            | All new members (status: seeker) auto-enrolled on registration                                                                                              |
| Two pathways           | Reconditioning Programme - existing believers re-engaging with structured formation. Beginners Programme - new to Kingdom life.                             |
| Four lessons           | Keys to the Kingdom \| Repentance and Reformation \| Community Programme \| The Secret of Living a Fulfilled Life (HAL Beginners)                           |
| Gifting assessment     | Weeks 5-8: spiritual gifts, natural abilities, vocational skills mapped to Kingdom Pathway and Service Order                                                |
| Outcome                | Placement in a permanent Sceptre Community. Recommendation for Certificate enrolment. induction_completed_at set on User model.                             |
| Placement confirmation | Steward confirms placement via POST /api/learn/certifications/{id}/confirm/ with placement_tenant_id set. This is a special case of the certification flow. |

## **4.3 The Four Induction Lessons**

| **Lesson**                                            | **Content focus**                                                                                                         |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Keys to the Kingdom                                   | Foundational introduction to the KGS framework. What the Kingdom is. What governance means. The mandate of the community. |
| Repentance and Reformation                            | The spiritual and personal foundation. Inner alignment with Kingdom values. The Reconditioning pathway foundation.        |
| Community Programme                                   | Introduction to the Sceptre Community Programme. Community life, accountability, gathering practice, participation.       |
| The Secret of Living a Fulfilled Life - HAL Beginners | Practical formation for daily Kingdom living. The Beginners pathway foundation.                                           |

**Pathway distinction**

The induction_pathway field on the User model (reconditioning | beginners) records background context only. It does not gate individual lessons - all four lessons are required for all entry types. The pathway distinction informs the steward's pastoral approach and the community placement, not the content consumed.

**-- ADVANCEMENT**

**The Advancement Workflow**

Request. Evidence. Review. Confirm. The only authorised path to a higher level.

## **5.1 Why Advancement Requires Human Confirmation**

Competence level advancement in the KGS is not automatic. It is not triggered solely by programme completion. It requires a human being - a steward with appropriate authority - to confirm that the person has demonstrated genuine formation, not just academic completion.

**_Advancement requires steward confirmation at each level - ensuring progression is tied to genuine formation, not just time served._**

This is not bureaucracy. It is accountability. The competence level is a statement about a person's formation, character, and readiness for the responsibilities that come with that level. That statement requires a witness - someone who knows the person pastorally, not just academically.

## **5.2 The Advancement Workflow**

The advancement workflow is a three-party process: the learner, the shepherd, and the confirming steward.

- Learner completes all required lessons in their current qualification programme
- Programme Activity reaches progress: 100 - the certification signal fires automatically
- A draft Certification Record is created (record_type: "certification", status: "draft")
- Learner sees "Awaiting certification" banner on their My Learning page
- Learner's shepherd is notified - they review the learner's pastoral formation, participation record, and service engagement
- Shepherd recommends advancement to the confirming steward (or raises concerns)
- Confirming steward reviews the Certification Record - programme completion, pastoral endorsement, activity record
- Steward confirms via POST /api/learn/certifications/{id}/confirm/ - the sole authorised write path
- competence_level increments by 1. CertificationConfirmation audit record created.
- Learner notified via email and in-app notification: "Congratulations - you have advanced to Level {n}"
- New level unlocks additional features and platform access immediately

## **5.3 Who Can Confirm at Each Level**

| **Advancing to level** | **Confirming steward minimum level**                                |
| ---------------------- | ------------------------------------------------------------------- |
| Level 1 (Certificate)  | Level 3 - the community steward who manages the learner's community |
| Level 2 (Diploma)      | Level 3 - same community steward or district steward                |
| Level 3 (Degree)       | Level 4 - district or provincial steward with broader authority     |
| Level 4 (Masters)      | Level 5 - apostolic steward with network-wide authority             |
| Induction placement    | Level 3 - the induction coordinator or receiving community steward  |

This confirmation hierarchy reflects the KGS authority structure. The more significant the advancement, the higher the authority required to confirm it. A Level 5 advancement requires Level 5 confirmation - apostolic authority witnessing apostolic readiness.

## **5.4 Evidence Required for Advancement**

The confirming steward reviews three categories of evidence before confirming:

**Academic evidence - Learn App**

- All programme lessons completed (progress: 100 on enrolment Activity)
- All required assessments submitted and reviewed
- No outstanding incomplete modules

**Participation evidence - Activity Engine**

- Regular gathering attendance over the programme period
- Active ministry participation within their Service Order
- Evidence of practical application of formation content

**Pastoral evidence - Formation product**

- Shepherd assessment - shepherd's written endorsement or concern
- Character and conduct - no outstanding pastoral concerns raised
- Service order alignment - person is active in a service role appropriate to their current level
- Competence demonstration - can the person articulate and apply what they have learned?

**The Formation product's role**

Ichebo Formation aggregates all three evidence categories and presents them to the confirming steward in a single review panel. The steward should not need to navigate between multiple apps - Formation brings the complete picture together. Academic record from Learn. Participation record from Activity Engine. Pastoral record from Formation itself.

**-- SHEPHERD SYSTEM**

**Pastoral Accountability Relationships**

Who pastors whom. The relational structure that makes formation real.

## **6.1 The Shepherd Relationship**

Every member of a Sceptre Community should have an identified shepherd - someone with a higher competence level who is responsible for their pastoral care, formation accountability, and ministry development. The shepherd system is the human layer that the Formation product makes visible and manageable.

In the current production system, the shepherd relationship is stored as:

UserPermission.metadata.shepherd_id = uuid // FK → User (the shepherd)

// The current implementation is minimal - a single ID in a JSONField.

// Ichebo Formation upgrades this to a proper pastoral relationship model.

## **6.2 The PastoralRelationship Model**

Ichebo Formation introduces a proper PastoralRelationship model replacing the metadata.shepherd_id workaround:

// PastoralRelationship - the Formation product's core data model

PastoralRelationship {

id: uuid

member_id: uuid // FK → User - the person being shepherded

shepherd_id: uuid // FK → User - the shepherd (must be higher competence_level)

tenant_id: uuid // the community this relationship is active in

assigned_at: ISO-8601

assigned_by: uuid // FK → User - the steward who made the assignment

status: "active" | "transferred" | "completed"

transferred_at: ISO-8601 | null

notes: text | null // pastoral notes - privacy-sensitive, Level 3+ only

created_at: ISO-8601

deleted_at: ISO-8601 | null

}

// Constraints:

// shepherd.competence_level > member.competence_level (shepherd must be higher)

// One active relationship per member per tenant

// Historical relationships retained (status: "transferred" or "completed")

// notes field: only visible to Level 3+ stewards - never to the member themselves

## **6.3 The Formation Pipeline View**

The Formation Pipeline is the steward's primary management surface. It shows every member of the community grouped by competence level - who is at each stage, who is progressing, and who may be stuck.

**Formation Pipeline - Steward View**

Seeker (0b) Member (L1) Disciple (L2) Steward (L3) Senior (L4) Architect (L5)

12 members 34 members 28 members 8 members 3 members 1 member

\[3 stuck >6mo\] \[5 stuck >1yr\] \[2 stuck >2yr\] -- -- --

Tap any column to see members. Red = no Learn activity or gathering in threshold period.

"Stuck" threshold: no Learn App activity AND no gathering attendance in 6 months (Level 0b-1), 12 months (Level 2-3), 24 months (Level 4+). The steward can tap a stuck member to see their last activity, their shepherd, and initiate a pastoral action.

**-- SERVICE ORDERS**

**24 Orders of Kingdom Service**

The formal structure of service roles. Six domains. Four orders each.

## **7.1 The 24 Service Orders**

The 24 Orders of Kingdom Service are the formal structure through which individuals contribute to the life, growth, and mission of the Kingdom community. Every member active in ministry is assigned to one primary Service Order. The Formation product manages these assignments.

| **Service Domain**                | **Orders**   | **Focus**                                                                                 |
| --------------------------------- | ------------ | ----------------------------------------------------------------------------------------- |
| Apostolic and Spiritual Ministry  | Orders 1-4   | Spiritual oversight, prophetic ministry, apostolic function, prayer and intercession      |
| Leadership and Governance Support | Orders 5-8   | Strategic leadership, governance administration, policy and procedure, accountability     |
| Formation and Teaching            | Orders 9-12  | Discipleship facilitation, formal teaching, curriculum development, training coordination |
| Mission and Outreach              | Orders 13-16 | Evangelism, community outreach, cross-cultural mission, expansion and planting            |
| Community Life and Care           | Orders 17-20 | Pastoral care, hospitality, social welfare, community integration and support             |
| Operations and Stewardship        | Orders 21-24 | Administration, financial stewardship, facilities, human resource coordination            |

## **7.2 Service Order Assignment**

Service Order assignment is managed by the community steward (Level 3+). The assignment is stored in UserPermission.metadata.service_order as a string reference to the Service Order slug.

The Formation product makes this assignment visible and meaningful:

- The member's active Service Order displayed on their formation profile
- KGS pathway alignment shown alongside the Order - which pathway this Order serves
- Service Order activity tracked via Activity Engine - activities tagged with metadata.service_order
- Formation pipeline can be filtered by Service Order - steward can see all members in a given Order
- Skills register integration - the member's skill records (activity_type: "skill") linked to their Service Order

**One primary Order**

Every active member should have one primary Service Order. They may participate in activities across multiple domains, but their primary assignment determines their formation track and their accountability structure within the community.

**-- PRODUCT DESIGN**

**Formation Product Surfaces**

Three surfaces. Steward management. Member journey. Network oversight.

## **8.1 Surface 1 - The Formation Pipeline (Level 3+)**

The primary steward surface. The steward's complete view of their community's formation health.

- Pipeline view: members grouped by competence level with "stuck" indicators
- Member detail: full formation profile - level, shepherd, service order, programme progress, participation record
- Certification queue: members awaiting confirmation - academic evidence, participation evidence, pastoral assessment panel
- Shepherd assignments: manage shepherd-to-disciple relationships across the community
- Service order assignments: assign or reassign members to Service Orders
- Formation reports: summary of advancement activity, stuck member alerts, overall community formation health

## **8.2 Surface 2 - My Formation Journey (All levels)**

The individual member's view of their own formation. Personal, encouraging, transparent.

- Formation level badge - current competence level with the KGS name
- Active programme - current qualification programme, progress percentage, next lesson
- Pathway progress - visual indicators across all eight Kingdom Pathways
- My shepherd - who is pastoring me. Direct message link (future).
- My flock - who I am shepherding (if assigned as a shepherd)
- My Service Order - current assignment with Order name and domain
- Advancement status - am I complete for advancement? What is pending?
- Formation history - full level progression with dates and confirming stewards

## **8.3 Surface 3 - Network Formation Overview (Level 4+)**

The district or provincial steward's view of formation across multiple communities.

- Formation health per community - pipeline summary (how many at each level) per tenant in scope
- Network advancement activity - recent certifications confirmed across the network
- Stuck member alerts - communities with high proportions of stuck members
- Service Order coverage - which Orders are underrepresented across the network
- Formation trends - competence level distribution over time across the network

## **8.4 The Certification Review Panel**

The most critical UI element in the Formation product. This is where the confirming steward reviews all evidence and makes the advancement decision.

| **Panel section**      | **Contents**                                                                                                                                                          |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Member identity        | Name, avatar, current level, programme, shepherd name, community                                                                                                      |
| Academic evidence      | Programme completion percentage. All lessons listed with completion status. Assessments submitted. Duration enrolled.                                                 |
| Participation evidence | Gathering attendance rate over programme period. Ministry activity count. Service Order engagement summary.                                                           |
| Pastoral assessment    | Shepherd's name and their recommendation (endorse / hold / concern). Steward notes field (free text, Level 3+ only, never visible to member). Pastoral notes history. |
| Formation history      | Previous certifications - when, at what level, confirmed by whom.                                                                                                     |
| Decision               | Confirm advancement button. Hold for review button. Request more evidence button. Each requires a note from the confirming steward.                                   |

# **Part 9 - Data Model and Integration**

## **9.1 Core Data Models**

Ichebo Formation introduces two new models beyond what the current production system contains:

**PastoralRelationship**

Replaces UserPermission.metadata.shepherd_id. Full model specified in Part 6.2.

**FormationNote**

Pastoral notes attached to a member's formation record. Written by Level 3+ stewards. Never visible to the member. Privacy-sensitive.

FormationNote {

id: uuid

member_id: uuid // the person this note is about

author_id: uuid // Level 3+ steward who wrote it

tenant_id: uuid

content: text // the pastoral note

note_type: "observation" | "concern" | "endorsement" | "advancement_review"

created_at: ISO-8601

deleted_at: ISO-8601 | null

// Privacy rules:

// - Never returned in any API endpoint accessible to the member

// - Visible only to Level 3+ users within the tenant scope

// - Not synced to Ichebo Desktop in MVP (privacy design deferred)

// - Included in the Certification Review Panel for the confirming steward

}

## **9.2 Integration with Learn App**

Formation does not own the certification flow - it consumes it. The Learn App triggers the certification signal. Formation confirms it and writes the competence_level.

| **Learn App owns**                                                        | **Formation product owns**          |
| ------------------------------------------------------------------------- | ----------------------------------- |
| Programme, course, lesson records                                         | PastoralRelationship records        |
| Enrolment Activity (programme enrolment)                                  | FormationNote records               |
| Certification signal (at 100% progress)                                   | Certification Review Panel UI       |
| CertificationConfirmation audit record                                    | Formation pipeline view             |
| The certification endpoint (POST /api/learn/certifications/{id}/confirm/) | Network formation overview          |
| competence_level write (via the single authorised path)                   | Service Order assignment management |

## **9.3 Integration with Activity Engine**

Formation reads from the Activity Engine for participation evidence. It never writes to the Activity Engine directly - it observes.

- Gathering attendance: Activity Engine activities with activity_type: "event" or "gathering" for the member's tenant
- Ministry participation: Activity Engine activities with metadata.service_order set and assigned_to: member_id
- Mission activity: Activity Engine activities with kgs_pathway: "mission"
- Skill records: Activity Engine activities with activity_type: "skill" - the member's gifts register

All participation evidence is read at certification review time - Formation queries the Activity Engine via DRF and presents the summary in the Certification Review Panel.

# **Part 10 - Build Sequence and Deferred Items**

## **10.1 Entry Requirement**

**Gate**

Ichebo Formation build does not begin until: (1) the Learn App certification flow is stable in production, (2) the Activity Engine is providing reliable participation data, (3) the PastoralRelationship model design has been reviewed for privacy implications.

## **10.2 Build Phases**

| **Phase**                          | **What it builds**                                                                                                                                                    |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| H.1 - PastoralRelationship model   | New model replacing metadata.shepherd_id. Migration of existing shepherd assignments. Django + DRF endpoints. Constraint enforcement (shepherd.level > member.level). |
| H.2 - My Formation Journey surface | Individual member view. Level badge, active programme, pathway progress, shepherd display, service order display, advancement status, formation history.              |
| H.3 - Formation Pipeline surface   | Steward pipeline view. Members grouped by level. Stuck member detection. Member detail with full formation profile.                                                   |
| H.4 - Certification Review Panel   | Evidence aggregation UI. Academic + participation + pastoral evidence in one panel. Shepherd recommendation. Confirming steward decision flow.                        |
| H.5 - FormationNote model          | Pastoral notes. Privacy enforcement (Level 3+ only, never visible to member). Integration with Certification Review Panel.                                            |
| H.6 - Network Formation Overview   | Level 4+ multi-community view. Formation health per tenant. Advancement activity feed. Stuck member alerts.                                                           |
| H.7 - Service Order management UI  | Assignment and reassignment. Service Order activity linkage. Skills register integration.                                                                             |

## **10.3 Deferred Items**

- Full pastoral notes UI for mobile - privacy design required; desktop-first in Phase 1
- Formation analytics - advancement rates, time-at-level averages, community comparison. Phase 2.
- Shepherd direct messaging - in-app message thread between shepherd and disciple. Layer 10 (requires WebSockets).
- Formation pathway visualisation - interactive eight-pathway progress diagram. Phase 2.
- Peer accountability groups - small group accountability structures within the community. Phase 2.
- Cross-community shepherd assignment - for members who move between communities. Phase 2.
- Formation reporting for funders and denominational bodies - evidenceable discipleship data. Phase 2.

**Ichebo Christian Services**

_DOC H - Ichebo Formation Product Specification v1.0 - May 2026 - Canonical Reference_