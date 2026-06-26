# Ichebo Platform — Data Contract & Architecture Document

> **Version:** v11 — 2026-05-13 (Canonical)
> **Previous version:** v10 — 2026-04-27
> **Status:** Approved — Canonical Reference
> **Supersedes:** All previous data contract versions (v1–v10)
>
> **How this document was produced:**
> v10 (2026-04-27) was the canonical consolidation of the full Version 2 data contract. This v11 applies the following amendments arising from the May 2026 ecosystem architecture session and the ADR set (ADR-012 through ADR-021):
>
> **v11 Amendments:**
> 1. Architecture statement updated — Apostolic Command Shell, DESIGN.md, and dual-shell pattern added as locked architectural facts (ADR-012, ADR-013, ADR-015).
> 2. Handbook-as-tenant superseded — Part 1 architecture statement amended per ADR-020. Handbook-as-tenant remains in production but is formally superseded by Ichebo Handbook standalone product direction.
> 3. Ecosystem architecture additions — Part 21 added: Sync Engine data contracts (ChangeLog table, SyncableMixin, push/pull endpoints, conflict rules). Required for Ichebo Desktop build planning.
> 4. Go engine specification note added — Part 22 added: language-agnostic engine specification reference. Both Go and Python/Django implementations must conform to this contract.
> 5. Part 23 added — Ichebo Desktop data scope. Defines which data domains are in scope for Ichebo Desktop MVP.
> 6. Migration schedule updated (Part 18) — UUID migration and soft delete pattern added as pre-Layer-5 requirements.
> 7. ADR cross-reference table added (Part 1) — maps data contract decisions to their governing ADRs.
>
> **Everything in v10 not listed above is carried forward unchanged and remains authoritative.**

> **For Claude:** When implementing, read this document fully before writing any code. All schemas, rules, and patterns here are authoritative. Do not infer from app code. For ecosystem (Version 3+) work, read the ADR set (ADR-012 through ADR-021) in addition to this document.

**Goal:** Define the complete, locked data contracts, service boundaries, and schema definitions for the Ichebo platform — the digital expression of the Kingdom Governance System (KGS) framework.

**Architecture:** Django 4.2 LTS + PostgreSQL backend (single source of truth for the cloud platform). Architecture decisions:
1. Materialised path for tenant hierarchy
2. Single records table with record_class discriminator
3. Paraclete as a standalone orchestration service separate from the Activity Engine
4. **v11 amendment:** Handbook-as-tenant is the current production implementation. ADR-020 formally supersedes this decision — Ichebo Handbook is a standalone product. The Handbook tenant at /global/handbook/ remains in production pending migration to the Ichebo Handbook product. No new features are built into the Handbook tenant.
5. Apostolic Command Shell as canonical desktop web interface (ADR-012)
6. DESIGN.md + design-preview.html as locked design system authority (ADR-013)
7. Dual-shell rendering (Stage Mode / Mobile Mode) as two first-class paths (ADR-015)

**UI Architecture (locked):** All web UIs are built in Django templates + HTMX. Stage Mode (Level 3+, desktop ≥1024px): Apostolic Command Shell four-column grid. Mobile Mode (all users, mobile): mobile-first shell with bottom navigation. No vanilla JS app files. storage.js retained for UI state only.

**Mobile (Flutter):** Flutter app targets Android (iOS Version 3+). All data access through DRF endpoints. Delta sync via GET /api/sync/changes/ (Part 17). Full Sync Engine for Ichebo Desktop (Part 21).

**Tech Stack:** Python/Django 4.2 LTS, Django REST Framework, PostgreSQL, Django templates, HTMX, Flutter (mobile + desktop), Go (foundation engines — Version 3+).

---

## ADR Cross-Reference

| ADR | Data contract impact |
|-----|---------------------|
| ADR-003 | Part 3 — single records table, record_class discriminator |
| ADR-006 | Part 1.5 — competence_level one write path |
| ADR-016 | Part 21 — local-first data rules (UUID PKs, soft deletes) |
| ADR-018 | Part 21 — Sync Engine data contracts |
| ADR-019 | Part 22 — Go engine language-agnostic specification |
| ADR-020 | Part 2.5 — Handbook-as-tenant superseded |
| ADR-011 | Part 12 — five qualification programmes, induction structure |

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

**Note:** BibleTranslation, BibleBook, and BibleVerse (Part 13) are exempt from this rule. They are read-only reference data loaded by management command, not governed platform entities.

### 1.2 record_class is the permission gate, not record_type

`record_type` describes *what* the record is (prayer, journal, mandate). `record_class` describes *how* the system governs it:

| record_class | Who creates | Default visibility | Mutable after creation | Example types |
|---|---|---|---|---|
| personal | Any user | private | Yes | journal, dream, prayer |
| organizational | Level 2+ | tenant | Yes, with audit | event, programme, campaign |
| governance | Level 4+ | tenant or public | Versioned only | mandate, statement, calendar |

Permission checks MUST read record_class before evaluating anything else.

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

`competence_level` may only be written by `POST /api/learn/certifications/{id}/confirm/`. No other code may write to this field. This is an absolute lock — ADR-006.

### 1.6 Single records table — no new model tables for content types

All content is stored in the single `records_record` table using the record_class / record_family / record_type discriminator. Do not create new model tables for new content types.

### 1.7 UUID primary keys on all models (Version 3+ requirement)

From the UUID migration (Phase E.1 in the roadmap), all model primary keys must be UUIDField(primary_key=True, default=uuid.uuid4). This applies to all cloud-side Django models and all local SQLite models for Ichebo Desktop. Records created offline must have a permanent UUID identity before reaching the cloud. This is a non-negotiable requirement of the local-first architecture (ADR-016) and the Sync Engine (ADR-018).

**Current production state (Version 2):** Models use UUIDs on Record, Activity, Relationship, Tenant, and UserPermission. User model uses Django's default integer PK. UUID migration (Phase E.1) addresses remaining models before Version 3 work begins.

### 1.8 Soft deletes — no hard deletes anywhere

