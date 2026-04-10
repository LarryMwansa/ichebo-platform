# ICS Platform — Data Contract & Architecture Document

> **Version:** v8 — 2026-04-08
> **Previous version:** v7 — 2026-04-08
>
> **v8 Amendments (Community App — pre-build):**
> 1. `record_family: "community"` formally defined (Part 3.1): types
>    `announcement` and `gathering` are MVP; `report` and `pastoral_note`
>    are deferred. Family → type mapping updated. Record type enum updated
>    to include `announcement` and `gathering`.
> 2. `UserPermission.metadata` added (Part 2.2): two optional fields —
>    `shepherd_id` (pastoral supervisor FK) and `service_order` (KGS service
>    order free-text label). No new model required.
> 3. `GatheringRecord` dual-write pattern documented (Part 14.4): creating a
>    gathering in the Community App writes both a `community/gathering` Record
>    and an `activity/event` Activity atomically. The Community App view is the
>    transaction coordinator.
> 4. `gathering` Record `custom_fields` specification added (Part 14.4): format,
>    location, stream_url, capacity. `format` enum: `in_person | digital | hybrid`.
>    `stream_url` is MVP placeholder for the Video App (deferred).
> 5. Calendar App Part 11.4 phasing updated: Community events now move from
>    "future" to Phase 3 (post-Community App build). `source_app: "community"`
>    is active in MVP via the gathering dual-write pattern.
> 6. Part 14 (Community App Engine) added: two-surface model, member directory
>    query patterns, announcement access rules, gathering dual-write, Video App
>    integration boundary, membership management rules, and DRF endpoint summary.
> 7. `MembershipRequest` model documented as deferred (Deferred section and
>    Part 14.8). Schema included so Django model can be stubbed in MVP.
> 8. Part 12 updated: Task 5.4 Community App marked as system design complete
>    (`2026-04-08-ics-community-app-system-design.md`). Community App deferred
>    items added to Deferred section.
>
> **Everything else in v7 is unchanged and remains locked.**

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

**v8 Amendment:** `metadata` field added carrying two optional Community App fields.
No migration required — `metadata` is a `JSONField` with `default=dict`.

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
  granted_by:   "uuid",

  // v8: Community App metadata (optional, JSONField default={})
  metadata: {
    shepherd_id:   "uuid | null",
    // user_id of the pastoral supervisor assigned to this member within this tenant.
    // Set by a steward (Level 3+) via the Community App member management interface.
    // Null = no pastoral assignment recorded yet.
    // Read by: Community App member profile view, "My Community" surface.

    service_order: "string | null"
    // Free-text KGS Service Order label (e.g. "Order of Pastoral Care").
    // Matches the 24 Orders defined in the KGS (Part VI of KGS framework document).
    // Not a FK — KGS Service Orders are not modelled as DB rows in MVP.
    // Set by a steward (Level 3+) via the Community App member management interface.
    // Read by: member directory, member profile, team gifts view (Activity App).
  }
}
```

**Indexing:** No new index required. `shepherd_id` lookups use
`UserPermission.objects.filter(metadata__shepherd_id=steward_id, tenant_path__startswith=scope_path)`
— acceptable at MVP member counts. Add `GinIndex` on `metadata` post-MVP if performance degrades.

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

**v8 Amendment:** `record_type` enum extended with `announcement` and `gathering`.
`community` family → type mapping formally defined (was placeholder comment).

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

  record_type:  "prayer | dream | note | sermon | class | principle | concept | divine_pattern | narrative | subject | entity | mandate | statement | programme | framework | protocol | procedure | calendar | event | campaign | project | habit | task | skill | course | lesson | assignment | quiz | certification | key | property | bible_note | announcement | gathering | custom",
  // Family → Type mapping (enforced at service layer):
  //   journal     → prayer | dream | note | sermon
  //   governance  → class | principle | concept | divine_pattern | narrative |
  //                 subject | entity | mandate | statement | programme |
  //                 framework | protocol | procedure | calendar
  //   activity    → event | campaign | project | habit | task | skill
  //   learning    → programme | course | lesson | assignment | quiz | certification
  //   reference   → key | property
  //   bible       → bible_note
  //   community   → announcement | gathering
  //                 (report | pastoral_note — deferred to Phase 2, schema in Part 14.8)
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
  // community/announcement: no required custom_fields
  // community/gathering: see Part 14.4 for custom_fields specification

  metadata: {
    source_app:    "records | bible | activity | learn | community | ...",
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

  from_record_id: "uuid",
  to_record_id:   "uuid | null",          // null only when bible_verse_id is set
  bible_verse_id: "uuid | null",          // FK → bible.BibleVerse; null except for scripture links

  // Constraint: exactly one of to_record_id or bible_verse_id must be non-null.
  // Enforced by: model .clean() + DRF serializer validation.

  direction: "directed | bidirectional",

  relationship_type: "relates_to | derived_from | references | answers | fulfills | requests | has_symbol | matches_pattern | assigned_to | tracks | completes | part_of | aligns_with | authorised_by | tagged_in",

  notes:    "string | null",
  strength: "weak | medium | strong | null",

  deleted_at: "ISO-8601 | null"
}
```

