# ICS Platform — Data Contract & Architecture Document

> **Version:** v7 — 2026-04-08
> **Previous version:** v6 — 2026-04-08
>
> **v7 Amendments (Bible App — source data structure confirmed):**
> 1. `BibleTranslation` model expanded (Part 13.1): five fields added from the
>    confirmed JSON `metadata` structure: `language_full`, `year`, `description`,
>    `copyright_statement`, `is_copyright`. `is_public` mapping clarified:
>    derived from `metadata.restrict == 0`. `is_copyright` derived from
>    `metadata.copyright == 0` (0 = public domain → False).
> 2. `BibleTranslation` in Part 13.2 translations table updated: `Copyright`
>    and `Language` columns added. All three translations confirmed public domain.
> 3. Load command note updated: all three files (KJV, ASV, WEB) confirmed to
>    share the same flat `metadata` + `verses` JSON structure. Single management
>    command handles all three. `TESTAMENT_MAP` and `BOOK_CODE_MAP` hardcoded
>    (flat JSON carries no testament or short book code fields).
> 4. Verse count note updated: ~31,102 per translation (WEB confirmed).
>    Total at setup ~93,306 rows. Exact counts vary slightly by translation.
>
> **Everything else in v6 is unchanged and remains locked.**
>
> **v6 Amendments (Bible App — pre-build):**
> 1. Three new Bible models added — `BibleTranslation`, `BibleBook`, `BibleVerse`
>    (Part 13). These are not Record objects. They are read-only after initial load
>    via management command. Three public domain translations loaded at setup:
>    KJV (default), ASV, WEB.
> 2. `Relationship` object amended (Part 3.2): `to_record_id` is now nullable.
>    New optional field `bible_verse_id` (FK → `bible.BibleVerse`) added as an
>    alternative target. Exactly one of `to_record_id` or `bible_verse_id` must be
>    non-null on every Relationship row. Enforcement: model `.clean()` + DRF serializer
>    validation. Migration required on `records_relationship` table.
> 3. `UserProfile` amended (Part 2.1 note): new field
>    `preferred_bible_translation` (FK → `bible.BibleTranslation`, nullable).
>    Null = use system default (`BibleTranslation.is_default=True`).
> 4. `Relationship.bible_verse_id` indexing added to Part 8.3 indexing strategy.
> 5. `records/models.py` app ownership rule updated in Part 6.2: Relationship
>    now has FK dependency on `bible.BibleVerse`.
> 6. `bible/` Django app entry in Part 6.1 file map updated: now a full app
>    with models, not just a static viewer.
> 7. Part 13 (Bible App Engine) added: Bible data model, translation management,
>    annotation patterns, Handbook linkage pattern, Learn cross-reference convention,
>    access rules by competence level, and DRF endpoint summary.
> 8. Part 12 (What to Build Next) updated: Bible App marked as system design
>    complete (`2026-04-08-ics-bible-app-system-design_v1.md`); Bible App
>    deferred items added to Deferred section.
> 9. `custom_fields.scripture_reference` convention formally documented for
>    Lesson Records (Part 9 note added to 9.2).
>
> **Everything else in v5 is unchanged and remains locked.**

> **For Claude:** When implementing, read this document fully before writing any code.
> All schemas, rules, and patterns here are authoritative. Do not infer from app code.

**Goal:** Define the complete, locked data contracts, service boundaries, and schema
definitions for the ICS (Integrated Community System) platform — the digital twin of
the Kingdom Governance System (KGS).

**Architecture:** Django + PostgreSQL backend (single source of truth). Four locked
architectural decisions: (1) materialized path for tenant hierarchy, (2) single `records`
table with `record_class` discriminator, (3) Paraclete as a standalone orchestration
service separate from the Activity Engine, (4) Handbook as a prime `tier:"handbook"`
tenant at `/global/handbook/` with Level 5 access only.

**UI Architecture (locked — 2026-04-07):** All app UIs are built in Django templates +
HTMX. There are no vanilla JS app files (`activity-app.js`, `learn-app.js`, etc.). HTMX
handles dynamic interactions. `storage.js` is retained for UI state only (theme, session
token). The data contract schemas and DRF service layer are unaffected by this decision.

**Tech Stack:** Python/Django 4.2, Django REST Framework, PostgreSQL, Django templates,
HTMX, mobile-first CSS with CSS variables.

---

## Part 1 — Core Principles (Non-Negotiable)

### 1.1 Every object carries four mandatory fields

Every stored entity — record, user, tenant, activity — must include:

```js
{
  id:         "uuid-v4",
  tenant_id:  "uuid | null",      // null = platform-level / personal only
  created_by: "user_id",
  created_at: "ISO-8601-timestamp"
}
```

No exceptions. These four fields are how the permission system, audit log, and
multi-tenancy all work. Missing any one of them means that object cannot be governed.

**Note:** `BibleTranslation`, `BibleBook`, and `BibleVerse` (Part 13) are exempt
from this rule. They are read-only reference data loaded by management command,
not governed platform entities.

### 1.2 record_class is the permission gate, not record_type

`record_type` describes *what* the record is (prayer, journal, mandate).
`record_class` describes *how* the system governs it:

| record_class  | Who creates   | Default visibility | Mutable after creation | Example types               |
|---------------|---------------|--------------------|------------------------|-----------------------------|
| personal      | Any user      | private            | Yes                    | journal, dream, prayer      |
| organizational| Level 2+      | tenant             | Yes, with audit        | event, programme, campaign  |
| governance    | Level 4+      | tenant or public   | Versioned only         | mandate, statement, calendar|

Permission checks MUST read `record_class` before evaluating anything else.

### 1.3 Tenant paths are the scope system

Every tenant has a `path` field. Every permission check that involves scope uses
prefix matching on this path. This is the materialized path pattern.

```
/global/
/global/africa/
/global/africa/southafrica/
/global/africa/southafrica/gauteng/
/global/africa/southafrica/gauteng/pretoria-north/
/global/africa/southafrica/gauteng/pretoria-north/sceptre-community-abc/
```

A user with `scope_path = "/global/africa/southafrica/gauteng/"` can see all
records whose tenant path starts with that prefix. Query: `WHERE tenant_path
LIKE '/global/africa/southafrica/gauteng/%'`.

### 1.4 Services own their domain. Apps call services.

No app template may bypass the DRF service layer. All reads and writes go through
DRF endpoints. Django views prepare context from DRF responses or direct ORM calls
within their own Django app boundary only. Cross-app data access always goes through
the API or a shared service module.

---

## Part 2 — User & Identity Schema

### 2.1 User object

```js
User = {
  // Core (mandatory on all objects)
  id:           "uuid",
  tenant_id:    null,            // Users are platform-level, not tenant-scoped
  created_by:   "uuid | null",   // null = self-registered
  created_at:   "ISO-8601",

  // Identity
  email:        "string",
  display_name: "string",
  avatar_url:   "string | null",

  // Competence & Formation
  // 0a = Guest (anonymous, no account) — not stored, describes unauthenticated sessions
  // 0b = Seeker (registered, formation not yet complete) — status: 'seeker'
  // 1–5 = active formation levels mapped to KGS (see section 2.3)
  competence_level: 0 | 1 | 2 | 3 | 4 | 5,

  // Platform status
  status: "seeker | active | suspended | pending_verification",

  // Settings
  preferences: {
    theme:    "system | light | dark",
    language: "en | ...",
    timezone: "Africa/Johannesburg | ..."
  },

  updated_at: "ISO-8601"
}
```

**UserProfile extension (Django model — `accounts.UserProfile`):**
In addition to the User fields above, `UserProfile` carries:

```python
preferred_bible_translation = FK → bible.BibleTranslation (nullable)
# null = use BibleTranslation.objects.get(is_default=True) at read time
# Set via HTMX translation switcher in the Bible App reader
# Updated by: POST /bible/htmx/translation/set/
```

### 2.2 UserPermission object

```js
UserPermission = {
  id:           "uuid",
  tenant_id:    "uuid",
  created_by:   "uuid",
  created_at:   "ISO-8601",

  user_id:      "uuid",
  tenant_path:  "/global/africa/southafrica/gauteng/pretoria/",
  role:         "seeker | disciple | branch-steward | district-steward | provincial-steward | national-steward | regional-steward | continental-steward | global-steward | admin",
  level:        0 | 1 | 2 | 3 | 4 | 5,
  is_active:    true | false,
  granted_at:   "ISO-8601",
  granted_by:   "uuid"
}
```

### 2.3 Competence levels mapped to KGS

| Level | KGS Name               | Platform label     | Role token          | What they can do                              |
|-------|------------------------|--------------------|---------------------|-----------------------------------------------|
| 0a    | Guest                  | Guest              | *(no User object)*  | Landing page, public records, tenant directory |
| 0b    | Seeker                 | Seeker             | `seeker`            | Bible reader, personal records (limited), Learning portal entry, no tenant membership |
| 1     | Foundational Disciple  | Member             | `member`            | Full personal records, join one tenant, learn |
| 2     | Active Contributor     | Disciple/Operator  | `disciple`          | Org records, lead small groups within a node  |
| 3     | Functional Minister    | Steward            | `branch-steward` or higher | Manage teams, create programmes        |
| 4     | Leader                 | Senior Steward     | `district-steward` or higher | Create governance records, manage tenant |
| 5     | Apostolic Steward      | Architect          | `global-steward` or `admin` | Cross-tenant governance, Handbook access, system config |

**Level 0b (Seeker) access rules:**
- Can create personal records but limited to 10 total until Level 1 is reached
- Cannot join a tenant or participate in community features
- Can browse the Learning portal and begin foundation programmes
- Can read scripture and create personal bible notes (subject to 10-record limit)
- Cannot see tenant (organizational) bible notes — no tenant membership
- Cannot see Handbook scripture references — Level 5 only

### 2.4 Tenant object

```js
Tenant = {
  id:           "uuid",
  tenant_id:    "uuid | null",
  created_by:   "uuid",
  created_at:   "ISO-8601",

  name:         "string",
  slug:         "string",
  path:         "/global/africa/southafrica/gauteng/pretoria/sceptre-abc/",

  tier: "handbook | church_node | church_collective | district | provincial | national | regional | continental | global",
  affiliation: "ichebo | independent | affiliate",
  status: "active | pending | suspended",
  is_collective: false,

  description:  "string | null",
  logo_url:     "string | null",
  location: {
    country:  "string",
    province: "string",
    city:     "string",
    coordinates: { lat: 0.0, lng: 0.0 }
  },

  settings: {
    allow_public_records:  false,
    require_approval:      true,
    max_members:           null
  },

  updated_at: "ISO-8601"
}
```

---

## Part 2.5 — The Handbook (Prime Tenant)

### 2.5.1 Fixed path and identity

```js
HandbookTenant = {
  id:          "handbook-singleton-uuid",
  tenant_id:   null,
  created_by:  "system",
  created_at:  "ISO-8601",
  name:        "The Handbook",
  slug:        "handbook",
  path:        "/global/handbook/",
  tier:        "handbook",
  affiliation: "ichebo",
  status:      "active",
  is_collective: false,
  settings: {
    allow_public_records: false,
    require_approval:     true,
    max_members:          null
  }
}
```

### 2.5.2 Access rules

- **Read:** Level 5 only
- **Write:** Level 5 only
- The permission check algorithm (Part 7) treats `tier: "handbook"` as a short-circuit

### 2.5.3 What the Handbook produces

| record_type     | Description                                           |
|-----------------|-------------------------------------------------------|
| `class`         | A branch or category of Kingdom knowledge             |
| `principle`     | A foundational rule or truth                          |
| `concept`       | An idea or theological construct                      |
| `divine_pattern`| A recurring pattern observed in scripture/governance  |
| `narrative`     | A story or account carrying governance meaning        |
| `subject`       | A topic or domain of study                            |
| `entity`        | A named actor, body, or structure                     |
| `framework`     | A structured system of related principles             |
| `protocol`      | A defined sequence of steps for an occasion           |
| `procedure`     | An operational process for recurring tasks            |
| `mandate`       | A directive from the Kingdom Mandate                  |
| `statement`     | A formal declaration or position                      |
| `programme`     | A governance-context structured programme (record_class:'governance' — distinct from learning programme) |
| `calendar`      | A time-governed plan of seasons and appointed times   |

**Handbook ↔ Scripture linkage (v6):** Handbook governance records derive their
authority from scripture. A Level 5 Architect may link any governance record to the
specific `BibleVerse` row(s) from which it derives, using a `Relationship` object
with `relationship_type: "references"`, `direction: "directed"`, and
`bible_verse_id` set (see Part 3.2 amendment). This replaces the need for
free-text scripture citations in record content.

### 2.5.4 Hierarchy and Relationship System (HRS)

Core HRS relationship types:

| relationship_type     | From → To example                                      |
|-----------------------|--------------------------------------------------------|
| `part_of`             | governance_principle → governance_framework            |
| `derived_from`        | governance_concept → governance_divine_pattern         |
| `aligns_with`         | governance_programme → governance_mandate              |
| `authorised_by`       | governance_procedure → governance_mandate              |
| `references`          | governance_narrative → governance_subject              |
| `references`          | governance_record → BibleVerse (via bible_verse_id)    |
| `has_subject`         | governance_framework → governance_subject              |
| `has_entity`          | governance_mandate → governance_entity                 |

---

## Part 3 — Records Engine Schema

### 3.1 Record object (universal)

```js
Record = {
  // Core (mandatory)
  id:           "uuid",
  tenant_id:    "uuid | null",
  created_by:   "uuid",
  created_at:   "ISO-8601",

  // Classification (read record_class FIRST in all permission checks)
  record_class: "personal | organizational | governance",

  record_family: "journal | governance | activity | learning | reference | bible | community",

  record_type:  "prayer | dream | note | sermon | class | principle | concept | divine_pattern | narrative | subject | entity | mandate | statement | programme | framework | protocol | procedure | calendar | event | campaign | project | habit | task | skill | course | lesson | assignment | quiz | certification | key | property | bible_note | custom",
  // Family → Type mapping (enforced at service layer):
  //   journal     → prayer | dream | note | sermon
  //   governance  → class | principle | concept | divine_pattern | narrative |
  //                 subject | entity | mandate | statement | programme |
  //                 framework | protocol | procedure | calendar
  //   activity    → event | campaign | project | habit | task | skill
  //   learning    → programme | course | lesson | assignment | quiz | certification
  //   reference   → key | property
  //   bible       → bible_note
  //   community   → (future: discussion, announcement, report)
  // Governance types require record_class:'governance' and Level 4+ (Level 5 for Handbook)
  // 'programme' appears in BOTH governance and learning families.
  //   record_class:'governance' = KGS framework programme (Handbook-authored)
  //   record_class:'organizational' = Qualification Programme (Certificate → Doctorate)

  origin: "user | system | paraclete | import",

  title:        "string",
  content:      "string | null",
  summary:      "string | null",

  status: "draft | submitted | active | completed | archived | locked",
  // 'submitted' = awaiting review by a higher authority
  // 'locked' = only valid for governance records after approval

  locked_by:  "uuid | null",
  locked_at:  "ISO-8601 | null",

  version:             "integer | null",
  previous_version_id: "uuid | null",
  superseded_by:       "uuid | null",

  tags:       [],
  categories: [],

  custom_fields: {},

  metadata: {
    source_app:    "records | bible | activity | learn | ...",
    record_origin: "string | null",
    custom_field_definitions: []
  },

  permissions: {
    visibility:   "private | tenant | collective | public",
    // private    = only created_by can read
    // tenant     = any member of exactly this tenant can read
    // collective = this tenant + its parent chain up to the first Church Collective tier
    // public     = any authenticated user (Level 0b and above)
    required_level: 1,
    roles_allowed:  [],
    can_edit:       [],
  },

  updated_at:    "ISO-8601",
  deleted_at:    "ISO-8601 | null"
}
```

