# ICS Platform — Data Contract & Architecture Document

> **Version:** v10 — 2026-04-27 (Canonical Consolidated)
> **Previous version:** v9 — 2026-04-10
> **Status:** Approved — Canonical Reference
> **Supersedes:** All previous data contract versions (v1–v9)
>
> **How this document was produced:**
> v9 was the accumulated canonical reference. v10 (2026-04-25) was a partial rewrite that
> introduced 9 formal amendments but accidentally omitted large sections of v9 that remain
> authoritative. This document is the correct consolidation: v9 as the full base, with all
> 9 v10 amendments applied in-place, journal family types corrected to match MVP reality,
> governance record type list and Relationship.strength kept as v9, and all three previously
> undocumented breaking changes resolved by explicit decision.
>
> **Amendment decisions applied:**
> 1. Journal family types corrected to MVP reality: `prayer | spirit | dream | dar | note`
>    (`sermon` and `article` retired; `spirit`, `dar` formalised from MVP code).
>    User-defined custom types are a planned V2 feature — not in this contract.
> 2. Governance record type list: v9 list retained (v10 rewrite list discarded as undocumented).
> 3. `Relationship.strength`: v9 enum (`weak | medium | strong | null`) retained.
>    Float type from v10 rewrite discarded as undocumented breaking change.
>
> **For Claude:** When implementing, read this document fully before writing any code.
> All schemas, rules, and patterns here are authoritative. Do not infer from app code.

**Goal:** Define the complete, locked data contracts, service boundaries, and schema definitions for the ICS (Integrated Community System) platform — the digital twin of the Kingdom Governance System (KGS).

**Architecture:** Django + PostgreSQL backend (single source of truth). Four locked architectural decisions: (1) materialised path for tenant hierarchy, (2) single `records` table with `record_class` discriminator, (3) Paraclete as a standalone orchestration service separate from the Activity Engine, (4) Handbook as a prime `tier:"handbook"` tenant at `/global/handbook/` with Level 5 write access only (Level 4+ read — see Part 2.5.2).

**UI Architecture (locked — 2026-04-07):** All app UIs are built in Django templates + HTMX. There are no vanilla JS app files. HTMX handles dynamic interactions. `storage.js` is retained for UI state only (theme, session token). The data contract schemas and DRF service layer are unaffected by this decision.

**Mobile (v10 — ADR-001):** Flutter mobile app targets iOS and Android. All data access goes through the same DRF endpoints. Delta sync via `GET /api/sync/changes/` (Part 11).

**Tech Stack:** Python/Django 4.2 LTS, Django REST Framework, PostgreSQL, Django templates, HTMX, Flutter (mobile).

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

### 1.5 competence_level has one write path only

`competence_level` may only be written by `POST /api/learn/certifications/{id}/confirm/`. No other code may write to this field. This is an absolute lock — see ADR-003.

### 1.6 Single records table — no new model tables for content types

All content is stored in the single `records_record` table using the `record_class` / `record_family` / `record_type` discriminator. Do not create new model tables for new content types.

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
  email:        "string",        // Username field — unique, required
  display_name: "string",
  avatar_url:   "string | null", // @property returning avatar.url (MinIO ImageField) (v10)

  // Competence & Formation
  // 0a = Guest (anonymous, no account) — not stored, describes unauthenticated sessions
  // 0b = Seeker (registered, formation not yet complete) — status: 'seeker'
  // 1–5 = active formation levels mapped to KGS (see section 2.3)
  competence_level: 0 | 1 | 2 | 3 | 4 | 5,  // SOLE WRITE PATH: POST /api/learn/certifications/{id}/confirm/

  // Platform status
  status: "seeker | active | suspended | pending_verification",

  // Settings (DB-persisted via JSONField — not localStorage)
  preferences: {
    theme:    "system | light | dark",
    language: "en | ...",
    timezone: "Africa/Johannesburg | ..."
  },

  // v10 Amendment 10.2 — Induction tracking
  induction_enrolled_at:  "ISO-8601 | null",  // set when UserPermission for Induction Tenant created
  induction_completed_at: "ISO-8601 | null",  // set when certifications/confirm/ called with induction_completion context
  induction_pathway:      "reconditioning | beginners | null",  // set on entrant type selection

  // v10 Amendment 10.7 — FCM push token
  fcm_token: "string | null",  // Firebase Cloud Messaging — updated by Flutter app on login

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

