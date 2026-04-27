# ICS Platform — Data Contract & Architecture Document

> **Version:** v9 — 2026-04-10
> **Previous version:** v8 — 2026-04-08
>
> **v9 Amendments (Governance App — pre-build):**
> 1. `record_type` enum: `"article"` added to journal family (Part 3.1) — **superseded by MVP amendment below**.
> 2. `journal` family → type mapping updated to include `"article"` (Part 3.1) — **superseded by MVP amendment below**.
> 3. `governance` family: `"calendar"` type marked deferred (Part 3.1 note).
> 4. Handbook read access rule amended: Level 4+ read, Level 5 write (Part 2.5.2).
> 5. Property Attributes `custom_fields` specification added (Part 15.3).
> 6. Governance record lifecycle defined: `draft → active → locked → superseded` (Part 15.4).
> 7. Governance App record type authority matrix added (Part 15.5).
> 8. Part 15 (Governance App Engine) added — three-surface model, branch structure, HRS relationship viewer, Keys Library surface, DRF endpoints.
> 9. Part 12 updated: Task 5.5 Governance App marked as system design complete (`2026-04-10-ics-governance-app-system-design.docx`).
>
> **v8 Amendments (Community App — pre-build):**
> 1. `record_family: "community"` formally defined (Part 3.1).
> 2. `UserPermission.metadata` added (Part 2.2).
> 3. Gathering dual-write pattern documented (Part 14.4).
> 4. `gathering` Record `custom_fields` specification added (Part 14.4).
> 5. Calendar App Part 11.4 phasing updated.
> 6. Part 14 (Community App Engine) added.
> 7. `MembershipRequest` model documented as deferred (Part 14.8).
> 8. Part 12 updated with Community App system design status.
>
> **Everything else in v8 is unchanged and remains locked.**

> **For Claude:** When implementing, read this document fully before writing any code. All schemas, rules, and patterns here are authoritative. Do not infer from app code.

**Goal:** Define the complete, locked data contracts, service boundaries, and schema definitions for the ICS (Integrated Community System) platform — the digital twin of the Kingdom Governance System (KGS).

**Architecture:** Django + PostgreSQL backend (single source of truth). Four locked architectural decisions: (1) materialised path for tenant hierarchy, (2) single `records` table with `record_class` discriminator, (3) Paraclete as a standalone orchestration service separate from the Activity Engine, (4) Handbook as a prime `tier:"handbook"` tenant at `/global/handbook/` with Level 5 write access only (Level 4+ read — see Part 2.5.2).

**UI Architecture (locked — 2026-04-07):** All app UIs are built in Django templates + HTMX. There are no vanilla JS app files (`activity-app.js`, `learn-app.js`, etc.). HTMX handles dynamic interactions. `storage.js` is retained for UI state only (theme, session token). The data contract schemas and DRF service layer are unaffected by this decision.

**Tech Stack:** Python/Django 4.2, Django REST Framework, PostgreSQL, Django templates, HTMX, mobile-first CSS with CSS variables.

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

No exceptions. These four fields are how the permission system, audit log, and multi-tenancy all work. Missing any one of them means that object cannot be governed.

**Note:** `BibleTranslation`, `BibleBook`, and `BibleVerse` (Part 13) are exempt from this rule. They are read-only reference data loaded by management command, not governed platform entities.

### 1.2 record_class is the permission gate, not record_type

`record_type` describes *what* the record is (prayer, journal, mandate). `record_class` describes *how* the system governs it:

| record_class   | Who creates   | Default visibility | Mutable after creation | Example types                |
|----------------|---------------|--------------------|------------------------|------------------------------|
| personal       | Any user      | private            | Yes                    | journal, dream, prayer       |
| organizational | Level 2+      | tenant             | Yes, with audit        | event, programme, campaign   |
| governance     | Level 4+      | tenant or public   | Versioned only         | mandate, statement, calendar |

Permission checks MUST read `record_class` before evaluating anything else.

### 1.3 Tenant paths are the scope system

Every tenant has a `path` field. Every permission check that involves scope uses prefix matching on this path. This is the materialised path pattern.

```
/global/
/global/africa/
/global/africa/southafrica/
/global/africa/southafrica/gauteng/
/global/africa/southafrica/gauteng/pretoria-north/
/global/africa/southafrica/gauteng/pretoria-north/sceptre-community-abc/
```

A user with `scope_path = "/global/africa/southafrica/gauteng/"` can see all records whose tenant path starts with that prefix. Query: `WHERE tenant_path LIKE '/global/africa/southafrica/gauteng/%'`.

### 1.4 Services own their domain. Apps call services.

No app template may bypass the DRF service layer. All reads and writes go through DRF endpoints. Django views prepare context from DRF responses or direct ORM calls within their own Django app boundary only. Cross-app data access always goes through the API or a shared service module.

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

  // Settings (DB-persisted via JSONField — not localStorage)
  preferences: {
    theme:    "system | light | dark",
    language: "en | ...",
    timezone: "Africa/Johannesburg | ..."
  },

  updated_at: "ISO-8601"
}
```

**UserProfile extension (Django model — `accounts.UserProfile`):**

```python
preferred_bible_translation = FK → bible.BibleTranslation (nullable)
# null = use BibleTranslation.objects.get(is_default=True) at read time
# Set via HTMX translation switcher in the Bible App reader
# Updated by: POST /bible/htmx/translation/set/

bio = TextField(null=True, blank=True)
```

### 2.2 UserPermission object

**v8 Amendment:** `metadata` field added carrying two optional Community App fields. No migration required — `metadata` is a `JSONField` with `default=dict`.

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
    // Set by a steward (Level 3+) via Community App member management.
    // Null = no pastoral assignment recorded yet.

    service_order: "string | null"
    // Free-text KGS Service Order label (e.g. "Order of Pastoral Care").
    // Matches the 24 Orders defined in the KGS framework.
    // Not a FK — KGS Service Orders are not modelled as DB rows in MVP.
    // Set by a steward (Level 3+) via Community App member management.
  }
}
```

