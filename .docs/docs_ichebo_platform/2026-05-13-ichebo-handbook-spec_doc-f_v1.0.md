**ICHEBO HANDBOOK**

**Product Specification**

_DOC F - Version 1.0 - May 2026_

| **Field**      | **Value**                                                                                    |
| -------------- | -------------------------------------------------------------------------------------------- |
| Document       | DOC F - Ichebo Handbook Product Specification                                                |
| Version        | 1.0 - May 2026                                                                               |
| Status         | Approved - Canonical Reference                                                               |
| ADR references | ADR-020 (Handbook as standalone product), ADR-014 (The Desk)                                 |
| Data contract  | data-contract-v11-canonical-2026-05-13.md Parts 2.5, 3, 15                                   |
| Depends on     | DOC A (Product Vision), DOC E (Engine Specs)                                                 |
| KGS reference  | kingdom_governance_system.md - Part II (Kingdom Mandate), Part III (Governance Architecture) |
| Authors        | Chizola (domain); Claude (technical)                                                         |

**_The Handbook is not a feature of the platform. It is the institutional memory that authorises the platform to exist. It precedes all tenants. It governs all communities. It is the living record of the apostolic mandate._**

**-- UNDERSTANDING**

**What the Handbook Actually Is**

The institutional memory of the KGS. Not a tenant. Not an app. A standalone product that precedes all tenants.

## **1.1 The Architectural Correction - ADR-020**

The Ichebo Handbook has been implemented in the current production system as a special tenant - a prime tenant at /global/handbook/ with tier: "handbook" and Level 5 write access. This was a pragmatic workaround that enabled Handbook functionality within the existing tenant hierarchy model.

**LOCKED - ADR-020**

The Handbook-as-tenant implementation is formally superseded. Ichebo Handbook is a standalone product - not a tenant, not an app within another product, not a special-case tier in the tenant hierarchy. The Handbook-as-tenant implementation at /global/handbook/ remains in production as a working workaround and will be migrated when Ichebo Handbook is built as a standalone product. No new features are built into the Handbook tenant.

## **1.2 The Correct Understanding**

The KGS is the authoritative reference. Reading it carefully reveals what the Handbook actually is:

**_The Handbook is the institutional memory and governing intelligence of the entire system. It holds the mandate, the methodology, the keys, and the principles that give rise to all communities. It precedes tenants. It authorises them. It governs them._**

The correct mental model - not a hierarchy but a sequence of founding:

**The Handbook**

_Institutional memory - mandate, HRS methodology, prophetic keys, governance principles, version history of all governing documents._

The Handbook exists before the network. It is the deposit of apostolic revelation that the framework is built upon.

**The KGS Framework**

_The governing framework published from the Handbook to the network._

The framework is derived from the Handbook. Communities receive it as the basis for their governance.

**Network of Sceptre Communities**

_Communities that receive and operate under the framework._

Tenants in the technical sense. They do not author the Handbook - they receive its outputs.

**Apostolic Authority**

_Persons who steward the Handbook and govern the network._

The Level 5 architects who maintain the living deposit and govern its application across the network.

## **1.3 Why This Distinction Matters**

A tenant is a node in the network hierarchy. It has a path, a tier, a parent, and a scope. It exists within the materialized path tree. The Handbook is none of these things.

The Handbook cannot be archived. It cannot be moved. It cannot be superseded by another tenant. It is the root of the entire knowledge structure - not a node within it. Modelling it as a tenant introduces category errors that compound as the platform evolves: it implies the Handbook could theoretically be deleted, reorganised, or have its access rules changed like any other tenant.

As a standalone product, the Handbook has its own service, its own data domain, its own access model, and its own authorship environment. It publishes downward to the network. The network does not write back to it.

**-- KNOWLEDGE ARCHITECTURE**

**The Handbook Knowledge Stack**

Five knowledge layers. Each informs the next. HRS is the interpretive methodology throughout.

## **2.1 The KGS Knowledge Stack**