### 3.3 Controlled relationship type vocabulary

**Activity App usage (Part 10.6):**

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

**Community App usage (v8):**

| Community record type | Use relationship_type | Direction                               |
|-----------------------|-----------------------|-----------------------------------------|
| `gathering`           | `aligns_with`         | gathering_record → activity_event_record |

A `gathering` Record is always linked to its corresponding `event` Activity via
`aligns_with` — this is written atomically by the Community App dual-write transaction.
See Part 14.4 for the full dual-write pattern.

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
  //             NOTE: gathering Activities created via Community App carry
  //             metadata.source_app:'community' to distinguish origin
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
  recurrence_rule:"string | null",

  // Hierarchy
  parent_activity_id: "uuid | null",

  // Progress
  status:   "pending | in_progress | completed | cancelled | deferred",
  progress: 0,

  // Assignment
  assigned_to: "uuid | null",

  // KGS alignment
  kgs_pillar:   "apostolic | strategy | formation | programmes | mission | communities | stewardship | null",
  kgs_pathway:  "new_life | spiritual_formation | community_life | service | leadership | learning | mission | apostolic_stewardship | null",

  // Metadata
  metadata: {
    source_app:   "activity | paraclete | learn | governance | community",
    // source_app:'community' = this event Activity was created by the Community App
    // dual-write (gathering create). Allows Activity App to filter out community-
    // owned events from its "Ministry events" list, or surface them distinctly.
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

*(Unchanged from v5)*

| Field          | Usage for `skill` type                                              |
|----------------|---------------------------------------------------------------------|
| `title`        | Name of the gift or skill (e.g. "Teaching", "Administration")       |
| `description`  | How this gift manifests in the user's life and ministry             |
| `progress`     | Self-assessed competence: 0–100 (maps loosely to KGS levels 1–5 × 20) |
| `kgs_pathway`  | Which Kingdom Pathway this gift primarily serves                    |
| `metadata.service_order` | KGS Service Order this gift aligns with (optional)       |
| `status`       | `active` = current gift; `archived` = no longer active/relevant     |
| `tenant_id`    | Null = personal register; tenant-scoped = visible to steward        |

### 4.2 ActivityLog object

*(Unchanged from v5)*

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

### 4.3 Activity assignment model

*(Unchanged from v5)*

| Who                   | Can assign to                          | Constraint                         |
|-----------------------|----------------------------------------|------------------------------------|
| Level 1–2 (personal)  | Self only (`assigned_to = created_by`) | Personal activities only           |
| Level 3+ (steward)    | Any user within their `scope_path`     | `activity.tenant_id` must be within assigning user's `UserPermission.tenant_path` |
| Level 3+ (steward)    | `assigned_to = null` (team-visible)    | For campaign/project containers    |

---

## Part 5 — Paraclete Service Contract

*(Unchanged from v5)*

The Paraclete is a standalone orchestration service. It does NOT own any data.
It reads from other engines and produces suggestions, reminders, and insights.
It never writes directly to Records or Activities — it calls their services.

### 5.1 What Paraclete is responsible for

- Reading user's activities, records, and schedules to generate intelligent reminders
- Detecting patterns across records (recurring dream symbols, prayer themes, habit streaks)
- Producing "today's focus" digest based on user's competence level, active activities,
  and KGS calendar
- Surfacing record link suggestions based on content similarity
- Generating discipline prompts aligned to the user's KGS pathway

### 5.2 What Paraclete is NOT responsible for

- Storing any data (reads only — no writes)
- Displaying UI (the Dashboard and Activity App consume its output)
- Authentication or permission enforcement (it inherits the calling user's context)

### 5.3 ParacleteDigest object

```js
ParacleteDigest = {
  user_id:         "uuid",
  generated_at:    "ISO-8601",
  pending_tasks:   Activity[],      // due today or overdue, assigned_to = user
  upcoming_events: CalendarEvent[], // next 7 days
  habit_streaks:   { activity_id: uuid, streak_days: integer }[],
  discipline_prompt: "string | null",
  link_suggestions:  { record_id: uuid, suggested_record_id: uuid, reason: string }[],
  active_reminders:  Activity[]     // activity_type:'reminder', status:'pending'
}
```

### 5.4 Paraclete filter contracts (Activity Engine filters required)

```
GET /api/activities/?assigned_to={user_id}&due_today=true
GET /api/activities/?assigned_to={user_id}&overdue=true
GET /api/activities/?activity_type=habit&status=in_progress&created_by={user_id}
GET /api/activities/?activity_type=reminder&status=pending&created_by={user_id}
GET /api/activities/?tenant_id={id}&status=pending
```

---

## Part 6 — Django App Structure & File Map

### 6.1 Django apps (canonical list)

```
~/ics/
  ics_project/          ← Django project settings + root URLs
  accounts/             ← User, UserProfile, UserPermission models + auth
  tenants/              ← Tenant model + path resolution
  records/              ← Record + Relationship models (Records Engine)
  activity/             ← Activity + ActivityLog models (Activity Engine)
  learn/                ← CertificationConfirmation model + curriculum endpoint
  bible/                ← BibleTranslation, BibleBook, BibleVerse models
  community/            ← Community App (v8 — NEW Django app)
  calendar_app/         ← Calendar aggregation service (no models)
  paraclete/            ← Orchestration service (no models)
  frontend/             ← Static assets (CSS, storage.js)
```

### 6.2 App ownership rules (cross-app dependency policy)

| Model              | Owner app   | Other apps may...                              |
|--------------------|-------------|------------------------------------------------|
| Record             | records     | read via DRF only                              |
| Relationship       | records     | read/write via DRF only; FK dep on bible.BibleVerse |
| Activity           | activity    | read via DRF; Community App creates via DRF    |
| ActivityLog        | activity    | read via DRF only                              |
| UserPermission     | accounts    | read/write via DRF; Community App writes metadata fields |
| BibleVerse         | bible       | read via DRF; referenced by Relationship FK    |
| BibleTranslation   | bible       | read via DRF; FK dep in accounts.UserProfile   |
| Tenant             | tenants     | read via DRF only                              |

**Community App owns no models.** It is a UI + coordination layer that writes to
Records, Activity, and UserPermission via their respective DRF endpoints.

---

## Part 7 — Permission Check Algorithm

*(Unchanged from v3)*

```python
def can_access(user, record):
    # 1. Handbook short-circuit
    if record.tenant.tier == 'handbook':
        return user.competence_level >= 5

    # 2. record_class gate (check FIRST before anything else)
    if record.record_class == 'governance' and user.competence_level < 4:
        return False

    # 3. Visibility scope
    if record.permissions.visibility == 'private':
        return record.created_by == user.id

    if record.permissions.visibility == 'tenant':
        return UserPermission.objects.filter(
            user=user,
            tenant_path=record.tenant.path,
            is_active=True
        ).exists()

    if record.permissions.visibility == 'collective':
        return UserPermission.objects.filter(
            user=user,
            tenant_path__startswith=record.tenant.collective_root_path,
            is_active=True
        ).exists()

    if record.permissions.visibility == 'public':
        return user.competence_level >= 1  # Level 0b cannot see public org records

    # 4. Level gate
    if user.competence_level < record.permissions.required_level:
        return False

    return True
```

---

## Part 8 — Indexing Strategy

### 8.1 Records table indexes

```sql
CREATE INDEX idx_records_tenant_id ON records(tenant_id);
CREATE INDEX idx_records_record_class ON records(record_class);
CREATE INDEX idx_records_record_family ON records(record_family);
CREATE INDEX idx_records_record_type ON records(record_type);
CREATE INDEX idx_records_created_by ON records(created_by);
CREATE INDEX idx_records_status ON records(status);
CREATE INDEX idx_records_deleted_at ON records(deleted_at);
CREATE INDEX idx_records_custom_fields ON records USING gin(custom_fields);
```

### 8.2 Activity table indexes

```sql
CREATE INDEX idx_activity_tenant_id ON activity(tenant_id);
CREATE INDEX idx_activity_activity_type ON activity(activity_type);
CREATE INDEX idx_activity_assigned_to ON activity(assigned_to);
CREATE INDEX idx_activity_status ON activity(status);
CREATE INDEX idx_activity_due_at ON activity(due_at);
CREATE INDEX idx_activity_scheduled_at ON activity(scheduled_at);
CREATE INDEX idx_activity_parent_id ON activity(parent_activity_id);
CREATE INDEX idx_activity_deleted_at ON activity(deleted_at);
CREATE INDEX idx_activity_metadata ON activity USING gin(metadata);
```

### 8.3 Relationship table indexes

```sql
CREATE INDEX idx_rel_from_record ON relationship(from_record_id);
CREATE INDEX idx_rel_to_record ON relationship(to_record_id);
CREATE INDEX idx_rel_bible_verse ON relationship(bible_verse_id);  -- v6
CREATE INDEX idx_rel_type ON relationship(relationship_type);
CREATE INDEX idx_rel_deleted_at ON relationship(deleted_at);
```

### 8.4 UserPermission table indexes

```sql
CREATE INDEX idx_perm_user_id ON user_permission(user_id);
CREATE INDEX idx_perm_tenant_path ON user_permission(tenant_path varchar_pattern_ops);
CREATE INDEX idx_perm_is_active ON user_permission(is_active);
```

**Note (v8):** `UserPermission.metadata` is a JSONField. `shepherd_id` and
`service_order` queries are infrequent (steward-level, not hot paths). No GinIndex
added in MVP. Add post-MVP if query times degrade.

---

## Part 9 — Cross-App Data Patterns

### 9.1 Record + Activity dual write

When the platform needs both a persistent Record and an active Activity for the same
thing (e.g., a learning programme creates a Record for the content and an Activity
for tracking enrolment progress), the convention is:

1. The orchestrating app creates the Record first (POST /api/records/)
2. Then creates the Activity with a Relationship linking the two (POST /api/activities/ + POST /api/relationships/)
3. If either step fails, the view rolls back both (Django transaction.atomic)

This pattern is used by: Learn App (programme enrolment), Community App (gathering
create — see Part 14.4).

### 9.2 Learn App: scripture_reference convention

Lesson Records (`record_family:'learning'`, `record_type:'lesson'`) MAY carry a
`scripture_reference` key in `custom_fields`:

```js
custom_fields: {
  scripture_reference: "JHN 3:16"
  // Format: "{BOOK_CODE} {chapter}:{verse}"
  // Range: "ROM 8:1-4" ({BOOK_CODE} {chapter}:{start}-{end})
}
```

Enforced by the Learn App authorship form. Used by the Bible App annotation panel.

---

## Part 10 — Activity App Engine (Data Patterns & Contracts)

*(Unchanged from v5)*

### 10.1 Purpose

The Activity App is the operational execution layer of the KGS. It enables:
- Members to manage personal disciplines (tasks, habits, goals, reminders, skills)
- Stewards to coordinate team campaigns and projects
- The platform to feed Paraclete with rich activity data

### 10.2 Two-surface model

```
Activity App
  │
  ├── "My Activities"  (personal surface)
  │     Scope:  tenant_id: null, created_by = request.user
  │     Types:  task, habit, goal, skill, reminder
  │     Also:   read-only programme cards (Learn enrolments)
  │     Nesting: flat only
  │
  └── "Ministry"  (organisational surface)
        Scope:  tenant_id in user's tenants
        Types:  task, habit, event, campaign, project, reminder
        Includes: "Assigned to me" queue — first-class tab
        Nesting: two-level (campaign/project → task)
        Create: campaign/project = Level 3+; task = Level 1+
```

### 10.3 Nesting rules

- Campaign → Project → Task: three-level supported in data; two-level exposed in Activity App UI
- Personal activities: flat only (no nesting)
- A Task may have at most one parent (campaign or project)
- Campaigns have no parent_activity_id (they are top-level)

### 10.4 Assignment model

*(See Part 4.3)*

### 10.5 Template pattern

```js
// Template activity (created by Level 4+)
Activity {
  metadata: { is_template: true, template_id: null }
  status: "pending"
  assigned_to: null
}

// Instance created from template (any Level 2+ user)
Activity {
  metadata: { is_template: false, template_id: "{source_template_id}" }
  // All other fields copied from template except:
  // status → 'pending', assigned_to → creating user or selected
}
```

### 10.6 Relationship type rules for Activity App

*(See Part 3.3)*

### 10.7 Required API filters

```
GET /api/activities/?assigned_to={user_id}
GET /api/activities/?due_today=true
GET /api/activities/?overdue=true
GET /api/activities/?activity_type={type}
GET /api/activities/?status={status}
GET /api/activities/?tenant_id={tenant_id}
GET /api/activities/?parent_activity_id={activity_id}
GET /api/activities/?metadata__source_app={app}
GET /api/activities/?surface=personal
GET /api/activities/?surface=ministry
GET /api/activities/?metadata__is_template=true&tenant_id={id}
```

---

## Part 11 — Calendar App Service Contract

*(Updated in v8: Community events phase clarified)*

### 11.1 Purpose

Multiple ICS apps need time-based views of platform data:
- Activity App: events and scheduled activities
- Dashboard: today's agenda
- Learn App: programme milestones and due dates (future)
- Community App: gathering events — **active in MVP via dual-write**
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

**Community events in Calendar (v8):** Gathering events are `activity_type:'event'`
Activities with `metadata.source_app:'community'`. The Calendar endpoint already
queries the Activity table — community gatherings appear automatically once the
Community App creates them via the dual-write pattern (Part 14.4). No Calendar App
changes required to surface community events.

Filtering for community gatherings specifically:
```
GET /api/calendar/events/?source_app=community
```

### 11.4 MVP scope and phasing

| Phase | What it builds |
|-------|----------------|
| MVP (built with Activity App) | Backend aggregation endpoint; queries Activity table only |
| Phase 2 (post-Community App — v8) | Community events active via `metadata.source_app:'community'`; no code change required |
| Phase 3 (post-Learn App) | Add Record events (programme milestones, governance calendars) |
| Calendar UI | Full month/week grid view in Django templates + HTMX (Phase 3) |

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
      (empty in MVP — grid view added in Phase 3)
```

---

## Part 12 — What to Build Next (Ordered)

*Updated in v8: Community App system design marked complete.*

### Phase 3 — Activity App (Django app + templates)

See Activity App system design document (`2026-04-08-ics-activity-app-system-design.md`).

### Phase 4 — Identity + Tenant JS services

*(Unchanged)*

### Phase 5 — Remaining apps

5.1 Bible App — system design complete (`2026-04-08-ics-bible-app-system-design_v2.md`)
5.2 Learn App — system design complete (`2026-04-07-ics-learn-app-system-design_v2.md`)
5.3 Activity App — system design complete (`2026-04-08-ics-activity-app-system-design.md`)
5.4 Community App — system design complete (`2026-04-08-ics-community-app-system-design.md`)
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

*(Unchanged from v7)*

### 13.1 Bible data model

```python
BibleTranslation {
  id:                  uuid (PK)
  code:                string, unique     # 'KJV', 'ASV', 'WEB'
  name:                string
  language:            string
  language_full:       string
  year:                string | null
  description:         text | null
  copyright_statement: text | null
  is_copyright:        boolean
  is_public:           boolean
  is_default:          boolean
  created_at:          datetime
}

BibleBook {
  id:        integer (auto PK)
  code:      string, unique
  name:      string
  testament: 'OT' | 'NT'
  order:     integer, unique
}

BibleVerse {
  id:          uuid (PK)
  translation: FK → BibleTranslation
  book:        FK → BibleBook
  chapter:     integer
  verse:       integer
  text:        string
  unique_together: (translation, book, chapter, verse)
}
```

### 13.2 Translations loaded at setup

| Code | Name | Language | Copyright | Default |
|---|---|---|---|---|
| KJV | King James Version | English (en) | Public Domain | Yes |
| ASV | American Standard Version | English (en) | Public Domain | No |
| WEB | World English Bible | English (en) | Public Domain | No |

### 13.3 Bible note Record pattern

*(Unchanged from v7 — see v7 for full pattern)*

### 13.4 Seeker bible note limit

*(Unchanged from v7)*

### 13.5 Handbook ↔ scripture linkage pattern

*(Unchanged from v7)*

### 13.6 Learn App cross-reference convention

*(Unchanged from v7 — see Part 9.2)*

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
GET  /api/bible/health/
GET  /api/bible/translations/
GET  /api/bible/books/
GET  /api/bible/verses/?book_code={code}&chapter={n}
GET  /api/bible/verses/?book_code={code}&chapter={n}&translation_code={code}
GET  /api/bible/verse-context/{verse_id}/

GET  /bible/
GET  /bible/{book_code}/{chapter}/

GET  /bible/htmx/chapter/
GET  /bible/htmx/annotation/{verse_id}/
POST /bible/htmx/note/save/
DELETE /bible/htmx/note/{note_id}/delete/
POST /bible/htmx/translation/set/

GET  /api/records/?record_family=bible&record_type=bible_note
GET  /api/records/?record_family=learning&record_type=lesson
     &custom_fields__scripture_reference__icontains={ref}

POST /api/relationships/
GET  /api/relationships/?bible_verse_id={id}
```

---

## Part 14 — Community App Engine (Data Patterns & Contracts)

This section defines the data patterns, access rules, and integration contracts
that power the Community App. The Community App owns **no models**. It is a UI and
transaction coordination layer that writes to Records, Activity, and UserPermission
via their respective DRF endpoints.

### 14.1 Purpose

The Community App is the digital expression of KGS Pillar 6 — Communities & Networks.
Its purpose is to make the life of a Sceptre Community (church node) visible and
manageable on the platform, serving two audiences:

- **Members** — see their community, their formation journey, upcoming gatherings,
  and announcements from their leadership
- **Stewards (Level 3+)** — manage their community membership, post announcements,
  create gatherings, and view the formation pipeline of those in their care

The Community App is the primary surface for the KGS Kingdom Participation Model
(Connection → Formation → Alignment → Service → Leadership).

### 14.2 Two-surface model

```
Community App
  │
  ├── "My Community"  (member surface — Level 1+)
  │     What it shows:
  │       - Member's active tenant(s): name, tier, description
  │       - Their formation stage (competence_level mapped to KGS Participation Model)
  │       - Their service order placement (UserPermission.metadata.service_order)
  │       - Their shepherd (UserPermission.metadata.shepherd_id → display_name)
  │       - Upcoming gatherings (next 30 days) from Calendar endpoint
  │       - Latest announcements (community Records, visibility:'tenant')
  │       - Read-only view of gifts register summary (links to Activity App)
  │     Scope: UserPermission rows where user_id = request.user, is_active = True
  │
  └── "Community Management"  (steward surface — Level 3+)
        What it shows:
          - Member directory: all UserPermission rows in steward's scope_path
          - Formation pipeline: members grouped by competence_level
          - Member profile: detail view of any member within scope
          - Announcement management: create, view, archive
          - Gathering management: create, view, cancel
          - Pastoral assignments: set shepherd_id on member's UserPermission
          - Service order placement: set service_order on member's UserPermission
        Scope: UserPermission.tenant_path LIKE '{steward.scope_path}%'
```

### 14.3 Community Record types (MVP)

#### announcement

A broadcast message from a steward to their community members.

```js
Record {
  record_class:   "organizational",
  record_family:  "community",
  record_type:    "announcement",
  title:          "string",            // e.g. "Sunday Service Change"
  content:        "string",            // announcement body (markdown)
  status:         "active | archived",
  tenant_id:      "uuid",              // always tenant-scoped
  created_by:     "uuid",              // must be Level 3+ (steward)
  metadata: {
    source_app: "community"
  },
  permissions: {
    visibility:     "tenant",          // all members of this tenant see it
    required_level: 1,
    roles_allowed:  [],
    can_edit:       []
  }
}
```

**Access rules:**
- Create: Level 3+ only (steward)
- Read: Level 1+ within the tenant (visibility:'tenant')
- Edit/archive: creating steward or Level 4+ above them in scope_path
- Delete (soft): creating steward only

#### gathering

A scheduled community event — a service, cell meeting, prayer session, or any
organised gathering (physical, digital, or hybrid).

```js
Record {
  record_class:   "organizational",
  record_family:  "community",
  record_type:    "gathering",
  title:          "string",            // e.g. "Sunday Morning Service"
  content:        "string | null",     // agenda / description
  status:         "active | completed | cancelled",
  tenant_id:      "uuid",
  created_by:     "uuid",              // must be Level 3+ (steward)
  metadata: {
    source_app: "community"
  },
  custom_fields: {
    // Format of the gathering
    format:      "in_person | digital | hybrid",

    // Physical location (used when format is 'in_person' or 'hybrid')
    location:    "string | null",      // free-text address or venue name

    // Stream URL (used when format is 'digital' or 'hybrid')
    // MVP: external URL only (YouTube Live, Zoom, Google Meet, etc.)
    // Video App integration: when the Video App is built, it will own native
    // streaming. The Community App gathering will carry stream_url as a link
    // to the Video App's stream record. No change to this field — the URL
    // will simply point to an internal ICS Video App URL instead of external.
    stream_url:  "string | null",

    // Capacity (optional — for physical or hybrid gatherings)
    capacity:    "integer | null",

    // Scheduled date and time — also stored on the linked Activity (see 14.4)
    // Stored here for denormalisation convenience on the gathering detail view.
    // Source of truth for scheduling is Activity.scheduled_at.
    scheduled_at: "ISO-8601 | null",
  },
  permissions: {
    visibility:     "tenant",
    required_level: 1,
    roles_allowed:  [],
    can_edit:       []
  }
}
```

**Access rules:**
- Create: Level 3+ only
- Read: Level 1+ within the tenant
- Edit: creating steward or Level 4+ within scope
- Cancel: creating steward or Level 4+ within scope (sets status:'cancelled', also sets linked Activity.status:'cancelled')

### 14.4 Gathering dual-write pattern

Creating a gathering in the Community App produces two objects atomically and
links them with a Relationship. This is the same pattern as the Learn App's
programme enrolment. Both writes must succeed or both must fail.

```python
# Community App Django view — create_gathering (Level 3+)
# Wrapped in transaction.atomic()

# Step 1 — Create the gathering Record
record_response = requests.post('/api/records/', json={
    'record_class': 'organizational',
    'record_family': 'community',
    'record_type':   'gathering',
    'title':         form.cleaned_data['title'],
    'content':       form.cleaned_data['description'],
    'tenant_id':     tenant.id,
    'status':        'active',
    'metadata':      {'source_app': 'community'},
    'custom_fields': {
        'format':       form.cleaned_data['format'],
        'location':     form.cleaned_data.get('location'),
        'stream_url':   form.cleaned_data.get('stream_url'),
        'capacity':     form.cleaned_data.get('capacity'),
        'scheduled_at': form.cleaned_data['scheduled_at'],
    },
    'permissions': {'visibility': 'tenant', 'required_level': 1}
})

# Step 2 — Create the event Activity (feeds Calendar App)
activity_response = requests.post('/api/activities/', json={
    'activity_type':  'event',
    'title':          form.cleaned_data['title'],
    'description':    form.cleaned_data.get('description'),
    'scheduled_at':   form.cleaned_data['scheduled_at'],
    'tenant_id':      tenant.id,
    'kgs_pillar':     'communities',
    'kgs_pathway':    'community_life',
    'status':         'pending',
    'metadata':       {'source_app': 'community'},
})

# Step 3 — Link Record → Activity
relationship_response = requests.post('/api/relationships/', json={
    'from_record_id':    record_response['id'],
    'to_record_id':      activity_response['id'],
    'relationship_type': 'aligns_with',
    'direction':         'directed',
    'tenant_id':         tenant.id,
})
```

**Cancellation:** When a steward cancels a gathering, the Community App view:
1. PATCHes the Record: `status → 'cancelled'`
2. PATCHes the Activity: `status → 'cancelled'`

Both in `transaction.atomic()`. The Calendar endpoint will then exclude cancelled
Activities automatically (filter `status != 'cancelled'` on the Activity query).

**Video App integration boundary:** When the Video App is built (post-MVP), it
will introduce a native streaming record type. The Community App gathering creation
form will gain a "Use ICS Live Stream" toggle that sets `stream_url` to the Video
App's stream endpoint. No changes to the data contract are required at that time —
`stream_url` is already present as a string field.

### 14.5 Member directory query pattern

The member directory is built from `UserPermission` rows scoped to the steward's
authority path.

```python
# Member directory — all active members within steward's scope
members = UserPermission.objects.filter(
    tenant_path__startswith=steward_scope_path,
    is_active=True
).select_related('user').order_by('user__display_name')

# Formation pipeline — grouped by competence_level
pipeline = members.values('user__competence_level').annotate(count=Count('id'))

# Pastoral flock — members assigned to a specific shepherd
flock = UserPermission.objects.filter(
    metadata__shepherd_id=steward.id,
    tenant_path__startswith=steward_scope_path,
    is_active=True
).select_related('user')

# Members in a specific service order
order_members = UserPermission.objects.filter(
    metadata__service_order="Order of Pastoral Care",
    tenant_path__startswith=steward_scope_path,
    is_active=True
).select_related('user')
```

### 14.6 Membership management rules (MVP — steward-initiated only)

In MVP, all membership actions are steward-initiated. Self-service join requests
are deferred (see Part 14.8).

**Adding a member:**
1. Steward selects an existing platform user (Level 1+ with `status:'active'`)
2. Community App view calls `POST /api/permissions/` with:
   ```js
   { user_id, tenant_id, tenant_path, role, level, is_active: true,
     granted_by: steward.id }
   ```
3. The `UserPermission` row is created; the user now has tenant membership

**Removing a member:**
- Soft deactivation only: PATCH `/api/permissions/{id}/` → `is_active: false`
- The `UserPermission` row is retained for audit purposes
- Hard deletion is prohibited at DRF layer (no DELETE on UserPermission)

**Setting pastoral assignment:**
```python
PATCH /api/permissions/{permission_id}/
{ "metadata": { "shepherd_id": steward_user_id } }
```

**Setting service order:**
```python
PATCH /api/permissions/{permission_id}/
{ "metadata": { "service_order": "Order of Community Building" } }
```

**Induction requirement (deferred):** The full join flow — requiring a Seeker to
complete induction training before being added to a community — depends on the
Learn App's certification flow. This integration is post-MVP. In MVP, stewards
manually verify induction status before adding a member.

### 14.7 Community App access rules

| Level | My Community surface | Community Management surface |
|-------|---------------------|------------------------------|
| Seeker (0b) | ✗ No tenant membership | ✗ |
| Member (1) | ✓ Own tenants only | ✗ |
| Disciple (2) | ✓ Own tenants + limited directory (names only) | ✗ |
| Branch-Steward (3) | ✓ Full | ✓ Own branch: full directory, announcements, gatherings, assignments |
| Senior Steward (4+) | ✓ Full | ✓ Scope: district/province/national depending on role — multi-branch |
| Architect (5) | ✓ Full | ✓ Cross-tenant visibility; all communities in scope |

**Level 2 limited directory:** Disciples may view the member directory for their own
tenant with display names and service orders only. `shepherd_id`, email, and formation
detail are hidden — Level 3+ only.

### 14.8 Deferred: MembershipRequest model (stub)

The `MembershipRequest` model is deferred to Phase 2 of the Community App.
The schema is documented here so the Django model can be stubbed with a migration
at MVP time and activated without a migration change in Phase 2.

```python
# community/models.py — stubbed, not wired to UI in MVP
class MembershipRequest(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant_id    = models.UUIDField()
    created_by   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                     related_name='membership_requests')
    created_at   = models.DateTimeField(auto_now_add=True)

    user         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                     related_name='requests_made')
    tenant       = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    status       = models.CharField(max_length=20,
                                    choices=[('pending','Pending'),
                                             ('approved','Approved'),
                                             ('denied','Denied')],
                                    default='pending')
    reviewed_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='requests_reviewed')
    reviewed_at  = models.DateTimeField(null=True, blank=True)
    note         = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'community_membership_request'
```

**Phase 2 activation** adds: the self-service join request UI, the steward approval
queue, the induction-training gate (Learn App integration), and the auto-create
`UserPermission` on approval.

### 14.9 Deferred: report and pastoral_note record types

These types are pre-registered in the `community` family but not built in MVP.

**report** — a structured community health or activity report, authored by a steward,
visibility:'collective' or 'tenant'. `record_class:'organizational'`, Level 3+.

**pastoral_note** — a confidential note by a steward about a specific member's
formation journey. `record_class:'personal'` (despite being steward-authored),
`permissions.visibility:'private'`. Requires careful UI design around privacy —
deferred to Phase 2.

### 14.10 Community App DRF endpoints

The Community App uses existing platform endpoints. No new DRF ViewSets are
introduced unless the app warrants a dedicated endpoint for convenience.

```
# Existing endpoints consumed by Community App

# Member directory
GET  /api/permissions/?tenant_path__startswith={scope}&is_active=true

# Membership management
POST   /api/permissions/                    create UserPermission (add member)
PATCH  /api/permissions/{id}/              update (set shepherd_id, service_order, is_active)

# Announcements and gatherings
GET    /api/records/?record_family=community&record_type=announcement&tenant_id={id}
POST   /api/records/                        create announcement or gathering Record
PATCH  /api/records/{id}/                   edit / archive / cancel Record
GET    /api/records/?record_family=community&record_type=gathering&tenant_id={id}

# Activities (gathering dual-write)
POST   /api/activities/                     create event Activity for gathering
PATCH  /api/activities/{id}/               cancel gathering's linked Activity

# Relationships (gathering link)
POST   /api/relationships/                  link gathering Record → event Activity

# Upcoming gatherings (Calendar endpoint)
GET    /api/calendar/events/?source_app=community&tenant_id={id}&from={ISO}&to={ISO}

# Member gifts register (cross-app read — Activity App endpoint)
GET    /api/activities/?activity_type=skill&tenant_id={id}&created_by={member_id}

# New Community App convenience endpoints (Django template views — not DRF)
GET    /community/                          My Community surface
GET    /community/management/              Community Management surface (Level 3+)
GET    /community/management/members/      Member directory
GET    /community/management/members/{id}/ Member profile detail
GET    /community/management/pipeline/     Formation pipeline view
POST   /community/htmx/announcement/create/ HTMX announcement create
POST   /community/htmx/gathering/create/    HTMX gathering create (dual-write)
POST   /community/htmx/member/shepherd/    HTMX set shepherd assignment
POST   /community/htmx/member/order/       HTMX set service order
GET    /community/htmx/announcements/      HTMX announcement list partial
GET    /api/community/health/              Health check
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
- Custom RRULE recurrence UI (Activity App)

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
- iCal export
- Subscription feed for external calendar apps

**Activity App specific:**
- Full RRULE custom recurrence builder
- Activity analytics (completion rates, habit streaks dashboard)
- Bulk assignment
- Cross-tenant campaign templates

**Bible App specific:**
- Reading plans
- Verse highlights
- Scripture full-text search
- Licensed translations (NIV, ESV, NLT)
- African language translations
- Paraclete "You haven't read today" prompt
- Cross-reference chains
- Audio Bible

**Community App specific:**
- `MembershipRequest` model — self-service join request flow (schema in Part 14.8)
- Induction training gate (Learn App integration before member is added)
- `report` record type — community health/activity reports (schema stub in Part 14.9)
- `pastoral_note` record type — confidential steward notes on members (Part 14.9)
- Attendance tracking (`AttendanceLog` model — deferred; privacy-sensitive)
- `PastoralAssignment` model (upgrade from `UserPermission.metadata.shepherd_id`)
- GinIndex on `UserPermission.metadata` (add if query performance degrades)
- Community analytics dashboard (formation pipeline trends, service order coverage)
- Collective-level gathering visibility (across Church Collective network)
- Notifications on new announcements (Notifications App stub — Phase 5.7)
