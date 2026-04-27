# Ichebo Platform — Data Contract v10

**Version:** v10 — 2026-04-25 (Full Consolidated Rewrite)
**Previous version:** v9 — 2026-04-10
**Status:** Approved — Canonical Reference
**Supersedes:** All previous data contract versions (v1–v9)

This is the single authoritative data contract for the Ichebo platform. It defines every schema, every relationship type, every endpoint, and every data rule. All development — web (Django templates + HTMX) and mobile (Flutter) — is governed by this document.

Do not implement any schema change not recorded here. When a change is needed, amend this document first, increment the version, then implement.

---

## Core Principles (Non-Negotiable)

### Four Mandatory Fields

Every stored entity — Record, User, Tenant, Activity — must include:

```js
{
  id:         "uuid-v4",
  tenant_id:  "uuid | null",   // null = platform-level or personal
  created_by: "uuid",
  created_at: "ISO-8601"
}
```

**Exception:** `BibleTranslation`, `BibleBook`, and `BibleVerse` are read-only reference data loaded by management command — exempt from this rule.

### Key Architectural Rules

- `record_class` is the permission gate, not `record_type`. Check `record_class` first in all permission logic.
- Tenant paths are the scope system — prefix matching on `path` field. Never use JOIN for scope — always use `LIKE '/path/%'`.
- `competence_level` has **one write path only:** `POST /api/learn/certifications/{id}/confirm/`. No other code may write to this field.
- All enrolment = `Activity (activity_type: "programme")`. No separate Enrolment model exists.
- Single `records` table with discriminator — no new model tables for content types.
- Cross-app data access goes through DRF endpoints or shared service modules only.

---

## Part 1 — User & Identity

### 1.1 User Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid | Primary key |
| `tenant_id` | null | Users are platform-level — always null |
| `created_by` | uuid \| null | null = self-registered |
| `created_at` | ISO-8601 | |
| `email` | string | Username field — unique, required |
| `display_name` | string | Preferred name shown in UI |
| `avatar_url` | string \| null | `@property` returning `avatar.url` (MinIO ImageField) |
| `competence_level` | 0\|1\|2\|3\|4\|5 | **SOLE WRITE PATH:** `POST /api/learn/certifications/{id}/confirm/` only |
| `status` | enum | `"seeker \| active \| suspended \| pending_verification"` |
| `preferences` | JSONField | `{theme, language, timezone}` — DB-persisted, not localStorage |
| `induction_enrolled_at` | datetime \| null | Set when UserPermission for Induction Tenant created (v10) |
| `induction_completed_at` | datetime \| null | Set when `certifications/confirm/` called with `induction_completion` context (v10) |
| `induction_pathway` | string \| null | `"reconditioning" \| "beginners" \| null` — set on profile registration (v10) |
| `fcm_token` | string \| null | Firebase Cloud Messaging token — updated by Flutter app on login (v10) |
| `updated_at` | ISO-8601 | `auto_now=True` |

### 1.2 UserProfile Extension

| Field | Type | Notes |
|-------|------|-------|
| `preferred_bible_translation` | FK \| null | FK → `bible.BibleTranslation`; null = use `is_default=True` |
| `bio` | text \| null | |
| `full_name` | string | Legal/formal name — from profile registration (v10) |
| `address` | text \| null | Physical address (v10) |
| `country` | string \| null | ISO 3166-1 alpha-2 (e.g. `"ZA"`). Used for induction placement geography. (v10) |
| `id_number` | EncryptedChar \| null | National ID or passport. **ENCRYPTED** (`django-encrypted-model-fields`). Never returned in API response without Level 4+ gate. (v10) |
| `age` | integer \| null | (v10) |
| `gender` | string \| null | `"male" \| "female" \| "prefer_not_to_say" \| null` (v10) |
| `occupation` | string \| null | (v10) |
| `education` | string \| null | Highest qualification description (v10) |
| `born_again` | boolean \| null | Kingdom participation indicator (v10) |

