**ICHEBO**

**Ecosystem Architecture**

_Living Document - Version 0.1_

May 2026 - Ichebo Christian Services

This document captures the full output of the Ichebo product architecture brainstorm session of May 2026. It defines the strategic vision, product family, ecosystem architecture, engine specifications, and open design questions for the Ichebo platform. It is a living document - it will evolve as design decisions are made and locked in dedicated advisory sessions.

**Status**

_Version 0.1 - Brainstorm capture. Directions recorded here are strategic. Formal locking follows in dedicated sessions per Ichebo build methodology. Nothing here supersedes previously locked system designs._

**Governing principle**

_Build right or build nothing. The Django prototype proved the domain. This document designs the real thing._

# **Part I - Philosophy and Strategic Vision**

## **1.1 The KGS as the True Specification**

The Kingdom Governance System is not a set of features to be implemented. It is a complete institutional operating system - with mandate, governance, formation, ministry, operations, and expansion as integrated pillars. The Ichebo platform is the digital expression of that system.

Every architectural decision must be read through the KGS. The KGS is the authority. Technology serves it - technology does not shape it.

| **KGS Component**            | **What it governs**                           | **Ichebo expression**                |
| ---------------------------- | --------------------------------------------- | ------------------------------------ |
| Mandate                      | Why the system exists - Kingdom purpose       | Handbook product                     |
| Governance Architecture      | 7-Pillar structure, authority flows           | Governance product + Network product |
| Leadership Administration    | 12 Administrative offices, accountability     | Identity service + roles             |
| Ministry & Service Structure | 24 Orders, Kingdom Participation Model        | Community product + Activity engine  |
| Formation & Leadership Dev   | 8 Pathways, competence levels, qualifications | Formation product + Learn product    |
| Operational Systems          | Calendars, governance cycles, Annual Rhythm   | Calendar product                     |
| Expansion & Mission          | SEND, DMN, new community formation            | Network product + Sync engine        |

## **1.2 The Local-First Philosophy**

**Core principle**

_The person has a device. How do we leverage that resource? Most software treats the device as a thin client. Local-first inverts that - the device is the primary computer. The cloud is just coordination._

This is not a product feature. It is a philosophy. It shapes every architectural decision in the Ichebo ecosystem. The device is trusted. The community owns its data. The cloud coordinates - it does not control.

## **1.3 The Prototype Principle**

The current Django build is not a failure. It is the prototype that taught us the domain. Prototypes exist to prove understanding - not to become production systems. The Django build has proven:

- The record / activity / relationship data model works
- The tenant hierarchy and materialised path approach is correct
- The Handbook cannot be modelled as a tenant - it is architecturally distinct
- The KGS has more domain depth than a single Django app can elegantly express
- Each major domain deserves its own purpose-built home

**Decision**

_Pause feature-building on the Django prototype. Complete the ecosystem architecture design. Then build each product and engine properly - starting with the foundation layer._

## **1.4 The Competitive Position**

No platform in the faith-based technology space is:

- Built local-first
- Truly cross-platform - desktop, mobile, web from a single codebase
- Offline-capable with a proper sync layer
- Structured around an apostolic governance framework
- Designed to serve individual → community → network as a connected ecosystem

Existing competitors - Planning Center, ChurchSuite, Elvanto, Breeze - are cloud-first, browser-dependent, designed for the congregational model. None serve apostolic networks. None work offline. None are local-first. Ichebo is genuinely new ground.

# **Part II - The Ichebo Product Family**

## **2.1 Three Surfaces, One Ecosystem**

Three client surfaces serve three different users at three different scales. They share one architecture, one set of engines, and one data contract.

| **Surface**    | **Primary user**                 | **Role in the ecosystem**                                     |
| -------------- | -------------------------------- | ------------------------------------------------------------- |
| Ichebo Desktop | Community steward / local pastor | Primary product - full offline community operating system     |
| Ichebo Mobile  | Individual member                | Personal companion - devotional, activity, formation progress |
| Ichebo Web     | Network and apostolic leadership | Cloud dashboard - governance, network visibility, compliance  |

