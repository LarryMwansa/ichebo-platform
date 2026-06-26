**ICHEBO**

**Product Architecture Brainstorm**

_Session Capture Document - May 2026_

This document captures the full output of an impromptu product architecture brainstorm session. It covers the strategic vision for the Ichebo product family, the local-first architecture decision, the sync engine as the core technical component, and the modular engine approach. It is a working document - a foundation for formal product and technical specification work that follows.

**Session note**

_This was an open-ended exploration session. Decisions recorded here are strategic directions, not locked specifications. Formal locking follows in dedicated advisory sessions per the Ichebo build methodology._

# **Section 1 - Strategic Vision**

## **1.1 The Philosophy Anchor**

The session began with a question about desktop executables and evolved into a fundamental rethinking of how the Ichebo platform relates to the devices its users carry. The anchoring insight:

**Core principle**

_The person has a device. How do we leverage that resource? Most software treats the device as a thin client. Local-first inverts that - the device is the primary computer. The cloud is just coordination._

This is not a product feature. It is a philosophy. It shapes every architectural decision that follows.

## **1.2 The Product Family**

The brainstorm produced a clear three-product vision sharing one architecture:

| **Product**    | **Primary User**               | **Role**                                                           |
| -------------- | ------------------------------ | ------------------------------------------------------------------ |
| Ichebo Mobile  | Individual member              | Personal companion - Bible, activity, discipleship progress        |
| Ichebo Desktop | Community steward              | Community operating system - member registry, activity, governance |
| Ichebo Cloud   | Network / apostolic leadership | Network coordination, compliance, cross-community visibility       |

Each product serves a different user at a different scale. Same data. Same KGS logic. Different surface.

## **1.3 The Primary Product Decision**

A critical strategic question was asked and answered in this session:

**Question**

_Are you building Ichebo Desktop as a companion to the cloud - or as the primary product that the cloud serves?_

The answer locked:

**Decision - LOCKED**

_Ichebo Desktop is the primary product. The cloud exists to connect and give visibility to what is already happening locally on every desktop. Option B._

Implication: A community can run Ichebo Desktop permanently without internet and lose nothing. The cloud is the optional coordination layer - not the product itself.

## **1.4 The Competitive Position**

No platform in the faith-based technology space is built local-first, cross-platform, offline-capable, with a sync layer connecting individual → community → network. This is genuinely new ground.

Existing competitors (Planning Center, ChurchSuite, Elvanto, Breeze) are all cloud-first, browser-dependent, and designed for the congregational model. None serve apostolic networks. None work offline. None are local-first.

# **Section 2 - The Two-Product Architecture**

## **2.1 Ichebo Cloud - Identity, Trust and Compliance Layer**

The cloud's role is not to run communities. Its role is specifically:

- Verify KGS compliance before issuing a licence
- Set up the tenant correctly in the network hierarchy
- Issue the Desktop installation with a verified identity
- Connect each installation to the correct position in the apostolic network
- Provide network leadership with cross-community visibility
- Coordinate sync between desktop nodes

**The passport office analogy**

_You go once, in person, to prove who you are and get your document. After that you travel freely without returning. The cloud is Ichebo's passport office. The desktop is the freedom that follows._

## **2.2 Ichebo Desktop - The Community Operating System**

The desktop product serves the community steward. It runs fully offline. Every daily operation happens locally.

MVP scope (ruthlessly minimal):

- **People - member registry, levels, shepherd assignments**
- **Activity - log attendance, service, participation**
- **Sync - status, last synced, pending changes**

Explicitly out of MVP:

- Learn LMS
- Paraclete intelligence layer
- Video / streaming
- Full KGS five-level permission complexity
- Multi-community hierarchy management

## **2.3 KGS Onboarding Flow**

Every community must be KGS-verified before a desktop licence is issued. This is a governance feature, not just a technical gate. It means every node in the Ichebo network is a legitimate KGS-compliant community by definition.

The flow:

- Community applies via Ichebo Cloud
- KGS compliance verified - apostolic covering, tier, network position confirmed
- Tenant created in cloud - position in hierarchy locked
- Desktop licence issued - installation key generated
- Community installs Ichebo Desktop, enters key
- Desktop activates with verified identity and syncs initial data
- Community operates fully offline from here
- Syncs to cloud whenever internet is available

**Important**

_Step 2 requires a human in the loop - not just a form. KGS compliance is not a checkbox. Someone with authority (Paul Reuben's team initially) approves each community before a licence is issued. This keeps growth deliberate rather than viral._

# **Section 3 - The Sync Engine**

## **3.1 Strategic Position**

**The secret sauce**

_The sync engine is not a feature. It is the product. Whoever controls the sync layer controls the network. No competitor can buy it. No price increase can take it away. No acquisition changes your access to it._

The sync engine is owned entirely by Ichebo. It is not a third-party library or a SaaS component. It is custom code implementing a custom protocol - and over time, it could be published as the Ichebo Sync Protocol: a standard for KGS-compliant community data synchronisation that other developers could implement.

## **3.2 The Four Jobs**

| **Job** | **Description**                                            |
| ------- | ---------------------------------------------------------- |
| TRACK   | Know what changed, where, and when - on the device         |
| PUSH    | Send local changes to the cloud when internet is available |
| PULL    | Receive cloud changes and write them locally               |
| RESOLVE | Decide what wins when both sides changed the same record   |

## **3.3 The ChangeLog Table**

Lives on the device. Every write to local SQLite appends a row here. This is the engine's memory.

| **Field**    | **Description**                                 |
| ------------ | ----------------------------------------------- |
| id           | UUID - unique identifier for this change event  |
| entity_type  | String - e.g. "member", "activity", "record"    |
| entity_id    | UUID - the record that changed                  |
| operation    | Enum - CREATE \| UPDATE \| DELETE               |
| changed_at   | Timestamp - when it happened locally            |
| synced_at    | Timestamp - null until successfully pushed      |
| device_id    | UUID - which installation made this change      |
| payload_hash | String - checksum of the data at time of change |

## **3.4 Conflict Resolution Rules**

Not every conflict is equal. Rules are applied by data type:

| **Data type**                           | **Rule**                     | **Reason**                                         |
| --------------------------------------- | ---------------------------- | -------------------------------------------------- |
| Governance records - Handbook, Mandates | Cloud wins always            | Authority flows from apostolic leadership downward |
| Permissions and roles                   | Cloud wins always            | Authority flows downward, never upward             |
| Community settings                      | Cloud wins always            | Set at onboarding, controlled by network           |
| Member registry                         | Last write wins by timestamp | Steward updates legitimate from both sides         |
| Activity logs                           | Merge - both versions kept   | Both are real events                               |
| Personal records - journal, Bible notes | Local wins always            | Personal and private to the device                 |

## **3.5 Non-Negotiable Data Rules**

- **UUID primary keys everywhere - both SQLite and PostgreSQL. No auto-increment integers. Ever.**
- **Soft deletes only - no hard deletes anywhere in the system. A deleted_at timestamp is set; the ChangeLog records a DELETE operation.**
- **SQLite WAL mode - PRAGMA journal_mode=WAL. Required for safe concurrent access between UI and background sync process.**
- **Idempotency - every push operation must be safe to run twice without creating duplicate records.**
- **Device identity - stable UUID generated on first run, stored locally. How the cloud knows which node sent which change.**

## **3.6 Sync Triggers**

- On connectivity detected - app monitors network state; when it goes offline → online, sync starts automatically in background
- On app open - if online, sync runs silently on launch
- Manual - user taps "Sync now" from the status bar

Sync never blocks the UI. It runs in a background process. The user keeps working.

## **3.7 Sync Status - What the User Sees**

Four states only. Always visible, always calm:

| **State** | **Display**                           |
| --------- | ------------------------------------- |
| Synced    | ● Synced - 2 minutes ago \[Sync now\] |
| Offline   | ○ Offline - 47 changes pending        |
| Syncing   | ⟳ Syncing - 23 of 47 changes...       |
| Conflict  | ⚠ 3 records need attention \[Review\] |

## **3.8 Sync Engine Build Order**

This sequence is non-negotiable. UI features are built after the data layer is solid.

- Design UUID schema - both SQLite and PostgreSQL models
- Build ChangeLog table and write trigger (every local write appends here)
- Build soft delete pattern (no hard deletes anywhere)
- Build /api/sync/push/ endpoint on cloud
- Build /api/sync/pull/ endpoint on cloud
- Build sync engine background process on desktop
- Build conflict resolution rules
- Build ConflictQueue and user review UI
- Build sync status bar
- Test - offline for 7 days, then sync - everything reconciles correctly

_📌 The UI of the app - member registry, activity log, all of it - comes after step 3. Every UI feature is a write to SQLite plus a ChangeLog entry. Once that pattern works, every feature follows the same pattern._

# **Section 4 - Technology Stack**

## **4.1 Stack Decision**

| **Layer**      | **Language / Technology** | **Reason**                                                                           |
| -------------- | ------------------------- | ------------------------------------------------------------------------------------ |
| Desktop UI     | Flutter / Dart            | Cross-platform, native rendering, one codebase - Windows, macOS, Linux, Android, iOS |
| Sync Engine    | Go                        | Fast, concurrent, single binary, embeddable, purpose-built for this type of work     |
| Cloud API      | Python / Django / DRF     | Already built, proven, retained as canonical service layer                           |
| Local database | SQLite (via Go)           | Embedded, zero config, no server process, battle-tested                              |
| Cloud database | PostgreSQL                | Already running on Hetzner VPS                                                       |

## **4.2 Why Go for the Sync Engine**

- Designed exactly for concurrent networked systems that need to be reliable, fast, and small
- A Go binary is a single executable file - no runtime dependencies, starts in milliseconds
- Handles concurrency with goroutines elegantly - background sync while user works
- Compiles to every platform - Windows, macOS, Linux, Android (via gomobile)
- Can be embedded in the Flutter desktop app via FFI bridge
- Can also run as a standalone service for self-hosted Docker deployments
- Can be tested completely independently of the UI

## **4.3 The Rust Question**

Rust would produce the fastest, most memory-efficient, most provably correct sync engine possible. Its ownership model makes entire classes of data corruption errors impossible at compile time.

**Recommendation**

_Write the sync engine in Go first. Get it working, get it tested, get a community running on it. If a performance wall is hit - which is unlikely at community scale for years - rewrite the hot path in Rust. Go now, Rust later if the stars align._

## **4.4 Architecture Diagram**

The three-layer architecture:

| **Layer**              | **Components**                                                                             |
| ---------------------- | ------------------------------------------------------------------------------------------ |
| Flutter UI (Dart)      | All user-facing screens - People, Activity, Governance, Sync status bar                    |
| Go Sync Engine         | ChangeLog management, Push/Pull logic, Conflict resolution, SQLite R/W, Network monitoring |
| Python / DRF Cloud API | Sync endpoints, existing app endpoints, tenant management, KGS compliance                  |

Flutter calls the Go sync engine via FFI or gRPC bridge. The Go engine calls the DRF cloud API over HTTPS. Clean separation. Each layer testable independently.

# **Section 5 - The Modular Engine Architecture**

## **5.1 The Instinct**

**From the session**

_"As I have been building this in Django, I have felt that hang on, maybe Django is doing too much - there should be another way of getting this done."_

This instinct is correct and important. Django is excellent for what it does - but it couples domain logic to the web framework, to PostgreSQL, and to the request lifecycle. The desktop cannot use Django engines directly. The modular approach solves this.

## **5.2 The Four Engines**

The current cloud platform already has four implicit engines. The modular approach makes them explicit, portable, and independently deployable:

| **Engine**           | **Responsibility**                                                                                                          |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Records Engine       | Create / read / update / soft-delete records. Enforce record_class rules. Handle record_family / record_type taxonomy.      |
| Activity Engine      | Log participation events. Track ActivityLog entries. Calculate progress. Same rules, same data shapes, both environments.   |
| Relationships Engine | Create / read / traverse relationships. Direction-aware. bible_verse_id links. derived_from chains. Version history chains. |
| Sync Engine          | ChangeLog management. Push / Pull / Resolve. Orchestrates the other three engines during sync operations.                   |

## **5.3 The Elegant Implication**

The sync engine does not sync raw data. It syncs through the other engines.

- When it pulls a record from the cloud → passes through Records Engine to write locally
- When it pushes an activity log → passes through Activity Engine
- When it syncs a relationship → passes through Relationships Engine

The engines are the rules. The sync engine is the transport. The same rules are enforced twice - once locally in Go, once on the cloud in Python/Django. The data contract is the shared specification both sides implement.

## **5.4 Engine-to-App Mapping**

Each app is a UI surface that calls the appropriate engines. The engine does not know or care whether it is being called by Flutter or a Django template.

| **App**        | **Engines called**                                          |
| -------------- | ----------------------------------------------------------- |
| Bible App      | Records Engine (bible_note records)                         |
| Learn App      | Records Engine + Activity Engine (progress tracking)        |
| Activity App   | Activity Engine + Records Engine                            |
| Community App  | Records Engine + Activity Engine + Relationships Engine     |
| Governance App | Records Engine + Relationships Engine (version chains, HRS) |
| Paraclete      | All four engines - read-only, intelligence layer            |

## **5.5 Language-Agnostic Specification**

Each engine must be defined as a language-agnostic specification - data shapes, rules, and behaviours - that both Go (desktop) and Python/Django (cloud) implement independently. The data contract v9 is the starting point for this specification.

This means:

- The Records Engine in Go enforces the same record_class rules as the Django Records Engine
- The Activity Engine in Go produces the same ActivityLog entries as the Django Activity Engine
- Both sides speak the same data shapes - the data contract is the lingua franca
- Either side can be tested independently against the specification

## **5.6 Desktop Build Sequence Implication**

This changes the recommended build order for Ichebo Desktop. The engines come before the UI.

- Sync Engine data model - UUID schema, ChangeLog, soft delete pattern
- Records Engine - Go module, SQLite, full record_class enforcement
- Activity Engine - Go module, ActivityLog, progress logic
- Relationships Engine - Go module, direction-aware traversal
- Sync Engine transport layer - push/pull/resolve using the three engines above
- Flutter UI - calling engines via FFI/gRPC bridge
- Cloud DRF endpoints - updated to match same data contracts

# **Section 6 - Brainstorm To-Do List**

Everything identified in this session that needs to go into formal product documentation. These are open items - not yet written.

## **DOC 1 - Ichebo Product Vision Document**

_📌 New document - does not yet exist_

- Local-first philosophy statement
- Two-product definition: Ichebo Desktop and Ichebo Cloud
- Three-layer ecosystem map: Mobile → Desktop → Cloud
- The passport office framing - cloud as identity/compliance, desktop as operations
- Data sovereignty statement - community owns their data on their device
- Strategic competitive positioning - local-first, cross-platform, offline-capable, sync layer
- Growth model - deliberate not viral; human approval at onboarding

## **DOC 2 - Ichebo Desktop Product Specification**

_📌 New document - does not yet exist_

- Product definition: community operating system, runs fully offline
- Platform targets: Windows, macOS, Linux (via Flutter)
- MVP scope: People → Activity → Sync
- Out of MVP: Learn LMS, Paraclete, Video, full KGS permission complexity
- First-run experience: three-screen setup wizard
- Five-section information architecture: Home / People / Activity / Governance / Sync
- Sync status bar: four states
- Dark mode as non-optional from day one
- Onboarding path: cloud verification → licence key → desktop activation

## **DOC 3 - Ichebo Sync Engine Specification**

_📌 New document - the secret sauce_

- Sync engine as standalone Go binary - embeddable and independently testable
- Four jobs: Track / Push / Pull / Resolve
- ChangeLog table schema - full field definitions
- UUID primary key requirement - both SQLite and PostgreSQL
- Soft delete pattern - full specification
- SyncableMixin definition - cloud side (Django model)
- Device identity specification
- Conflict resolution rules by record type - full matrix
- ConflictQueue table and user review UI spec
- Three sync triggers specification
- Idempotency guarantee specification
- API endpoints: /api/sync/push/ and /api/sync/pull/?since=
- SQLite WAL mode requirement
- Sync engine build order - 10 steps
- **Go sync engine core modules sketch**

_📌 TO DO - held from this session: sketch of Go sync engine core modules_

## **DOC 4 - Ichebo Technical Architecture Document**

_📌 New document or major update to existing_

- Full stack by layer: Flutter/Dart → Go → Python/DRF → SQLite → PostgreSQL
- FFI/gRPC bridge between Flutter and Go binary
- KGS onboarding flow - full sequence diagram
- Human-in-the-loop approval specification
- Materialised path tenant hierarchy carried into Desktop (scoped to one root)
- "Django is doing too much" - the case for separation of concerns across engines

## **DOC 5 - Ichebo Cloud Onboarding and Compliance Specification**

_📌 New document - does not yet exist_

- KGS compliance as condition of access - full requirements
- Application workflow on cloud
- Human approval process specification
- Licence key generation and issuance
- Tenant position in network hierarchy locked at onboarding
- Initial data sync payload - what gets pushed to desktop on first activation

## **DOC 6 - Ichebo Engine Specifications**

_📌 New document - one per engine_

- Records Engine - language-agnostic specification: data shapes, record_class rules, record_family/record_type taxonomy
- Activity Engine - language-agnostic specification: ActivityLog, progress calculation, participation logic
- Relationships Engine - language-agnostic specification: direction-aware traversal, version chains, HRS
- Sync Engine - as specified in DOC 3
- Engine-to-app mapping - which engines each app calls
- Data contract v9 as the starting specification for all engines

# **Section 7 - Open Questions and Next Brainstorm**

## **7.1 The "Django is Doing Too Much" Question**

This instinct surfaced at the end of the session and deserves a full dedicated brainstorm. The question in full:

**Open question for next session**

_If the domain logic (records, activities, relationships, governance) is extracted into standalone engines - what does Django actually own? Is it just the web layer (auth, routing, templates)? Should the engines be rewritten in Go and Django reduced to a thin API adapter? Or is there a hybrid where Django orchestrates but does not own the logic? What is the right separation of concerns?_

## **7.2 Remaining Brainstorm Agenda**

- Go sync engine core modules - sketch the module structure
- The "Django doing too much" question - separation of concerns deep dive
- Ichebo Mobile - what does the individual companion app look like?
- Self-hosted Docker deployment - for organisations that want cloud behaviour without Ichebo's cloud
- The Ichebo Sync Protocol - when and how to publish it as an open standard
- Pricing model - per-installation vs per-seat vs network licence
- The master roadmap update - where does Desktop fit relative to current Phase 5 build?

## **7.3 What This Session Confirmed**

- Local-first is the right architectural philosophy for the Ichebo context
- The sync engine is the strategic moat - it must be owned, not bought
- Go is the right language for the sync engine and modular engines
- Flutter is the right client framework for cross-platform reach
- The existing DRF investment is retained and extended, not replaced
- KGS compliance as condition of access is a governance feature, not just technical
- The "Django doing too much" instinct is valid and needs to be designed through

**Ichebo Christian Services**

_Brainstorm Session Capture - May 2026 - Internal Working Document_