### 3.2 Relationship object

**v6 Amendment:** `to_record_id` is now nullable. A new optional field
`bible_verse_id` has been added. Exactly one of the two must be non-null.

```js
Relationship = {
  id:           "uuid",
  tenant_id:    "uuid | null",
  created_by:   "uuid",
  created_at:   "ISO-8601",

  from_record_id: "uuid",             // always required — the originating record

  // Target — exactly ONE of the following must be non-null:
  to_record_id:   "uuid | null",      // FK → Record (null when bible_verse_id is set)
  bible_verse_id: "uuid | null",      // FK → bible.BibleVerse (null when to_record_id is set)
  // Constraint: to_record_id XOR bible_verse_id. Both null = invalid. Both set = invalid.
  // Enforced by: records.Relationship.clean() + records RelationshipSerializer.validate()

  direction: "directed | bidirectional",
  // directed: from_record → target (either to_record_id or bible_verse_id)
  // bidirectional: either record can be the "source"
  // Note: bible_verse_id target is always directed (governance record → verse)

  relationship_type: "relates_to | derived_from | references | answers | fulfills | requests | has_symbol | matches_pattern | assigned_to | tracks | completes | part_of | aligns_with | authorised_by | tagged_in",

  notes:    "string | null",
  strength: "weak | medium | strong | null",

  deleted_at: "ISO-8601 | null"
}
```

### 3.3 Controlled relationship type vocabulary

| Type            | Direction    | Domain          | Example                                              |
|-----------------|--------------|-----------------|------------------------------------------------------|
| relates_to      | bidirectional| General         | Dream relates to journal entry                       |
| derived_from    | directed     | General         | Note derived from sermon                             |
| references      | directed     | General         | Activity references Bible verse                      |
| references      | directed     | Bible/Governance| Governance record → BibleVerse (bible_verse_id set)  |
| answers         | directed     | Prayer          | Answer record → Prayer record                        |
| fulfills        | directed     | Prayer/Activity | Testimony → Prayer request                           |
| requests        | directed     | Prayer          | Prayer request → God (conceptual)                    |
| has_symbol      | directed     | Dreams          | Dream → Symbol reference                             |
| matches_pattern | bidirectional| Dreams          | Dream matches recurring pattern                      |
| assigned_to     | directed     | Activity        | Task → User (use metadata.assigned_user_id)          |
| tracks          | directed     | Activity        | Habit → Programme                                    |
| completes       | directed     | Activity        | Task → Goal                                          |
| part_of         | directed     | Governance/Learn| Calendar → Programme; Lesson → Course                |
| aligns_with     | directed     | Governance      | Activity → Mandate                                   |
| authorised_by   | directed     | Governance      | Programme → Mandate                                  |

**Activity App relationship type rules (v5):**

| Activity type      | Use relationship_type | Direction                        |
|--------------------|-----------------------|----------------------------------|
| `task`, `habit`    | `tracks`              | activity_record → target_record  |
| `goal`, `reminder` | `tracks`              | activity_record → target_record  |
| `campaign`, `event`| `aligns_with`         | activity_record → mandate/programme |
| `project`          | `aligns_with`         | activity_record → campaign_record |
| `skill`            | `aligns_with`         | skill_record → service_order_record (if linked) |

The Learn App exclusively uses `tracks` (lesson/habit → programme) and `part_of`
(lesson → course → programme). Activity App links must not use `part_of` — that
relationship type is reserved for curriculum and governance hierarchy structure.

**Bible App relationship type rules (v6):**

| From             | relationship_type | Target field       | Who can create     |
|------------------|-------------------|--------------------|--------------------|
| Governance record| `references`      | `bible_verse_id`   | Level 5 only       |

All other Relationships involving Bible content (e.g. a journal note referencing a
verse the user was reflecting on) use `to_record_id` pointing to a `bible_note`
Record, not directly to a `BibleVerse`. Direct `bible_verse_id` Relationships are
exclusively for formal Handbook governance linkages.

---

## Part 4 — Activity Engine Schema

### 4.1 Activity object

The Activity Engine operates on its own objects AND writes records into the
Records Engine for persistence and linking. Activities are the execution layer;
Records are the memory layer.

```js
Activity = {
  // Core (mandatory)
  id:           "uuid",
  tenant_id:    "uuid | null",
  created_by:   "uuid",
  created_at:   "ISO-8601",

  // Classification
  activity_type: "task | habit | goal | event | campaign | project | programme | reminder | skill",
  // task      = a single actionable item; personal or assigned
  // habit     = a recurring personal discipline (recurrence always set)
  // goal      = a personal or team objective with measurable progress
  // event     = a scheduled gathering, service, or ministry occasion
  // campaign  = a time-bound operational initiative (KGS Harvest Campaign etc.)
  // project   = a structured body of work nested under a campaign
  // programme = learning enrolment hierarchy — authored and owned by Learn App;
  //             read-only in Activity App
  // reminder  = a time-triggered prompt; created by user or Paraclete
  // skill     = a gift, talent, or competence entry in the user's gifts register;
  //             NOT a task — see 4.1.1 for full specification

  // Identity
  title:          "string",
  description:    "string | null",

  // Timing
  scheduled_at:   "ISO-8601 | null",
  due_at:         "ISO-8601 | null",
  recurrence:     "none | daily | weekly | monthly | custom",
  recurrence_rule:"string | null",  // RRULE format — only used when recurrence:'custom'
  // MVP UI exposes: none | daily | weekly | monthly (radio buttons)
  // recurrence:'custom' and recurrence_rule are deferred to post-MVP

  // Hierarchy (activities can nest)
  // Supported nesting in Activity App UI: campaign/project → task (two levels)
  // Three-level nesting (programme → project → task) is Learn App only
  parent_activity_id: "uuid | null",

  // Progress
  status:   "pending | in_progress | completed | cancelled | deferred",
  progress: 0,   // 0–100 integer

  // Assignment
  assigned_to: "uuid | null",  // user_id of the assigned individual
  // ASSIGNMENT VISIBILITY RULE (v5):
  // If assigned_to is null AND tenant_id is set, the activity is visible to ALL
  // members of that tenant with read access (i.e., all users with a UserPermission
  // row whose tenant_path matches or is a descendant of the tenant's path).
  // This is the "team-visible, unassigned" state — used for campaign headers and
  // project containers visible to the whole branch without being assigned to anyone.
  // If assigned_to is null AND tenant_id is null, the activity is personal and
  // visible to created_by only.
  //
  // COLLECTIVE ASSIGNMENT NOTE (deferred — v5):
  // assigned_to_tenant_id is reserved for future collective/network-level task
  // assignment. Not implemented in MVP.

  // KGS alignment
  kgs_pillar:   "apostolic | strategy | formation | programmes | mission | communities | stewardship | null",
  kgs_pathway:  "new_life | spiritual_formation | community_life | service | leadership | learning | mission | apostolic_stewardship | null",

  // Metadata
  metadata: {
    source_app:   "activity | paraclete | learn | governance",
    icon:         "string | null",
    color:        "string | null",
    is_template:  false,
    template_id:  "uuid | null",
    service_order: "string | null",
  },

  updated_at:  "ISO-8601",
  deleted_at:  "ISO-8601 | null"
}
```