The Handbook organises knowledge across five layers, each informing the next. This is the structure that the Governance App currently implements partially - the Handbook product implements it completely and properly.

**Apostolic Layer - The Prophet's Handbook**

_Three branches: Reference Library, Keys Library, Mandate Branch_

The primary authorship surface. Level 5 architects build, maintain, and draw from Apostolic Properties.

**Knowledge Layer - Reference Library**

_Classes, Principles, Concepts, Divine Patterns_

HRS-produced knowledge compiled from Scripture. Objective, shared. Forms the interpretive vocabulary of the network.

**Personal Layer - Keys Library**

_Key Records (personal symbol-to-meaning mappings)_

Built from Dream Journal and Spirit Journal over time. Subjective, per-operator, private. Informs the Mandate.

**Authority Layer - Mandate Branch**

_Mandates, Frameworks, Statements, Protocols, Procedures_

Outward-flowing governance documents. Received directive translated into Kingdom work. References scripture via HRS.

**Execution Layer - Connected Systems**

_Activity campaigns, Learn programmes, Community gatherings_

Applications of the Mandate. These exist in the community platform - the Handbook governs their direction.

## **2.2 The Three Branches**

The Handbook is organised around three branches. Every governance record belongs to one branch.

| **Branch**        | **Record types**                                                                          | **Access level**                                                                                            |
| ----------------- | ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Reference Library | class, principle, concept, divine_pattern                                                 | Level 3+ read - Level 5 write. Shared, objective, HRS-produced knowledge from Scripture.                    |
| Mandate Branch    | mandate, statement, framework, narrative, subject, entity, protocol, procedure, programme | Level 4+ read - Level 5 write. Outward-flowing governance. Received directive translated into Kingdom work. |
| Keys Library      | key                                                                                       | Owner only - Level 3+ to create. Personal, subjective, per-architect. Built from journal practice.          |

## **2.3 The Full Record Type Registry**

Every governance record type, what it is, and which branch it belongs to:

| **Record type** | **What it is**                                                                             | **Branch**        |
| --------------- | ------------------------------------------------------------------------------------------ | ----------------- |
| class           | A branch or category of Kingdom knowledge - the highest level of classification            | Reference Library |
| principle       | A foundational rule or truth derivable from scripture or apostolic experience              | Reference Library |
| concept         | An idea or theological construct - a named understanding of how the Kingdom works          | Reference Library |
| divine_pattern  | A recurring pattern observed in scripture and confirmed in governance experience           | Reference Library |
| mandate         | A directive from the Kingdom Mandate - what the community is sent to do                    | Mandate Branch    |
| statement       | A formal declaration of position, belief, or intent                                        | Mandate Branch    |
| framework       | A structured system of related principles - how things relate and operate together         | Mandate Branch    |
| narrative       | A story or account carrying governance meaning - precedent and testimony                   | Mandate Branch    |
| subject         | A topic or domain of study - the named field a governance area addresses                   | Mandate Branch    |
| entity          | A named actor, body, or structure - a person, office, or institution in the governance map | Mandate Branch    |
| protocol        | A defined sequence of steps for a recurring occasion - how things are done                 | Mandate Branch    |
| procedure       | An operational process for recurring tasks - the detailed how                              | Mandate Branch    |
| programme       | A structured governance-context programme - not the same as a Learn programme              | Mandate Branch    |
| key             | A personal symbol-to-meaning mapping derived from journal practice                         | Keys Library      |
| calendar        | A time-governed plan of seasons and appointed times - DEFERRED to Phase 2                  | Deferred          |

## **2.4 HRS Property Attributes**

Reference Library record types (class, principle, concept, divine_pattern) carry six HRS classification attributes in their custom_fields. These are author-defined free-text - not validated as enums, allowing the HRS methodology to evolve without schema changes.