## **2.2 The Primary Product Decision - Locked**

**LOCKED - Desktop is Primary**

_Ichebo Desktop is the primary product. The cloud exists to connect and give visibility to what is already happening locally on every desktop. A community can run Ichebo Desktop permanently without internet and lose nothing. The cloud is the optional coordination layer - not the product itself._

The implication: imagine the internet goes down permanently in a region for six months. Ichebo Desktop works perfectly and loses nothing. The cloud was always the optional layer.

## **2.3 The Cloud as Passport Office**

The cloud's specific role:

- Verify KGS compliance before issuing a desktop licence
- Set up the tenant correctly - tier, position in apostolic network hierarchy
- Issue the installation with a verified identity
- Connect each installation to the correct position in the network
- Provide apostolic leadership with cross-community visibility
- Coordinate sync between desktop nodes across the network

**The passport office analogy**

_You go once, in person, to prove who you are and get your document. After that you travel freely without returning. The cloud is Ichebo's passport office. The desktop is the freedom that follows._

## **2.4 The KGS Onboarding Flow**

Every community must be KGS-verified before a desktop licence is issued. This is a governance feature. Every node in the Ichebo network is a legitimate KGS-compliant community by definition.

- Community applies via Ichebo Cloud
- KGS compliance verified - apostolic covering, tier, network position confirmed
- Human approval by authorised leader - not a checkbox, not a form
- Tenant created in cloud - position in hierarchy locked in materialised path
- Desktop licence issued - installation key generated
- Community installs Ichebo Desktop, enters key on first run
- Desktop activates with verified identity - initial sync payload delivered
- Community operates fully offline from this point
- Syncs to cloud whenever internet is available

**Important**

_Step 3 requires a human in the loop with authority. This keeps growth deliberate rather than viral - a healthy constraint, not a limitation._

# **Part III - Ecosystem Architecture**

## **3.1 The Full Ecosystem Map**

The Ichebo ecosystem is organised in four layers: Foundation Engines, Governance Products, Formation Products, and Community Products. All layers are served by a shared API Gateway and connected by the Sync Engine.

| **FOUNDATION LAYER - Shared engines, no UI, called by all products** | |
| --- | | --- |
| **Identity Service** | Authentication, users, competence levels, roles, tenant management, licence issuance. Django is appropriate here. |
| **Records Engine** | The data spine - create, read, update, soft-delete records. Enforces record_class, record_family, record_type rules. Language: Go. Portable to Desktop. |
| **Activity Engine** | Participation tracking, ActivityLog, progress calculation, completion signals. Language: Go. Portable to Desktop. |
| **Relationships Engine** | Direction-aware traversal, HRS methodology, bible_verse links, derived_from chains, version history. Language: Go. |
| **Bible Engine** | Scripture text, translations (KJV, ASV, WEB), search, reference resolution. Language: Go. Text only - no HRS logic lives here. |
| **Calendar Engine** | Governance cycles, Annual Operational Rhythm, programme milestones, event coordination across products. Language: Go. |
| **Sync Engine** | Local-first coordination - ChangeLog, Push/Pull/Resolve. Orchestrates all engines during sync. Language: Go. The secret sauce. |

| **GOVERNANCE PRODUCTS - For architects and apostolic network leadership** | |
| --- | | --- |
| **Ichebo Handbook** | The institutional memory and governing intelligence of the entire system. Mandate documents, HRS library, prophetic keys, governance principles, scripture-governance mappings. Level 5 access only. Publishes downward to the network. |
| **Ichebo Governance** | Tenant-level governance for community stewards. Local handbook, mandates, keys library, governance records. Receives authorised content from Handbook. |
| **Ichebo Network** | Apostolic network management. Tenant hierarchy, cross-community visibility, SEND and DMN coordination, expansion tracking. |