# v10 Amendment 10.3 — Profile registration fields (PII)
full_name   = CharField(max_length=255)           # Legal/formal name
address     = TextField(null=True, blank=True)
country     = CharField(max_length=2, null=True)  # ISO 3166-1 alpha-2 (e.g. "ZA")
id_number   = EncryptedCharField(null=True)       # National ID / passport — ENCRYPTED
age         = IntegerField(null=True)
gender      = CharField(choices=['male','female','prefer_not_to_say'], null=True)
occupation  = CharField(max_length=255, null=True)
education   = TextField(null=True)                # Highest qualification description
born_again  = BooleanField(null=True)             # Kingdom participation indicator
```

**SECURITY:** `id_number` must be stored encrypted (`django-encrypted-model-fields`). Store `FIELD_ENCRYPTION_KEY` in `.env` — never in code. `id_number` must be `write_only` in `UserProfileSerializer`. Access requires an explicit Level 4+ admin endpoint. Never returned in any standard API response.

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
  granted_by:   "uuid",

  // Community App metadata (optional, JSONField default={})
  metadata: {
    shepherd_id:   "uuid | null",
    // user_id of the pastoral supervisor assigned to this member within this tenant.
    // Set by a steward (Level 3+) via Community App member management.

    service_order: "string | null"
    // Free-text KGS Service Order label (e.g. "Order of Pastoral Care").
    // Not a FK — KGS Service Orders are not modelled as DB rows in MVP.
  }
}
```

**Indexing note:** No GinIndex on `metadata` in MVP. `shepherd_id` lookups use `UserPermission.objects.filter(metadata__shepherd_id=steward_id, tenant_path__startswith=scope_path)`. Add `GinIndex` post-MVP if performance degrades.

### 2.3 Competence levels mapped to KGS

| Level | KGS Name               | Platform label    | Role token              | What they can do                              |
|-------|------------------------|-------------------|-------------------------|-----------------------------------------------|
| 0a    | Guest                  | Guest             | *(no User object)*      | Landing page, public records, tenant directory |
| 0b    | Seeker                 | Seeker            | `seeker`                | Bible reader, personal records (limited), induction, no tenant membership |
| 1     | Foundational Disciple  | Member            | `disciple`              | Full personal records, join one tenant, learn |
| 2     | Active Contributor     | Disciple/Operator | `disciple`              | Org records, lead small groups within a node  |
| 3     | Functional Minister    | Steward           | `branch-steward` or higher | Manage teams, create programmes, confirm certs |
| 4     | Leader                 | Senior Steward    | `district-steward` or higher | Create governance records, manage tenant  |
| 5     | Apostolic Steward      | Architect         | `global-steward` or `admin` | Cross-tenant governance, Handbook write, system config |

**Level 0b (Seeker) access rules:**

- Can create personal records but limited to 10 total until Level 1 is reached
- Cannot join a tenant or participate in community features
- Can browse the Learning portal and begin induction / foundation programmes
- Can read scripture and create personal bible notes (subject to 10-record limit)
- Cannot see tenant (organizational) bible notes — no tenant membership
- Cannot see Handbook scripture references — Level 3+ read (Reference Library), Level 4+ read (Mandate Branch)

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

  // v10 Amendment 10.1: "induction" added to tier enum
  tier: "handbook | church_node | church_collective | district | provincial | national | regional | continental | global | induction",
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