> **SECURITY:** `id_number` must be `write_only` in `UserProfileSerializer`. Access requires an explicit Level 4+ admin endpoint. Use `django-encrypted-model-fields`. Store `FIELD_ENCRYPTION_KEY` in `.env` — never in code.

### 1.3 UserPermission Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid | |
| `tenant_id` | uuid | The tenant this permission applies to |
| `created_by` | uuid | |
| `created_at` | ISO-8601 | |
| `user_id` | uuid | FK → User |
| `tenant_path` | string | Denormalised path for scope queries (prefix match) |
| `role` | enum | `"seeker \| disciple \| branch-steward \| district-steward \| provincial-steward \| national-steward \| regional-steward \| continental-steward \| global-steward \| admin"` |
| `level` | 0–5 | Mirrors `competence_level` at time of grant. Not auto-synced. |
| `is_active` | boolean | False when user leaves a tenant or induction completes |
| `granted_at` | ISO-8601 | |
| `granted_by` | uuid | FK → User |
| `metadata` | JSONField | `{shepherd_id: uuid\|null, service_order: string\|null}` |

### 1.4 Competence Levels — KGS Mapping

| Level | KGS Name | Platform Label | Role Token | Key Capabilities |
|-------|----------|---------------|------------|-----------------|
| 0a | Guest | Guest | (no User object) | Landing page, public records only |
| 0b | Seeker | Seeker | `seeker` | Bible, limited personal records, induction |
| 1 | Foundational Disciple | Member | `member/disciple` | Full personal records, join one tenant, learn |
| 2 | Active Contributor | Disciple | `disciple` | Org records, lead small groups within node |
| 3 | Functional Minister | Steward | `branch-steward+` | Manage teams, create programmes, confirm certs |
| 4 | Leader | Senior Steward | `district-steward+` | Create governance records, manage tenant |
| 5 | Apostolic Steward | Architect | `global-steward/admin` | Cross-tenant governance, Handbook, system config |

---

## Part 2 — Tenant

### 2.1 Tenant Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid | |
| `name` | string | |
| `slug` | string | URL-safe identifier |
| `path` | string | Materialised path — e.g. `"/global/africa/southafrica/gauteng/pretoria/"` |
| `tier` | enum | `"branch \| district \| province \| national \| regional \| continental \| global \| induction"` (v10: `induction` added) |
| `affiliation` | string \| null | `"ichebo"` for system-managed tenants |
| `status` | enum | `"active \| suspended \| archived"` |
| `coordinator_user` | FK \| null | FK → User; Community Coordinator for this tenant (v10) |
| `community_theme` | string | e.g. `"Education"`, `"Healthcare"`, `"Ministry"` (v10) |
| `area_of_operation` | text | Geographic or functional scope description (v10) |
| `logo` | ImageField | Stored in MinIO `ics-media` bucket. `logo_url` `@property` returns URL. (v10) |
| `created_at` | ISO-8601 | |
| `updated_at` | ISO-8601 | `auto_now=True` |

### 2.2 Induction Tenant — System Singleton

The Induction Tenant is seeded by `python manage.py seed_induction_tenant`. It has `tier: "induction"` and `path: "/global/induction/"`. It cannot be deleted or renamed via normal UI flows.

- **Content scoping rule:** users in the Induction Tenant see only Records with `metadata.source_app == "induction"`.
- **On induction completion:** Induction Tenant `UserPermission.is_active` set to `False`; home tenant `UserPermission` created (`level=1`, `role="disciple"`).

---

## Part 3 — Record

### 3.1 Record Object — Complete Schema