| **FORMATION PRODUCTS - For community and individual growth** | |
| --- | | --- |
| **Ichebo Formation** | Competence tracking, advancement requests, shepherd confirmation workflow, level history, ordination records. The Eight Kingdom Pathways live here. |
| **Ichebo Learn / Academy** | Content delivery - video lessons, written content, assessments, curriculum. Calls Video Engine for media. Calls Formation for progress. |
| **Ichebo Calendar** | Community and network operational calendar. Governance cycles, the Seven-Year Programme milestones, gathering schedules, Annual Rhythm. |

| **COMMUNITY PRODUCTS - For daily community operations** | |
| --- | | --- |
| **Ichebo Community** | Member registry, shepherd assignments, pastoral relationships, social graph, gatherings, announcements. Two internal concerns: tenant admin and social engine - to be separated as complexity grows. |
| **Ichebo Bible** | Personal scripture engagement for all members - reading, notes, highlights, reading plans. Calls Bible Engine for text. No HRS functionality. |
| **Ichebo Media** | Video upload, transcoding, storage, CDN delivery, live streaming (RTMP/HLS), learning video with progress tracking. A full product in itself. |

| **INTELLIGENCE LAYER** | |
| --- | | --- |
| **Paraclete** | Reads all engines, surfaces insights, produces digests. Rule-based MVP. LLM-capable later. Read-only consumer - never writes to any engine directly. |

## **3.2 The Handbook - Properly Understood**

**The critical correction**

_The current workaround of modelling the Handbook as a special tenant at /global/handbook/ is exactly that - a workaround. The Handbook is not a tenant. A tenant is a community node. The Handbook is the doctrinal and governance foundation that gives rise to all tenants. It precedes them. It authorises them. It governs them._

The right mental model:

| **Layer**           | **What it is**                                                             |
| ------------------- | -------------------------------------------------------------------------- |
| Handbook            | Institutional memory - mandate, HRS, prophetic keys, governance principles |
| KGS Framework       | The governing framework - published from the Handbook                      |
| Network of Tenants  | Communities that receive and operate under the framework                   |
| Apostolic Authority | Persons who steward the Handbook and govern the network                    |

The Handbook workspace must be:

- A fully-fledged product - Ichebo Handbook - not an app within another product
- Its own service with its own data domain
- Access by invitation only - Level 5 architects and above
- Version-controlled - every document has a full history
- The HRS methodology lives here as a first-class citizen - not as a relationship type in a records table
- Publishes downward to the network - communities receive outputs, they cannot edit the Handbook

## **3.3 The Bible Engine and HRS - The Right Separation**

There are two completely different relationships with scripture in the KGS:

| **Relationship**              | **Description**                                                                                                                                       |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Personal scripture engagement | A member reads, takes notes, highlights, follows reading plans. Devotional. Personal. Informal. Served by Ichebo Bible.                               |
| HRS scripture methodology     | An architect uses scripture as interpretive source material for governance documents. Scholarly. Authoritative. Versioned. Served by Ichebo Handbook. |

These are two completely different use cases that happen to involve the same biblical text. The right separation:

- **Bible Engine - provides scripture text only. No HRS logic. Called by both products.**
- **Ichebo Bible - personal reader. Notes, highlights, plans. No HRS functionality.**
- **Ichebo Handbook - contains its own HRS Scripture module. Advanced mapping tool for architects. Links passages to governance documents. Version-controlled, audited, Level 5 only.**

**Principle**

_Same Bible Engine. Different surfaces. Different purposes. The engine serves both - it returns scripture text. What each product does with that text is completely different._

# **Part IV - Separation of Concerns**

## **4.1 The Django Question**

**The instinct that started this**

_"As I have been building this in Django, I have felt that hang on, maybe Django is doing too much - there should be another way of getting this done."_

This instinct is correct. Django is a web framework. It is excellent at what it was designed to do. It is not designed to be a video processing engine, a real-time streaming server, a sync coordination layer, a social graph engine, or a long-running background service. When pushed into those roles - it bends, and systems become fragile.

## **4.2 What Django Actually Owns**

Django stays as the web layer for the cloud platform. Its domain is precisely:

- HTTP routing and request handling
- Session management and authentication
- Serving the web UI (templates or API responses)
- Admin interface for network management
- ORM access to PostgreSQL for Identity and tenant data

Everything with its own physics - video, streaming, sync, social graph, formation logic - deserves a purpose-built home in the right language.

## **4.3 The Microservices Consideration**

The microservices approach is correct in direction. The cost must be understood:

| **What you gain**                                     | **What it costs**                                    |
| ----------------------------------------------------- | ---------------------------------------------------- |
| Each service independently deployable                 | More infrastructure to manage                        |
| Each service in the right language                    | More network calls between services                  |
| Failure isolation - one service down, others continue | Service discovery complexity                         |
| Independent scaling per service                       | Cross-service debugging is harder                    |
| Teams can own separate services                       | Data consistency across services requires discipline |

**Recommendation**

_Design with clean service boundaries from the start - even if some services begin as Django modules. Extract to standalone services as each domain's complexity demands it. This is the pragmatic path for a solo developer that does not sacrifice the architecture._

## **4.4 The Three-Phase Separation Plan**

**Phase 1 - Clean the Boundaries (Now)**

Keep Django but stop adding domain logic to it. Extract all business rules into Python modules that Django calls - not Django doing the logic itself. The engines are modules first, services later.

- Records rules → Python module called by Django
- Activity logic → Python module called by Django
- Relationship rules → Python module called by Django
- Django becomes the thin HTTP layer that calls modules

**Phase 2 - Extract Engines (Desktop Build)**

As Ichebo Desktop is built, the Go engines are built properly. The cloud Django app begins calling the same engine specifications via internal API. Django becomes a thin adapter over Go engines.

- Records Engine built in Go - cloud Django calls it
- Activity Engine built in Go - cloud Django calls it
- Relationships Engine built in Go - cloud Django calls it
- Sync Engine built in Go - embedded in Desktop, also runs on cloud

**Phase 3 - Service Extraction (As Products Mature)**

As each product's complexity demands it, services are extracted:

- Community social graph extracted when it needs to scale independently
- Video Engine built as standalone Ichebo Media service
- Formation Engine extracted as Ichebo Formation service
- Calendar Engine formalised as independent service
- API Gateway formalised - clients do not know which service answers

# **Part V - Technology Stack**

## **5.1 Stack by Layer**

| **Layer**             | **Language / Technology**              | **Rationale**                                                                                                     |
| --------------------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Desktop / Mobile UI   | Flutter / Dart                         | One codebase - Windows, macOS, Linux, Android, iOS. Native rendering per platform. Strong offline/SQLite support. |
| Foundation Engines    | Go                                     | Fast, concurrent, single binary, embeddable, no runtime dependencies. Purpose-built for this type of work.        |
| Cloud API / Web layer | Python / Django / DRF                  | Retained as the cloud web layer and API adapter. Not the domain logic owner.                                      |
| Local database        | SQLite (via Go)                        | Embedded, zero config, no server process. WAL mode for concurrent access.                                         |
| Cloud database        | PostgreSQL                             | Already running on Hetzner VPS. UUID PKs throughout.                                                              |
| Video processing      | Go + FFmpeg                            | Transcoding pipeline, upload handler, stream coordinator.                                                         |
| Live streaming        | MediaMTX or nginx-rtmp                 | RTMP ingest, HLS/DASH delivery. Purpose-built - not a framework.                                                  |
| Object storage        | Hetzner Object Storage (S3-compatible) | Video, audio, document storage. CDN delivery layer on top.                                                        |
| Intelligence layer    | Python                                 | AI/ML ecosystem lives here. Paraclete service.                                                                    |
| API Gateway           | Go or Nginx + lightweight router       | Routes requests, handles auth tokens, tenant context, rate limiting.                                              |

## **5.2 Why Go for the Engines**