### 4.1.1 `skill` activity type — gifts register specification

`skill` activities are not tasks. They form a structured gifts and competence
register for each user. They do not have `due_at`, `recurrence`, or `parent_activity_id`
set in normal usage. The following fields carry meaning:

| Field          | Usage for `skill` type                                              |
|----------------|---------------------------------------------------------------------|
| `title`        | Name of the gift or skill (e.g. "Teaching", "Administration")       |
| `description`  | How this gift manifests in the user's life and ministry             |
| `progress`     | Self-assessed competence: 0–100 (maps loosely to KGS levels 1–5 × 20) |
| `kgs_pathway`  | Which Kingdom Pathway this gift primarily serves                    |
| `metadata.service_order` | KGS Service Order this gift aligns with (optional)       |
| `status`       | `active` = current gift; `archived` = no longer active/relevant     |
| `tenant_id`    | Null = personal register; tenant-scoped = visible to steward        |

**Not used on `skill` type:** `due_at`, `scheduled_at`, `recurrence`,
`recurrence_rule`, `parent_activity_id`, `assigned_to`, `is_template`.

### 4.2 ActivityLog object

Every status change or progress update on an Activity must be logged.

```js
ActivityLog = {
  id:           "uuid",
  tenant_id:    "uuid | null",
  created_by:   "uuid",
  created_at:   "ISO-8601",

  activity_id:  "uuid",
  event_type:   "created | status_changed | progress_updated | assigned | linked | commented",
  previous_value: "any | null",
  new_value:      "any | null",
  note:           "string | null"
}
```

### 4.3 Activity assignment model (v5)

| Who                   | Can assign to                          | Constraint                         |
|-----------------------|----------------------------------------|------------------------------------|
| Level 1–2 (personal)  | Self only (`assigned_to = created_by`) | Personal activities only           |
| Level 3+ (steward)    | Any user within their `scope_path`     | `activity.tenant_id` must be within assigning user's `UserPermission.tenant_path` |
| Level 3+ (steward)    | `assigned_to = null` (team-visible)    | For campaign/project containers    |

The materialized path permission check MUST be enforced in the DRF view — not only
in the template. A Level 3 steward cannot assign activities to users outside their
`scope_path`, even if they know the user's ID.

---

## Part 5 — Paraclete Service Contract

The Paraclete is a standalone orchestration service. It does NOT own any data.
It reads from other engines and produces suggestions, reminders, and insights.
It never writes directly to Records or Activities — it calls their services.

### 5.1 What Paraclete is responsible for

- Reading user's activities, records, and schedules to generate intelligent reminders
- Detecting patterns across records (recurring dream symbols, prayer themes, habit streaks)
- Producing "today's focus" digest based on user's competence level, active activities,
  and KGS calendar
- Cross-linking suggestions: "This prayer relates to that journal entry from last week"
- Generating structured prompts for daily spiritual disciplines

### 5.2 What Paraclete is NOT responsible for

- Storing any data of its own (no Paraclete tables)
- Replacing the Activity Engine or Records Engine
- User authentication or permissions

### 5.3 Paraclete Django service API

`paraclete/service.py` calls Django ORM directly (not other DRF endpoints).
It is a Python orchestration module, not a web service calling itself.

```
GET  /api/paraclete/digest/              daily digest
GET  /api/paraclete/reminders/           pending reminders
GET  /api/paraclete/suggest/{record_id}/ link suggestions
GET  /api/paraclete/prompt/              discipline prompt
POST /api/paraclete/respond/             accept/dismiss suggestion
```

### 5.4 Activity endpoint filters required by Paraclete (v5)

```
GET /api/activities/?due_today=true&assigned_to={user_id}
GET /api/activities/?overdue=true&assigned_to={user_id}
GET /api/activities/?activity_type=habit&assigned_to={user_id}&status=in_progress
GET /api/activities/?tenant_id={tenant_id}&status=pending
GET /api/activities/?parent_activity_id={activity_id}
GET /api/activities/?metadata__source_app=learn&assigned_to={user_id}
```

### 5.5 ParacleteDigest object

```js
ParacleteDigest = {
  generated_at:       "ISO-8601",
  user_id:            "uuid",
  greeting:           "string",
  focus_for_today:    "string",
  pending_activities: Activity[],
  recent_records:     Record[],
  active_prayer_count: 0,
  suggested_links:    LinkSuggestion[],
  discipline_prompt:  DisciplinePrompt
}
```

---

## Part 6 — Service Boundaries (File Map)

### 6.1 Django app structure

```
~/ics/
  accounts/          ← User, UserProfile (+ preferred_bible_translation v6), UserPermission
  tenants/           ← Tenant
  records/           ← Record, Relationship (+ bible_verse_id FK v6)
  activity/          ← Activity, ActivityLog
  learn/             ← CertificationConfirmation; learning UI views
  bible/             ← BibleTranslation, BibleBook, BibleVerse (v6 — full models)
                        Management commands: load_bible
                        Bible reader template views + HTMX partials
  paraclete/         ← Orchestration service (no models)
  calendar/          ← Calendar aggregation service (no models — Phase 6)
  community/         ← (future)
  governance/        ← (future)
  notifications/     ← stub
  ics_project/       ← Django project settings, root URLs

static/
  css/
    main.css         ← platform-wide styles, CSS variables
    learn.css        ← Learn App styles
    activity.css     ← Activity App styles
    bible.css        ← Bible App styles (v6)
  js/
    core/
      storage.js     ← UI state only (theme, session token)
      // No app-level JS files. All app UIs are Django templates + HTMX.
  data/
    // bible/*.json  ← Translation source files (gitignored if >50MB)
```

### 6.2 Django app ownership rules

```
accounts app     → owns User, UserPermission, UserProfile models + auth endpoints
                   UserProfile.preferred_bible_translation has FK dependency on bible app
tenants app      → owns Tenant model + tenant endpoints
records app      → owns Record, Relationship models + CRUD endpoints
                   Relationship.bible_verse_id has FK dependency on bible app
                   Migration order: bible app must migrate before records app
                   (or use a deferred FK — see migration note in Part 8.5)
activity app     → owns Activity, ActivityLog models + CRUD endpoints
                   + Activity App Django views and templates
learn app        → owns CertificationConfirmation model
                   + Learn App Django views and templates
                   + calls records + activity endpoints for data
bible app        → owns BibleTranslation, BibleBook, BibleVerse models
                   + Bible App Django views and templates
                   + management commands for loading translation data
                   + DRF endpoints at /api/bible/
paraclete app    → owns no models
                   + orchestrates reads from records + activity via ORM
calendar app     → owns no models
                   + aggregates Activity objects by scheduled_at/due_at
                   + Calendar App Django views (Phase 2 of calendar)
```

---

## Part 7 — Permission Check Algorithm

Every permission check across the system follows this exact sequence.

```
checkPermission(user, record) → boolean

0. Level 0 gate
   - IF user is Guest (no User object): only public records pass
   - IF user.status === 'seeker' (Level 0b): only personal records they created
     pass, plus public records — no tenant or collective records

1. Handbook short-circuit
   - IF record.tenant_path starts with '/global/handbook/':
     require user.competence_level >= 5
     IF fails: deny immediately

2. Load user's UserPermission rows for their active tenants

3. Read record.record_class
   - IF 'governance': require level >= 4 to write, >= record.permissions.required_level to read
   - IF 'organizational': require level >= 2 to write
   - IF 'personal' AND record.created_by !== user.id: check visibility only
   - Records with status:'submitted' are readable only by created_by and Level 5 users

4. Check record.permissions.visibility
   - 'private': only record.created_by passes
   - 'tenant': user must have UserPermission row matching record.tenant_id's path
   - 'collective': user must have UserPermission row that is a prefix of record's tenant path
   - 'public': passes for any authenticated user (Level 0b and above)

5. Check record.permissions.required_level
   - user.competence_level must be >= required_level

6. Check record.permissions.roles_allowed
   - IF empty: any role at required_level passes
   - IF populated: user must have a matching role in UserPermission

7. Return true only if ALL checks passed
```