```js
Record {
  // Mandatory on all objects
  id:           "uuid"
  tenant_id:    "uuid | null"     // null = personal record
  created_by:   "uuid"
  created_at:   "ISO-8601"

  // Classification (3-tier discriminator)
  record_class:  "personal | organizational | governance"
  record_family: "journal | governance | activity | learning | reference | bible | community"
  record_type:   "[see Part 3.2]"
  origin:        "user | system | paraclete | import"

  // Content
  title:    "string"
  content:  "string | null"
  summary:  "string | null"

  // Lifecycle
  status: "draft | submitted | active | completed | archived | locked | superseded"
  locked_by:  "uuid | null"
  locked_at:  "ISO-8601 | null"

  // Governance versioning
  version:             "integer | null"
  previous_version_id: "uuid | null"
  superseded_by:       "uuid | null"

  // Metadata
  tags:         []
  categories:   []
  custom_fields: {}        // JSONField — app-specific extensions
  metadata: {
    source_app:  "string"  // which app created this record
    record_origin: "string | null"
    custom_field_definitions: []
  }

  // Permissions
  permissions: {
    visibility:     "private | tenant | collective | public"
    required_level: 0-5
    roles_allowed:  []
    can_edit:       []
  }

  updated_at:  "ISO-8601"
  deleted_at:  "ISO-8601 | null"  // soft delete
}
```

### 3.2 Record Type Registry

| `record_family` | `record_type` values | `record_class` | Min level |
|----------------|---------------------|----------------|-----------|
| `journal` | `dream, prayer, note, spirit_journal` | `personal` | 0b |
| `governance` | `doctrine, divine_pattern, covenant, decree, protocol, ordinance, standard, mandate, law, statute, framework, constitution, programme (KGS)` | `governance` | 4 (write), 3 (read) |
| `activity` | `event, campaign, project, task, habit, skill, reminder, goal` | `organizational` | 2 |
| `learning` | `programme, course, lesson, assignment, quiz, certification` | `organizational` | 1 (enrol), 4 (author) |
| `reference` | `key, property, attachment (v10)` | `personal / organizational` | 3 (key), 1 (property) |
| `bible` | `bible_note` | `personal` | 0b |
| `community` | `announcement, gathering, report (deferred), pastoral_note (deferred)` | `organizational` | 1 (read), 3 (create) |

> **Note:** `attachment` (v10) stores file metadata. The file is stored in MinIO `ics-private` bucket. `custom_fields["file_url"]` carries the presigned URL (1-hour expiry). No separate Attachment model.

### 3.3 Relationship Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid | |
| `tenant_id` | uuid \| null | |
| `created_by` | uuid | |
| `created_at` | ISO-8601 | |
| `from_record_id` | uuid | |
| `to_record_id` | uuid \| null | null only when `bible_verse_id` is set |
| `bible_verse_id` | uuid \| null | FK → `bible.BibleVerse`. Exactly one of `to_record_id` or `bible_verse_id` must be non-null. |
| `relationship_type` | enum | See 3.4 |
| `direction` | enum | `"directed \| bidirectional"` |
| `strength` | float \| null | 0.0–1.0, reserved for future AI scoring |
| `notes` | string \| null | |
| `deleted_at` | ISO-8601 \| null | Soft delete |

### 3.4 Relationship Type Registry

| `relationship_type` | Meaning | Example |
|--------------------|---------|---------|
| `part_of` | Hierarchical containment — child belongs to parent | lesson → course → programme |
| `derived_from` | Conceptual origin — this was inspired by or comes from that | mandate → divine_pattern |
| `aligns_with` | Thematic alignment — conceptually related without hierarchy | programme → mandate |
| `authorised_by` | Governance authority — this is permitted or governed by that | procedure → mandate |
| `references` | Citation — this cites or quotes that | governance record → BibleVerse |
| `tracks` | Progress link — activity tracks completion of a record | lesson task Activity → lesson Record |
| `community_ref` | Community → governance link | gathering → doctrine (v10) |

---

## Part 4 — Activity