Handbook read access is tiered by record type. Write remains Level 5 only.

```python
# Permission check algorithm (Part 7 Handbook branch):
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
| `programme`     | A governance-context structured programme (`record_class:'governance'`) |
| `calendar`      | A time-governed plan — **deferred to Phase 2**         |

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

Note: `has_subject` and `has_entity` are retired. Existing data using these types is retained in the DB but no new relationships of these types should be created. Migration of existing rows is deferred.

### 2.5.5 Induction Tenant — System Singleton (v10)

The Induction Tenant is seeded by `python manage.py seed_induction_tenant`. It has `tier: "induction"` and `path: "/global/induction/"`. It cannot be deleted or renamed via normal UI flows.

```js
InductionTenant = {
  name:        "Induction",
  slug:        "induction",
  path:        "/global/induction/",
  tier:        "induction",
  affiliation: "ichebo",
  status:      "active",
  settings: { allow_public_records: false, require_approval: false, max_members: null }
}
```

- **Content scoping:** users in the Induction Tenant see only Records with `metadata.source_app == "induction"`.
- **On induction completion:** Induction Tenant `UserPermission.is_active` set to `False`; home tenant `UserPermission` created (`level=1`, `role="disciple"`).

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

  record_type: "[see Part 3.2 type registry]",

  // Family → Type mapping (enforced at service layer):
  //   journal     → prayer | spirit | dream | dar | note
  //                 prayer    = personal prayer entry
  //                 spirit    = Spirit Journal entry (prophetic / hearing from God)
  //                 dream     = Dream Journal entry
  //                 dar       = Daily Activity Report (personal ministry summary)
  //                 note      = General journal / reflection entry
  //                 NOTE: 'sermon' and 'article' are retired. User-defined custom types
  //                 are planned for a future version — not in this contract.
  //   governance  → class | principle | concept | divine_pattern | narrative |
  //                 subject | entity | mandate | statement | programme |
  //                 framework | protocol | procedure
  //                 NOTE: "calendar" is registered in this family but deferred
  //                 to Governance App Phase 2. No UI is built for it in MVP.
  //   activity    → event | campaign | project | habit | task | skill
  //   learning    → programme | course | lesson | assignment | quiz | certification
  //   reference   → key | property | attachment (v10)
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
  // 'submitted'  = awaiting review by a higher authority
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
  // community/gathering: see Part 14.4 for custom_fields specification
  // governance/reference types: see Part 15.3 for Property Attributes custom_fields
  // reference/attachment (v10): custom_fields["file_url"] = presigned MinIO URL (1-hour expiry)

  metadata: {
    source_app:    "records | bible | activity | learn | community | governance | induction | ...",
    record_origin: "string | null",
    custom_field_definitions: []
  },

  permissions: {
    visibility:   "private | tenant | collective | public",
    // private    = only created_by can read
    // tenant     = any member of exactly this tenant can read
    // collective = this tenant + its parent chain up to the first Church Collective tier
    // public     = any authenticated user (Level 1 and above — Level 0b excluded)
    required_level: 1,
    roles_allowed:  [],
    can_edit:       [],
  },

  updated_at:    "ISO-8601",
  deleted_at:    "ISO-8601 | null"
}
```

### 3.2 Record Type Registry (full)

| record_family  | record_type values                                                                  | record_class       | Min level         |
|----------------|-------------------------------------------------------------------------------------|--------------------|-------------------|
| `journal`      | `prayer`, `spirit`, `dream`, `dar`, `note`                                          | `personal`         | 0b                |
| `governance`   | `class`, `principle`, `concept`, `divine_pattern`, `narrative`, `subject`, `entity`, `mandate`, `statement`, `programme`, `framework`, `protocol`, `procedure` | `governance` | 4 (write), 3 (read) |
| `activity`     | `event`, `campaign`, `project`, `habit`, `task`, `skill`                            | `organizational`   | 2                 |
| `learning`     | `programme`, `course`, `lesson`, `assignment`, `quiz`, `certification`              | `organizational`   | 1 (enrol), 4 (author) |
| `reference`    | `key`, `property`, `attachment` (v10)                                               | `personal` / `organizational` | 3 (key), 1 (property) |
| `bible`        | `bible_note`                                                                        | `personal`         | 0b                |
| `community`    | `announcement`, `gathering`, `report` (deferred), `pastoral_note` (deferred)       | `organizational`   | 1 (read), 3 (create) |

