# ICS Platform — Data Contract & Architecture Document

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Define the complete, locked data contracts, service boundaries, and schema definitions for the ICS (Integrated Community System) platform — the digital twin of the Kingdom Governance System (KGS).

**Architecture:** Vanilla JS frontend (IIFE module pattern) migrating to Django. Three locked architectural decisions: (1) materialized path for tenant hierarchy, (2) single `records` table with `record_class` discriminator, (3) Paraclete as a standalone orchestration service separate from the Activity Engine.

**Tech Stack:** HTML/CSS/Vanilla JS (frontend-first) → Django + PostgreSQL (backend migration). localStorage via `storage.js` abstraction. Namespaced IIFE modules.

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

Every tenant has a `path` field. Every permission check that involves scope uses prefix matching on this path. This is the materialized path pattern.

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

No app file (bible.js, records-app.js) may directly read or write storage.
All reads and writes go through the relevant engine service. This is what makes Django migration clean — you swap the storage adapter inside the service, and every app that calls it is unaffected.

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
  competence_level: 1 | 2 | 3 | 4 | 5,

  // Platform status
  status: "active | suspended | pending_verification",

  // Settings
  preferences: {
    theme:    "system | light | dark",
    language: "en | ...",
    timezone: "Africa/Johannesburg | ..."
  },

  updated_at: "ISO-8601"
}
```

### 2.2 UserPermission object

This is what controls what a user can do WHERE. A user may have multiple
UserPermission rows — one per tenant they belong to with a specific role.

```js
UserPermission = {
  id:           "uuid",
  tenant_id:    "uuid",           // mandatory on all objects
  created_by:   "uuid",
  created_at:   "ISO-8601",

  user_id:      "uuid",           // FK → User
  tenant_path:  "/global/africa/southafrica/gauteng/pretoria/",
  role:         "member | disciple | coordinator | shepherd | servant | regional | continental | global | admin",
  level:        1 | 2 | 3 | 4 | 5,
  is_active:    true | false,
  granted_at:   "ISO-8601",
  granted_by:   "uuid"            // FK → User
}
```

### 2.3 Competence levels mapped to KGS

| Level | KGS Name               | Platform label     | What they can do                         |
|-------|------------------------|--------------------|------------------------------------------|
| 1     | Foundational Disciple  | Member             | Personal records, join tenants, learn    |
| 2     | Active Contributor     | Operator           | Org records, lead small groups           |
| 3     | Functional Minister    | Coordinator        | Manage teams, create programmes          |
| 4     | Leader                 | Shepherd/Builder   | Create governance records, manage tenant |
| 5     | Apostolic Steward      | Steward/Architect  | Cross-tenant governance, system config   |

### 2.4 Tenant object

```js
Tenant = {
  id:           "uuid",
  tenant_id:    "uuid | null",    // parent tenant (null = top-level)
  created_by:   "uuid",
  created_at:   "ISO-8601",

  name:         "string",
  slug:         "string",         // url-safe identifier
  path:         "/global/africa/southafrica/gauteng/pretoria/sceptre-abc/",

  // Classification
  tier: "church_node | church_collective | district | provincial | national | regional | continental | global",

  // Affiliation
  affiliation: "ichebo | independent | affiliate",

  // Status
  status: "active | pending | suspended",
  is_collective: false,           // true when 3+ child nodes have formed a collective

  // Profile
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

## Part 3 — Records Engine Schema

### 3.1 Record object (universal)

```js
Record = {
  // Core (mandatory)
  id:           "uuid",
  tenant_id:    "uuid | null",    // null = personal record not attached to any tenant
  created_by:   "uuid",
  created_at:   "ISO-8601",

  // Classification (read record_class FIRST in all permission checks)
  record_class: "personal | organizational | governance",
  record_type:  "journal | prayer | dream | note | bible_note | sermon | governance_mandate | governance_statement | governance_calendar | governance_programme | activity_event | activity_campaign | activity_project | activity_habit | activity_task | learning_course | learning_certification | reference_key | reference_property | custom",

  // Content
  title:        "string",
  content:      "string | null",  // rich text / markdown
  summary:      "string | null",  // auto-generated or user-provided

  // Status lifecycle
  status: "draft | active | completed | archived | locked",
  // 'locked' is only valid for governance records after approval

  // Governance versioning (governance records only, null on personal/org)
  version:        "integer | null",
  superseded_by:  "uuid | null",  // FK → Record (governance only)

  // Taxonomy
  tags:       [],                 // string array
  categories: [],                 // string array (user-defined pillars)

  // Custom fields (user-defined, schema-free)
  custom_fields: {},              // key-value, any JSON-serializable value

  // System metadata (structured, app-written)
  metadata: {
    source_app:    "records | bible | activity | learn | ...",
    icon:          "string | null",
    color:         "string | null",
    is_template:   false,
    template_id:   "uuid | null"
  },

  // Permissions
  permissions: {
    visibility:   "private | tenant | collective | public",
    // private = only created_by
    // tenant = members of this tenant
    // collective = members of this tenant + parent collectives
    // public = anyone
    required_level: 1,           // minimum competence level to read
    roles_allowed:  [],          // empty = any role at required_level can read
    can_edit:       [],          // user_ids or role strings that can edit
  },

  updated_at:    "ISO-8601",
  deleted_at:    "ISO-8601 | null"  // soft delete
}
```

### 3.2 Relationship object

```js
Relationship = {
  id:           "uuid",
  tenant_id:    "uuid | null",
  created_by:   "uuid",
  created_at:   "ISO-8601",

  from_record_id: "uuid",
  to_record_id:   "uuid",

  // Direction MUST be set — this prevents double-checking in graph queries
  direction: "directed | bidirectional",
  // directed: from_record → to_record (e.g. ANSWER → PRAYER)
  // bidirectional: either record can be the "source" (e.g. RELATES_TO)

  relationship_type: "relates_to | derived_from | references | answers | fulfills | requests | has_symbol | matches_pattern | assigned_to | tracks | completes | part_of | aligns_with | authorised_by | tagged_in",

  // Optional context
  notes:    "string | null",
  strength: "weak | medium | strong | null",

  deleted_at: "ISO-8601 | null"   // soft delete
}
```

### 3.3 Controlled relationship type vocabulary

| Type            | Direction   | Domain          | Example                               |
|-----------------|-------------|-----------------|---------------------------------------|
| relates_to      | bidirectional| General        | Dream relates to journal entry        |
| derived_from    | directed    | General         | Note derived from sermon              |
| references      | directed    | General         | Activity references Bible verse       |
| answers         | directed    | Prayer          | Answer record → Prayer record         |
| fulfills        | directed    | Prayer/Activity | Testimony → Prayer request            |
| requests        | directed    | Prayer          | Prayer request → God (conceptual)     |
| has_symbol      | directed    | Dreams          | Dream → Symbol reference              |
| matches_pattern | bidirectional| Dreams         | Dream matches recurring pattern       |
| assigned_to     | directed    | Activity        | Task → User (note: user is not a record — use metadata.assigned_user_id) |
| tracks          | directed    | Activity        | Habit → Programme                     |
| completes       | directed    | Activity        | Task → Goal                           |
| part_of         | directed    | Governance      | Calendar → Programme                  |
| aligns_with     | directed    | Governance      | Activity → Mandate                    |
| authorised_by   | directed    | Governance      | Programme → Mandate                   |

---

## Part 4 — Activity Engine Schema

### 4.1 Activity object

The Activity Engine operates on its own objects AND writes records into the
Records Engine for persistence and linking. Activities are the execution layer; Records are the memory layer.

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
  recurrence:     "none | daily | weekly | monthly | custom",
  recurrence_rule:"string | null",  // RRULE format for custom recurrence

  // Hierarchy (activities can nest: programme → project → campaign → task)
  parent_activity_id: "uuid | null",

  // Progress
  status:   "pending | in_progress | completed | cancelled | deferred",
  progress: 0,   // 0–100 integer

  // Assignment
  assigned_to: "uuid | null",  // user_id

  // Linked records (activities reference records, not the other way around)
  linked_record_ids: [],        // array of Record uuids

  // KGS alignment
  kgs_pillar:   "apostolic | strategy | formation | programmes | mission | communities | stewardship | null",
  kgs_pathway:  "new_life | spiritual_formation | community_life | service | leadership | learning | mission | apostolic_stewardship | null",

  // Metadata
  metadata: {
    source_app:  "activity | paraclete | learn | governance",
    icon:        "string | null",
    color:       "string | null",
    is_template: false
  },

  updated_at:  "ISO-8601",
  deleted_at:  "ISO-8601 | null"
}
```

### 4.2 ActivityLog object

Every status change or progress update on an Activity must be logged. This is how the dashboard and reporting systems reconstruct history.

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

---

## Part 5 — Paraclete Service Contract

The Paraclete is a standalone orchestration service. It does NOT own any data. It reads from other engines and produces suggestions, reminders, and insights. It never writes directly to Records or Activities — it calls their services.

### 5.1 What Paraclete is responsible for

- Reading user's activities, records, and schedules to generate intelligent
  reminders
- Detecting patterns across records (recurring dream symbols, prayer themes, habit streaks)
- Producing "today's focus" digest based on user's competence level, active activities, and KGS calendar
- Cross-linking suggestions: "This prayer relates to that journal entry from
  last week — link them?"
- Generating structured prompts for daily spiritual disciplines

### 5.2 What Paraclete is NOT responsible for

- Storing any data of its own (no Paraclete tables/collections)
- Replacing the Activity Engine (it calls the Activity Engine)
- Replacing the Records Engine (it calls the Records Engine)
- User authentication or permissions (it receives a resolved user context)

### 5.3 Paraclete service API (frontend)

```js
// ICSParaclete namespace — loaded as IIFE, depends on ICSRecords + ICSActivity