| **HRS Attribute**     | **What it captures**                                                                      |
| --------------------- | ----------------------------------------------------------------------------------------- |
| complexity            | e.g. "foundational", "advanced", "initiatory" - how demanding this knowledge is           |
| relationship_position | e.g. "central", "peripheral", "mediating" - where this sits in the knowledge graph        |
| position              | Structural position in the HRS taxonomy                                                   |
| direction             | e.g. "inward", "outward", "bilateral" - the flow of this principle in operation           |
| speed                 | e.g. "progressive", "immediate", "cyclical" - the temporal character of this knowledge    |
| emotional_tone        | e.g. "declarative", "invitational", "corrective" - the relational register of this record |

**-- HRS METHODOLOGY**

**The Hierarchy and Relationship System**

The interpretive methodology that gives the knowledge graph its meaning. Scripture is the foundation.

## **3.1 What HRS Is**

The Hierarchy and Relationship System (HRS) is the interpretive methodology of the Handbook. It is not merely a tagging system or a categorisation scheme. It is a structured approach to deriving governance principles from scripture and mapping the relationships between those principles with precision.

HRS provides:

- A vocabulary for describing what governance concepts are and how they relate to each other
- A method for anchoring every governance claim in scripture - no principle is asserted without a scriptural derivation
- A graph structure connecting classes to principles to concepts to mandates - the full knowledge map
- A personal discipline (the Keys Library) that connects individual prophetic experience to the shared governance vocabulary

## **3.2 HRS Relationship Types in the Handbook**

The Handbook uses a controlled subset of the Relationships Engine vocabulary. These are the HRS-specific relationship types and their governance meaning:

| **Relationship type** | **Direction** | **Governance meaning**                                                                          |
| --------------------- | ------------- | ----------------------------------------------------------------------------------------------- |
| part_of               | directed      | B is a component of A - governance_principle part_of governance_framework                       |
| derived_from          | directed      | B is derived from or inspired by A - concept derived_from divine_pattern                        |
| aligns_with           | directed      | A supports or is consistent with B - programme aligns_with mandate                              |
| authorised_by         | directed      | A is authorised or governed by B - procedure authorised_by mandate                              |
| references            | directed      | A references or cites B - narrative references subject; governance record references BibleVerse |
| has_symbol            | bidirectional | A and B share symbolic meaning - key record has_symbol divine_pattern                           |
| matches_pattern       | directed      | A exemplifies or instantiates the pattern of B                                                  |

## **3.3 HRS Scripture Module - The Critical Separation**

There are two completely different relationships with scripture in the Ichebo ecosystem. This distinction is architecturally critical:

| **Surface**                            | **Relationship with scripture**                                                                                                                                                             |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Ichebo Bible (product)                 | Personal scripture engagement - reading, notes, highlights, reading plans. Calls Bible Engine for text. No HRS functionality.                                                               |
| Ichebo Handbook - HRS Scripture Module | Advanced scripture mapping for architects. Links passages to governance documents. Version-controlled, audited, Level 5 only. Calls Bible Engine for text, adds the HRS relationship layer. |

**The architectural rule**

The Bible Engine provides text to both surfaces. What each product does with that text is completely different. The HRS scripture mapping tool lives exclusively in Ichebo Handbook. It is never built into the Bible App. The Bible App returns text. The Handbook builds meaning.

## **3.4 Scripture Linkage Pattern**

An architect creates a scripture link by adding a Relationship from a governance record to a BibleVerse. This is the standard Relationships Engine pattern - the HRS-specific detail is that bible_verse_id is set instead of to_record_id.

The HRS Scripture Module in the Handbook product provides the authorship UI for this - a scripture search tool within The Desk's Options Bar, allowing an architect to find a verse, read its text, and link it to the record they are authoring in a single workflow.

Example: an architect authors a mandate record about community formation. They link it to Matthew 28:19-20 ("Go therefore and make disciples") as the scriptural authority for the mandate. The relationship type is "references", direction "directed". The Bible Engine provides the verse text when the relationship is displayed.

**-- PRODUCT DESIGN**

**The Handbook Workspace**

A dedicated authorship environment. Not The Desk. Informed by The Desk.

## **4.1 The Desk as Proof of Concept**