> **attachment (v10):** stores file metadata only. The file is stored in MinIO `ics-private` bucket. `custom_fields["file_url"]` carries the presigned URL (1-hour expiry). No separate Attachment model.

### 3.3 Relationship object

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

  // v10 Amendment 10.5: "community_ref" added (scheduled for Version 2.3)
  relationship_type: "relates_to | derived_from | references | answers | fulfills | requests | has_symbol | matches_pattern | assigned_to | tracks | completes | part_of | aligns_with | authorised_by | tagged_in | community_ref",

  notes:    "string | null",
  strength: "weak | medium | strong | null",   // enum — NOT float

  metadata: {},  // JSONField — extra context stored by the creating app

  deleted_at: "ISO-8601 | null"
}
```

### 3.4 Controlled relationship type vocabulary

**Activity App usage (Part 10.6):**

| Activity type       | Use relationship_type | Direction                            |
|---------------------|-----------------------|--------------------------------------|
| `task`, `habit`     | `tracks`              | activity_record → target_record      |
| `goal`, `reminder`  | `tracks`              | activity_record → target_record      |
| `campaign`, `event` | `aligns_with`         | activity_record → mandate/programme  |
| `project`           | `aligns_with`         | activity_record → campaign_record    |
| `skill`             | `aligns_with`         | skill_record → service_order_record  |

The Learn App exclusively uses `tracks` and `part_of`. Activity App links must not use `part_of` — reserved for curriculum and governance hierarchy structure.

**Community App usage:**

| Community record type | Use relationship_type | Direction                                |
|-----------------------|-----------------------|------------------------------------------|
| `gathering`           | `aligns_with`         | gathering_record → activity_event_record |
| `gathering`, `announcement` | `community_ref` (v10 — Version 2.3) | community_record → governance_record |

**Governance App usage:**

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

  // Identity
  title:          "string",
  description:    "string | null",

  // Timing
  scheduled_at:   "ISO-8601 | null",
  due_at:         "ISO-8601 | null",
  completed_at:   "ISO-8601 | null",  // set automatically on status → completed
  recurrence:     "none | daily | weekly | monthly | custom",
  recurrence_rule:"string | null",

  // Hierarchy
  parent_activity_id: "uuid | null",

  // v10 Amendment 10.4 — Explicit Record link (replaces loose metadata coupling)
  linked_record_id: "uuid | null",  // FK → records.Record, SET_NULL on delete
  // Replaces: metadata['programme_record_id'], metadata['lesson_record_id'] (deprecated)
  // New code MUST use linked_record_id. Old metadata keys retained for backward compat only.

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
    source_app:   "activity | paraclete | learn | governance | community | induction",
    icon:         "string | null",
    color:        "string | null",
    is_template:  false,
    template_id:  "uuid | null",
    service_order: "string | null",
    programme_record_id: "uuid | null",  // DEPRECATED — use linked_record_id
    lesson_record_id:    "uuid | null",  // DEPRECATED — use linked_record_id
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

Created by Django signal on every status transition. Immutable once written.

```js
ActivityLog = {
  id:           "uuid",
  tenant_id:    "uuid | null",
  created_by:   "uuid",
  created_at:   "ISO-8601",

  activity_id:    "uuid",
  event_type:     "created | status_changed | progress_updated | assigned | linked | commented",
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
  competence_level: 0 | 1 | 2 | 3 | 4 | 5,

  // Activity surface
  pending_count:    integer,
  overdue_count:    integer,
  due_today:        ActivityCard[],
  overdue_items:    ActivityCard[],
  habit_streaks:    HabitStreak[],   // { activity_id, title, streak, last_completed }

  // Reminders
  pending_reminders: ActivityCard[],

  // Learn
  active_enrolments: ProgrammeCard[],  // { record_id, title, progress }
  next_lesson:       LessonCard | null, // { record_id, title, programme_title, url }

  // Prompt
  discipline_prompt: "string",
  prompt_pathway:    "string",

  // DAR
  dar_today: DARCard | null,  // { record_id, title, created_at, url }

  // Suggestions (rule-based)
  suggestions: [{ text: "string", priority: 1|2|3, action_url: "string" }],
  suggestion_method: "rules | deferred",

  // Team (Level 3+)
  team_pending_count:  integer | null,
  team_overdue_count:  integer | null,
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

### 5.5 Paraclete endpoints

```
GET /api/paraclete/digest/        — full ParacleteDigest for the authenticated user
GET /api/paraclete/reminders/     — pending reminders only
GET /api/paraclete/prompt/        — discipline prompt only
GET /api/paraclete/suggest/{id}/  — suggestions for a specific record (deferred — stub in MVP)
POST /api/paraclete/respond/      — user responds to a suggestion (deferred — stub in MVP)
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
  community/        ← Community App (Django app, no models except MembershipRequest stub)
  governance/       ← Governance App (Django app, no models, UI layer only)
  calendar_app/     ← Calendar aggregation service (no models)
  paraclete/        ← Orchestration service (ParacletePrompt model only)
  frontend/         ← Static assets (CSS, storage.js, navbar.js)
  notifications/    ← Notification model (v10)
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
| Notification     | notifications | written by signals in other apps                     |

**Community App and Governance App own no models.** They are UI + coordination layers that write to Records, Activity, and UserPermission via their respective DRF endpoints.

---

## Part 7 — Permission Check Algorithm

```python
def can_access(user, record):
    # 1. Handbook short-circuit
    if record.tenant and record.tenant.tier == 'handbook':
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
    if record.permissions['visibility'] == 'private':
        return record.created_by == user.id

    if record.permissions['visibility'] == 'tenant':
        return UserPermission.objects.filter(
            user=user,
            tenant_path=record.tenant.path,
            is_active=True
        ).exists()

    if record.permissions['visibility'] == 'collective':
        return UserPermission.objects.filter(
            user=user,
            tenant_path__startswith=record.tenant.collective_root_path,
            is_active=True
        ).exists()

    if record.permissions['visibility'] == 'public':
        return user.competence_level >= 1  # Level 0b cannot see public org records

    # 4. Level gate
    if user.competence_level < record.permissions['required_level']:
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

**Note:** `UserPermission.metadata` is a JSONField. No GinIndex added in MVP. Add post-MVP if query times degrade.

---

## Part 9 — Cross-App Data Patterns

### 9.1 Record + Activity dual write

When the platform needs both a persistent Record and an active Activity for the same thing:

1. Create the Record first (`POST /api/records/`)
2. Create the Activity with `linked_record` set (`POST /api/activities/`)
3. Create the Relationship linking the two (`POST /api/relationships/`)
4. Wrap all three in `django.db.transaction.atomic()`

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

*(See Part 3.4)*

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

**Community events in Calendar:** Gathering events are `activity_type:'event'` Activities with `metadata.source_app:'community'`. The Calendar endpoint already queries the Activity table — community gatherings appear automatically. Filtering: `GET /api/calendar/events/?source_app=community`

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

## Part 12 — Learn App Engine (Data Patterns & Contracts)

### 12.1 Learning content structure

All learning content is stored as Records with `record_family: "learning"`. Curriculum structure is defined by `Relationship (relationship_type: "part_of")`.

- **Programme:** `record_class: "organizational"`, `record_type: "programme"`
- **Course:** `record_type: "course"` — linked to programme via `part_of`
- **Lesson:** `record_type: "lesson"` — linked to course via `part_of`. May have `custom_fields["video_url"]`
- **Assignment / Quiz:** `record_type: "assignment" | "quiz"`
- **Certification:** `record_type: "certification"` — created by signal when programme Activity reaches `progress: 100`

### 12.2 Enrolment pattern

Enrolment = `Activity (activity_type: "programme")`. No separate Enrolment model exists.

```js
{
  activity_type:  "programme",
  assigned_to:    user.id,
  linked_record:  programme_record.id,   // v10 — was metadata.programme_record_id
  status:         "in_progress",
  progress:       0-100,
  metadata: {
    source_app:  "learn",
    kgs_pathway: "Service"
  }
}
```

### 12.3 Five Qualification Programmes

| Programme | Level | Duration | Prerequisites |
|-----------|-------|----------|---------------|
| Certificate | 1 | 1 year | None |
| Diploma     | 2 | 3 years | Certificate |
| Degree      | 3 | 4 years | Diploma |
| Masters     | 4 | 4–5 years | Degree |
| Doctorate   | 5 | 7 years | Masters |

### 12.4 Three Induction Programmes (v10)

| Programme | Entrant type | Court |
|-----------|-------------|-------|
| Reconditioning Programme | Existing believers | Outer Court |
| Beginners Programme | Kingdom-curious newcomers | Outer Court |
| Community Programme | All inductees | Inner Court (auto-enrolled on Outer Court completion) |

### 12.5 CertificationConfirmation model

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid | |
| `certification_record_id` | uuid | FK → `records.Record` |
| `confirmed_by` | FK → User | The confirming steward (Level 3+) |
| `learner_id` | uuid | FK → User |
| `previous_competence_level` | integer | |
| `new_competence_level` | integer | |
| `confirmed_at` | ISO-8601 | `auto_now_add=True` |
| `notes` | string \| null | |
| `placement_tenant_id` | uuid \| null | Set when `context == "induction_completion"` (v10) |

### 12.6 `certifications/confirm/` — Extended Logic (v10)

**Standard behaviour (all calls):** set certification Record `status → "active"`; increment `competence_level` by 1 (via `learn/services.py::confirm_certification_record()` — the sole authorised write path); create `CertificationConfirmation` audit record.

**Extended behaviour when `metadata.context == "induction_completion"` (v10):**

Request body adds: `{ "placement_tenant_id": "uuid" }` (required)

In addition to standard logic:

1. Set `user.induction_completed_at = now()`
2. Create `UserPermission`: `tenant_id=placement_tenant_id`, `level=1`, `role="disciple"`, `is_active=True`
3. Deactivate Induction Tenant `UserPermission`: `is_active=False`
4. Write `ActivityLog`: `"Induction completed — placed in {tenant.name}"`
5. Send email notification via Brevo

**Validation:**
- `placement_tenant_id` required when `metadata.context == "induction_completion"`
- Confirming user must be Level 3+ within the Induction Tenant
- `placement_tenant_id` must be a valid, active, non-induction tenant

### 12.7 Learn App DRF endpoints

```
GET  /api/learn/health/
GET  /api/learn/programmes/{id}/curriculum/
GET  /api/learn/certifications/queue/
POST /api/learn/certifications/{id}/confirm/
```

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
| See Handbook references         | ✗        | ✗        | ✓ (Ref Library) | ✓ |

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
    format:           "in_person | digital | hybrid",
    location:         "string | null",
    stream_url:       "string | null",
    start_at:         "ISO-8601",            // v10: renamed from scheduled_at
    duration_minutes: "integer | null",      // v10: replaces capacity
  },
  permissions: { visibility: "tenant", required_level: 1 }
}
```

Access rules: Create = Level 3+; Read = Level 1+ within tenant; Cancel = creating steward or Level 4+.

### 14.4 Gathering dual-write pattern

Creating a gathering produces two objects atomically and links them with a Relationship. Both writes must succeed or both must fail (`transaction.atomic`).

```python
# Step 1 — Create gathering Record
# Step 2 — Create event Activity with linked_record = gathering_record.id (feeds Calendar App)
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