**Activity permission check (supplement):**

Activities are not Records and do not carry a `permissions` object. Activity
visibility is governed by:

1. `tenant_id: null` + `created_by = user.id` → personal, visible to owner only
2. `tenant_id: set` + `assigned_to = user.id` → visible to the assigned user
3. `tenant_id: set` + `assigned_to: null` → visible to ALL members of that tenant
   (per assignment visibility rule in Part 4.1)
4. `tenant_id: set` + any value → visible to stewards whose `scope_path` is a
   prefix of the activity's tenant path (stewards can see all team activities)

**Bible App permission rules (v6 — supplement):**

Bible verse data (`BibleVerse`) is not governed by the standard permission check.
It is public reference data accessible to all authenticated users.

Bible note Records (`record_family:'bible'`, `record_type:'bible_note'`) follow
the standard `checkPermission` algorithm. Key rules:

| Note class      | record_class    | visibility | Who can read              | Who can create |
|-----------------|-----------------|------------|---------------------------|----------------|
| Personal note   | `personal`      | `private`  | created_by only           | Any auth user  |
| Tenant note     | `organizational`| `tenant`   | All members of that tenant| Level 3+ only  |

Handbook ↔ Bible Relationships (`bible_verse_id` set) are readable in the Bible
App only by users with `competence_level >= 5`. The `from_record` governance record
itself is additionally gated by the standard Handbook short-circuit (Step 1 above).

---

## Part 8 — Migration Notes (Django Readiness)

### 8.1 What maps cleanly to Django models

- `Record` → `records.Record`
- `Relationship` → `records.Relationship` (amended in v6 — see 8.5)
- `User` → `auth.User` extended by `accounts.UserProfile` (amended in v6 — see 8.6)
- `UserPermission` → `accounts.UserPermission`
- `Tenant` → `tenants.Tenant`
- `Activity` → `activity.Activity`
- `ActivityLog` → `activity.ActivityLog`
- `BibleTranslation` → `bible.BibleTranslation` (new in v6)
- `BibleBook` → `bible.BibleBook` (new in v6)
- `BibleVerse` → `bible.BibleVerse` (new in v6)

### 8.2 Tenant materialized path in Django

```python
# tenants/models.py
class Tenant(models.Model):
    path = models.CharField(max_length=500, db_index=True)

    def get_descendants(self):
        return Tenant.objects.filter(path__startswith=self.path).exclude(pk=self.pk)

    def get_ancestors(self):
        parts = self.path.strip('/').split('/')
        ancestor_paths = ['/' + '/'.join(parts[:i+1]) + '/' for i in range(len(parts)-1)]
        return Tenant.objects.filter(path__in=ancestor_paths)
```

### 8.3 Indexing strategy

```python
# records/models.py
class Record(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['tenant_id']),
            models.Index(fields=['record_family']),
            models.Index(fields=['record_type']),
            models.Index(fields=['record_class']),
            models.Index(fields=['created_by']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['tenant_id', 'record_family']),
            models.Index(fields=['tenant_id', 'record_class']),
        ]

# records/models.py — Relationship (v6 amended)
class Relationship(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['from_record_id']),
            models.Index(fields=['to_record_id']),          # nullable — index still useful
            models.Index(fields=['bible_verse_id']),        # NEW v6 — Handbook linkage queries
            models.Index(fields=['relationship_type']),
        ]

# activity/models.py
class Activity(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['tenant_id']),
            models.Index(fields=['activity_type']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['status']),
            models.Index(fields=['due_at']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['parent_activity_id']),
            models.Index(fields=['created_by']),
            models.Index(fields=['tenant_id', 'activity_type']),
            models.Index(fields=['tenant_id', 'assigned_to']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['assigned_to', 'due_at']),
        ]

# bible/models.py — BibleVerse (new v6)
class BibleVerse(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['translation', 'book', 'chapter']),  # chapter load query
            models.Index(fields=['book', 'chapter', 'verse']),        # verse lookup
        ]
```

Also index `tenant.path`, `relationship.from_record_id`, `relationship.to_record_id`,
and `relationship.bible_verse_id` — all Relationship query directions must be indexed.

### 8.4 Permissions table upgrade (deferred)

At Django migration, evaluate splitting into a separate `RecordPermission` table
for fine-grained per-user and per-role access control. Do not implement early.

### 8.5 Relationship migration note (v6)

The `records.Relationship` table requires two migration steps for the v6 amendment:

1. Make `to_record_id` nullable: `ALTER TABLE records_relationship ALTER COLUMN to_record_id DROP NOT NULL`
2. Add `bible_verse_id` FK column: `ALTER TABLE records_relationship ADD COLUMN bible_verse_id UUID REFERENCES bible_bibleverses(id)`

**Migration order dependency:** The `bible` app migrations must run before the
`records` app migration that adds `bible_verse_id`. In `records/migrations/`, the
migration adding this field must declare `dependencies = [('bible', '0001_initial')]`.

If the migration order cannot be guaranteed at deployment, use a deferred FK:
```python
bible_verse = models.ForeignKey(
    'bible.BibleVerse',
    null=True, blank=True,
    on_delete=models.CASCADE,
    related_name='governance_references'
)
```
Django resolves string FK references lazily, so this will work as long as both
apps are in `INSTALLED_APPS` before `migrate` runs.

### 8.6 UserProfile migration note (v6)

`accounts.UserProfile` gains `preferred_bible_translation` (nullable FK to
`bible.BibleTranslation`). Same deferred FK approach applies if needed.
Migration is non-breaking: all existing UserProfile rows will have `null`
for this field, which correctly resolves to the system default translation.

---

## Part 9 — Learn App Engine (Data Patterns & Contracts)

### 9.1 The Learning Hierarchy

```
Apostles Programme          → governance record (record_class:'governance',
│                              record_family:'governance', record_type:'programme')
│
├── Qualification Programme → record_class:'organizational', record_family:'learning',
│   (Certificate | Diploma |   record_type:'programme'
│    Degree | Masters |
│    Doctorate)
│
│     └── Course             → record_class:'organizational', record_family:'learning',
│           │                   record_type:'course'
│           │
│           ├── Lesson       → record_family:'learning', record_type:'lesson'
│           ├── Assignment   → record_family:'learning', record_type:'assignment'
│           └── Quiz         → record_family:'learning', record_type:'quiz'
│
└── Curriculum               → Relationship objects (relationship_type:'part_of')
                               traversed from programme record downward
```

### 9.2 Qualification Programme record — key fields

```js
Record {
  record_class:   "organizational",
  record_family:  "learning",
  record_type:    "programme",
  title:          "Certificate Programme",
  status:         "draft",
  permissions: {
    visibility:     "public",
    required_level: 0,
  },
  metadata: {
    source_app:              "learn",
    competence_level_target: 1,
    duration_years:          1,
    prerequisites:           [],
    qualification:           "Certificate"
  }
}
```

**Lesson Record — `scripture_reference` convention (v6):**
Lesson Records (`record_type:'lesson'`) MAY include a `scripture_reference` key
in `custom_fields` to indicate the primary Bible passage the lesson addresses:

```js
custom_fields: {
  scripture_reference: "JHN 3:16"
  // Format: "{BOOK_CODE} {chapter}:{verse}"
  // Range format: "ROM 8:1-4" (book chapter:start-end)
  // This is a convention enforced by the Learn App authorship form,
  // not a DB constraint. The Bible App queries this field to surface
  // lesson cross-references in the reader.
}
```

