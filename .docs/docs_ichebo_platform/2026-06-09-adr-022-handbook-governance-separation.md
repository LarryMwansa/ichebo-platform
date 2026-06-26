# ADR-022 — Handbook and Governance Separation of Concerns

**ICHEBO**

**Architecture Decision Record**

| Field   | Value                                |
|---------|--------------------------------------|
| Number  | ADR-022                              |
| Status  | APPROVED                             |
| Date    | June 2026                            |
| Authors | Chizola (domain); Claude (technical) |

---

## Context

The Version 2 build produced two overlapping systems for governance document management:

**The Governance App** — a UI layer over `records.Record` with `record_family='governance'`. Correctly implements the data contract (Part 1.6, Part 6.1): no owned models, reads from the single records table. Has three surfaces: Reference Library, Mandate Branch, and Keys Library.

**The `handbook/` Django app** — contains a `HandbookRecord` model that is a parallel content store operating outside the data contract. This model violates Part 1.6 ("no new model tables for content types") and Part 6.1 (Governance App owns no models). It was built as a separate implementation before the data contract was fully locked.

**The Desk** — a governance authorship tool (`governance/desk_views.py`) currently sitting under the Governance app URL namespace. It writes `records.Record` rows correctly but is navigationally separate from both Governance and Handbook, sitting as its own icon in the sidebar.

**The problem:** the current arrangement has no clear separation between *reading* governance documents and *authoring* them. There is no single place where a Level 4-5 invited architect goes to consume and produce governance content. Governance has become both a reading room and a write surface. The Desk exists in isolation. Handbook is a dead-end with a rogue model.

**The direction:** establish a clean separation of concerns.

- **Governance App** → read-only public library of published governance records
- **Handbook** → the invited authorship workspace for Level 4-5 architects; The Desk moves here
- **Records App** → personal journal and record management; gets a dedicated desktop layout

This is a lateral move that separates concerns without introducing new data models. It is fully compliant with the data contract.

---

## Decision

**DECISION**

*The Handbook is the governance authorship workspace for Level 4-5 invited architects. The Governance App is the read-only governance library for Level 3-5 readers. Both are UI layers over `records.Record` with `record_family='governance'`. No new content model tables are introduced. The `HandbookRecord` model is retired and its data migrated into `records.Record`. The Records App receives a dedicated full-width desktop layout.*

---

## What Changes

### 1. The Governance App — Read-Only Library

Governance becomes the publicly readable face of the governance document corpus.

**Surfaces retained:**
- Reference Library — classes, principles, concepts, divine patterns (Level 3+ read)
- Mandate Branch — mandates, statements, frameworks, narratives, subjects, entities, protocols, procedures, programmes (Level 4+ read)
- Keys Library — personal keys (owner only, Level 3+)

**What is removed:**
- All write/create/edit UI within Governance
- The Desk entry point within Governance templates
- HTMX create/edit/lock/supersede partials are removed from Governance navigation (they remain in the Handbook)

**Access rules unchanged** per Part 2.5.2 and Part 15.4. Governance displays only records with status `active` or `locked` — no drafts visible in the public library view.

**KGS documents visible here:** Frameworks, Mandates, Procedures, Programmes, Statements — any `records.Record` with `record_family='governance'` and status `active` or `locked` within the user's permission scope.

---

### 2. The Handbook — Invited Authorship Workspace

Handbook is the governance document management workspace. Entry requires a `HandbookAccess` record (reader / author / editor roles — unchanged).

**The Desk is relocated here.** The Desk editor (`governance/desk_views.py`) moves into the Handbook surface. The `edit_note` sidebar icon is removed. Authors enter write mode from within the Handbook.

**Handbook provides:**
- Full read access to all governance records (including drafts for authors/editors)
- Create, edit, version, lock, supersede governance records
- HRS relationship management between records
- Inline editor (The Desk functionality embedded)
- Access management (editor role only)
- Keys Library access (personal governance keys)

**The `HandbookAccess` model is retained.** It is a permission gate model, not a content model. It does not violate Part 1.6. It governs entry to the authorship workspace and maps users to roles (reader / author / editor).

**Sidebar icon:** The `auto_stories` handbook icon in the sidebar becomes the single entry point for governance authorship. Level 3+ users who do not have `HandbookAccess` see a "request access" state. The `edit_note` Desk icon is removed.

---

### 3. The `HandbookRecord` Model — Retired

The `HandbookRecord` model in `handbook/models.py` violates Part 1.6 of the data contract.

**Migration path:**
1. Audit existing `HandbookRecord` rows in the database
2. For each row, create a corresponding `records.Record` with:
   - `record_family = 'governance'`
   - `record_type` = mapped from `HandbookRecord.record_type` (types are identical)
   - `record_class = 'governance'`
   - `title`, `content`, `summary`, `status` carried over directly
   - `custom_fields` populated from HRS attribute fields (`complexity`, `relationship_position`, `position`, `direction`, `speed`, `emotional_tone`)
   - `previous_version_id` and `superseded_by` mapped where applicable
   - `tenant_id` set to the Handbook tenant singleton UUID