The Desk - built in Version 2 as part of the Apostolic Command Shell - is the most important proof of concept for the Handbook product. It demonstrated three things conclusively:

- Governance authorship is a distinct discipline requiring its own environment. The generic records list view is for browsing. The Desk is for creating and editing. These are different cognitive modes and deserve different interfaces.
- The Handbook's authorship needs - HRS methodology, scripture mapping, mandate versioning, prophetic key management - exceed what can be provided within a community governance app. The Desk shows the shape of what the Handbook product needs to be.
- The Options Bar as a metadata sidecar is the correct pattern for record properties, HRS relationships, and scripture links. This pattern carries directly into the Handbook product design.

The Handbook product is The Desk, completed and given its own home.

## **4.2 Product Attributes**

| **Attribute**   | **Value**                                                                                                      |
| --------------- | -------------------------------------------------------------------------------------------------------------- |
| Product type    | Standalone - its own service, its own data domain, its own UI surface                                          |
| Access          | Invitation only - Level 5 architects and designated stewards appointed by apostolic authority                  |
| Authorship      | Level 5 only - read access per existing governance rules (Level 3+ Reference Library, Level 4+ Mandate Branch) |
| Version control | Every governance document has a full version history - previous_version_id chain                               |
| Audit trail     | Every write action is logged - who created, who edited, who locked, who superseded                             |
| Publishing      | Content is published downward to the network - communities receive Handbook outputs via sync                   |
| Isolation       | Communities cannot edit the Handbook - they receive it. The Handbook does not receive from communities.        |
| Status          | Version 3+ - planned. Layer 9 of the roadmap.                                                                  |
| ADR reference   | ADR-020                                                                                                        |

## **4.3 The Handbook Workspace - Surface Design**

The Handbook product is a dedicated workspace. Its surface borrows the Apostolic Command Shell's four-column architecture but is tuned for governance authorship:

| **Zone**               | **Width**           | **Function in Handbook context**                                                                                                                                                    |
| ---------------------- | ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Branch Navigator       | 72-120px - Ink dark | Three branches: Reference Library, Mandate Branch, Keys Library. Active branch highlighted with red left rule.                                                                      |
| Knowledge Explorer     | 280px - Ink 2       | Browse and search records within the active branch. Organised by record type with collapsible groups. Filter by status, date, author.                                               |
| The Authorship Canvas  | Flexible - Stone    | The editorial writing surface. Markdown authorship. Record title, content, summary. Playfair Display for record titles. 680px max-width centred.                                    |
| The Properties Sidecar | 320px - Stone 2     | Tabbed: Properties (HRS attributes, status, lifecycle controls) \| Relationships (HRS graph - incoming and outgoing) \| Scripture (linked Bible verses) \| History (version chain). |

## **4.4 The Authorship Canvas - Key Features**

**Record creation flow**

- Architect selects branch and record type from Knowledge Explorer
- New record opens in Authorship Canvas with title field focused
- Architect authors in markdown - live preview mode available
- For Reference Library records: HRS attributes panel appears in Properties Sidecar
- Architect adds scripture links via Scripture tab in Properties Sidecar
- Architect adds HRS relationships via Relationships tab
- Save as draft → review → activate → lock (following the record lifecycle)

**The markdown authorship environment**

- Obsidian-style live preview - edit and preview in the same canvas, toggle between modes
- Formatting toolbar: headings (H1-H4), bold, italic, blockquote, link - floating above the content area
- Auto-save: debounced 3-second save on keystroke - "Saved" pulse in the toolbar
- Writing measure: 680px max-width centred in the canvas - optimal for long-form governance writing
- Record ID displayed in Fira Code monospace at the top - governance records are identified precisely

**HRS attributes panel (Reference Library records)**

- Six labelled fields: Complexity, Relationship Position, Position, Direction, Speed, Emotional Tone
- Free-text input - no enum constraints
- "Not assessed" shown for null values - not blank, not empty
- Attributes visible in the Properties tab of the Sidecar

**Record lifecycle controls**