### 9.3 Qualification levels

| Competence Level | Qualification | Duration | Prerequisites                       |
|------------------|---------------|----------|-------------------------------------|
| Level 1          | Certificate   | 1 year   | None                                |
| Level 2          | Diploma       | 3 years  | Certificate                         |
| Level 3          | Degree        | 4 years  | Diploma + Certificate               |
| Level 4          | Masters       | 4–5 years| Degree + Diploma + Certificate      |
| Level 5          | Doctorate     | 7 years  | Masters + all prior                 |

### 9.4 KGS Pathway → Programme mapping

| Programme   | KGS Pathways                                                   |
|-------------|----------------------------------------------------------------|
| Certificate | new_life; community_life; learning                             |
| Diploma     | spiritual_formation; service; mission; learning                |
| Degree      | leadership; learning                                           |
| Masters     | leadership; apostolic_stewardship                              |
| Doctorate   | leadership; apostolic_stewardship                              |

### 9.5 Content authorship and review workflow

```
Level 4 user authors → status: "draft"
Level 4 user submits → status: "submitted" (visible to created_by + Level 5 only)
Level 5 approves     → status: "active"    (published)
Level 5 locks        → status: "locked"    (immutable; fork required for new version)
```

### 9.6 Enrolment — Activity Engine pattern

```
Programme Enrolment Activity (activity_type: "programme")
  │  assigned_to: user_id
  │  status: in_progress | progress: 0–100
  │  kgs_pathway: "learning"
  │  metadata.source_app: "learn"
  │  metadata.programme_record_id: "uuid"
  │
  ├── Course Activity (activity_type: "project")
  │     parent_activity_id: enrolment_activity.id
  │
  │     ├── Lesson Activity (activity_type: "task")
  │     ├── Assignment Activity (activity_type: "task", metadata.is_assessment: true)
  │     └── Quiz Activity (activity_type: "task", metadata.is_assessment: true)
  │
  └── [next Course Activity...]
```

**Progress roll-up:** Course progress = (completed tasks ÷ total) × 100.
Programme progress = average of all Course progress values.

### 9.7 Certification and competence level advancement

Auto-create draft Certification Record when Programme Activity hits 100%.

```js
Record {
  record_class:   "personal",
  record_family:  "learning",
  record_type:    "certification",
  status:         "draft",
  metadata: {
    source_app:             "learn",
    programme_record_id:    "uuid",
    enrolment_activity_id:  "uuid",
    target_level:           1
  }
}
```

Steward confirmation: `POST /api/learn/certifications/{id}/confirm/`
- Gated to `competence_level >= 3`
- Sets `certification.status = "active"`
- Increments `user.competence_level`
- Writes ActivityLog entry

`competence_level` is read-only everywhere except this endpoint.

### 9.8 Learn App endpoints

```
GET  /api/records/?record_family=learning&record_type=programme
GET  /api/records/?record_family=learning&record_type=course
GET  /api/records/{id}/
GET  /api/records/?status=submitted&record_family=learning
POST /api/activities/
PATCH /api/activities/{id}/
GET  /api/learn/health/
GET  /api/learn/programmes/{id}/curriculum/
GET  /api/learn/certifications/queue/
POST /api/learn/certifications/{id}/confirm/
```

---

## Part 10 — Activity App Engine (Data Patterns & Contracts)

*Unchanged from v5.*

### 10.1 Two-surface model

```
Activity App
  │
  ├── "My Activities" surface  (personal, tenant_id: null)
  │     Activity types: task, habit, goal, skill, reminder
  │     Visibility: created_by = request.user only
  │     Nesting: flat (no parent_activity_id)
  │     Includes: read-only programme activities (Learn enrolments)
  │
  └── "Ministry" surface  (tenant-scoped)
        Activity types: task, habit, event, campaign, project, reminder
        Visibility: assigned_to = request.user (assigned queue)
                    OR created_by = request.user AND tenant in user's tenants
                    OR tenant_id in user's tenants AND assigned_to null (team-visible)
        Nesting: two-level (campaign/project → task)
        Create rights: campaign/project = Level 3+ only; task = Level 1+
```

### 10.2 Activity type treatment in the UI

| Type       | Surface    | Create/Edit UI | Notes                                        |
|------------|------------|----------------|----------------------------------------------|
| `task`     | Both       | Full           | Personal (flat) or assigned (ministry)        |
| `habit`    | Both       | Full           | Recurrence always set                         |
| `goal`     | Personal   | Full           | Progress tracked manually                    |
| `event`    | Ministry   | Full           | scheduled_at required; renders in dated list  |
| `campaign` | Ministry   | Level 3+ create| KGS campaign structure container             |
| `project`  | Ministry   | Level 3+ create| Nested under campaign                        |
| `programme`| Personal   | Read-only      | Owned by Learn App; shown as progress card   |
| `reminder` | Both       | Create-only    | No dedicated view; Paraclete surfaces these  |
| `skill`    | Personal   | Gifts register | List + add; not task-like; see Part 4.1.1    |

### 10.3 Nesting rules

```
Level 1 (parent): campaign or project  — created by Level 3+, tenant-scoped
  └── Level 2 (child): task            — created by Level 1+, inherits tenant_id

Personal activities are always flat (parent_activity_id: null).

Learn App three-level hierarchy (programme → project → task) is produced by
the Learn App and rendered read-only in the Activity App personal surface.
The Activity App create form MUST NOT allow parent_activity_id to point to
a programme activity — this constraint is enforced in the DRF serializer.
```

### 10.4 Template activity pattern

```
Template Activity (metadata.is_template: true)
  tenant_id:    set (tenant-scoped templates only — no personal templates)
  created_by:   Level 4+ user
  status:       'active' when ready for use

Instantiation:
  New Activity
    ← all fields copied from template
    ← status:       'pending'
    ← assigned_to:  creating user OR steward-selected user
    ← is_template:  false
    ← template_id:  source template's id
    ← id:           new uuid
    ← created_by:   creating user
    ← created_at:   now
```

Templates are surfaced only in the "start from template" affordance on the
activity create form. Level 2+ users may instantiate. Level 4+ users may create.

### 10.5 Record linking pattern (Activity App)

When a user links a Record to an Activity from the Activity App:

1. The Activity App view calls `GET /api/records/?search={q}&tenant_id={tenant_id}`
   to populate the typeahead dropdown.
2. On form save, the view creates a `Relationship` object:
   - `from_record_id`: the Activity's corresponding Record (if one exists) or a
     system Record created to represent this Activity
   - `to_record_id`: the selected Record's id
   - `bible_verse_id`: null (Activity App never links directly to BibleVerse)
   - `relationship_type`: per the rules in Part 3.3 (based on activity_type)
   - `direction`: "directed"
   - `tenant_id`: matching the Activity's tenant_id

### 10.6 Ministry surface — "Assigned to me" queue

```
Query:
  Activity.objects.filter(
      assigned_to=request.user,
      tenant_id__isnull=False,
      status__in=['pending', 'in_progress']
  ).order_by('due_at')

Renders:
  - Grouped by campaign/project parent (if parent_activity_id set)
  - Flat tasks listed separately
  - Due today / overdue highlighted
  - HTMX status update buttons (mark in_progress, mark complete)
```

### 10.7 Activity App endpoints (Django — required)

```
GET    /api/activities/
POST   /api/activities/
GET    /api/activities/{id}/
PATCH  /api/activities/{id}/
DELETE /api/activities/{id}/

?assigned_to={user_id}
?due_today=true
?overdue=true
?activity_type={type}
?status={status}
?tenant_id={tenant_id}
?parent_activity_id={activity_id}
?metadata__source_app={app}
?surface=personal
?surface=ministry

GET    /api/activities/?metadata__is_template=true&tenant_id={id}
POST   /api/activities/{id}/instantiate/
GET    /api/calendar/events/?from={ISO}&to={ISO}&tenant_id={id}
```