3. Migrate `HandbookRelationship` rows into `records.Relationship`
4. Drop the `handbook_handbookrecord` and `handbook_handbookrelationship` tables
5. Retain `handbook_handbookaccess` table and `HandbookAccess` model

**The `HandbookAccess` model and its table are not dropped.** The `handbook/` app is retained as a UI-only app with no content models — same pattern as Governance, Community, Calendar.

---

### 4. The Records App — Dedicated Desktop Layout

The Records App currently renders inside the editorial hub frame shared with The Desk, making the desktop view cramped and hard to use.

**Change:** Records gets its own full-width desktop workspace layout:
- Full-width list with column-grouped record types
- Inline search and status filters
- Detail view with full content rendering and relationship panel
- The Desk is no longer accessible from the Records context bar — authorship is exclusively via Handbook

---

### 5. Sidebar Navigation Update

The Primary Sidebar order changes (per ADR-012, which this ADR amends for items 2 and 3):

| Position | App | Icon | Was |
|---|---|---|---|
| 1 | Dashboard | `dashboard` | unchanged |
| 2 | Handbook | `auto_stories` | was Desk (`edit_note`) then Governance (`gavel`) |
| 3 | Governance | `gavel` | was Governance (no change in icon) |
| 4 | Community | `groups` | unchanged |
| 5 | Formation | `school` | unchanged |
| 6 | Activity | `task_alt` | unchanged |
| 7 | Bible Reader | `menu_book` | unchanged |
| 8 | Video & Broadcast | `live_tv` | unchanged |
| Bottom | Tenancy Hub | `account_balance` | unchanged |

The `edit_note` Desk icon is removed. The Handbook icon moves to position 2.

---

## Data Contract Compliance

| Data contract rule | Compliance |
|---|---|
| Part 1.6 — single records table, no new content model tables | `HandbookRecord` is retired. Handbook becomes a UI layer over `records.Record`. No new models. ✓ |
| Part 6.1 — Governance App owns no models | Unchanged. Governance remains model-free. ✓ |
| Part 2.5 — Handbook-as-tenant (production) | The Handbook tenant at `/global/handbook/` is the `tenant_id` for all Handbook-authored governance records. ✓ |
| Part 2.5.2 — Access rules | `HandbookAccess` gates the authorship workspace. Level gates (3+ Reference, 4+ Mandate, 5 write) enforced at record level. ✓ |
| Part 15.1 — Three-surface Governance model | Reference Library, Mandate Branch, Keys Library surfaces all retained. ✓ |
| Part 1.4 — Services own their domain | All writes go through the records service layer. Handbook is a UI over records, not a bypass. ✓ |
| ADR-014 — The Desk as canonical governance authorship surface | The Desk is relocated into Handbook. Its function is preserved and elevated. This ADR amends ADR-014. ✓ |
| ADR-020 — Ichebo Handbook as standalone product | This ADR describes the current platform implementation only. The Handbook-as-standalone-product direction (ADR-020) is not contradicted — this is an interim arrangement until that product is built. ✓ |

---

## Consequences

**Immediate build work:**
1. Audit and migrate `HandbookRecord` data → `records.Record`
2. Handbook app: remove `HandbookRecord`, `HandbookRelationship` models; keep `HandbookAccess`
3. Handbook views: rewrite to query `records.Record` with `record_family='governance'`; embed The Desk editor
4. Governance views: strip write UI; show only active/locked records
5. Records App: new dedicated full-width desktop layout
6. Sidebar: remove Desk icon, reorder (Handbook → position 2)

**No data loss:** all governance records remain in `records.Record`. No content is deleted.

**No API changes:** the records DRF endpoints are unchanged. No new endpoints required.

**Access control:** `HandbookAccess` continues to gate the authorship workspace. Governance read access is governed by `competence_level` alone (no `HandbookAccess` required to read published records).

**Future (ADR-020):** When Ichebo Handbook ships as a standalone product, the migration path is from this UI layer to that product. The data is already in the correct format (`records.Record`) for that migration.

---

## Amendments to Prior ADRs

| ADR | Amendment |
|---|---|
| ADR-012 | Sidebar order updated: Desk icon removed, Handbook moves to position 2. Navigation structure table in ADR-012 is superseded by the table in this ADR. |
| ADR-014 | The Desk is relocated into the Handbook surface. Its canonical authorship function is preserved but its URL namespace and sidebar icon change. ADR-014 statement "The Desk is the canonical governance authorship surface" is amended to "The Handbook is the canonical governance authorship surface; The Desk editor is embedded within it." |
| ADR-020 | No amendment. ADR-020's standalone product direction is unaffected. This ADR describes the current platform implementation only. |