ICSParaclete = {
  // Generate today's digest for the dashboard
  getDailyDigest(userId) → Promise<ParacleteDigest>,

  // Get reminders due in the next N minutes
  getPendingReminders(userId, windowMinutes) → Promise<Reminder[]>,

  // Suggest record links based on content similarity / type patterns
  suggestLinks(recordId) → Promise<LinkSuggestion[]>,

  // Detect patterns in a record type (e.g. recurring dream symbols)
  detectPatterns(userId, recordType) → Promise<Pattern[]>,

  // Generate a daily spiritual discipline prompt
  getDisciplinePrompt(userId) → Promise<DisciplinePrompt>,

  // Mark a suggestion as acted on / dismissed
  respondToSuggestion(suggestionId, action: "accepted | dismissed") → Promise<void>
}
```

### 5.4 ParacleteDigest object

```js
ParacleteDigest = {
  generated_at:    "ISO-8601",
  user_id:         "uuid",
  greeting:        "string",           // personalised greeting
  focus_for_today: "string",           // 1-2 sentence focus from KGS calendar
  pending_activities: Activity[],      // due today or overdue
  recent_records:     Record[],        // last 3 personal records
  active_prayer_count: 0,
  suggested_links:    LinkSuggestion[],
  discipline_prompt:  DisciplinePrompt
}
```

---

## Part 6 — Service Boundaries (File Map)

### 6.1 Frontend file structure (current → target)

```js
/assets/js/
  /core/
    storage.js          ← exists, keep (localStorage abstraction)
    router.js           ← exists, keep (auth guards + navigation)
    auth.js             ← exists, keep (register/login/logout)
    main.js             ← exists, keep (boot + component loader)

  /engines/             ← NEW — these replace scattered page scripts
    records.service.js  ← CRUD + schema enforcement for Records
    records.store.js    ← in-memory state for Records
    relationships.service.js ← create/query Relationships
    activity.service.js ← CRUD for Activities
    activity.store.js   ← in-memory state for Activities
    identity.service.js ← user profile, competence, tenant memberships
    tenant.service.js   ← tenant CRUD + path resolution
    paraclete.service.js← orchestration — calls other services, no storage

  /apps/                ← thin consumers — UI logic only
    bible.js
    records-app.js
    activity-app.js
    learn-app.js
    community-app.js
    governance-app.js
    dashboard-app.js

  /components/          ← reusable UI (navbar already here)
    navbar.js
    app-drawer.js
    bottom-nav.js
    ...