---

## Part 11 — Calendar App Service Contract

*Unchanged from v5.*

### 11.1 Purpose

Multiple ICS apps need time-based views of platform data:
- Activity App: events and scheduled activities
- Dashboard: today's agenda
- Learn App: programme milestones and due dates (future)
- Community App: service dates and gatherings (future)
- Paraclete: upcoming activities for digest generation

### 11.2 Calendar event object

```js
CalendarEvent = {
  id:             "uuid",
  source_type:    "activity | record",
  source_app:     "activity | learn | governance | community",
  title:          "string",
  scheduled_at:   "ISO-8601 | null",
  due_at:         "ISO-8601 | null",
  activity_type:  "string | null",
  record_type:    "string | null",
  tenant_id:      "uuid | null",
  status:         "string",
  kgs_pillar:     "string | null",
  kgs_pathway:    "string | null"
}
```

### 11.3 Calendar endpoint

```
GET /api/calendar/events/
    ?from={ISO-8601-date}
    &to={ISO-8601-date}
    &tenant_id={uuid}
    &activity_type={type}
    &source_app={app}
```

Returns: `CalendarEvent[]` sorted by `scheduled_at` ascending, then `due_at`.

### 11.4 MVP scope and phasing

| Phase | What it builds |
|-------|----------------|
| MVP (built with Activity App) | Backend aggregation endpoint; queries Activity table only |
| Phase 2 (post-Learn App) | Add Record events (programme milestones, governance calendars) |
| Phase 3 (post-Community App) | Add Community events |
| Calendar UI | Full month/week grid view in Django templates + HTMX (Phase 2) |

### 11.5 Django app structure

```
~/ics/calendar/
  __init__.py
  apps.py
  views.py
  serializers.py
  urls.py
  service.py
  templates/
    calendar/
      (empty in MVP — grid view added in Phase 2)
```

---

## Part 12 — What to Build Next (Ordered)

*Updated in v6: Bible App system design marked complete.*

### Phase 3 — Activity App (Django app + templates)

See Activity App system design document (`2026-04-08-ics-activity-app-system-design.md`).

Build order within Phase 3:
1. `activity` Django app models verified + migration confirmed
2. DRF `ActivityViewSet` with all required filters (Part 10.7)
3. `ActivityLog` write-on-change signal
4. Template views: My Activities, Ministry surface, Assigned to Me queue
5. HTMX interactions: status update, progress update, create form
6. Record linking typeahead (HTMX)
7. Template activity instantiation endpoint + UI
8. `calendar` Django app backend (aggregation endpoint only — no UI in Phase 3)
9. Gifts register (skill type) — personal surface

### Phase 4 — Identity + Tenant JS services

*(Unchanged — these are UI state helpers, not app builds)*

### Phase 5 — Remaining apps

5.1 Bible App — system design complete (`2026-04-08-ics-bible-app-system-design_v2.md`)
    Data contract amendment applied in v6. Build after Bible app migrations confirmed.
5.2 Learn App — system design complete (`2026-04-07-ics-learn-app-system-design_v2.md`)
5.3 Activity App — system design complete (`2026-04-08-ics-activity-app-system-design.md`)
5.4 Community App
5.5 Governance App
5.6 Profile + Settings
5.7 Notifications stub

### Phase 6 — Paraclete Service

`paraclete/service.py` calls Django ORM directly using the Activity filters
defined in Part 5.4. Returns `ParacleteDigest` for Dashboard consumption.

### Phase 7 — Dashboard

Dashboard renders real `ParacleteDigest`. Shows pending activities, recent records,
active prayer count, discipline prompt. Role-aware and tenant-aware.

### Phase 8 — Calendar App Phase 2

Full calendar grid UI (month/week views) in Django templates + HTMX.
Records engine events added to aggregation endpoint.

### Phase 9 — Production Hardening

SSL, static files, logging, systemd Gunicorn service.

---

## Part 13 — Bible App Engine (Data Patterns & Contracts)

This section defines the data models, access rules, and integration patterns that
power the Bible App. The Bible App introduces the only platform models that are
exempt from the four mandatory fields rule (Part 1.1): `BibleTranslation`,
`BibleBook`, and `BibleVerse` are read-only reference data, not governed entities.

### 13.1 Bible data model

```python
BibleTranslation {
  id:                  uuid (PK)
  code:                string, unique     # 'KJV', 'ASV', 'WEB' ← metadata.shortname
  name:                string             # 'World English Bible' ← metadata.name
  language:            string             # 'en' ← metadata.lang_short
  language_full:       string             # 'English' ← metadata.lang
  year:                string | null      # '2006' ← metadata.year
  description:         text | null        # HTML ← metadata.description
  copyright_statement: text | null        # 'This Bible is in the Public Domain.' ← metadata.copyright_statement
  is_copyright:        boolean            # False = public domain ← metadata.copyright == 0
  is_public:           boolean            # True = unrestricted ← metadata.restrict == 0
  is_default:          boolean            # exactly one row True — KJV at setup
  created_at:          datetime
}

BibleBook {
  id:        integer (auto PK)
  code:      string, unique           # 'GEN', 'MAT', 'REV' — hardcoded via BOOK_CODE_MAP
  name:      string                   # 'Genesis' ← verses[].book_name
  testament: 'OT' | 'NT'             # hardcoded via TESTAMENT_MAP (not in JSON)
  order:     integer, unique          # 1–66 ← verses[].book (integer)
}
# BibleBook is translation-independent. 66 rows. Loaded once from first occurrence
# of each book integer in the flat verses array. testament and code are resolved
# from hardcoded lookup maps — the source JSON does not carry these fields.

BibleVerse {
  id:          uuid (PK)
  translation: FK → BibleTranslation
  book:        FK → BibleBook
  chapter:     integer                # ← verses[].chapter
  verse:       integer                # ← verses[].verse
  text:        string                 # ← verses[].text
  unique_together: (translation, book, chapter, verse)
}
# ~31,102 verses per translation (WEB confirmed). ~93,306 rows at setup (3 translations).
# Exact count varies slightly by translation due to variant text inclusion.
```

### 13.2 Translations loaded at setup

| Code | Name | Language | Copyright | Default | JSON structure |
|---|---|---|---|---|---|
| KJV | King James Version | English (en) | Public Domain | Yes | Flat `metadata` + `verses` |
| ASV | American Standard Version | English (en) | Public Domain | No | Flat `metadata` + `verses` |
| WEB | World English Bible | English (en) | Public Domain | No | Flat `metadata` + `verses` |

All three share the identical flat JSON structure. All three are public domain
(`metadata.copyright: 0`, `metadata.restrict: 0`). Licensed translations (NIV,
ESV, NLT) require publisher agreements — deferred post-MVP.

The single `load_bible` management command handles all three without modification.
`is_public` is derived from `metadata.restrict == 0`. `is_copyright` is derived
from `metadata.copyright == 0` (0 = public domain → `False`). Testament and
canonical short book code are resolved from hardcoded lookup maps in the command —
these fields are not present in the source JSON.

**Load command:**
```bash
python manage.py load_bible KJV --set-default
python manage.py load_bible ASV
python manage.py load_bible WEB
```

Data files (`bible/data/*.json`) are added to `.gitignore` if they exceed
GitHub's file size limits. The management command is committed; data is loaded
at deployment. Use `--file /path/to/file.json` to specify an alternate file path.

### 13.3 Bible note Record pattern

Personal notes and tenant notes on verses are stored as standard Records:

```js
// Personal bible note
Record {
  record_class:   "personal",
  record_family:  "bible",
  record_type:    "bible_note",
  title:          "John 3:16",              // auto-populated from verse reference
  content:        "string",                 // the user's note text
  status:         "active",
  tenant_id:      null,                     // personal notes are always platform-level
  metadata: {
    source_app: "bible"
  },
  custom_fields: {
    book_code: "JHN",                       // BibleBook.code
    chapter:   3,
    verse:     16,
  },
  permissions: {
    visibility:     "private",
    required_level: 1,
    roles_allowed:  [],
    can_edit:       []
  }
}

// Tenant (community) bible note — Level 3+ only
Record {
  record_class:   "organizational",
  record_family:  "bible",
  record_type:    "bible_note",
  title:          "John 3:16",
  content:        "string",                 // steward's teaching note
  status:         "active",
  tenant_id:      "uuid",                   // branch tenant id
  metadata: {
    source_app: "bible"
  },
  custom_fields: {
    book_code: "JHN",
    chapter:   3,
    verse:     16,
  },
  permissions: {
    visibility:     "tenant",              // visible to all branch members
    required_level: 1,
    roles_allowed:  [],
    can_edit:       []
  }
}
```

### 13.4 Seeker bible note limit

Seeker (Level 0b) users may create personal `bible_note` Records subject to the
platform-wide 10-record limit for all personal records. The `htmx_save_note` view
enforces this check:

```python
if user.userprofile.competence_level == 0:
    count = Record.objects.filter(
        record_class='personal',
        created_by=user,
        deleted_at__isnull=True
    ).count()
    if count >= 10:
        return render(request, 'bible/_note_limit_reached.html')
```

Note: the limit is 10 total personal Records across all apps, not 10 bible notes.
A Seeker who has 8 journal records can only create 2 bible notes before hitting
the limit.

### 13.5 Handbook ↔ scripture linkage pattern

Governance records authored in the Handbook may be linked to the specific Bible
verse(s) from which they derive authority. This uses the amended `Relationship`
object with `bible_verse_id` set:

```js
Relationship {
  from_record_id: "uuid",          // governance record id (principle, mandate, etc.)
  to_record_id:   null,            // null when bible_verse_id is set
  bible_verse_id: "uuid",          // BibleVerse.id
  relationship_type: "references",
  direction:      "directed",      // always directed: governance record → verse
  tenant_id:      null,            // Handbook records are platform-level
  created_by:     "uuid",          // Level 5 user only
}
```

**Read path (Bible App):** When a user taps a verse in the reader, the annotation
panel queries:

```python
Relationship.objects.filter(
    bible_verse=verse,
    relationship_type='references',
    deleted_at__isnull=True
).select_related('from_record')
```

Results are shown only to users with `competence_level >= 5`.

**Write path (Governance App):** The Governance App authorship UI (Phase 5.5)
will include a "Link to Scripture" affordance on governance record forms. This
is the only UI through which `bible_verse_id` Relationships are created. The
Bible App reader is read-only for Handbook references.

### 13.6 Learn App cross-reference convention

Lesson Records (`record_family:'learning'`, `record_type:'lesson'`) MAY carry a
`scripture_reference` key in `custom_fields`:

```js
custom_fields: {
  scripture_reference: "JHN 3:16"
  // Format: "{BOOK_CODE} {chapter}:{verse}"
  // Range: "ROM 8:1-4" ({BOOK_CODE} {chapter}:{start}-{end})
}
```

The Bible App reader surfaces matching lessons in the annotation panel by querying:

```python
Record.objects.filter(
    record_family='learning',
    record_type='lesson',
    status='active',
    custom_fields__scripture_reference__icontains=f"{verse.book.code} {verse.chapter}:{verse.verse}"
)
```

This is a convention, not a DB constraint. Enforced by the Learn App authorship
form. The link to the lesson in the annotation panel is gated to enrolment status —
non-enrolled users see the lesson title and "Enrol to access".

### 13.7 Bible App access rules by competence level

| Feature                        | Level 0b | Level 1+ | Level 3+ | Level 5  |
|--------------------------------|----------|----------|----------|----------|
| Read scripture (any translation)| ✓       | ✓        | ✓        | ✓        |
| Switch translation             | ✓        | ✓        | ✓        | ✓        |
| Create personal bible note     | ✓ (limit)| ✓        | ✓        | ✓        |
| Edit/delete own note           | ✓        | ✓        | ✓        | ✓        |
| See tenant (community) notes   | ✗        | ✓        | ✓        | ✓        |
| Publish tenant note            | ✗        | ✗        | ✓        | ✓        |
| See Learn cross-references     | ✗        | ✓        | ✓        | ✓        |
| See Handbook references        | ✗        | ✗        | ✗        | ✓        |

### 13.8 Bible App DRF endpoints

```
# Bible data (new — Bible App)
GET  /api/bible/health/
GET  /api/bible/translations/
GET  /api/bible/books/
GET  /api/bible/verses/?book_code={code}&chapter={n}
GET  /api/bible/verses/?book_code={code}&chapter={n}&translation_code={code}
GET  /api/bible/verse-context/{verse_id}/

# Bible template view routes
GET  /bible/
GET  /bible/{book_code}/{chapter}/

# HTMX partial routes
GET  /bible/htmx/chapter/
GET  /bible/htmx/annotation/{verse_id}/
POST /bible/htmx/note/save/
DELETE /bible/htmx/note/{note_id}/delete/
POST /bible/htmx/translation/set/

# Existing Records endpoints (verify filters work — no changes)
GET  /api/records/?record_family=bible&record_type=bible_note
GET  /api/records/?record_family=learning&record_type=lesson
     &custom_fields__scripture_reference__icontains={ref}

# Existing Relationship endpoint (amendment applied)
POST /api/relationships/            (with bible_verse_id in payload — Governance App)
GET  /api/relationships/?bible_verse_id={id}
```

---

## Deferred (Post-MVP)

**Platform-wide:**
- Full `RecordPermission` table (fine-grained per-user permissions)
- `CustomFieldSchema` formal validation system
- Video/Live streaming app
- In-service Display app
- Donations feature
- Advanced Paraclete AI features (pattern detection, auto-linking)
- Push notifications (mobile)
- `assigned_to_tenant_id` on Activity (collective/network assignment)
- Custom RRULE recurrence UI (Activity App — `recurrence:'custom'` + `recurrence_rule`)

**Learn App specific:**
- Rich text editor for lesson authorship
- Quiz auto-grading with score display
- Assignment peer review
- Paraclete "continue your lesson" integration
- Learning analytics dashboard
- Offline lesson caching
- Video lessons

**Calendar App specific:**
- Record events in aggregation (programme milestones, governance calendars)
- Community events
- iCal export
- Subscription feed for external calendar apps

**Activity App specific:**
- Full RRULE custom recurrence builder
- Activity analytics (completion rates, habit streaks dashboard)
- Bulk assignment (assign multiple tasks to multiple users in one action)
- Cross-tenant campaign templates (template visible across Church Collective network)

**Bible App specific:**
- Reading plans (personal Activity `activity_type:'habit'`, `kgs_pathway:'spiritual_formation'`)
- Verse highlights (colour-coded, no text — notes cover MVP use case)
- Scripture full-text search (`SearchVectorField` on `BibleVerse`)
- Licensed translations (NIV, ESV, NLT — publisher licensing required)
- African language translations (Zulu, Xhosa, Afrikaans — same load mechanism)
- Paraclete "You haven't read today" prompt (Phase 6 integration)
- Cross-reference chains (canonical verse-to-verse references)
- Audio Bible (deferred with Video/Live app)
- Relationship-engine-based Learn cross-references (upgrade from `custom_fields` convention)