### 4.1 Activity Object

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid | |
| `tenant_id` | uuid \| null | null = personal activity |
| `created_by` | uuid | |
| `created_at` | ISO-8601 | |
| `activity_type` | enum | `"task \| habit \| goal \| event \| campaign \| project \| programme \| reminder \| skill"` |
| `title` | string | |
| `description` | string \| null | |
| `status` | enum | `"pending \| in_progress \| completed \| cancelled \| archived"` |
| `assigned_to` | uuid \| null | FK → User |
| `parent_activity_id` | uuid \| null | FK → Activity. Two-level nesting max in UI. |
| `linked_record` | FK \| null | FK → `records.Record`, `SET_NULL` on delete. Replaces loose metadata coupling. (v10) |
| `kgs_pathway` | string \| null | KGS pathway label (e.g. `"Service"`, `"Mission"`) |
| `due_at` | ISO-8601 \| null | |
| `scheduled_at` | ISO-8601 \| null | |
| `completed_at` | ISO-8601 \| null | Set automatically on `status → completed` |
| `progress` | integer | 0–100 |
| `recurrence` | JSONField \| null | RRULE-lite `{frequency, interval, days_of_week}` |
| `metadata` | JSONField | `{source_app, is_template, template_id, programme_record_id (deprecated)}` |
| `updated_at` | ISO-8601 | `auto_now=True` |
| `deleted_at` | ISO-8601 \| null | Soft delete |

### 4.2 ActivityLog Object

Created by Django signal on every status transition. Immutable once written.

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid | |
| `activity_id` | uuid | FK → Activity |
| `changed_by` | uuid | FK → User |
| `from_status` | string | |
| `to_status` | string | |
| `changed_at` | ISO-8601 | `auto_now_add=True` |
| `notes` | string \| null | |

### 4.3 Activity Type Rules

| Type | Surface | Nesting | Min Create Level |
|------|---------|---------|-----------------|
| `task` | My Activities, Ministry | Under campaign/project, or flat | 1 |
| `habit` | My Activities | Flat only (personal) | 1 |
| `goal` | My Activities | Flat only | 1 |
| `skill` | My Activities | Flat only — gifts/competence register | 1 |
| `reminder` | My Activities | Flat only | 1 |
| `event` | Ministry, Video/Live | Flat (may have linked Gathering Record) | 3 |
| `campaign` | Ministry | Parent of project/task | 3 |
| `project` | Ministry | Child of campaign, parent of task | 3 |
| `programme` | Learn App (enrolment) | Parent of project (course) and task (lesson) | 1 (enrol) |

---

## Part 5 — Bible

### 5.1 Bible Models

- **BibleTranslation:** `id, code ("KJV"|"ASV"|"WEB"), name, is_default, is_public`
- **BibleBook:** `id, translation_id, code (3-letter), name, testament ("OT"|"NT"), chapter_count, book_order`
- **BibleVerse:** `id, book_id, chapter, verse, text`

Three translations loaded at setup: KJV (default), ASV, WEB. ~93,306 verse rows total. Exempt from the four mandatory fields rule.

### 5.2 Bible Endpoints

```
GET  /api/bible/translations/
GET  /api/bible/books/?translation_code={code}
GET  /api/bible/chapters/{book_code}/{chapter}/?translation_code={code}
GET  /api/bible/verses/{id}/
POST /bible/htmx/translation/set/
GET  /api/bible/health/
```

---

## Part 6 — Learn App

### 6.1 Learning Content (Records)

All learning content is stored as Records with `record_family: "learning"`. Curriculum structure is defined by `Relationship (relationship_type: "part_of")`.

- **Programme:** `record_class: "organizational"`, `record_type: "programme"`.
- **Course:** `record_type: "course"`. Linked to programme via `part_of`.
- **Lesson:** `record_type: "lesson"`. Linked to course via `part_of`. May have `custom_fields["video_url"]`.
- **Assignment / Quiz:** `record_type: "assignment" | "quiz"`.
- **Certification:** `record_type: "certification"`. Created by signal when programme Activity reaches `progress: 100`.

### 6.2 Enrolment Pattern

Enrolment = `Activity (activity_type: "programme")`. No separate Enrolment model exists.

```js
{
  activity_type: "programme",
  assigned_to:   user.id,
  linked_record: programme_record.id,
  status:        "in_progress",
  progress:      0-100,
  metadata: {
    source_app:  "learn",
    kgs_pathway: "Service"
  }
}
```

### 6.3 CertificationConfirmation Model

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

### 6.4 Five Qualification Programmes