- Status displayed as a badge: draft → active → locked → superseded
- "Publish" button - transitions draft to active. Level 5 only. Requires confirmation.
- "Lock" button - transitions active to locked. Level 5 only. Confirmation with "Record will be immutable after locking."
- "Create new version" button - appears on locked records. Creates a new draft with previous_version_id set. Level 5 only.
- Superseded records: greyed out in Knowledge Explorer, full version chain visible in History tab

**-- ACCESS MODEL**

**Who Can Do What**

Authority flows from apostolic leadership downward. The Handbook is never democratised.

## **5.1 Access Rules**

| **Role / Level**                        | **Branch access**                                                         | **Authorship**                                                                                                         |
| --------------------------------------- | ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Level 0b-2 (Seeker, Member, Disciple)   | No access to Handbook                                                     | None                                                                                                                   |
| Level 3 (Functional Minister)           | Reference Library - read only (class, principle, concept, divine_pattern) | Keys Library - create and manage own key records only                                                                  |
| Level 4 (Leader)                        | Reference Library + Mandate Branch - read only                            | None (read only)                                                                                                       |
| Level 5 (Apostolic Steward / Architect) | All branches - full read                                                  | Full authorship - create, edit, publish, lock, supersede all record types. Add HRS relationships. Add scripture links. |

## **5.2 Invitation-Only Access**

Access to the Handbook workspace is not granted by competence level alone. Level 5 is the minimum - it is not sufficient. Access requires invitation by apostolic authority.

The onboarding flow for a new Handbook architect:

- Apostolic leadership identifies a Level 5 architect for Handbook access
- Access granted via the Handbook product's access management panel - not via tenant membership
- Architect receives notification: "You have been granted access to the Handbook workspace"
- Architect logs into the Handbook product - separate from the community platform login

**The governance principle**

The Handbook is not self-service. Access is appointed, not earned by meeting a threshold. This mirrors the KGS governance structure: authority is given, not claimed. The platform enforces this - no Level 5 user may add themselves to the Handbook workspace.

## **5.3 Keys Library - Personal Access**

The Keys Library is the exception to the strict invitation model. Level 3+ users can access and author their own key records from within the Governance App (current implementation) or the Handbook product (future). Keys are personal - they are never shared or visible to other users.

A key record represents a personal symbol-to-meaning mapping: a symbol encountered in a Dream Journal entry, interpreted through prayerful study, linked to a Reference Library record that provides the HRS vocabulary for understanding it. This is a spiritual discipline, not a governance function. The Keys Library honours it with a private, personal surface.

**-- PUBLISHING**

**How the Handbook Flows Downward**

Content published in the Handbook is delivered to communities via sync. Communities receive - they do not edit.

## **6.1 The Publishing Flow**

The Handbook publishes downward to the network. When an architect activates a governance record, it becomes available to communities according to the access rules. When they sync to the cloud, the record is included in their pull payload.

The unidirectional publishing model:

| **Handbook architects author and publish governance records**                                     |
| ------------------------------------------------------------------------------------------------- |
| ↓ (publishes downward)                                                                            |
| **Ichebo Cloud includes active Handbook records in sync pull payloads**                           |
| ↓ (synced to device)                                                                              |
| Communities receive and read Handbook content - read-only on Desktop, read-only in Governance App |

## **6.2 What Gets Published**

| **Record status** | **Published to network?**                                                                                      |
| ----------------- | -------------------------------------------------------------------------------------------------------------- |
| draft             | No - visible only to the authoring architect in the Handbook workspace                                         |
| active            | Yes - visible to all users with appropriate level access via the Governance App and Ichebo Desktop (read-only) |
| locked            | Yes - visible and immutable. Represents the finalised, authoritative version.                                  |
| superseded        | Yes - retained for version history. Marked as superseded. Not featured in browse views.                        |

## **6.3 Conflict Resolution for Handbook Records**

Per the Sync Engine conflict resolution rules (DOC C, ADR-018): governance records and Handbook records use the Cloud Wins rule. Always. A community steward cannot locally override a Handbook record. The apostolic authority of the Handbook is preserved at the data level - not just as a permission rule but as a sync invariant.