All entities must carry a `deleted_at` DateTimeField(null=True, blank=True). Hard deletion via the DELETE HTTP method or ORM .delete() is prohibited. Instead: PATCH to set deleted_at. All default querysets filter to deleted_at IS NULL. This is required for Sync Engine conflict resolution and audit trail integrity.

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
  avatar_url:   "string | null", // @property returning avatar.url (MinIO ImageField)

  // Competence & Formation
  competence_level: 0 | 1 | 2 | 3 | 4 | 5,
  // SOLE WRITE PATH: POST /api/learn/certifications/{id}/confirm/
  // 0a = Guest (anonymous) — not stored; describes unauthenticated sessions
  // 0b = Seeker (registered, formation not yet started) — status: 'seeker'
  // 1–5 = active formation levels mapped to KGS

  // Platform status
  status: "seeker | active | suspended | pending_verification",

  // Settings (DB-persisted via JSONField — not localStorage)
  preferences: {
    theme:    "system | light | dark",
    language: "en | ...",
    timezone: "Africa/Johannesburg | ..."
  },

  // Induction tracking (v10 Amendment 10.2)
  induction_enrolled_at:  "ISO-8601 | null",
  induction_completed_at: "ISO-8601 | null",
  induction_pathway:      "reconditioning | beginners | null",

  // FCM push token (v10 Amendment 10.7)
  fcm_token: "string | null",  // Firebase Cloud Messaging — updated by Flutter app on login

  updated_at: "ISO-8601"
}
```

**UserProfile extension (Django model — accounts.UserProfile):**

```python
preferred_bible_translation = FK → bible.BibleTranslation (nullable)
bio = TextField(null=True, blank=True)

# v10 Amendment 10.3 — Profile registration fields (PII)
full_name   = CharField(max_length=255)
address     = TextField(null=True, blank=True)
country     = CharField(max_length=2, null=True)  # ISO 3166-1 alpha-2
id_number   = EncryptedCharField(null=True)       # National ID — ENCRYPTED
age         = IntegerField(null=True)
gender      = CharField(choices=['male','female','prefer_not_to_say'], null=True)
occupation  = CharField(max_length=255, null=True)
education   = TextField(null=True)
born_again  = BooleanField(null=True)
```

**SECURITY:** id_number stored encrypted (django-encrypted-model-fields). FIELD_ENCRYPTION_KEY in .env only. id_number is write_only in UserProfileSerializer. Access requires an explicit Level 4+ admin endpoint. Never returned in any standard API response.

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
    service_order: "string | null"
    // KGS Service Order label — string reference to ServiceOrder.slug
    // V2.4+: validated against ServiceOrder table
  }
}
```

### 2.3 Competence levels mapped to KGS

| Level | KGS Name | Platform label | Role token | What they can do |
|---|---|---|---|---|
| 0a | Guest | Guest | (no User object) | Landing page, public records, tenant directory |
| 0b | Seeker | Seeker | seeker | Bible reader, personal records (limited), induction, no tenant membership |
| 1 | Foundational Disciple | Member | disciple | Full personal records, join one tenant, learn |
| 2 | Active Contributor | Disciple/Operator | disciple | Org records, lead small groups within a node |
| 3 | Functional Minister | Steward | branch-steward or higher | Manage teams, create programmes, confirm certs |
| 4 | Leader | Senior Steward | district-steward or higher | Create governance records, manage tenant |
| 5 | Apostolic Steward | Architect | global-steward or admin | Cross-tenant governance, Handbook write, system config |