### 14.10 TenantInvitation model (v10 — Version 2.5)

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid | |
| `tenant_id` | uuid | FK → Tenant |
| `email` | string | Invitee email |
| `invited_by` | uuid | FK → User |
| `accepted_at` | datetime \| null | |
| `status` | string | `"pending \| accepted \| declined \| expired"` |
| `created_at` | ISO-8601 | |

Scheduled for Version 2.5 migration. See Part 18 migration schedule.

### 14.11 Community App DRF endpoints

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

# Gathering — dual write
POST   /api/activities/
PATCH  /api/activities/{id}/
POST   /api/relationships/

GET    /api/records/?record_family=community&record_type=gathering&tenant_id={id}

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
  complexity:            "string | null",
  relationship_position: "string | null",
  position:              "string | null",
  direction:             "string | null",
  speed:                 "string | null",
  emotional_tone:        "string | null",
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

```js
Record {
  record_class:   "personal",
  record_family:  "reference",
  record_type:    "key",
  title:          "string",    // the symbol or term (e.g. "Lion", "Water", "North")
  content:        "string",    // the operator's personal interpretation / meaning
  summary:        "string | null",
  tenant_id:      null,
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

# Rendered as a timeline:
#   v1 [locked, superseded] → v2 [locked, superseded] → v3 [active]
#   Each entry: version number, title, locked_at date, locked_by display_name
```