- Designed for concurrent networked systems that need to be reliable, fast, and small
- A Go binary is a single executable - no runtime dependencies, starts in milliseconds
- Goroutines handle background sync while user works - no UI blocking
- Compiles to every platform - Windows, macOS, Linux, Android via gomobile
- Can be embedded in Flutter via FFI bridge
- Can run as a standalone cloud service for self-hosted Docker deployments
- Each engine is independently testable, independently deployable
- The Sync Engine as a Go binary can be published as an open protocol in future

## **5.3 The Rust Question**

Rust would produce the fastest, most memory-efficient, most provably correct engines on earth. Its ownership model makes entire classes of data corruption errors impossible at compile time.

**Recommendation**

_Write the engines in Go first. Get them working, tested, and running in production. If a performance wall is hit - rewrite the hot path in Rust. Go now, Rust when the stars align._

## **5.4 The Video Engine - Architecture**

Video serves three distinct purposes in the KGS context:

- Teaching video - sermon recordings, ministry content
- Learning video - Academy curriculum delivery
- Live streaming - gathered meetings, network-wide broadcasts

Each has different technical requirements. All share one Video Engine infrastructure.

| **Pipeline**   | **Components**                                                                                                               |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Upload         | Chunked upload → Hetzner Object Storage → Transcoding queue → Multiple quality outputs → Thumbnail generation → CDN delivery |
| Live streaming | RTMP ingest (MediaMTX) → Transcode to HLS → CDN distribution → DVR recording → Archive on stream end                         |
| Playback       | HLS player in Flutter → Quality adaptive → Offline download for Desktop → Progress tracking via Activity Engine              |
| Learning video | Same as upload pipeline + chapter markers + completion tracking + offline download                                           |

**Decision**

_Ichebo Media is a full standalone product. It cannot live inside Django. The Video Engine is Go + FFmpeg. Storage is Hetzner Object Storage. Delivery is HLS via CDN. This is a 6-month engineering track built properly._

# **Part VI - The Sync Engine**

## **6.1 Strategic Position**

**The secret sauce**

_The sync engine is not a feature. It is the product. Whoever controls the sync layer controls the network. No competitor can buy it. No price increase can take it away. No acquisition changes your access to it. It is owned entirely by Ichebo._

Over time the sync engine could be published as the Ichebo Sync Protocol - a standard for KGS-compliant community data synchronisation that other developers could implement. You become the standard, not just a product.

## **6.2 The Four Jobs**

| **Job** | **Description**                                                                           |
| ------- | ----------------------------------------------------------------------------------------- |
| TRACK   | Know what changed, where, and when - on the device. Every write appends to the ChangeLog. |
| PUSH    | Send local changes to the cloud when internet is available. Idempotent, batched, ordered. |
| PULL    | Receive cloud changes and write them locally through the appropriate engines.             |
| RESOLVE | Decide what wins when both sides changed the same record. Rules-based by data type.       |

## **6.3 Non-Negotiable Data Rules**

- **UUID primary keys everywhere - both SQLite and PostgreSQL. No auto-increment integers. Ever.**
- **Soft deletes only - no hard deletes anywhere. deleted_at timestamp. ChangeLog records DELETE operation.**
- **SQLite WAL mode - PRAGMA journal_mode=WAL. Required for concurrent UI + background sync.**
- **Idempotency - every push operation safe to run twice. Same UUID, same operation, cloud ignores duplicate.**
- **Device identity - stable UUID on first run, stored locally. How cloud identifies which node sent which change.**

## **6.4 Conflict Resolution Rules**

| **Data type**                           | **Rule**                     | **Reason**                                         |
| --------------------------------------- | ---------------------------- | -------------------------------------------------- |
| Governance records - Handbook, Mandates | Cloud wins always            | Authority flows from apostolic leadership downward |
| Permissions and roles                   | Cloud wins always            | Authority flows downward, never upward             |
| Community settings                      | Cloud wins always            | Set at onboarding, controlled by network           |
| Member registry                         | Last write wins by timestamp | Steward updates legitimate from both sides         |
| Activity logs                           | Merge - both versions kept   | Both are real events, not duplicates               |
| Personal records - journal, notes       | Local wins always            | Personal and private to the device                 |