```

### 6.2 Service dependency rules

```
apps → engines (allowed)
engines → storage.js (allowed)
engines → other engines (allowed, but document the dependency)
apps → storage.js (NOT allowed — go through an engine)
paraclete.service.js → records.service.js (allowed)
paraclete.service.js → activity.service.js (allowed)
paraclete.service.js → storage.js directly (NOT allowed)
```

### 6.3 Script load order (index.html)

```html
<!-- 1. Core (no dependencies) -->
<script src="/assets/js/core/storage.js"></script>

<!-- 2. Engines (depend on storage) -->
<script src="/assets/js/engines/identity.service.js"></script>
<script src="/assets/js/engines/tenant.service.js"></script>
<script src="/assets/js/engines/records.service.js"></script>
<script src="/assets/js/engines/records.store.js"></script>
<script src="/assets/js/engines/relationships.service.js"></script>
<script src="/assets/js/engines/activity.service.js"></script>
<script src="/assets/js/engines/activity.store.js"></script>

<!-- 3. Paraclete (depends on records + activity engines) -->
<script src="/assets/js/engines/paraclete.service.js"></script>

<!-- 4. Auth + Router (depend on identity engine) -->
<script src="/assets/js/core/auth.js"></script>
<script src="/assets/js/core/router.js"></script>