### 15.9 Journal → Governance linkage pattern

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

```
# Reference Library browse
GET  /api/records/?record_family=governance&record_class=governance&record_type={type}&tenant_id={handbook_id}
GET  /api/records/{id}/
GET  /api/records/{id}/related/   (v10 — Amendment 10.9)

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

## Part 16 — Notifications (v10)

### 16.1 Notification model

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid | |
| `user` | FK → User | |
| `notification_type` | string | `"announcement \| task_assigned \| certification_confirmed \| induction_completed \| level_advanced \| gathering_scheduled"` |
| `source_app` | string | `"community \| learn \| activity \| governance"` |
| `source_record_id` | uuid \| null | |
| `source_activity_id` | uuid \| null | |
| `message` | text | |
| `is_read` | boolean | Default `False` |
| `created_at` | datetime | `auto_now_add=True` |

### 16.2 Notification trigger points

| Event | Email? |
|-------|--------|
| Announcement created | No |
| Task `assigned_to` set | No |
| Certification confirmed | Yes (via Brevo) |
| Induction placement confirmed | Yes (via Brevo) |
| Record locked (Governance) | No |

### 16.3 Notification endpoints

```
GET  /api/notifications/
GET  /api/notifications/unread-count/
POST /api/notifications/{id}/read/
POST /api/notifications/read-all/
```

---

## Part 17 — Delta Sync API (v10)

For Flutter mobile client. Uses existing `updated_at` fields — no model changes required.

```
GET /api/sync/changes/?since={iso_timestamp}
```

**Response:**

```json
{
  "since":         "ISO-8601",
  "retrieved_at":  "ISO-8601",
  "has_more":      false,
  "records":       [],
  "activities":    [],
  "notifications": []
}
```

Max 500 items per type per call. Paginate using `since=` + last `updated_at` when `has_more: true`.

**Implementation:** New file `core/views/sync.py` — `SyncChangesView(APIView)`. New URL: `path('api/sync/changes/', ...)` in `ics_project/urls.py`.

---

## Part 18 — Migration Schedule

| When | App | Change |
|------|-----|--------|
| Pre-Build (done) | `activity` | `Activity.linked_record = FK(records.Record, SET_NULL, null=True)` |
| Pre-Build (done) | `records` | `Relationship.metadata = JSONField(default=dict)` |
| Before V2.1 G1 | `tenants` | `Tenant.tier` choices: add `"induction"` |
| Before V2.1 G2 | `accounts` | Add `induction_enrolled_at`, `induction_completed_at`, `induction_pathway` to User |
| Before V2.1 G2 | `accounts` | Add profile registration fields to UserProfile (`full_name`, `address`, `country`, `id_number` encrypted, `age`, `gender`, `occupation`, `education`, `born_again`) |
| Before V2.3 | `accounts` | Add `fcm_token` to User |
| Version 2.3 | `records` | `Relationship.relationship_type` choices: add `"community_ref"` |
| Version 2.5 | `tenants` | Add `coordinator_user` FK, `community_theme`, `area_of_operation`, `logo` ImageField |
| Version 2.5 | `community` | New `TenantInvitation` model |

---

## Part 19 — API Versioning Strategy

Current state: all endpoints at `/api/` (unversioned) — acceptable during development.

Before first mobile production release: all endpoints move to `/api/v1/`. The `v1` prefix is then frozen — breaking changes require `/api/v2/`.

**Breaking change:** removing a field, changing a field type, changing URL, changing HTTP method, changing auth requirement.

**Not a breaking change:** adding new optional fields.

---

## Part 20 — Complete Endpoint Reference

| App | Endpoints |
|-----|-----------|
| Auth | `POST /api/auth/register/` `POST /api/auth/login/` `POST /api/auth/logout/` `GET/PATCH /api/auth/me/` |
| Records | `GET/POST /api/records/` `GET/PATCH/DELETE /api/records/{id}/` `GET /api/records/{id}/related/` |
| Relationships | `GET/POST /api/relationships/` `GET/PUT/DELETE /api/relationships/{id}/` |
| Activities | `GET/POST /api/activities/` `GET/PATCH/DELETE /api/activities/{id}/` `GET /api/activities/{id}/log/` |
| Bible | `GET /api/bible/health/` `GET /api/bible/translations/` `GET /api/bible/books/` `GET /api/bible/verse-context/{id}/` `GET /api/bible/verses/` |
| Learn | `GET /api/learn/health/` `GET /api/learn/programmes/{id}/curriculum/` `GET /api/learn/certifications/queue/` `POST /api/learn/certifications/{id}/confirm/` |
| Calendar | `GET /api/calendar/events/` `GET /api/calendar/health/` |
| Paraclete | `GET /api/paraclete/digest/` `GET /api/paraclete/reminders/` `GET /api/paraclete/prompt/` `GET /api/paraclete/suggest/{id}/` `POST /api/paraclete/respond/` |
| Notifications | `GET /api/notifications/` `GET /api/notifications/unread-count/` `POST /api/notifications/{id}/read/` `POST /api/notifications/read-all/` |
| Sync | `GET /api/sync/changes/?since={iso_timestamp}` |
| Permissions | `GET /api/permissions/` `POST /api/permissions/` `PATCH /api/permissions/{id}/` |
| Community | `GET /api/community/health/` |
| Governance | `GET /api/governance/health/` |

---

## Deferred (Post-MVP / Future Versions)

### Platform-wide

- Full `RecordPermission` table (fine-grained per-user permissions)
- `CustomFieldSchema` formal validation system
- Video/Live streaming app
- In-service Display app
- Donations feature
- Advanced Paraclete AI features (pattern detection, auto-linking)
- User-defined custom journal record types (planned V2+ feature)
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
- Full month/week grid view (Phase 3)

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

- `MembershipRequest` model UI (model stubbed — Part 14.8)
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