**Sync rule**

Governance records - Handbook and Mandates: Cloud wins always. Authority flows from apostolic leadership downward. Local cannot override. This is the technical expression of the governance principle: communities receive the Handbook, they do not revise it.

**-- MIGRATION**

**From Handbook-as-Tenant to Standalone Product**

A careful, phased migration that preserves all existing data.

## **7.1 Current Production State**

The current production system runs Handbook functionality through a special tenant:

| **Attribute**                  | **Current production value**                                         |
| ------------------------------ | -------------------------------------------------------------------- |
| Tenant ID                      | handbook-singleton-uuid (fixed, seeded by management command)        |
| Path                           | /global/handbook/                                                    |
| Tier                           | handbook                                                             |
| Access control                 | Special-cased in the permission algorithm - not normal tenant access |
| Write access                   | competence_level >= 5 only                                           |
| Read - Reference Library types | competence_level >= 3                                                |
| Read - Mandate types           | competence_level >= 4                                                |

This implementation works and will remain in production until the Ichebo Handbook standalone product is built. No new features are added to the Handbook tenant.

## **7.2 Migration Path**

When Ichebo Handbook is built as a standalone product, migration proceeds in phases:

- Audit all existing Handbook records in the tenant - catalogue every record, its type, status, relationships, and scripture links
- Build the Handbook standalone product with its own service and data domain
- Migrate all existing records from the Handbook tenant into the Handbook product's domain - preserving IDs, version chains, relationships, and scripture links
- Update all Governance App references from the tenant path to the Handbook product API
- Update Sync Engine pull payload to source Handbook content from the Handbook product rather than the tenant records
- Remove the handbook tier from the Tenant model after confirming all data is migrated and all references are updated
- Produce a data contract v12 amendment removing the Handbook-as-tenant section

**Migration principle**

IDs are preserved through migration. A governance record's UUID is its permanent identity - it does not change when it moves from the tenant context to the Handbook product domain. This is why UUID primary keys are non-negotiable.

**-- TECHNICAL SPECIFICATION**

**Service Architecture**

Own service. Own data domain. Own API. Publishes via the cloud sync layer.

## **8.1 Service Attributes**

| **Attribute**    | **Value**                                                                                                        |
| ---------------- | ---------------------------------------------------------------------------------------------------------------- |
| Service type     | Standalone - separate from the Django community platform                                                         |
| Language         | Python (Django) initially - same reasoning as Governance App. Go extraction in Phase 3 if complexity demands it. |
| Data domain      | Own PostgreSQL schema (or separate tables in the shared DB with handbook\_ prefix)                               |
| API              | DRF endpoints - consumed by the Handbook workspace UI and by the Sync Engine                                     |
| Authentication   | Shared identity service (accounts app) - same user accounts, separate access grants                              |
| Design authority | DESIGN.md governs all visual decisions in the Handbook workspace UI                                              |

## **8.2 Core API Endpoints**

| **Endpoint**                                 | **Purpose**                                                                               |
| -------------------------------------------- | ----------------------------------------------------------------------------------------- |
| GET /api/handbook/records/                   | List records - filter by branch, type, status. Includes HRS attributes.                   |
| GET /api/handbook/records/{id}/              | Full record detail including relationships and scripture links.                           |
| POST /api/handbook/records/                  | Create a new record. Level 5 only.                                                        |
| PATCH /api/handbook/records/{id}/            | Update record content. Level 5 only. Locked records: reject content field changes.        |
| POST /api/handbook/records/{id}/publish/     | Transition draft → active. Level 5 only.                                                  |
| POST /api/handbook/records/{id}/lock/        | Transition active → locked. Level 5 only. Confirmation required.                          |
| POST /api/handbook/records/{id}/new-version/ | Create a new draft version of a locked record. Level 5 only.                              |
| GET /api/handbook/records/{id}/history/      | Full version chain - previous versions and superseded records.                            |
| GET /api/handbook/publish-feed/?since={ts}   | Sync feed - all active/locked records modified since timestamp. Used by Sync Engine pull. |
| GET /api/handbook/access/                    | Returns the requesting user's access level to the Handbook workspace.                     |