**Level 0b (Seeker) access rules:**
- Can create personal records but limited to 10 total until Level 1
- Cannot join a tenant or participate in community features
- Can browse the Learning portal and begin induction programmes
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

  tier: "handbook | church_node | church_collective | district | provincial | national | regional | continental | global | induction",
  affiliation: "ichebo | independent | affiliate",
  status: "active | pending | suspended",
  is_collective: false,

  // V2.5 additions
  coordinator_user:  "uuid | null",  // FK → User
  community_theme:   "string | null",
  area_of_operation: "string | null",
  is_agency:         false,          // True for 6 constitutional service domain tenants

  description:  "string | null",
  logo_url:     "string | null",
  location: {
    country:     "string",
    province:    "string",
    city:        "string",
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

## Part 2.5 — The Handbook (Current Production Implementation)

> **v11 Amendment — ADR-020:** The Handbook-as-tenant is the current production implementation and remains in operation. ADR-020 formally supersedes the Handbook-as-tenant architectural decision. Ichebo Handbook is a standalone product that will eventually replace this implementation. No new features are to be built into the Handbook tenant. The migration path is defined in ADR-020.

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
  is_agency:   false,
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
if record.tenant.tier == "handbook":
    if record.record_type in REFERENCE_LIBRARY_TYPES:
        return user.competence_level >= 3   # read
    else:
        return user.competence_level >= 4   # read (Mandate branch)
# Write always requires competence_level >= 5

REFERENCE_LIBRARY_TYPES = ["class", "principle", "concept", "divine_pattern"]
```

| Access type | Reference Library types | Mandate branch types | Write (all types) |
|---|---|---|---|
| Level 3+ | ✓ Read | ✗ | ✗ |
| Level 4+ | ✓ Read | ✓ Read | ✗ |
| Level 5 | ✓ Read | ✓ Read | ✓ Write |

### 2.5.3 Governance types (Handbook-authored records)

| Type | Description |
|---|---|
| class | A category or classification of knowledge |
| principle | A foundational rule or truth |
| concept | An idea or theological construct |
| divine_pattern | A recurring pattern observed in scripture/governance |
| narrative | A story or account carrying governance meaning |
| subject | A topic or domain of study |
| entity | A named actor, body, or structure |
| framework | A structured system of related principles |
| protocol | A defined sequence of steps for an occasion |
| procedure | An operational process for recurring tasks |
| mandate | A directive from the Kingdom Mandate |
| statement | A formal declaration or position |
| programme | A governance-context structured programme (record_class: governance) |
| calendar | A time-governed plan — **deferred to Governance App Phase 2** |

**Handbook ↔ Scripture linkage:** A Level 5 Architect may link any governance record to specific BibleVerse rows using a Relationship with relationship_type: "references", direction: "directed", and bible_verse_id set (Part 3.2).

### 2.5.4 Hierarchy and Relationship System (HRS)

Core HRS relationship types:

| relationship_type | From → To example |
|---|---|
| part_of | governance_principle → governance_framework |
| derived_from | governance_concept → governance_divine_pattern |
| aligns_with | governance_programme → governance_mandate |
| authorised_by | governance_procedure → governance_mandate |
| references | governance_narrative → governance_subject |
| references | governance_record → BibleVerse (via bible_verse_id) |

Note: has_subject and has_entity are retired. Existing data using these types is retained in the DB but no new relationships of these types should be created.

### 2.5.5 Induction Tenant — System Singleton

The Induction Tenant is the onboarding entry point for all new platform users.

```js
InductionTenant = {
  id:     "induction-singleton-uuid",
  name:   "Induction",
  slug:   "induction",
  path:   "/global/induction/",
  tier:   "induction",
  status: "active",
  is_agency: false
}
```

All new users (status: "seeker") are automatically assigned a UserPermission for the Induction Tenant on registration (level: 0, role: "seeker", is_active: true). This UserPermission is deactivated (is_active: false) on induction completion and placement.

### 2.5.6 Six Agency Tenants — Constitutional (V2.4)

The six KGS Service Domain Agency Tenants are constitutional — they cannot be created, renamed, or deleted via the self-service UI. They are seeded by management command.

| Slug | Name | Orders |
|---|---|---|
| apostolic-ministry | Apostolic & Spiritual Ministry | 1–4 |
| leadership-governance | Leadership & Governance Support | 5–8 |
| formation-teaching | Formation & Teaching | 9–12 |
| mission-outreach | Mission & Outreach | 13–16 |
| community-life-care | Community Life & Care | 17–20 |
| operations-stewardship | Operations & Stewardship | 21–24 |

All have path: "/global/{slug}/" and parent: Prime Tenancy. is_agency: true. Excluded from tenant self-service create/edit/delete UI.

---

## Part 3 — Records Engine Schema

### 3.1 Record object

```js
Record = {
  // Core (mandatory)
  id:           "uuid",
  tenant_id:    "uuid | null",
  created_by:   "uuid",
  created_at:   "ISO-8601",

  // Classification
  record_class:  "personal | organizational | governance",
  record_family: "journal | governance | activity | learning | reference | bible | community",
  record_type:   "string",   // see Part 3.2 for full registry

  // Content
  title:    "string",
  content:  "string | null",
  summary:  "string | null",

  // Status
  status:              "draft | active | completed | archived | locked | superseded | submitted",
  previous_version_id: "uuid | null",
  superseded_by:       "uuid | null",

  // Custom fields (JSONField — per-record-type extensions)
  custom_fields: {},

  // Metadata
  metadata: {
    source_app:    "records | bible | activity | learn | community | governance | induction | ...",
    record_origin: "string | null",
    custom_field_definitions: []
  },

  permissions: {
    visibility:   "private | tenant | collective | public",
    required_level: 1,
    roles_allowed:  [],
    can_edit:       [],
  },

  updated_at:    "ISO-8601",
  deleted_at:    "ISO-8601 | null"
}
```

### 3.2 Record Type Registry (full)

| record_family | record_type values | record_class | Min level |
|---|---|---|---|
| journal | prayer, spirit, dream, dar, note | personal | 0b |
| governance | class, principle, concept, divine_pattern, narrative, subject, entity, mandate, statement, programme, framework, protocol, procedure | governance | 4 (write), 3 (read) |
| activity | event, campaign, project, habit, task, skill | organizational | 2 |
| learning | programme, course, lesson, assignment, quiz, certification | organizational | 1 (enrol), 4 (author) |
| reference | key, property, attachment | personal / organizational | 3 (key), 1 (property) |
| bible | bible_note | personal | 0b |
| community | announcement, gathering, report (deferred), pastoral_note (deferred) | organizational | 1 (read), 3 (create) |

> **attachment:** stores file metadata only. File stored in MinIO ics-private bucket. custom_fields["file_url"] carries the presigned URL (1-hour expiry). No separate Attachment model.

### 3.3 Relationship object

```js
Relationship = {
  id:           "uuid",
  tenant_id:    "uuid | null",
  created_by:   "uuid",
  created_at:   "ISO-8601",

  from_record_id: "uuid",
  to_record_id:   "uuid | null",
  bible_verse_id: "uuid | null",
  // Constraint: exactly one of to_record_id or bible_verse_id must be non-null.
  // Enforced by: model .clean() + DRF serializer validation.

  direction: "directed | bidirectional",
  relationship_type: "relates_to | derived_from | references | answers | fulfills | requests | has_symbol | matches_pattern | assigned_to | tracks | completes | part_of | aligns_with | authorised_by | tagged_in | community_ref",

  notes:    "string | null",
  strength: "weak | medium | strong | null",  // enum — NOT float

  metadata: {},  // JSONField

  deleted_at: "ISO-8601 | null"
}
```

### 3.4 Controlled relationship type vocabulary

**Activity App usage:**

| Activity type | Use relationship_type | Direction |
|---|---|---|
| task, habit | tracks | activity_record → target_record |
| goal, reminder | tracks | activity_record → target_record |
| campaign, event | aligns_with | activity_record → mandate/programme |
| project | aligns_with | activity_record → campaign_record |
| skill | aligns_with | skill_record → service_order_record |

**Community App usage:**

| Community record type | Use relationship_type | Direction |
|---|---|---|
| gathering | aligns_with | gathering_record → activity_event_record |
| gathering, announcement | community_ref (Version 2.3+) | community_record → governance_record |

**Governance App usage:**

| Governance record type | Use relationship_type | Direction |
|---|---|---|
| governance → governance | part_of | concept → framework |
| governance → governance | derived_from | mandate → divine_pattern |
| governance → governance | aligns_with | programme → mandate |
| governance → governance | authorised_by | procedure → mandate |
| governance → governance | references | narrative → subject |
| governance → BibleVerse | references | governance_record → BibleVerse |
| key (personal) → journal entry | derived_from | key_record → journal_entry |
| mandate → journal entry | derived_from | mandate_record → spirit_journal_entry |

---

## Part 4 — Activity Engine Schema

### 4.1 Activity object

```js
Activity = {
  id:           "uuid",
  tenant_id:    "uuid | null",
  created_by:   "uuid",
  created_at:   "ISO-8601",

  activity_type: "task | habit | goal | event | campaign | project | programme | reminder | skill",

  title:          "string",
  description:    "string | null",

  scheduled_at:   "ISO-8601 | null",
  due_at:         "ISO-8601 | null",
  completed_at:   "ISO-8601 | null",
  recurrence:     "none | daily | weekly | monthly | custom",
  recurrence_rule:"string | null",

  parent_activity_id: "uuid | null",
  linked_record_id:   "uuid | null",  // FK → records.Record, SET_NULL on delete

  status:   "pending | in_progress | completed | cancelled | deferred",
  progress: 0,  // 0–100

  assigned_to: "uuid | null",

  kgs_pillar:  "apostolic | strategy | formation | programmes | mission | communities | stewardship | null",
  kgs_pathway: "new_life | spiritual_formation | community_life | service | leadership | learning | mission | apostolic_stewardship | null",

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

### 4.1.1 skill activity type

| Field | Usage |
|---|---|
| title | Name of the gift or skill (e.g. "Teaching", "Administration") |
| description | How this gift manifests in ministry |
| progress | Self-assessed competence: 0–100 |
| kgs_pathway | Which Kingdom Pathway this gift primarily serves |
| metadata.service_order | KGS Service Order this gift aligns with |
| status | active = current gift; archived = no longer active |
| tenant_id | null = personal register; tenant-scoped = visible to steward |

### 4.2 ActivityLog object

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

Created by Django signal on every status transition. Immutable once written.

### 4.3 Activity assignment model

| Who | Can assign to | Constraint |
|---|---|---|
| Level 1–2 (personal) | Self only (assigned_to = created_by) | Personal activities only |
| Level 3+ (steward) | Any user within their scope_path | activity.tenant_id within assigning user's UserPermission.tenant_path |
| Level 3+ (steward) | assigned_to = null (team-visible) | For campaign/project containers |

---

## Part 5 — Paraclete Service Contract

The Paraclete is a standalone orchestration service. It does NOT own any data. It reads from other engines and produces suggestions, reminders, and insights. It never writes directly to Records or Activities.

### 5.1 Responsibilities
- Reading user's activities, records, and schedules to generate intelligent reminders
- Detecting patterns across records (recurring dream symbols, prayer themes, habit streaks)
- Producing "today's focus" digest based on competence level, active activities, and KGS calendar
- Surfacing record link suggestions based on content similarity
- Generating discipline prompts aligned to the user's KGS pathway

### 5.2 ParacleteDigest object

```js
ParacleteDigest = {
  user_id:         "uuid",
  generated_at:    "ISO-8601",
  competence_level: 0 | 1 | 2 | 3 | 4 | 5,

  pending_count:    integer,
  overdue_count:    integer,
  due_today:        ActivityCard[],
  overdue_items:    ActivityCard[],
  habit_streaks:    HabitStreak[],

  pending_reminders: ActivityCard[],

  active_enrolments: ProgrammeCard[],
  next_lesson:       LessonCard | null,

  discipline_prompt: "string",
  prompt_pathway:    "string",

  dar_today: DARCard | null,

  suggestions: [{ text: "string", priority: 1|2|3, action_url: "string" }],
  suggestion_method: "rules | deferred",

  team_pending_count:  integer | null,
  team_overdue_count:  integer | null,
}
```

### 5.3 Paraclete endpoints

```
GET /api/paraclete/digest/
GET /api/paraclete/reminders/
GET /api/paraclete/prompt/
GET /api/paraclete/suggest/{id}/   (stub in MVP)
POST /api/paraclete/respond/        (stub in MVP)
```

---

## Part 6 — Django App Structure & File Map

### 6.1 Django apps (canonical list)

```
~/ics/
  ics_project/      ← Django project settings + root URLs
  accounts/         ← User, UserProfile, UserPermission models + auth
  tenants/          ← Tenant model + path resolution + ServiceOrder model
  records/          ← Record + Relationship models (Records Engine)
  activity/         ← Activity + ActivityLog models (Activity Engine)
  learn/            ← CertificationConfirmation model + curriculum endpoint
  bible/            ← BibleTranslation, BibleBook, BibleVerse models
  community/        ← Community App (UI + coordination, no models except MembershipRequest stub)
  governance/       ← Governance App (UI layer only, no models)
  calendar_app/     ← Calendar aggregation service (no models)
  paraclete/        ← Orchestration service (ParacletePrompt model only)
  video_live/       ← Video / Live App (no models — uses Activity + records)
                      [SUPERSEDED 2026-06-23, see video-direction-v2-plan.md — already stale
                       before that document: BroadcastSchedule is a real model. video_live
                       is now models/webhooks infrastructure only (BroadcastSchedule, the
                       Go-engine webhook views); its app templates/views/URLs and sidebar
                       icon are retired. Consumed directly by community/ and learn/.]
  notifications/    ← Notification model
  frontend/         ← Static assets (CSS, storage.js, navbar.js)
```

### 6.2 App ownership rules

| Model | Owner app | Other apps may... |
|---|---|---|
| Record | records | read via DRF only |
| Relationship | records | read/write via DRF only |
| Activity | activity | read via DRF; Community App creates via DRF |
| ActivityLog | activity | read via DRF only |
| UserPermission | accounts | read/write via DRF; Community App writes metadata fields |
| BibleVerse | bible | read via DRF; referenced by Relationship FK |
| BibleTranslation | bible | read via DRF; FK dep in accounts.UserProfile |
| Tenant | tenants | read via DRF only |
| ServiceOrder | tenants | read via DRF only |
| Notification | notifications | written by signals in other apps |

Community App and Governance App own no models.

---

## Part 7 — Permission Check Algorithm

```python
def can_access(user, record):
    # 1. Handbook short-circuit
    if record.tenant and record.tenant.tier == 'handbook':
        REFERENCE_LIBRARY_TYPES = ['class', 'principle', 'concept', 'divine_pattern']
        if record.record_type in REFERENCE_LIBRARY_TYPES:
            return user.competence_level >= 3
        else:
            return user.competence_level >= 4
        # Write always requires competence_level >= 5 (handled at ViewSet level)

    # 2. record_class gate (check FIRST before anything else)
    if record.record_class == 'governance' and user.competence_level < 4:
        return False

    # 3. Visibility scope
    if record.permissions['visibility'] == 'private':
        return record.created_by == user.id

    if record.permissions['visibility'] == 'tenant':
        return UserPermission.objects.filter(
            user=user, tenant_path=record.tenant.path, is_active=True
        ).exists()

    if record.permissions['visibility'] == 'collective':
        return UserPermission.objects.filter(
            user=user,
            tenant_path__startswith=record.tenant.collective_root_path,
            is_active=True
        ).exists()

    if record.permissions['visibility'] == 'public':
        return user.competence_level >= 1

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

Note: UserPermission.metadata is a JSONField. Add GinIndex post-MVP if query times degrade.

---

## Part 9 — Cross-App Data Patterns

### 9.1 Record + Activity dual write

```python
# Step 1 — Create the Record first
# Step 2 — Create the Activity with linked_record set
# Step 3 — Create the Relationship linking the two
# Wrap all three in django.db.transaction.atomic()
```

Used by: Learn App (programme enrolment), Community App (gathering create).

### 9.2 Learn App: scripture_reference convention

```js
custom_fields: {
  scripture_reference: "JHN 3:16"
  // Format: "{BOOK_CODE} {chapter}:{verse}"
  // Range: "ROM 8:1-4"
}
```

---

## Part 10 — Activity App Engine

### 10.1 Two-surface model

```
Activity App
  ├── "My Activities"  (personal — tenant_id: null)
  │     Types: task, habit, goal, skill, reminder
  │     Nesting: flat only
  │
  └── "Ministry"  (organisational — tenant-scoped)
        Types: task, habit, event, campaign, project, reminder
        Nesting: two-level (campaign/project → task)
        "Assigned to me" queue — first-class tab
        Create: campaign/project = Level 3+; task = Level 1+
```

### 10.2 Required API filters

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

### 11.1 Calendar event object

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

### 11.2 Calendar endpoint

```
GET /api/calendar/events/
    ?from={ISO-8601-date}
    &to={ISO-8601-date}
    &tenant_id={uuid}
    &activity_type={type}
    &source_app={app}
```

Returns: CalendarEvent[] sorted by scheduled_at ascending, then due_at.

---

## Part 12 — Learn App Engine

### 12.1 Learning content structure

All learning content is stored as Records with record_family: "learning". Curriculum structure is defined by Relationship (relationship_type: "part_of").

- **Programme:** record_class: "organizational", record_type: "programme"
- **Course:** record_type: "course" — linked to programme via part_of
- **Lesson:** record_type: "lesson" — linked to course via part_of. May have custom_fields["video_url"]
- **Assignment / Quiz:** record_type: "assignment" | "quiz"
- **Certification:** record_type: "certification" — created by signal when programme Activity reaches progress: 100

### 12.2 Enrolment pattern

Enrolment = Activity (activity_type: "programme"). No separate Enrolment model.

```js
{
  activity_type:   "programme",
  assigned_to:     user.id,
  linked_record:   programme_record.id,
  status:          "in_progress",
  progress:        0-100,
  metadata: { source_app: "learn", kgs_pathway: "Service" }
}
```

### 12.3 Five Qualification Programmes (KGS canonical — ADR-011)

| Programme | Level | KGS Qualification | Duration | Prerequisites |
|---|---|---|---|---|
| New Life Programme | 1 | Certificate | 1 year | Induction Training |
| Foundation Programme | 2 | Diploma | 3 years | New Life Programme |
| Leaders Programme | 3 | Degree | 6–12 months | Foundation Programme |
| Builders Programme | 4 | Masters | 6–12 months | Leaders Programme |
| Architect's Programme | 5 | Doctorate | 2 years | Builders Programme |

### 12.4 Induction Training (canonical — ADR-011)

Induction Training is a record_type: "course" inside New Life Programme — not a standalone programme. All four lessons are required for all entrant types:

| Lesson | Covers |
|---|---|
| Keys To the Kingdom | Beginners pathway foundation |
| Repentance & Reformation | Reconditioning pathway |
| Community Programme | Sceptre Community life |
| The Secret of Living a Fulfilled Life — HAL Beginners | Practical formation |

induction_pathway on the User model records background context only — it does not gate individual lessons.

### 12.5 CertificationConfirmation model

| Field | Type | Notes |
|---|---|---|
| id | uuid | |
| certification_record_id | uuid | FK → records.Record |
| confirmed_by | FK → User | The confirming steward (Level 3+) |
| learner_id | uuid | FK → User |
| previous_competence_level | integer | |
| new_competence_level | integer | |
| confirmed_at | ISO-8601 | auto_now_add=True |
| notes | string | null | |
| placement_tenant_id | uuid | null | Set when context == "induction_completion" |

### 12.6 certifications/confirm/ extended logic

**Standard behaviour:** set certification Record status → "active"; increment competence_level by 1; create CertificationConfirmation audit record.

**Extended behaviour when metadata.context == "induction_completion":**

Request body adds: { "placement_tenant_id": "uuid" } (required)

In addition to standard logic:
1. Set user.induction_completed_at = now()
2. Create UserPermission: tenant_id=placement_tenant_id, level=1, role="disciple", is_active=True
3. Deactivate Induction Tenant UserPermission: is_active=False
4. Write ActivityLog: "Induction completed — placed in {tenant.name}"
5. Send email notification via Brevo

### 12.7 Learn App DRF endpoints

```
GET  /api/learn/health/
GET  /api/learn/programmes/{id}/curriculum/
GET  /api/learn/certifications/queue/
POST /api/learn/certifications/{id}/confirm/
```

---

## Part 13 — Bible App Engine

### 13.1 Bible data model

```python
BibleTranslation { id: uuid, code: string, name, language, is_default: boolean, ... }
BibleBook { id: integer, code: string, name, testament: 'OT'|'NT', order: integer }
BibleVerse { id: uuid, translation: FK, book: FK, chapter: integer, verse: integer, text: string }
# unique_together: (translation, book, chapter, verse)
```

### 13.2 Default translations loaded at setup

| Code | Name | Language | Copyright | Default |
|---|---|---|---|---|
| KJV | King James Version | English | Public Domain | Yes |
| ASV | American Standard Version | English | Public Domain | No |
| WEB | World English Bible | English | Public Domain | No |

### 13.3 Bible note Record pattern

record_family: "bible", record_type: "bible_note", record_class: "personal". Linked to verse via Relationship with bible_verse_id set.

### 13.4 Bible App access rules by competence level

| Feature | Level 0b | Level 1+ | Level 3+ | Level 5 |
|---|---|---|---|---|
| Read scripture | ✓ | ✓ | ✓ | ✓ |
| Switch translation | ✓ | ✓ | ✓ | ✓ |
| Create personal bible note | ✓ (limit 10) | ✓ | ✓ | ✓ |
| See tenant (community) notes | ✗ | ✓ | ✓ | ✓ |
| Publish tenant note | ✗ | ✗ | ✓ | ✓ |
| See Handbook references | ✗ | ✗ | ✓ (Ref Library) | ✓ |

### 13.5 Bible App DRF endpoints

```
GET  /api/bible/health/
GET  /api/bible/translations/
GET  /api/bible/books/
GET  /api/bible/verses/?book_code={code}&chapter={n}
GET  /api/bible/verse-context/{verse_id}/
```

---

## Part 14 — Community App Engine

The Community App owns no models. It is a UI and transaction coordination layer.

### 14.1 Community Record types

**announcement:** record_class: "organizational", record_family: "community", record_type: "announcement". Create = Level 3+. Read = Level 1+ within tenant.

**gathering:** record_class: "organizational", record_family: "community", record_type: "gathering".

```js
custom_fields: {
  format:           "in_person | digital | hybrid",
  location:         "string | null",
  stream_url:       "string | null",
  start_at:         "ISO-8601",
  duration_minutes: "integer | null",
}
```

### 14.2 Gathering dual-write pattern

Creating a gathering produces two objects atomically (transaction.atomic):
1. Create gathering Record
2. Create event Activity with linked_record = gathering_record.id
3. Link Record → Activity via Relationship (aligns_with, directed)

### 14.3 TenantInvitation model (V2.5)

| Field | Type | Notes |
|---|---|---|
| id | uuid | |
| tenant_id | uuid | FK → Tenant |
| email | string | Invitee email |
| invited_by | uuid | FK → User |
| token | string | urlsafe token, unique |
| status | string | pending | accepted | declined | expired |
| accepted_at | datetime | null | |
| expires_at | datetime | 7 days from created_at |
| created_at | ISO-8601 | |

**Accept logic:** check pending + not expired → resolve user by email → check competence_level >= 1 → create UserPermission → set accepted.

### 14.4 MembershipRequest model (stub — no UI in Version 2)

```python
class MembershipRequest(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tenant      = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)
    status      = models.CharField(choices=[('pending','Pending'),('approved','Approved'),('denied','Denied')], default='pending')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    note        = models.TextField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
```

---

## Part 15 — Governance App Engine

The Governance App owns no models. It is a UI and coordination layer over the Records Engine.

### 15.1 Three-surface model

```
Governance App
  ├── Reference Library  (Level 3+ read, Level 5 write)
  │     Record types: class, principle, concept, divine_pattern
  │     Tenant scope: Handbook only
  │
  ├── Mandate Branch  (Level 4+ read, Level 5 write)
  │     Record types: mandate, statement, framework, narrative, subject,
  │                   entity, protocol, procedure, programme
  │     Tenant scope: Handbook only
  │
  └── Keys Library  (owner only — Level 3+)
        Record type: key
        Tenant scope: null (personal records)
```

### 15.2 Property Attributes custom_fields (Reference Library types)

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

Free-text fields — not validated as enums.

### 15.3 Governance record lifecycle

```
draft → active → locked → superseded
```

| Status | Description | Who transitions |
|---|---|---|
| draft | Being authored; not published | Creator (Level 5) |
| active | Published and in effect | Creator (Level 5) |
| locked | Finalised; no further edits | Level 5 only |
| superseded | Replaced by newer version; retained for history | Level 5 only |

**Version chain:** previous_version_id and superseded_by fields enable traversal. When creating a new version: (1) lock the old record, (2) create new record with previous_version_id pointing to the old one, (3) PATCH old record's superseded_by to point to the new one.

### 15.4 Governance App record type authority matrix

| Record Type | Surface | Read | Write / Lock | Tenant Scope |
|---|---|---|---|---|
| class, principle, concept, divine_pattern | Reference Library | Level 3+ | Level 5 | Handbook |
| mandate, statement, framework, narrative, subject, entity, protocol, procedure, programme | Mandate Branch | Level 4+ | Level 5 | Handbook |
| key | Keys Library | Owner only | Level 3+ (own keys) | null (personal) |
| calendar | — Phase 2 — | — | — | — |

---

## Part 16 — Notifications

### 16.1 Notification model

| Field | Type | Notes |
|---|---|---|
| id | uuid | |
| user | FK → User | |
| notification_type | string | announcement | task_assigned | certification_confirmed | induction_completed | level_advanced | gathering_scheduled | tenant_invitation | member_added | member_removed |
| source_app | string | community | learn | activity | governance | tenants |
| source_record_id | uuid | null | |
| source_activity_id | uuid | null | |
| message | text | |
| is_read | boolean | Default False |
| created_at | datetime | auto_now_add=True |

### 16.2 Notification trigger points

| Event | Email (Brevo)? |
|---|---|
| Announcement created | No |
| Task assigned_to set | No |
| Certification confirmed | Yes |
| Induction placement confirmed | Yes |
| Record locked (Governance) | No |
| TenantInvitation created | Yes |
| Member added / removed | No |

### 16.3 Notification endpoints

```
GET  /api/notifications/
GET  /api/notifications/unread-count/
POST /api/notifications/{id}/read/
POST /api/notifications/read-all/
```

---

## Part 17 — Delta Sync API (Flutter Mobile)

For Flutter mobile client. Uses existing updated_at fields — no model changes required.

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

Max 500 items per type per call. Paginate using since= + last updated_at when has_more: true.

**Note:** This endpoint is for the Flutter mobile app. The full Sync Engine (Part 21) is for Ichebo Desktop. Both coexist.

---

## Part 18 — Migration Schedule

| When | App | Change |
|---|---|---|
| Pre-Build (done) | activity | Activity.linked_record = FK(records.Record, SET_NULL, null=True) |
| Pre-Build (done) | records | Relationship.metadata = JSONField(default=dict) |
| V2.1 (done) | tenants | Tenant.tier choices: add "induction" |
| V2.2 (done) | accounts | Add induction_enrolled_at, induction_completed_at, induction_pathway to User |
| V2.2 (done) | accounts | Add profile registration fields to UserProfile |
| V2.3 (done) | accounts | Add fcm_token to User |
| V2.3 (done) | records | Relationship.relationship_type choices: add "community_ref" |
| V2.4 (done) | tenants | Add ServiceOrder model, seed 24 orders |
| V2.5 (done) | tenants | Add coordinator_user, community_theme, area_of_operation, is_agency to Tenant |
| V2.5 (done) | tenants | Add TenantInvitation model |
| Pre-Layer-5 | all | UUID primary key migration — all model PKs to UUIDField |
| Pre-Layer-5 | all | Soft delete pattern — deleted_at on all models |
| Layer-5 (E.1) | core | ChangeLog table (SQLite + PostgreSQL) for Sync Engine |
| Layer-5 (E.4) | core | POST /api/sync/push/ and GET /api/sync/pull/?since= endpoints |

---

## Part 19 — API Versioning Strategy

Current state: all endpoints at /api/ (unversioned) — acceptable during development.

Before first mobile production release: all endpoints move to /api/v1/. The v1 prefix is then frozen — breaking changes require /api/v2/.

**Breaking change:** removing a field, changing a field type, changing URL, changing HTTP method, changing auth requirement.

**Not a breaking change:** adding new optional fields.

---

## Part 20 — Complete Endpoint Reference

| App | Endpoints |
|---|---|
| Auth | POST /api/auth/register/ POST /api/auth/login/ POST /api/auth/logout/ GET/PATCH /api/auth/me/ |
| Records | GET/POST /api/records/ GET/PATCH/DELETE /api/records/{id}/ GET /api/records/{id}/related/ |
| Relationships | GET/POST /api/relationships/ GET/PUT/DELETE /api/relationships/{id}/ |
| Activities | GET/POST /api/activities/ GET/PATCH/DELETE /api/activities/{id}/ GET /api/activities/{id}/log/ |
| Bible | GET /api/bible/health/ GET /api/bible/translations/ GET /api/bible/books/ GET /api/bible/verse-context/{id}/ GET /api/bible/verses/ |
| Learn | GET /api/learn/health/ GET /api/learn/programmes/{id}/curriculum/ GET /api/learn/certifications/queue/ POST /api/learn/certifications/{id}/confirm/ |
| Calendar | GET /api/calendar/events/ GET /api/calendar/health/ |
| Paraclete | GET /api/paraclete/digest/ GET /api/paraclete/reminders/ GET /api/paraclete/prompt/ GET /api/paraclete/suggest/{id}/ POST /api/paraclete/respond/ |
| Notifications | GET /api/notifications/ GET /api/notifications/unread-count/ POST /api/notifications/{id}/read/ POST /api/notifications/read-all/ |
| Sync (mobile) | GET /api/sync/changes/?since={iso_timestamp} |
| Sync (desktop) | POST /api/sync/push/ GET /api/sync/pull/?since={iso_timestamp}&device_id={uuid} |
| Permissions | GET /api/permissions/ POST /api/permissions/ PATCH /api/permissions/{id}/ |
| Community | GET /api/community/health/ |
| Governance | GET /api/governance/health/ |

---

## Part 21 — Sync Engine Data Contracts (Ichebo Desktop)

> **Reference:** ADR-018. This part defines the data contracts required for the full Sync Engine — distinct from the Delta Sync API (Part 17) which serves Flutter mobile.

### 21.1 SyncableMixin (Django model base — cloud side)

All models that participate in sync must inherit SyncableMixin:

```python
import uuid
from django.db import models

class SyncableMixin(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)  # soft delete
    device_id  = models.UUIDField(null=True, blank=True)      # which device originated this record

    class Meta:
        abstract = True
```

### 21.2 ChangeLog table schema (local SQLite — Ichebo Desktop)

```python
class ChangeLog(models.Model):  # SQLite only — not on cloud
    id           = UUIDField(primary_key=True, default=uuid.uuid4)
    entity_type  = CharField(max_length=50)    # "member", "activity", "record"
    entity_id    = UUIDField()                  # the record that changed
    operation    = CharField(choices=[('CREATE','CREATE'),('UPDATE','UPDATE'),('DELETE','DELETE')])
    changed_at   = DateTimeField()              # when it happened locally
    synced_at    = DateTimeField(null=True)     # null until successfully pushed
    device_id    = UUIDField()                  # which installation made this change
    payload_hash = CharField(max_length=64)     # checksum for conflict detection
```

### 21.3 Push endpoint (cloud side)

```
POST /api/sync/push/
```

**Request body:**
```json
{
  "device_id": "uuid",
  "changes": [
    {
      "entity_type": "member",
      "entity_id": "uuid",
      "operation": "CREATE | UPDATE | DELETE",
      "changed_at": "ISO-8601",
      "payload": { /* full entity data */ }
    }
  ]
}
```

**Response:**
```json
{
  "processed": integer,
  "results": [
    { "entity_id": "uuid", "status": "success | conflict | rejected", "reason": "string | null" }
  ]
}
```

Idempotency: if the same entity_id + operation + changed_at tuple is received twice, the second is silently ignored. UUID PKs make this reliable.

### 21.4 Pull endpoint (cloud side)

```
GET /api/sync/pull/?since={iso_timestamp}&device_id={uuid}&tenant_id={uuid}
```

**Response:**
```json
{
  "since":        "ISO-8601",
  "retrieved_at": "ISO-8601",
  "has_more":     false,
  "records":      [],
  "activities":   [],
  "members":      [],
  "governance":   []
}
```

Max 500 items per type per call. Paginate using since= + last updated_at when has_more: true.

### 21.5 Conflict resolution rules

| Data type | Rule | Reason |
|---|---|---|
| Governance records — Handbook, Mandates | Cloud wins always | Authority flows from apostolic leadership downward |
| Permissions and roles | Cloud wins always | Authority flows downward, never upward |
| Community settings | Cloud wins always | Set at onboarding, controlled by network |
| Member registry | Last write wins by timestamp | Steward updates legitimate from both sides |
| Activity logs | Merge — both versions kept | Both are real events |
| Personal records — journal, Bible notes | Local wins always | Personal and private to the device |

### 21.6 Non-negotiable sync data rules

- UUID primary keys everywhere — both SQLite and PostgreSQL. No auto-increment integers.
- Soft deletes only — no hard deletes. deleted_at timestamp set. ChangeLog records DELETE operation.
- SQLite WAL mode — PRAGMA journal_mode=WAL. Required for concurrent UI + background sync.
- Idempotency — every push operation safe to run twice.
- Device identity — stable UUID generated on first Desktop run, stored locally.

---

## Part 22 — Go Engine Language-Agnostic Specifications

> **Reference:** ADR-019. This part defines what each Go foundation engine must implement. Both the Go implementation (Ichebo Desktop / Layer 5) and the Python/Django implementation (cloud / current) must conform to these specifications.

### 22.1 Records Engine specification

**Must implement:**
- Create record: enforce four mandatory fields, enforce record_class permission gate, enforce single records table constraint
- Read record: apply permission algorithm (Part 7)
- Update record: enforce record_class mutability rules (governance records: versioned only)
- Soft delete: set deleted_at, append to ChangeLog

### 22.2 Activity Engine specification

**Must implement:**
- Create activity: enforce four mandatory fields, enforce assignment rules (Part 4.3)
- Status transition: trigger ActivityLog entry on every status change (immutable)
- Progress update: trigger certification signal when programme Activity reaches 100%
- Soft delete: set deleted_at, append to ChangeLog

### 22.3 Relationships Engine specification

**Must implement:**
- Create relationship: enforce exactly one of to_record_id or bible_verse_id non-null
- Enforce controlled relationship type vocabulary (Part 3.4)
- Traverse: from a record, return all relationships where from_record_id or to_record_id = record.id
- Direction-aware traversal: respect directed vs bidirectional

### 22.4 Bible Engine specification

**Must implement:**
- Return scripture text for a given (translation_code, book_code, chapter, verse)
- Return all verses for a given (translation_code, book_code, chapter)
- Resolve reference string (e.g. "JHN 3:16") to verse object
- Read-only — no write operations

### 22.5 Calendar Engine specification

**Must implement:**
- Aggregate events from Activity table (filtered by tenant, date range, type)
- Return CalendarEvent[] sorted by scheduled_at ascending
- Produce KGS Annual Rhythm events (governance cycles, programme milestones) — Version 3

---

## Part 23 — Ichebo Desktop Data Scope

> **Reference:** ADR-017. Defines which data domains are in scope for Ichebo Desktop MVP.

### 23.1 In scope for Desktop MVP

| Domain | What Desktop handles |
|---|---|
| People (Members) | UserPermission rows for the local tenant, competence levels, shepherd assignments |
| Activity | Activity logging, attendance, service participation for the local tenant |
| Sync | ChangeLog management, push/pull/resolve with Ichebo Cloud |
| Governance (read-only) | View local handbook and mandates received from cloud — no authorship in MVP |

### 23.2 Out of scope for Desktop MVP

- Learn LMS and formation pathway tracking
- Paraclete intelligence layer
- Video and media (Ichebo Media is Version 3+)
- Full KGS five-level permission complexity (simplified for single community)
- Multi-community hierarchy management (cloud handles this)
- Content authorship (The Desk is a web/cloud product)

### 23.3 Local SQLite schema scope

Desktop SQLite database contains: User (local device user only), UserPermission (local tenant members), Activity (local community), ActivityLog, Record (limited — announcements and gatherings received via sync), ChangeLog (sync engine), Settings (device preferences).

Desktop SQLite does NOT contain: Handbook governance records (received via sync as read-only snapshots), BibleVerse (full Bible data loaded separately), Learn programme content (synced on demand, not stored locally in MVP).

---

## Deferred (Post-MVP / Future Versions)

### Platform-wide
- Full RecordPermission table (fine-grained per-user permissions)
- CustomFieldSchema formal validation system
- Donations feature
- In-service Display app
- API versioning (/api/v1/) — before mobile production launch
- User-defined custom journal record types

### Learn App
- Rich text editor for lesson authorship
- Quiz auto-grading, assignment peer review
- Learning analytics dashboard
- Offline lesson caching

### Calendar App
- Record events in aggregation (programme milestones, governance calendars)
- iCal export
- Full month/week grid view

### Activity App
- Full RRULE custom recurrence builder
- Activity analytics
- Bulk assignment, cross-tenant campaign templates

### Bible App
- Reading plans, verse highlights, scripture full-text search
- Licensed translations (NIV, ESV, NLT — require publisher agreements)
- African language translations, audio Bible, cross-reference chains

### Community App
- MembershipRequest model UI (model stubbed — Part 14.4)
- pastoral_note record type (Part 14.1)
- report record type (Part 14.1)
- Attendance tracking (AttendanceLog model — privacy-sensitive)
- PastoralAssignment model (upgrade from UserPermission.metadata.shepherd_id)
- GinIndex on UserPermission.metadata
- Community analytics dashboard

### Governance App
- calendar record type (registered in governance family — Phase 2)
- Level 4 tenant-scoped governance records
- Full HRS graph visualisation

### Notifications
- Real-time delivery (Django Channels + WebSockets) — Layer 10
- Push notification to iOS — when iOS app is built

### Paraclete
- AI-assisted pattern detection (LLM) — Layer 10
- Link suggestion engine — Layer 10
- Prophetic prompt generation (LLM) — Layer 10

### Ichebo Handbook (standalone product — ADR-020)
- HRS as first-class citizen (not as relationship type in records table)
- Level 5 architect workspace
- Version-controlled governance document authorship
- Handbook-as-tenant migration

### Ichebo Media (standalone product — ADR-021)
- Self-hosted video upload, transcode, store, serve (Go + FFmpeg + Hetzner Object Storage)
- Live streaming (RTMP ingest, HLS delivery)
- Offline video download for Ichebo Desktop