<!-- 5. Main boot (depends on everything above) -->
<script src="/assets/js/core/main.js"></script>

<!-- 6. App scripts loaded per-page only -->
```

---

## Part 7 — Permission Check Algorithm

Every permission check across the system follows this exact sequence.
Implement this once in `identity.service.js`, call it everywhere.

```html
checkPermission(user, record) → boolean

1. Load user's UserPermission rows for their active tenants
2. Read record.record_class
   - IF 'governance': require level >= 4 to write, level >= record.permissions.required_level to read
   - IF 'organizational': require level >= 2 to write
   - IF 'personal' AND record.created_by !== user.id: check visibility only
3. Check record.permissions.visibility
   - 'private': only record.created_by passes
   - 'tenant': user must have a UserPermission row whose tenant_path matches record.tenant_id's path
   - 'collective': user must have a UserPermission row whose tenant_path is a prefix of the record's tenant path
   - 'public': passes for any authenticated user
4. Check record.permissions.required_level
   - user.competence_level must be >= required_level
5. Check record.permissions.roles_allowed
   - IF empty: any role at the required level passes
   - IF populated: user must have a matching role in UserPermission
6. Return true only if ALL checks passed
```

---

## Part 8 — Migration Notes (Django Readiness)

Every decision above was made with Django migration in mind.

### 8.1 What maps cleanly to Django models

- `Record` → `records.Record` (Django model, all fields map 1:1)
- `Relationship` → `records.Relationship`
- `User` → `auth.User` extended by `accounts.UserProfile`
- `UserPermission` → `accounts.UserPermission`
- `Tenant` → `tenants.Tenant`
- `Activity` → `activity.Activity`
- `ActivityLog` → `activity.ActivityLog`

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

### 8.3 Auto-login decision (still pending)

The current frontend auto-logs in after registration. Django will likely return
a token/session on registration response. Decision to make at migration time:
**keep auto-login** (use the token returned by register endpoint to immediately
authenticate) OR **redirect to login** (safer, more explicit). Either works
with this schema — no schema change required.

### 8.4 localStorage → Django API swap pattern

Each engine service has an internal `_storage` adapter. When migrating:

```js
// Before (localStorage)
async function getRecord(id) {
  return ICSStorage.get(`records.${id}`)
}

// After (Django API — change only this function, nothing else)
async function getRecord(id) {
  const res = await fetch(`/api/records/${id}/`, { headers: authHeaders() })
  return res.json()
}
```

The apps that call `ICSRecords.getRecord(id)` are unchanged.

---

## Part 9 — What to Build Next (Ordered)

These are the remaining tasks to complete the foundation before any app work.

### Phase 1 — Engine files (no app work yet)

1. Create `records.service.js` — implements Record CRUD using existing storage.js
2. Create `relationships.service.js` — implements Relationship CRUD
3. Create `records.store.js` — in-memory cache for current session records
4. Create `activity.service.js` — implements Activity CRUD
5. Create `activity.store.js` — in-memory cache
6. Create `identity.service.js` — wraps existing auth.js user data + competence + tenant
7. Create `tenant.service.js` — tenant path resolution + membership queries
8. Create `paraclete.service.js` — skeleton with stubbed methods (implement after engines work)

### Phase 2 — Refactor existing files

9. Refactor existing Records app JS to call `records.service.js` (no direct storage calls)
10. Update `main.js` script load order to match Section 6.3
11. Wire `identity.service.js` into router.js auth guard

### Phase 3 — First app build (Activity)

12. Build `activity-app.js` consuming `activity.service.js`
13. Wire activity ↔ records linking via `relationships.service.js`

### Phase 4 — Dashboard

14. Build `dashboard-app.js` consuming Paraclete digest (stub data first)
15. Implement Paraclete getDailyDigest using real engine calls