## **8.3 Data Model**

The Handbook product owns its record domain. The model is an extension of the Records Engine schema - same mandatory fields, same record_class (all governance), same relationship patterns. The Handbook service enforces additional constraints:

- All records have record_class: governance - no exceptions
- All records have record_family: governance - no exceptions
- record_type must be in the Handbook record type registry (see Part 2.3)
- tenant_id is fixed to the Handbook service domain - not a community tenant
- All writes require the requesting user to have explicit Handbook workspace access (not just Level 5 competence)
- Audit log: every write action creates an audit entry - who, what, when, from what status to what status

## **8.4 Version History Data Model**

The version chain is navigable in both directions. Every record carries:

| **Field**           | **Purpose**                                                                     |
| ------------------- | ------------------------------------------------------------------------------- |
| previous_version_id | Points to the record this version supersedes. Null for the first version.       |
| superseded_by       | Points to the record that supersedes this one. Null until superseded.           |
| version_number      | Human-readable version label - "v1", "v2", "v3". Set automatically on creation. |
| locked_at           | Timestamp when record was locked. Null while draft or active.                   |
| locked_by           | UUID of the Level 5 user who locked the record.                                 |

The History tab in the Properties Sidecar renders the full chain - from the earliest version to the current one, with dates, authors, and status at each point.

# **Part 9 - Build Sequence and Deferred Items**

## **9.1 Entry Requirement**

**Gate**

Ichebo Handbook standalone product build does not begin until: (1) The Desk is confirmed stable in production, (2) The Sync Engine (DOC C) is complete and tested, (3) The Handbook-as-tenant audit is complete and all existing records are catalogued.

## **9.2 Build Phases**

| **Phase**                          | **What it builds**                                                                                                                                                             |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| K.1 - Handbook Service Foundation  | Standalone service. Own data domain. Core DRF endpoints. Access grant model (invitation-only, Level 5). Authentication via shared identity service.                            |
| K.2 - Handbook Workspace UI        | Four-zone authorship interface (Branch Navigator, Knowledge Explorer, Authorship Canvas, Properties Sidecar). Record CRUD. Status lifecycle controls. Version history display. |
| K.3 - HRS Relationships Module     | Relationships tab in Properties Sidecar. Add/remove/traverse HRS relationships. Full relationship type vocabulary. Direction and strength controls.                            |
| K.4 - HRS Scripture Module         | Scripture tab in Properties Sidecar. Bible Engine integration - search by reference, read verse text. Add scripture link. View linked verses in record detail.                 |
| K.5 - Publishing and Sync Feed     | Publish flow (draft → active → locked → superseded). GET /api/handbook/publish-feed/ endpoint. Sync Engine integration - Handbook records in pull payload.                     |
| K.6 - Keys Library                 | Personal key records. Private to the authoring architect. Linked to Reference Library records via has_symbol. Linked to Dream/Spirit Journal entries via derived_from.         |
| K.7 - Handbook-as-Tenant Migration | Full data migration. Existing records moved to Handbook product domain. References updated. Handbook tier removed from Tenant model. Data contract v12 amendment.              |

## **9.3 Deferred Items**

- calendar record type - registered in the record type registry, deferred to Phase 2 build
- HRS graph visualisation - full interactive graph of the knowledge network. Significant engineering. Version 3 Phase 2.
- Level 4 tenant-scoped governance records - communities creating their own governance records under the Handbook framework. Requires careful permission design.
- Public Handbook - a read-only public view of selected Reference Library records accessible without authentication. Version 3 Phase 2.
- Handbook API for external integrations - authorised third-party tools reading Handbook content via API key. Version 3+.

**Ichebo Christian Services**

_DOC F - Ichebo Handbook Product Specification v1.0 - May 2026 - Canonical Reference_