**Indexing note:** No new index required in MVP. `shepherd_id` lookups use `UserPermission.objects.filter(metadata__shepherd_id=steward_id, tenant_path__startswith=scope_path)` — acceptable at MVP member counts. Add `GinIndex` on `metadata` post-MVP if performance degrades.

### 2.3 Competence levels mapped to KGS

| Level | KGS Name               | Platform label    | Role token              | What they can do                              |
|-------|------------------------|-------------------|-------------------------|-----------------------------------------------|
| 0a    | Guest                  | Guest             | *(no User object)*      | Landing page, public records, tenant directory |
| 0b    | Seeker                 | Seeker            | `seeker`                | Bible reader, personal records (limited), Learning portal entry, no tenant membership |
| 1     | Foundational Disciple  | Member            | `member`                | Full personal records, join one tenant, learn |
| 2     | Active Contributor     | Disciple/Operator | `disciple`              | Org records, lead small groups within a node  |
| 3     | Functional Minister    | Steward           | `branch-steward` or higher | Manage teams, create programmes             |
| 4     | Leader                 | Senior Steward    | `district-steward` or higher | Create governance records, manage tenant  |
| 5     | Apostolic Steward      | Architect         | `global-steward` or `admin` | Cross-tenant governance, Handbook write, system config |

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

### 2.5.2 Access rules (v9 amendment)

**v9 Amendment:** Handbook read access changed from "Level 5 only" to tiered read by record type. Write remains Level 5 only.

```python
# Permission check algorithm update (Part 7 supplemented):
if record.tenant.tier == "handbook":
    if record.record_type in REFERENCE_LIBRARY_TYPES:
        # Reference Library types: shared, objective, HRS-produced knowledge
        return user.competence_level >= 3   # read
    else:
        # Mandate branch types: directional, governance
        return user.competence_level >= 4   # read
# Write always requires competence_level >= 5 (unchanged)

REFERENCE_LIBRARY_TYPES = ["class", "principle", "concept", "divine_pattern"]
```

| Access type | Reference Library types | Mandate branch types | Write (all types) |
|-------------|------------------------|----------------------|-------------------|
| Level 3+    | ✓ Read                 | ✗                    | ✗                 |
| Level 4+    | ✓ Read                 | ✓ Read               | ✗                 |
| Level 5     | ✓ Read                 | ✓ Read               | ✓ Write           |

### 2.5.3 Governance types (Handbook-authored records)

| Type            | Description                                            |
|-----------------|--------------------------------------------------------|
| `class`         | A category or classification of knowledge              |
| `principle`     | A foundational rule or truth                           |
| `concept`       | An idea or theological construct                       |
| `divine_pattern`| A recurring pattern observed in scripture/governance   |
| `narrative`     | A story or account carrying governance meaning         |
| `subject`       | A topic or domain of study                             |
| `entity`        | A named actor, body, or structure                      |
| `framework`     | A structured system of related principles              |
| `protocol`      | A defined sequence of steps for an occasion            |
| `procedure`     | An operational process for recurring tasks             |
| `mandate`       | A directive from the Kingdom Mandate                   |
| `statement`     | A formal declaration or position                       |
| `programme`     | A governance-context structured programme (record_class:'governance') |
| `calendar`      | A time-governed plan — **deferred to Phase 2** (v9)   |

**Handbook ↔ Scripture linkage:** A Level 5 Architect may link any governance record to specific `BibleVerse` rows using a `Relationship` with `relationship_type: "references"`, `direction: "directed"`, and `bible_verse_id` set (Part 3.2).

### 2.5.4 Hierarchy and Relationship System (HRS)

Core HRS relationship types:

| relationship_type  | From → To example                                        |
|--------------------|----------------------------------------------------------|
| `part_of`          | governance_principle → governance_framework              |
| `derived_from`     | governance_concept → governance_divine_pattern           |
| `aligns_with`      | governance_programme → governance_mandate                |
| `authorised_by`    | governance_procedure → governance_mandate                |
| `references`       | governance_narrative → governance_subject                |
| `references`       | governance_record → BibleVerse (via bible_verse_id)      |
| `has_subject`      | governance_framework → governance_subject                |
| `has_entity`       | governance_mandate → governance_entity                   |

---

## Part 3 — Records Engine Schema

### 3.1 Record object (universal)