| Programme | Level | Duration | Prerequisites |
|-----------|-------|----------|---------------|
| Certificate | 1 | 1 year | None |
| Diploma | 2 | 3 years | Certificate |
| Degree | 3 | 4 years | Diploma |
| Masters | 4 | 4–5 years | Degree |
| Doctorate | 5 | 7 years | Masters |

### 6.5 Three Induction Programmes

| Programme | Entrant type | Court |
|-----------|-------------|-------|
| Reconditioning Programme | Existing believers | Outer Court |
| Beginners Programme | Kingdom-curious newcomers | Outer Court |
| Community Programme | All inductees | Inner Court (auto-enrolled on Outer Court completion) |

### 6.6 `certifications/confirm/` — Extended Logic

**Standard behaviour (all calls):** set certification Record `status → "active"`; increment `competence_level` by 1; create `CertificationConfirmation` audit record.

**Extended behaviour when `metadata.context == "induction_completion"` (v10):**

- `placement_tenant_id` required in request body
- Set `user.induction_completed_at = now()`
- Create `UserPermission`: `tenant_id=placement_tenant_id`, `level=1`, `role="disciple"`, `is_active=True`
- Deactivate Induction Tenant `UserPermission`: `is_active=False`
- Write `ActivityLog`: `"Induction completed — placed in {tenant.name}"`
- Send email notification via Brevo

### 6.7 Learn Endpoints

```
GET  /api/learn/health/
GET  /api/learn/programmes/{id}/curriculum/
GET  /api/learn/certifications/queue/
POST /api/learn/certifications/{id}/confirm/
```

---

## Part 7 — Community App

### 7.1 Gathering Object (Record)

```js
Record {
  record_family: "community",
  record_type:   "gathering",
  record_class:  "organizational",
  custom_fields: {
    format:           "in_person | digital | hybrid",
    location:         "string | null",
    stream_url:       "string | null",
    start_at:         "ISO-8601",
    duration_minutes: integer
  }
}
```

**Dual-write pattern:** creating a Gathering also creates an `Activity (activity_type: "event")` atomically via `transaction.atomic()`.

### 7.2 TenantInvitation Model (v10)

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid | |
| `tenant_id` | uuid | FK → Tenant |
| `email` | string | Invitee email |
| `invited_by` | uuid | FK → User |
| `accepted_at` | datetime \| null | |
| `status` | string | `"pending \| accepted \| declined \| expired"` |
| `created_at` | ISO-8601 | |

---

## Part 8 — Notifications

### 8.1 Notification Model (Version 2 — Full)

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

### 8.2 Notification Trigger Points

| Event | Email? |
|-------|--------|
| Announcement created | No |
| Task `assigned_to` set | No |
| Certification confirmed | Yes |
| Induction placement confirmed | Yes |
| Record locked (Governance) | No |

---

## Part 9 — API Endpoints

### 9.1 `GET /api/auth/me/` — Complete Response Shape

```json
{
  "id":                    "uuid",
  "email":                 "string",
  "display_name":          "string",
  "avatar_url":            "string | null",
  "competence_level":      0,
  "status":                "seeker | active | suspended | pending_verification",
  "preferences": {
    "theme":    "system | light | dark",
    "language": "en",
    "timezone": "Africa/Johannesburg"
  },
  "active_tenant": {
    "id":   "uuid",
    "name": "string",
    "slug": "string",
    "tier": "string",
    "path": "string"
  },
  "induction_pathway":                "reconditioning | beginners | null",
  "induction_completed_at":           "ISO-8601 | null",
  "preferred_bible_translation_code": "KJV | ASV | WEB | null",
  "created_at":  "ISO-8601",
  "updated_at":  "ISO-8601"
}
```

### 9.2 API Versioning Strategy

Current state: all endpoints at `/api/` (unversioned) — acceptable during development. Before first mobile production release: all endpoints move to `/api/v1/`. The `v1` prefix is then frozen — breaking changes require `/api/v2/`.

**Breaking change:** removing a field, changing a field type, changing URL, changing HTTP method, changing auth requirement. Adding new optional fields is **not** a breaking change.

### 9.3 Complete Endpoint List