## **6.5 Sync Engine Build Order**

_※ This sequence is non-negotiable. The UI of every feature is built after the data layer is solid._

- Design UUID schema - both SQLite and PostgreSQL models
- Build ChangeLog table and write trigger
- Build soft delete pattern - no hard deletes anywhere
- Build Records Engine Go module
- Build Activity Engine Go module
- Build Relationships Engine Go module
- Build /api/sync/push/ endpoint on cloud
- Build /api/sync/pull/?since= endpoint on cloud
- Build sync engine background process - push/pull/resolve using engines
- Build conflict resolution rules
- Build ConflictQueue and user review UI
- Build sync status bar - four states
- 7-day offline test - everything reconciles correctly

# **Part VII - Formation, Learn, Calendar and Competence**

## **7.1 The Decision**

**Decision**

_Stop deferring. Stop building MVPs that are convenient placeholders. Plan right, wait if necessary, build right. These domains are central to the KGS and deserve proper system design before a single line of code is written._

## **7.2 Ichebo Formation - Competence is Not a Number**

Competence levels in the KGS are not a field on a user profile. They represent:

- Spiritual formation progress - verified by a shepherd, not self-reported
- Authority within the governance structure - what a person can do, govern, create
- Service order assignment - which of the 24 Orders a person operates in
- Advancement criteria - what must be demonstrated before level changes
- Accountability relationships - who confirms advancement

The Formation Engine needs:

- Advancement request workflow - member initiates, shepherd reviews, authority confirms
- Competence evidence records - what was demonstrated, by whom, when
- Level history - every change timestamped, who confirmed it
- Integration with Learn Academy - formation pathway completion as evidence
- Integration with Activity Engine - participation record as evidence
- The Eight Kingdom Pathways modelled as structured journeys, not tags

## **7.3 Ichebo Learn / Academy - Not a Generic LMS**

The KGS has Eight Kingdom Pathways, qualification programmes, and leadership development tracks. Learn is not a generic LMS. It is:

- A formation pathway system - structured journeys from Level 0 to Level 5
- A qualification framework - certificates and programmes mapping to KGS competence levels
- A teaching delivery platform - video lessons, written content, assignments, assessments
- A curriculum authorship tool - Level 5 architects build pathways; communities consume them

These are three distinct internal concerns that must be cleanly separated even if delivered as one product:

- Formation tracking - who is where on which pathway
- Content delivery - the Academy - video and text consumption
- Curriculum authorship - building and publishing pathways

Learn calls the Video Engine for all media delivery. Learn calls the Formation Engine for progress and advancement. Learn does not own formation logic.

## **7.4 Ichebo Calendar - Operational Rhythm, Not an Event List**

The KGS has an Annual Operational Rhythm, Governance Cycles, and a Seven-Year Programme. Calendar is not an event list. It is:

- A governance rhythm system - when governance cycles happen, when reviews occur
- A programme milestone tracker - the Seven-Year Programme has phases that must be visible
- A community operations calendar - gatherings, formation meetings, outreach
- A network coordination layer - synchronising activity across communities in the DMN

Calendar is a service that other products publish into and read from. Events are expressions of the KGS operational rhythm - not standalone records.

# **Part VIII - Open Questions and Next Steps**

## **8.1 Formal Documents Still to be Written**

These documents do not yet exist. Each requires a dedicated advisory session.

**DOC A - Ichebo Product Vision Document**

- **TODO - Local-first philosophy statement - the device as primary computer, cloud as coordination**
- **TODO - Full product family definition with user, role, and surface for each product**
- **TODO - Data sovereignty statement**
- **TODO - Competitive positioning statement**
- **TODO - Growth model - deliberate, not viral**

**DOC B - Ichebo Desktop Product Specification**

- **TODO - MVP scope locked: People → Activity → Sync - three functions only**
- **TODO - Five-section IA: Home / People / Activity / Governance / Sync**
- **TODO - First-run experience: three-screen setup wizard**
- **TODO - Sync status bar: four states specification**
- **TODO - Dark mode as non-optional from day one**
- **TODO - Platform targets: Windows, macOS, Linux**