**v9 Amendment:** `record_type` enum extended with `"article"`. `journal` family → type mapping updated. `"calendar"` type marked deferred in governance family.

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

  record_type: "prayer | dream | note | sermon | article | class | principle | concept |
                divine_pattern | narrative | subject | entity | mandate | statement |
                programme | framework | protocol | procedure | calendar | event | campaign |
                project | habit | task | skill | course | lesson | assignment | quiz |
                certification | key | property | bible_note | announcement | gathering | custom",

  // Family → Type mapping (enforced at service layer):
  //   journal     → prayer | dream | note | sermon | article
  //                 (article = general written entry or essay; Level 1+;
  //                  personal by default; may be linked to governance records
  //                  via Relationship but is not itself a governance record)
  //   governance  → class | principle | concept | divine_pattern | narrative |
  //                 subject | entity | mandate | statement | programme |
  //                 framework | protocol | procedure
  //                 NOTE: "calendar" is registered in this family but deferred
  //                 to Governance App Phase 2. No UI is built for it in MVP.
  //   activity    → event | campaign | project | habit | task | skill
  //   learning    → programme | course | lesson | assignment | quiz | certification
  //   reference   → key | property
  //   bible       → bible_note
  //   community   → announcement | gathering
  //                 (report | pastoral_note — deferred, schema in Part 14.8/14.9)
  // Governance types require record_class:'governance' and Level 4+ (Level 5 for Handbook write)
  // 'programme' appears in BOTH governance and learning families:
  //   record_class:'governance'     = KGS framework programme (Handbook-authored)
  //   record_class:'organizational' = Qualification Programme (Certificate → Doctorate)

  origin: "user | system | paraclete | import",

  title:        "string",
  content:      "string | null",
  summary:      "string | null",

  status: "draft | submitted | active | completed | archived | locked | superseded",
  // 'submitted'  = awaiting review by a higher authority (Learn App cert queue, Governance)
  // 'locked'     = approved governance record — only valid after lifecycle transition
  // 'superseded' = replaced by a new version; record retained for history chain

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
  // governance/reference types: see Part 15.3 for Property Attributes custom_fields

  metadata: {
    source_app:    "records | bible | activity | learn | community | governance | ...",
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

**v6 Amendment:** `to_record_id` is nullable. `bible_verse_id` optional field added. Exactly one of the two must be non-null.

```js
Relationship = {
  id:           "uuid",
  tenant_id:    "uuid | null",
  created_by:   "uuid",
  created_at:   "ISO-8601",

  from_record_id: "uuid",
  to_record_id:   "uuid | null",         // null only when bible_verse_id is set
  bible_verse_id: "uuid | null",         // FK → bible.BibleVerse; null except for scripture links

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

| Activity type       | Use relationship_type | Direction                            |
|---------------------|-----------------------|--------------------------------------|
| `task`, `habit`     | `tracks`              | activity_record → target_record      |
| `goal`, `reminder`  | `tracks`              | activity_record → target_record      |
| `campaign`, `event` | `aligns_with`         | activity_record → mandate/programme  |
| `project`           | `aligns_with`         | activity_record → campaign_record    |
| `skill`             | `aligns_with`         | skill_record → service_order_record  |

The Learn App exclusively uses `tracks` (lesson/habit → programme) and `part_of` (lesson → course → programme). Activity App links must not use `part_of` — that relationship type is reserved for curriculum and governance hierarchy structure.

**Community App usage (v8):**

| Community record type | Use relationship_type | Direction                                |
|-----------------------|-----------------------|------------------------------------------|
| `gathering`           | `aligns_with`         | gathering_record → activity_event_record |

A `gathering` Record is always linked to its corresponding `event` Activity via `aligns_with` — written atomically by the Community App dual-write transaction (Part 14.4).

**Governance App usage (v9):**

| Governance record type          | Use relationship_type | Direction                               |
|---------------------------------|-----------------------|-----------------------------------------|
| governance → governance         | `part_of`             | concept → framework                     |
| governance → governance         | `derived_from`        | mandate → divine_pattern                |
| governance → governance         | `aligns_with`         | programme → mandate                     |
| governance → governance         | `authorised_by`       | procedure → mandate                     |
| governance → governance         | `references`          | narrative → subject                     |
| governance → BibleVerse         | `references`          | governance_record → BibleVerse          |
| key (personal) → journal entry  | `derived_from`        | key_record → journal_entry              |
| mandate → journal entry         | `derived_from`        | mandate_record → spirit_journal_entry   |

---

## Part 4 — Activity Engine Schema

### 4.1 Activity object

The Activity Engine operates on its own objects AND writes records into the Records Engine for persistence and linking. Activities are the execution layer; Records are the memory layer.

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
  //             gathering Activities created via Community App carry metadata.source_app:'community'
  // campaign  = a time-bound operational initiative (KGS Harvest Campaign etc.)
  // project   = a structured body of work nested under a campaign
  // programme = learning enrolment hierarchy — authored and owned by Learn App; read-only in Activity App
  // reminder  = a time-triggered prompt; created by user or Paraclete
  // skill     = a gift, talent, or competence entry in the user's gifts register

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

| Field           | Usage for `skill` type                                              |
|-----------------|---------------------------------------------------------------------|
| `title`         | Name of the gift or skill (e.g. "Teaching", "Administration")       |
| `description`   | How this gift manifests in the user's life and ministry             |
| `progress`      | Self-assessed competence: 0–100                                     |
| `kgs_pathway`   | Which Kingdom Pathway this gift primarily serves                    |
| `metadata.service_order` | KGS Service Order this gift aligns with (optional)        |
| `status`        | `active` = current gift; `archived` = no longer active/relevant     |
| `tenant_id`     | Null = personal register; tenant-scoped = visible to steward        |

### 4.2 ActivityLog object

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

| Who                   | Can assign to                          | Constraint                           |
|-----------------------|----------------------------------------|--------------------------------------|
| Level 1–2 (personal)  | Self only (`assigned_to = created_by`) | Personal activities only             |
| Level 3+ (steward)    | Any user within their `scope_path`     | `activity.tenant_id` must be within assigning user's `UserPermission.tenant_path` |
| Level 3+ (steward)    | `assigned_to = null` (team-visible)    | For campaign/project containers      |

---

## Part 5 — Paraclete Service Contract

The Paraclete is a standalone orchestration service. It does NOT own any data. It reads from other engines and produces suggestions, reminders, and insights. It never writes directly to Records or Activities — it calls their services.

### 5.1 What Paraclete is responsible for

- Reading user's activities, records, and schedules to generate intelligent reminders
- Detecting patterns across records (recurring dream symbols, prayer themes, habit streaks)
- Producing "today's focus" digest based on user's competence level, active activities, and KGS calendar
- Surfacing record link suggestions based on content similarity
- Generating discipline prompts aligned to the user's KGS pathway

### 5.2 What Paraclete is NOT responsible for

- Storing any data (reads only — no writes)
- Displaying UI (Dashboard and Activity App consume its output)
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

### 5.4 Paraclete filter contracts

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
  ics_project/      ← Django project settings + root URLs
  accounts/         ← User, UserProfile, UserPermission models + auth
  tenants/          ← Tenant model + path resolution
  records/          ← Record + Relationship models (Records Engine)
  activity/         ← Activity + ActivityLog models (Activity Engine)
  learn/            ← CertificationConfirmation model + curriculum endpoint
  bible/            ← BibleTranslation, BibleBook, BibleVerse models
  community/        ← Community App (v8 — Django app, no models except MembershipRequest stub)
  governance/       ← Governance App (v9 — Django app, no models, UI layer only)
  calendar_app/     ← Calendar aggregation service (no models)
  paraclete/        ← Orchestration service (no models)
  frontend/         ← Static assets (CSS, storage.js, navbar.js)
```

### 6.2 App ownership rules (cross-app dependency policy)

| Model            | Owner app   | Other apps may...                                      |
|------------------|-------------|--------------------------------------------------------|
| Record           | records     | read via DRF only                                      |
| Relationship     | records     | read/write via DRF only; FK dep on bible.BibleVerse     |
| Activity         | activity    | read via DRF; Community App creates via DRF            |
| ActivityLog      | activity    | read via DRF only                                      |
| UserPermission   | accounts    | read/write via DRF; Community App writes metadata fields |
| BibleVerse       | bible       | read via DRF; referenced by Relationship FK            |
| BibleTranslation | bible       | read via DRF; FK dep in accounts.UserProfile           |
| Tenant           | tenants     | read via DRF only                                      |

**Community App and Governance App own no models.** They are UI + coordination layers that write to Records, Activity, and UserPermission via their respective DRF endpoints.

---

## Part 7 — Permission Check Algorithm

```python
def can_access(user, record):
    # 1. Handbook short-circuit (v9 amendment)
    if record.tenant.tier == 'handbook':
        REFERENCE_LIBRARY_TYPES = ['class', 'principle', 'concept', 'divine_pattern']
        if record.record_type in REFERENCE_LIBRARY_TYPES:
            return user.competence_level >= 3   # read
        else:
            return user.competence_level >= 4   # read (Mandate branch)
        # Write always requires competence_level >= 5 (handled at ViewSet level)

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
CREATE INDEX idx_records_tenant_id     ON records(tenant_id);
CREATE INDEX idx_records_record_class  ON records(record_class);
CREATE INDEX idx_records_record_family ON records(record_family);
CREATE INDEX idx_records_record_type   ON records(record_type);
CREATE INDEX idx_records_created_by    ON records(created_by);
CREATE INDEX idx_records_status        ON records(status);
CREATE INDEX idx_records_deleted_at    ON records(deleted_at);
CREATE INDEX idx_records_custom_fields ON records USING gin(custom_fields);
```

### 8.2 Activity table indexes

```sql
CREATE INDEX idx_activity_tenant_id   ON activity(tenant_id);
CREATE INDEX idx_activity_type        ON activity(activity_type);
CREATE INDEX idx_activity_assigned_to ON activity(assigned_to);
CREATE INDEX idx_activity_status      ON activity(status);
CREATE INDEX idx_activity_due_at      ON activity(due_at);
CREATE INDEX idx_activity_scheduled   ON activity(scheduled_at);
CREATE INDEX idx_activity_parent_id   ON activity(parent_activity_id);
CREATE INDEX idx_activity_deleted_at  ON activity(deleted_at);
CREATE INDEX idx_activity_metadata    ON activity USING gin(metadata);
```

### 8.3 Relationship table indexes

```sql
CREATE INDEX idx_rel_from_record  ON relationship(from_record_id);
CREATE INDEX idx_rel_to_record    ON relationship(to_record_id);
CREATE INDEX idx_rel_bible_verse  ON relationship(bible_verse_id);
CREATE INDEX idx_rel_type         ON relationship(relationship_type);
CREATE INDEX idx_rel_deleted_at   ON relationship(deleted_at);
```

### 8.4 UserPermission table indexes

```sql
CREATE INDEX idx_perm_user_id      ON user_permission(user_id);
CREATE INDEX idx_perm_tenant_path  ON user_permission(tenant_path varchar_pattern_ops);
CREATE INDEX idx_perm_is_active    ON user_permission(is_active);
```

**Note (v8):** `UserPermission.metadata` is a JSONField. `shepherd_id` and `service_order` queries are infrequent (steward-level, not hot paths). No GinIndex added in MVP. Add post-MVP if query times degrade.

---

## Part 9 — Cross-App Data Patterns

### 9.1 Record + Activity dual write

When the platform needs both a persistent Record and an active Activity for the same thing, the convention is:

1. The orchestrating app creates the Record first (`POST /api/records/`)
2. Then creates the Activity with a Relationship linking the two (`POST /api/activities/` + `POST /api/relationships/`)
3. If either step fails, the view rolls back both (`Django transaction.atomic`)

This pattern is used by: Learn App (programme enrolment), Community App (gathering create — Part 14.4).

### 9.2 Learn App: scripture_reference convention

Lesson Records (`record_family:'learning'`, `record_type:'lesson'`) MAY carry a `scripture_reference` key in `custom_fields`:

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
- Campaigns have no `parent_activity_id` (they are top-level)

### 10.4 Assignment model

*(See Part 4.3)*

### 10.5 Template pattern

```js
// Template activity (created by Level 4+)
Activity { metadata: { is_template: true, template_id: null } }

// Instance created from template (Level 2+ user)
Activity { metadata: { is_template: false, template_id: "{source_template_id}" } }
```

### 10.6 Relationship type rules

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

### 11.1 Purpose

Multiple ICS apps need time-based views of platform data:
- Activity App: events and scheduled activities
- Dashboard: today's agenda
- Learn App: programme milestones and due dates (Phase 3)
- Community App: gathering events — active in MVP via dual-write
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

**Community events in Calendar (v8):** Gathering events are `activity_type:'event'` Activities with `metadata.source_app:'community'`. The Calendar endpoint already queries the Activity table — community gatherings appear automatically. Filtering for community gatherings specifically: `GET /api/calendar/events/?source_app=community`

### 11.4 MVP scope and phasing

| Phase | What it builds |
|-------|----------------|
| MVP (built with Activity App) | Backend aggregation endpoint; queries Activity table only |
| Phase 2 (post-Community App) | Community events active via `metadata.source_app:'community'`; no code change required |
| Phase 3 (post-Learn App) | Add Record events (programme milestones, governance calendars) |
| Calendar UI | Full month/week grid view in Django templates + HTMX (Phase 3) |

### 11.5 Django app structure

```
~/ics/calendar_app/
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

*Updated in v9: Governance App system design marked complete. Phase numbering updated per Roadmap v3.*

### Phase 5 — Remaining apps (in order)

| Task | App | Status |
|------|-----|--------|
| 5.1 | Bible App | ✅ Complete — `2026-04-08-ics-bible-app-system-design_v2.md` |
| 5.2 | Learn App | 🔄 In Progress — `2026-04-07-ics-learn-app-system-design_v2.md` |
| 5.3 | Activity App | ⏳ Pending — `2026-04-08-ics-activity-app-system-design.md` |
| 5.4 | Community App | ⏳ Pending — `2026-04-08-ics-community-app-system-design.md` |
| 5.5 | Governance App | ⏳ Pending — `2026-04-10-ics-governance-app-system-design.docx` |
| 5.6 | Profile + Settings | ⏳ Pending — `2026-04-10-ics-profile-settings-notifications-spec.docx` |
| 5.7 | Notifications stub | ⏳ Pending — same spec as 5.6 |

### Phase 6 — Paraclete Service + Dashboard

`paraclete/service.py` calls Django ORM directly using the Activity filters defined in Part 5.4. Returns `ParacleteDigest` for Dashboard consumption. Dashboard renders digest widgets. Role-aware and tenant-aware.

Reference: `2026-04-10-ics-paraclete-service-system-design.docx`

### Phase 7 — Production Hardening

Error logging, security settings, systemd Gunicorn service, final smoke test. Nginx + Gunicorn setup is in Roadmap v3 Task 0.5.

---

## Part 13 — Bible App Engine (Data Patterns & Contracts)

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

| Code | Name                    | Language     | Copyright     | Default |
|------|-------------------------|--------------|---------------|---------|
| KJV  | King James Version      | English (en) | Public Domain | Yes     |
| ASV  | American Standard Version | English (en) | Public Domain | No    |
| WEB  | World English Bible     | English (en) | Public Domain | No      |

### 13.3 Bible note Record pattern

Bible notes are Records: `record_family: "bible"`, `record_type: "bible_note"`, `record_class: "personal"`. Linked to a verse via a `Relationship` with `bible_verse_id` set.

### 13.4 Seeker bible note limit

Level 0b (Seeker) is limited to 10 total Records across all personal record types. The service layer enforces this by counting `Record.objects.filter(created_by=user, deleted_at__isnull=True)` before allowing creation.

### 13.5 Handbook ↔ scripture linkage pattern

A Level 5 Architect links a governance record to a `BibleVerse` via `Relationship (references, directed, bible_verse_id set)`. No free-text scripture citations in record content.

### 13.6 Learn App cross-reference convention

*(See Part 9.2)*

### 13.7 Bible App access rules by competence level

| Feature                         | Level 0b | Level 1+ | Level 3+ | Level 5 |
|---------------------------------|----------|----------|----------|---------|
| Read scripture (any translation)| ✓        | ✓        | ✓        | ✓       |
| Switch translation              | ✓        | ✓        | ✓        | ✓       |
| Create personal bible note      | ✓ (limit)| ✓        | ✓        | ✓       |
| Edit/delete own note            | ✓        | ✓        | ✓        | ✓       |
| See tenant (community) notes    | ✗        | ✓        | ✓        | ✓       |
| Publish tenant note             | ✗        | ✗        | ✓        | ✓       |
| See Learn cross-references      | ✗        | ✓        | ✓        | ✓       |
| See Handbook references         | ✗        | ✗        | ✗        | ✓       |

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
GET  /api/records/?record_family=learning&record_type=lesson&custom_fields__scripture_reference__icontains={ref}
POST /api/relationships/
GET  /api/relationships/?bible_verse_id={id}
```

---

## Part 14 — Community App Engine (Data Patterns & Contracts)

The Community App owns **no models**. It is a UI and transaction coordination layer that writes to Records, Activity, and UserPermission via their respective DRF endpoints.

### 14.1 Purpose

The Community App is the digital expression of KGS Pillar 6 — Communities & Networks. It serves:
- **Members** — see their community, formation journey, upcoming gatherings, and announcements
- **Stewards (Level 3+)** — manage community membership, post announcements, create gatherings, view the formation pipeline

### 14.2 Two-surface model

```
Community App
  │
  ├── "My Community"  (member surface — Level 1+)
  │     Shows: active tenants, formation stage, service order placement,
  │            shepherd, upcoming gatherings, latest announcements, gifts register summary
  │     Scope: UserPermission rows where user_id = request.user, is_active = True
  │
  └── "Community Management"  (steward surface — Level 3+)
        Shows: member directory, formation pipeline, member profile, announcement
               management, gathering management, pastoral assignments, service order placement
        Scope: UserPermission.tenant_path LIKE '{steward.scope_path}%'
```

### 14.3 Community Record types (MVP)

#### announcement

```js
Record {
  record_class:   "organizational",
  record_family:  "community",
  record_type:    "announcement",
  title:          "string",
  content:        "string",          // announcement body (markdown)
  status:         "active | archived",
  tenant_id:      "uuid",
  created_by:     "uuid",            // must be Level 3+
  metadata:       { source_app: "community" },
  permissions:    { visibility: "tenant", required_level: 1 }
}
```

Access rules: Create = Level 3+; Read = Level 1+ within tenant; Edit/archive = creating steward or Level 4+ in scope.

#### gathering

```js
Record {
  record_class:   "organizational",
  record_family:  "community",
  record_type:    "gathering",
  title:          "string",
  content:        "string | null",
  status:         "active | completed | cancelled",
  tenant_id:      "uuid",
  created_by:     "uuid",            // must be Level 3+
  metadata:       { source_app: "community" },
  custom_fields: {
    format:       "in_person | digital | hybrid",
    location:     "string | null",
    stream_url:   "string | null",   // MVP: external URL; Video App integration later
    capacity:     "integer | null",
    scheduled_at: "ISO-8601 | null", // denormalised from Activity.scheduled_at
  },
  permissions: { visibility: "tenant", required_level: 1 }
}
```

Access rules: Create = Level 3+; Read = Level 1+ within tenant; Cancel = creating steward or Level 4+.

### 14.4 Gathering dual-write pattern

Creating a gathering produces two objects atomically and links them with a Relationship. Both writes must succeed or both must fail (`transaction.atomic`).

```python
# Step 1 — Create gathering Record
# Step 2 — Create event Activity (feeds Calendar App)
# Step 3 — Link Record → Activity via Relationship (aligns_with, directed)
```

**Cancellation:** PATCH Record `status → 'cancelled'` + PATCH Activity `status → 'cancelled'`, both in `transaction.atomic`.

**Video App boundary:** When the Video App is built (post-MVP), `stream_url` will point to an ICS Video App endpoint. No data contract change required at that time.

### 14.5 Member directory query pattern

```python
# All active members within steward's scope
members = UserPermission.objects.filter(
    tenant_path__startswith=steward_scope_path,
    is_active=True
).select_related('user').order_by('user__display_name')

# Formation pipeline — grouped by competence_level
pipeline = members.values('user__competence_level').annotate(count=Count('id'))

# Pastoral flock
flock = UserPermission.objects.filter(
    metadata__shepherd_id=steward.id,
    tenant_path__startswith=steward_scope_path,
    is_active=True
).select_related('user')
```

### 14.6 Membership management rules (MVP — steward-initiated only)

Self-service join requests are deferred (Part 14.8).

**Adding a member:** `POST /api/permissions/` with `{user_id, tenant_id, tenant_path, role, level, is_active: true, granted_by: steward.id}`

**Removing a member:** Soft deactivation only — `PATCH /api/permissions/{id}/` → `{is_active: false}`. Hard deletion is prohibited.

**Pastoral assignment:** `PATCH /api/permissions/{id}/` → `{metadata: {shepherd_id: steward_user_id}}`

**Service order:** `PATCH /api/permissions/{id}/` → `{metadata: {service_order: "Order of Community Building"}}`

### 14.7 Community App access rules

| Level | My Community surface | Community Management surface |
|-------|---------------------|------------------------------|
| Seeker (0b) | ✗ No tenant membership | ✗ |
| Member (1) | ✓ Own tenants only | ✗ |
| Disciple (2) | ✓ Own tenants + limited directory (names only) | ✗ |
| Branch-Steward (3) | ✓ Full | ✓ Own branch: full directory, announcements, gatherings |
| Senior Steward (4+) | ✓ Full | ✓ Scope: district/province/national depending on role |
| Architect (5) | ✓ Full | ✓ Cross-tenant visibility |

**Level 2 limited directory:** Display names and service orders only. `shepherd_id`, email, and formation detail are Level 3+ only.

### 14.8 Deferred: MembershipRequest model (stub)

```python
# community/models.py — stubbed, not wired to UI in MVP
class MembershipRequest(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant_id   = models.UUIDField()
    created_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                    related_name='membership_requests')
    created_at  = models.DateTimeField(auto_now_add=True)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                    related_name='requests_made')
    tenant      = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    status      = models.CharField(max_length=20,
                                   choices=[('pending','Pending'),
                                            ('approved','Approved'),
                                            ('denied','Denied')],
                                   default='pending')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='requests_reviewed')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    note        = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'community_membership_request'
```

### 14.9 Deferred: report and pastoral_note record types

**report** — community health or activity report, Level 3+, `record_class:'organizational'`, `visibility:'collective'` or `'tenant'`. Deferred to Community App Phase 2.

**pastoral_note** — confidential steward note on a specific member. `record_class:'personal'` (steward-authored), `visibility:'private'`. Privacy-sensitive design required. Deferred to Phase 2.

### 14.10 Community App DRF endpoints

```
# Member directory
GET    /api/permissions/?tenant_path__startswith={scope}&is_active=true

# Membership management
POST   /api/permissions/
PATCH  /api/permissions/{id}/

# Announcements and gatherings
GET    /api/records/?record_family=community&record_type=announcement&tenant_id={id}
POST   /api/records/
PATCH  /api/records/{id}/
GET    /api/records/?record_family=community&record_type=gathering&tenant_id={id}

# Activities (gathering dual-write)
POST   /api/activities/
PATCH  /api/activities/{id}/

# Relationships
POST   /api/relationships/

# Upcoming gatherings (Calendar endpoint)
GET    /api/calendar/events/?source_app=community&tenant_id={id}&from={ISO}&to={ISO}

# Member gifts register (Activity App endpoint)
GET    /api/activities/?activity_type=skill&tenant_id={id}&created_by={member_id}

# Django template views
GET    /community/
GET    /community/management/
GET    /community/management/members/
GET    /community/management/members/{id}/
GET    /community/management/pipeline/
POST   /community/htmx/announcement/create/
POST   /community/htmx/gathering/create/
POST   /community/htmx/member/shepherd/
POST   /community/htmx/member/order/
GET    /community/htmx/announcements/
GET    /api/community/health/
```

---

## Part 15 — Governance App Engine (Data Patterns & Contracts)

*(New in v9)*

The Governance App owns **no models**. It is a UI and coordination layer over the Records Engine.

### 15.1 Purpose

The Governance App is the digital expression of KGS Pillar 2 — Strategy & Governance. Its purpose is to make Apostolic Properties visible, maintainable, and traversable on the platform.

It is organised around three branches:
- **The Reference Library** — an objective, shared body of HRS-produced knowledge compiled from Scripture (Classes, Principles, Concepts, Divine Patterns)
- **The Keys Library** — a personal, per-operator interpretive library built from Dream Journal and Spirit Journal over time (Key Records)
- **The Mandate** — outward-flowing governance documents: received directives, strategic frameworks, protocols, and procedures

### 15.2 Three-surface model

```
Governance App
  │
  ├── Reference Library  (Level 3+ read, Level 5 write)
  │     Record types: class, principle, concept, divine_pattern
  │     Tenant scope: Handbook only
  │     Access: shared, objective, HRS-produced knowledge
  │
  ├── Mandate Branch  (Level 4+ read, Level 5 write)
  │     Record types: mandate, statement, framework, narrative, subject,
  │                   entity, protocol, procedure, programme
  │     Tenant scope: Handbook only
  │     Access: directional governance documents
  │
  └── Keys Library  (owner only — Level 3+)
        Record type: key
        Tenant scope: null (personal records)
        Access: private to the operator who created them
```

### 15.3 Property Attributes custom_fields (Reference Library types)

Six HRS attributes applicable to Reference Library record types (`class`, `principle`, `concept`, `divine_pattern`):

```js
custom_fields: {
  // HRS classification attributes (all optional)
  complexity:            "string | null",  // e.g. "foundational", "advanced"
  relationship_position: "string | null",  // e.g. "central", "peripheral"
  position:              "string | null",  // structural position in the HRS
  direction:             "string | null",  // e.g. "inward", "outward", "bilateral"
  speed:                 "string | null",  // e.g. "progressive", "immediate"
  emotional_tone:        "string | null",  // e.g. "declarative", "invitational"
}
```

These are author-defined free-text fields. Not validated as enums — free-text allows the HRS to evolve without schema changes.

### 15.4 Governance record lifecycle

```
draft → active → locked → superseded
```

| Status      | Description                                                  | Who transitions     |
|-------------|--------------------------------------------------------------|---------------------|
| `draft`     | Being authored; not published                                | Creator (Level 5)   |
| `active`    | Published and in effect; readable per Part 2.5.2 rules       | Creator (Level 5)   |
| `locked`    | Finalised; no further edits. Content frozen.                 | Level 5 only        |
| `superseded`| Replaced by a newer version. Retained for history chain.     | Level 5 only        |

**Note:** `"submitted"` status is present in the data model vocabulary but has no UI in Governance App MVP. No approval queue — Level 5 authors lock records directly.

**Version chain:** `previous_version_id` and `superseded_by` fields enable traversal. When creating a new version: (1) lock the old record, (2) create the new record with `previous_version_id` pointing to the old one, (3) PATCH the old record's `superseded_by` to point to the new one.

### 15.5 Governance App record type authority matrix

| Record Type      | Surface           | Read     | Write / Lock | Tenant Scope |
|------------------|-------------------|----------|--------------|--------------|
| **REFERENCE LIBRARY** | | | | |
| class            | Reference Library | Level 3+ | Level 5      | Handbook     |
| principle        | Reference Library | Level 3+ | Level 5      | Handbook     |
| concept          | Reference Library | Level 3+ | Level 5      | Handbook     |
| divine_pattern   | Reference Library | Level 3+ | Level 5      | Handbook     |
| **MANDATE BRANCH** | | | | |
| mandate          | Mandate           | Level 4+ | Level 5      | Handbook     |
| statement        | Mandate           | Level 4+ | Level 5      | Handbook     |
| framework        | Mandate           | Level 4+ | Level 5      | Handbook     |
| narrative        | Mandate           | Level 4+ | Level 5      | Handbook     |
| subject          | Mandate           | Level 4+ | Level 5      | Handbook     |
| entity           | Mandate           | Level 4+ | Level 5      | Handbook     |
| protocol         | Mandate           | Level 4+ | Level 5      | Handbook     |
| procedure        | Mandate           | Level 4+ | Level 5      | Handbook     |
| programme        | Mandate           | Level 4+ | Level 5      | Handbook     |
| **KEYS LIBRARY (personal)** | | | | |
| key              | Keys Library      | Owner only | Level 3+ (own keys) | null (personal) |
| **DEFERRED** | | | | |
| calendar         | — Phase 2 —       | —        | —            | —            |

### 15.6 HRS Relationship Viewer

Every governance record detail view includes a Linked Records panel — a read-only flat list of all Relationship rows where `from_record_id` or `to_record_id` equals the current record.

```python
# All relationships where this record is the source
GET /api/relationships/?from_record_id={record_id}

# All relationships where this record is the target
GET /api/relationships/?to_record_id={record_id}

# Scripture links
GET /api/relationships/?from_record_id={record_id}&bible_verse_id__isnull=false
# For each result: GET /api/bible/verses/{bible_verse_id}/ to fetch verse text

# Rendered panel shows:
#   Relationship type badge (part_of, derived_from, references, etc.)
#   Linked record: title + record_type chip
#   Scripture link: book chapter:verse + verse text (first 80 chars)
#   Direction indicator (directed → or ↔ bidirectional)
#   Click → opens linked record detail view
```

Full graph visualisation is deferred post-MVP.

### 15.7 Keys Library — Key Record pattern

Key Records are personal, private records forming an operator's interpretive symbol library.

```js
Record {
  record_class:   "personal",
  record_family:  "reference",
  record_type:    "key",
  title:          "string",    // the symbol or term (e.g. "Lion", "Water", "North")
  content:        "string",    // the operator's personal interpretation / meaning
  summary:        "string | null",
  tenant_id:      null,        // personal records have no tenant
  created_by:     "uuid",
  status:         "active | archived",
  metadata: {
    source_app:          "governance",
    source_journal_ids:  ["uuid", ...]  // links to Dream/Spirit Journal entries
  },
  permissions: {
    visibility:     "private",
    required_level: 3,
  },
  custom_fields: {
    symbol_class: "string | null",   // e.g. "animal", "element", "person"
    domain:       "string | null",   // e.g. "dreams", "scripture", "both"
  }
}
```

### 15.8 Version history chain

The version history of a governance record is traversable via `previous_version_id` and `superseded_by` fields, rendered as a linear history timeline on the record detail view.

```python
# To build the full chain for a record:
# 1. Start with current record (may have previous_version_id set)
# 2. Walk backward: GET /api/records/{previous_version_id}/ until null
# 3. Walk forward: GET /api/records/?previous_version_id={record_id}
#    (finds the record that superseded this one, if any)

# Rendered as a timeline:
#   v1 [locked, superseded] → v2 [locked, superseded] → v3 [active]
#   Each entry: version number, title, locked_at date, locked_by display_name
#   Click on earlier version → opens that version in read-only detail view
```

### 15.9 Journal → Governance linkage pattern

The Spirit Journal and Dream Journal (`record_family: "journal"`) are the input instruments that feed the Keys Library and Mandate branch.

```python
# Journal entry → Key Record link
Relationship {
  from_record_id:    key_record.id,
  to_record_id:      journal_entry.id,
  relationship_type: "derived_from",
  direction:         "directed"
}

# Journal entry → Mandate record link
Relationship {
  from_record_id:    mandate_record.id,
  to_record_id:      spirit_journal_entry.id,
  relationship_type: "derived_from",
  direction:         "directed"
}

# The Governance App authorship form includes a "Source Journal Entry" field
# that calls GET /api/records/?record_family=journal&created_by={user_id}
# and creates this Relationship on save.
```

### 15.10 Governance App DRF endpoints

The Governance App uses existing platform endpoints. No new DRF ViewSets are introduced.

```
# Reference Library browse
GET  /api/records/?record_family=governance&record_class=governance&record_type={type}&tenant_id={handbook_id}
GET  /api/records/{id}/

# Governance record create / edit / lifecycle
POST   /api/records/
PATCH  /api/records/{id}/

# Relationships (HRS viewer + journal links)
GET    /api/relationships/?from_record_id={id}
GET    /api/relationships/?to_record_id={id}
POST   /api/relationships/

# Scripture links
GET    /api/bible/verses/{bible_verse_id}/
GET    /api/relationships/?bible_verse_id__isnull=false&from_record_id={id}

# Keys Library
GET    /api/records/?record_family=reference&record_type=key&created_by={user_id}
POST   /api/records/
PATCH  /api/records/{id}/

# Source journal entries (for linking)
GET    /api/records/?record_family=journal&created_by={user_id}

# Django template views
GET    /governance/
GET    /governance/reference/
GET    /governance/reference/{type}/
GET    /governance/reference/{id}/
GET    /governance/mandate/
GET    /governance/mandate/{type}/
GET    /governance/mandate/{id}/
GET    /governance/keys/
GET    /governance/keys/{id}/

# HTMX partials
GET    /governance/htmx/reference/list/
GET    /governance/htmx/mandate/list/
POST   /governance/htmx/record/create/
POST   /governance/htmx/record/{id}/lock/
POST   /governance/htmx/record/{id}/supersede/
GET    /governance/htmx/record/{id}/links/
GET    /governance/htmx/record/{id}/history/
GET    /governance/htmx/journal/search/
GET    /api/governance/health/
```

---

## Deferred (Post-MVP)

### Platform-wide

- Full `RecordPermission` table (fine-grained per-user permissions)
- `CustomFieldSchema` formal validation system
- Video/Live streaming app
- In-service Display app
- Donations feature
- Advanced Paraclete AI features (pattern detection, auto-linking)
- Push notifications (mobile)
- `assigned_to_tenant_id` on Activity (collective/network assignment)
- Custom RRULE recurrence UI (Activity App)

### Learn App

- Rich text editor for lesson authorship
- Quiz auto-grading with score display
- Assignment peer review
- Paraclete "continue your lesson" integration
- Learning analytics dashboard
- Offline lesson caching
- Video lessons (`record_type: "video_lesson"`)

### Calendar App

- Record events in aggregation (programme milestones, governance calendars)
- iCal export
- Subscription feed for external calendar apps

### Activity App

- Full RRULE custom recurrence builder
- Activity analytics (completion rates, habit streaks dashboard)
- Bulk assignment
- Cross-tenant campaign templates

### Bible App

- Reading plans
- Verse highlights
- Scripture full-text search
- Licensed translations (NIV, ESV, NLT)
- African language translations
- Paraclete "You haven't read today" prompt
- Cross-reference chains
- Audio Bible

### Community App

- `MembershipRequest` model UI (model stubbed in MVP — Part 14.8)
- Induction training gate (Learn App integration)
- `report` record type (Part 14.9)
- `pastoral_note` record type (Part 14.9)
- Attendance tracking (`AttendanceLog` model — privacy-sensitive, deferred)
- `PastoralAssignment` model (upgrade from `UserPermission.metadata.shepherd_id`)
- GinIndex on `UserPermission.metadata`
- Community analytics dashboard
- Collective-level gathering visibility
- Notifications on new announcements

### Governance App

- `calendar` record type (registered in governance family — Phase 2)
- Level 4 create access for tenant-scoped governance records (Handbook-only in MVP)
- Full HRS graph visualisation (Linked Records panel is flat list in MVP)
- Governance App Phase 2: tenant-scoped governance records for Senior Stewards (Level 4)

### Notifications

- Full notification trigger system (depends on Activity, Community, and Governance signals)
- In-app notification preferences
- Email digest notifications