| App | Endpoints |
|-----|-----------|
| Auth | `POST /api/auth/register/` `POST /api/auth/login/` `POST /api/auth/logout/` `GET/PATCH /api/auth/me/` |
| Records | `GET/POST /api/records/` `GET/PATCH/DELETE /api/records/{id}/` `GET /api/records/{id}/related/` (v10) |
| Relationships | `GET/POST /api/relationships/` `GET/PUT/DELETE /api/relationships/{id}/` |
| Activities | `GET/POST /api/activities/` `GET/PATCH/DELETE /api/activities/{id}/` `GET /api/activities/{id}/log/` |
| Bible | `GET /api/bible/translations/` `GET /api/bible/books/` `GET /api/bible/chapters/{book}/{ch}/` |
| Learn | `GET /api/learn/health/` `GET /api/learn/programmes/{id}/curriculum/` `GET /api/learn/certifications/queue/` `POST /api/learn/certifications/{id}/confirm/` |
| Calendar | `GET /api/calendar/events/` `GET /api/calendar/health/` |
| Paraclete | `GET /api/paraclete/digest/` `GET /api/paraclete/reminders/` `GET /api/paraclete/prompt/` `GET /api/paraclete/suggest/{id}/` `POST /api/paraclete/respond/` |
| Notifications | `GET /api/notifications/` `GET /api/notifications/unread-count/` `POST /api/notifications/{id}/read/` `POST /api/notifications/read-all/` |
| Sync (v10) | `GET /api/sync/changes/?since={iso_timestamp}` |
| Permissions | `GET /api/permissions/` `POST /api/permissions/` `PATCH /api/permissions/{id}/` |

---

## Part 10 — Data Patterns

### 10.1 Record + Activity Dual Write

1. Create the Record first (`POST /api/records/`)
2. Create the Activity with `linked_record` set
3. Create the Relationship linking them

Wrap all three in `django.db.transaction.atomic()`.

### 10.2 Permission Check Pattern

```python
def check_record_access(user, record):
    if record.record_class == 'personal' and record.created_by != user.id:
        return False
    if record.permissions['visibility'] == 'private':
        return record.created_by == user.id
    if record.permissions['visibility'] == 'tenant':
        return user_in_tenant(user, record.tenant_id)
    if user.competence_level < record.permissions['required_level']:
        return False
    return True
```

### 10.3 Indexing Strategy

- **Records:** idx on `tenant_id`, `record_class`, `record_family`, `record_type`, `created_by`, `status`, `deleted_at`. GIN on `custom_fields`.
- **Activity:** idx on `tenant_id`, `activity_type`, `assigned_to`, `status`, `due_at`, `scheduled_at`, `parent_activity_id`, `deleted_at`. GIN on `metadata`.
- **Relationship:** idx on `from_record_id`, `to_record_id`, `bible_verse_id`, `relationship_type`, `deleted_at`.
- **UserPermission:** idx on `user_id`, `tenant_path` (`varchar_pattern_ops`), `is_active`.

---

## Part 11 — Delta Sync API (v10)

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

Max 500 items per type per call. Paginate using `since=` + last `updated_at` when `has_more: true`. Uses existing `updated_at` fields — no model changes.

---

## Part 12 — Migration Schedule

| When | App | Change |
|------|-----|--------|
| Pre-Build (now) | `activity` | `Activity.linked_record = FK(records.Record, SET_NULL, null=True)` |
| Before G1 | `tenants` | `Tenant.tier` choices: add `"induction"` |
| Before G2 | `accounts` | Add `induction_enrolled_at`, `induction_completed_at`, `induction_pathway` to User |
| Before G2 | `accounts` | Add `full_name`, `address`, `country`, `id_number` (encrypted), `age`, `gender`, `occupation`, `education`, `born_again` to UserProfile |
| Before G2 | `accounts` | Add `fcm_token` to User |
| Version 2.3 | `records` | `Relationship.relationship_type` choices: add `"community_ref"` |
| Version 2.5 | `tenants` | Add `coordinator_user` FK, `community_theme`, `area_of_operation`, `logo` ImageField |
| Version 2.5 | `community` | New `TenantInvitation` model |