**DOC C - Ichebo Sync Engine Specification**

- **TODO - Full ChangeLog table schema**
- **TODO - SyncableMixin definition - cloud side Django model**
- **TODO - Conflict resolution rules matrix - complete**
- **TODO - ConflictQueue table and review UI specification**
- **TODO - API endpoints specification: /api/sync/push/ and /api/sync/pull/**
- **TODO - Go sync engine core modules sketch - HELD from this session**

**DOC D - Ichebo Technical Architecture Document**

- **TODO - Full stack by layer with rationale**
- **TODO - FFI/gRPC bridge between Flutter and Go binary**
- **TODO - KGS onboarding flow - full sequence**
- **TODO - API Gateway specification**
- **TODO - Service extraction timeline**

**DOC E - Ichebo Engine Specifications (one per engine)**

- **TODO - Records Engine - language-agnostic specification**
- **TODO - Activity Engine - language-agnostic specification**
- **TODO - Relationships Engine - language-agnostic specification**
- **TODO - Bible Engine - language-agnostic specification**
- **TODO - Calendar Engine - language-agnostic specification**
- **TODO - Sync Engine - as in DOC C above**

**DOC F - Ichebo Handbook Product Specification**

- **TODO - Handbook as institutional memory - full scope definition**
- **TODO - HRS Scripture module specification within Handbook**
- **TODO - Access model - Level 5 only, invitation**
- **TODO - Publishing workflow - how content flows from Handbook to network**
- **TODO - Version control and audit trail specification**

**DOC G - Ichebo Media Product Specification**

- **TODO - Video Engine architecture - upload, transcode, store, serve**
- **TODO - Live streaming pipeline - RTMP ingest, HLS delivery**
- **TODO - Hetzner Object Storage integration**
- **TODO - CDN delivery layer**
- **TODO - Offline download for Desktop specification**
- **TODO - Progress tracking integration with Activity Engine**

**DOC H - Ichebo Formation Product Specification**

- **TODO - Eight Kingdom Pathways as structured journeys**
- **TODO - Advancement request and confirmation workflow**
- **TODO - Competence evidence records**
- **TODO - Integration with Learn Academy and Activity Engine**
- **TODO - 24 Service Orders assignment model**

**DOC I - Ichebo Cloud Onboarding and Compliance Specification**

- **TODO - KGS compliance requirements - full list**
- **TODO - Application and human approval workflow**
- **TODO - Licence key generation and issuance**
- **TODO - Initial sync payload specification**

## **8.2 Open Design Questions**

These questions are unresolved and require dedicated brainstorm or advisory sessions:

| **Question**                                                 | **Why it matters**                                                                             |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| Go sync engine core modules - what are they?                 | Sketch held from this session - first thing to complete                                        |
| Community social graph - when to separate from tenant admin? | Community product has two concerns today. The boundary needs defining.                         |
| Ichebo Learn - one product or three?                         | Formation tracking, Academy delivery, and Curriculum authorship may warrant separation         |
| Self-hosted Docker deployment                                | For organisations that want cloud behaviour without Ichebo's cloud - what does this look like? |
| The Ichebo Sync Protocol - when to publish?                  | When the engine is proven, publishing as an open protocol makes Ichebo the standard            |
| Pricing model                                                | Per-installation vs per-seat vs network licence - not yet decided                              |
| Master roadmap update                                        | Where does Desktop fit relative to current Phase 5 cloud build?                                |
| Django phase-out timeline                                    | When does Django become a thin adapter? What triggers extraction of each domain?               |

## **8.3 The One Sentence**

**Governing principle for all decisions that follow**

_Build right or build nothing. The prototype proved the domain. Now design the real thing - elegantly, robustly, in the right language, with the right architecture, honouring the depth of the KGS framework it serves._

**Ichebo Christian Services**

_Ecosystem Architecture v0.1 - May 2026 - Living Document - Internal_