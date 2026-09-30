**ICHEBO HANDBOOK**

**Product Specification**

_DOC F — Version 2.1 — September 2026_

| **Field** | **Value** |
|---|---|
| Document | DOC F — Ichebo Handbook Product Specification |
| Version | 2.1 — 29 September 2026 |
| Status | Revised — canonical once the decisions in Part 10 are locked |
| Supersedes | DOC F v2.0 (29 September 2026) and v1.0 (May 2026) |
| Terminology authority | Introduction to the Prophet's Handbook v1 (2026-09-29), locked. Where this document and the Introduction differ on the meaning of a term, the Introduction governs. |
| ADR references | ADR-020 (Handbook as standalone product); ADR-014 (The Desk); ADR-023 (proposed: Handbook terminology and HRS alignment) |
| Data contract | data-contract-v11-canonical-2026-05-13.md Parts 1.2, 2.3, 2.5, 3, 15. A v12 amendment is required (Part 8.4). |
| Depends on | DOC A (Product Vision), DOC C (Sync Engine), DOC E (Engine Specs) |
| KGS reference | kingdom_governance_system.md — Part II (The Kingdom Mandate), Part III (Governance Architecture) |
| Authors | Chizola (domain); Claude (technical) |

**_The Handbook is not a feature of the platform. It is the institutional memory that authorises the platform to exist. It precedes all tenants. It governs all communities. It is the living record of the apostolic mandate._**

---

## Revision History

| Version | Date | Summary |
|---|---|---|
| 1.0 | May 2026 | First canonical specification. Handbook defined as a standalone product (ADR-020). Three "branches", HRS attribute set, record type registry, workspace design, publishing model, tenant migration path, build phases K.1–K.7. |
| 2.0 | 29 September 2026 | Terminology realigned to the locked *Introduction to the Prophet's Handbook* v1, the domain source for HRS. **Branches** renamed **Libraries**, and the Mandate Branch renamed the **Mandate Library**. **"Architect"** restored to its true meaning (one person) and **Handbook Stewards** introduced. **Operator** and **host** defined. Reference Library categories corrected to Symbols, Principles, Concepts and Divine Patterns, with **Class** as a grouping record. Narrative, subject and entity reclassified as **HRS analysis elements**, removed from the Mandate Library. HRS Framework separated from the Mandate framework. Definitions of principle, concept and divine pattern corrected. The six HRS attributes retired. Relationship types relabelled **record links**, and the HRS analysis links (has_subject, has_entity) proposed for reinstatement. **Journal privacy invariant** added. HRS section rebuilt around Divine Communications. Build status updated: K.1–K.6 complete. New phase **K.8 — Terminology and HRS Alignment** added. |
| 2.1 | 29 September 2026 | **HRS Bible** added as the fourth part of the Operator's Toolkit, alongside the Libraries, Journals and Resources, as the Introduction lists them. The route `app.ichebo.org/bible/` moves permanently into the Handbook as the HRS Bible. All other users read Scripture at `bible.ichebo.org` (the Ichebo Bible). The Critical Separation (Part 3.8) is restated around the two Bibles. Branch Navigator becomes the **Toolkit Navigator**. New Part 8.5 (Bible route migration), new phase **K.9 — HRS Bible**, and decisions D9–D11 added. |

---

# Part 0 — Terminology

This part fixes the vocabulary used throughout the document. Definitions are condensed from the *Introduction to the Prophet's Handbook* v1, which remains the authority.

## 0.1 People and Roles

| Term | Meaning |
|---|---|
| **The Architect** | The one person who developed the Hierarchy and Relationship System and who manages the Handbook. A single role held by one person. It is not a class of users and not a competence level. |
| **Handbook Steward** | A person appointed by the Architect to work in the Handbook alongside the Architect. Always written in full as "Handbook Steward" in platform contexts, to avoid confusion with the Level 3 platform label "Steward" (see Part 10, D1). |
| **Operator** | Anyone who uses the Operator's Toolkit: building libraries, keeping journals and interpreting divine communications. |
| **Host** | The operator in their role as keeper of their own journals. Journals are private: the host alone authors and reads them. |

## 0.2 Handbook Structure

| Term | Meaning |
|---|---|
| **Prophet's Handbook** | The Handbook: the home of the Operator's Toolkit. |
| **Operator's Toolkit** | The four places the operator works in: the HRS Bible, the Libraries, the Journals and the Resources. |
| **HRS Bible** | The Handbook's Bible: the Scriptures read with their Handbook links. Here the operator finds a reference in its place in the Scriptures and sees every Handbook record linked to it. Replaces `app.ichebo.org/bible/`. |
| **Ichebo Bible** | The personal Bible product at `bible.ichebo.org`, used by all other users. Reading, notes, highlights, reading plans. No HRS functionality. |
| **Library** | One of the three main divisions of the Handbook: the Reference Library, the Keys Library and the Mandate Library. Never "branch". |
| **Reference Library** | Also known as the Prophet's Library. Properties found in the language and thinking of Yahweh, compiled from the Holy Scriptures. |
| **Keys Library** | Also known as the Dream Library. Key symbols and devices gathered from the host's Dream Journal and Spirit Journal. Personal. |
| **Mandate Library** | Governing documents through which the Kingdom Mandate (Acts 1:1–8; Luke 19:13) is carried into ordered Kingdom work. |
| **Journals** | Private tracking records kept by the host: D.A.R (Daily Analysis Record), My Journal, Dream Journal, Prayer Journal, Spirit Journal. |
| **Resources** | The knowledge base compiled using HRS. |

## 0.3 HRS Terms

| Term | Meaning |
|---|---|
| **Divine Communications** | Messages conveyed by the Most High God, or through His appointed agents, to a chosen audience. In the Handbook the term also covers messages conveyed by other spiritual (ethereal) powers and their agents to a targeted audience. |
| **Narrative (Narration)** | A complete piece of divine communication containing a message for a given audience. It tells a storyline of a subject and its entities, symbolic or literal. It may also be a single symbol whose features each tell part of the story. |
| **Subject** | A person or thing actively working on an entity, producing according to the condition affecting it. |
| **Entity** | A person or thing toward which the condition or action of the subject is directed. Originally "object", and named "entity" throughout the Handbook and the codebase. |
| **Person** | Any living being with sentient qualities: humans, all celestial beings, fallen beings. |
| **Hierarchy** | The positional interaction between the ruling party (subject) and the subservient party (entity). |
| **Relationship** | How the entity acts under the influence working on it through the condition affecting the subject. |
| **Symbol (Presentation)** | A device, mark or character used to stand for a thing. |
| **Class** | A category of subjects and entities sharing similar attributes. It carries its own meaning, which every symbol in it shares. |
| **Principle** | A category of divine action and its outcome. Includes Foundation (Genesis) Principles and Root Principles. |
| **Concept** | The premise on which a principle can be put to work. Many concepts may come from one Root Principle. |
| **Divine Pattern** | An antitypical event, sequence or narration appointed as a figure of something to come. |
| **HRS Framework** | A collection of principles, concepts and divine patterns that make up a construct or system, determining its classes and their relationships. Distinct from a Mandate-Library framework. |
| **G.S.S.** | General Signification of Symbols, the reference basis for compiling HRS databases (William Barclay, *The Daily Study Bible*). |

## 0.4 Retired Terms

These terms from v1.0 must not be used in new documents, code comments, UI copy or data contract text.

| Retired term | Replacement |
|---|---|
| Branch / Mandate Branch / Branch Navigator | Library / Mandate Library / Toolkit Navigator |
| HRS Scripture Module (as a separate tool) | Part of the HRS Bible (Part 3.8) |
| "Architect" or "architects" meaning Level 5 users | Level 5 (Apostolic Steward); Handbook Steward; the Architect (one person only) |
| "Apostolic Properties" | Properties (of the Reference Library) |
| HRS relationship types, used for the general graph | Record links (Part 3.6). "HRS relationship" now means only the hierarchy and relationship identified between a subject and its entities. |
| HRS property attributes (complexity, relationship_position, position, direction, speed, emotional_tone) | Retired (Part 3.7) |

---

# Part 1 — What the Handbook Actually Is

## 1.1 The Architectural Correction — ADR-020

The Handbook was first implemented as a special tenant: a prime tenant at `/global/handbook/` with `tier: "handbook"` and Level 5 write access. This was a pragmatic workaround that let the Handbook run within the existing tenant hierarchy.

**LOCKED — ADR-020.** The Handbook-as-tenant implementation is formally superseded. The Ichebo Handbook is a standalone product: not a tenant, not an app within another product, not a special-case tier in the tenant hierarchy. No new features are built into the Handbook tenant.

The standalone product has been built (phases K.1–K.6, Part 9). The status of the tenant data migration (K.7) is recorded in Part 9.

## 1.2 The Correct Understanding

The Handbook is the institutional memory and governing intelligence of the entire system. It holds the mandate, the HRS methodology, the keys and the principles that give rise to all communities. It precedes tenants, authorises them and governs them.

The correct mental model is a sequence of founding, not a hierarchy:

**The Handbook.** The institutional memory: the HRS Bible, the Reference Library, the Mandate Library, the HRS methodology, and the version history of all governing documents. It exists before the network. It is the deposit of apostolic revelation the framework is built on.

**The KGS Framework.** The governing framework published from the Handbook to the network. In HRS terms the KGS is itself a framework, which is why it lives in the Operator's Toolkit under *Frameworks*.

**Network of Sceptre Communities.** The communities that receive the framework and operate under it. They are tenants in the technical sense. They do not author the Handbook; they receive what it publishes.

**The Architect and the Handbook Stewards.** The Architect manages the Handbook and appoints Handbook Stewards to work in it. Apostolic authority governs how the Handbook is applied across the network.

## 1.3 Why This Distinction Matters

A tenant is a node in the network hierarchy. It has a path, a tier, a parent and a scope within the materialised path tree. The Handbook is none of these things.

The Handbook cannot be archived, moved or superseded by another tenant. It is the root of the whole knowledge structure, not a node within it. Modelling it as a tenant introduces category errors that compound over time: it implies the Handbook could be deleted, reorganised, or have its access rules changed like any other tenant.

As a standalone product, the Handbook has its own service, data domain, access model and authorship environment. It publishes downward to the network. The network does not write back to it.

---

# Part 2 — Knowledge Architecture

## 2.1 The Operator's Toolkit

The Handbook organises the Operator's Toolkit into four places, as the Introduction lists them: the HRS Bible, the three Libraries, the Journals and the Resources. HRS is the method used throughout.

| Part of the Toolkit | What it holds | Character |
|---|---|---|
| **HRS Bible** | The Scriptures, read with the Handbook records linked to each passage | The source the Reference Library is compiled from. Text from the Bible Engine; links from the Handbook. |
| **Reference Library** | Symbols, Principles, Concepts and Divine Patterns compiled from Scripture, with the Classes, Narratives and HRS Frameworks that organise them | Objective, shared. The interpretive vocabulary of the network. |
| **Keys Library** | Key records: the host's key symbols and devices, drawn from the Dream and Spirit Journals and interpreted against the Reference Library | Subjective, personal, owner-only |
| **Mandate Library** | Mandates, statements, frameworks, protocols, procedures and programmes | Outward-flowing governance documents published to the network |
| **Journals** | The host's D.A.R, My Journal, Dream, Prayer and Spirit Journals | Private to the host. They supply data to the Keys Library. |
| **Resources** | The knowledge base compiled using HRS | Reference material |

The **execution layer** sits outside the Handbook: Activity campaigns, Learn programmes and Community gatherings in the community platform. These are applications of the Mandate Library. The Handbook governs their direction but does not hold them.

## 2.2 The Three Libraries

Every Handbook record belongs to exactly one Library.

| Library | Record types | Access |
|---|---|---|
| Reference Library | symbol, class, principle, concept, divine_pattern, narrative, hrs_framework | Level 3+ read. Authorship by the Architect and Handbook Stewards. |
| Mandate Library | mandate, statement, framework, protocol, procedure, programme | Level 4+ read. Authorship by the Architect and Handbook Stewards. |
| Keys Library | key | Owner only. Level 3+ may create their own. |

## 2.3 The Reference Library

The Reference Library has **four main categories**, as the Introduction defines them: Symbols, Principles, Concepts and Divine Patterns.

Three **supporting record types** organise those categories:

- **Class** groups symbols. A class is written once as its own record and holds the meaning its members share. For example, the class of wild animals and predators carries the self-centeredness reading, with the kosher exception. Each symbol links to its class with a `part_of` link (Part 3.6).
- **Narrative** holds a divine communication under HRS analysis. The subjects and entities identified in it are linked to the narrative, and the analysis itself is written in the narrative's content (Part 3.5).
- **HRS Framework** gathers the principles, concepts and divine patterns that make up a construct or system, and determines its classes and their relationships.

## 2.4 The Mandate Library

The Mandate Library holds the governing documents through which the Kingdom Mandate is carried into ordered Kingdom work.

The Kingdom Mandate is the commission Christ gave His apostles before His ascension (Acts 1:1–8). It calls His people to occupy and influence the world for the purposes of God until He returns (Luke 19:13).

The Reference Library holds what the Scriptures reveal of God's language and thinking. The Keys Library holds personal signals received by the host. The Mandate Library holds what is sent outward.

A Mandate-Library **framework** keeps the conventional meaning of the word: a structured governance framework. It is a different record type from an HRS Framework (`hrs_framework`), which lives in the Reference Library.

## 2.5 The Full Record Type Registry

| Record type | What it is | Library | Change from v1.0 |
|---|---|---|---|
| symbol | A device, mark or character used to stand for a thing (also called a presentation) | Reference | **New** |
| class | A category of subjects and entities sharing similar attributes. Carries the meaning its member symbols share. | Reference | **Redefined** (was "a branch or category of Kingdom knowledge") |
| principle | A category of divine action and its outcome | Reference | **Redefined** (dropped "or apostolic experience") |
| concept | The premise on which a principle can be put to work | Reference | **Redefined** |
| divine_pattern | An antitypical event, sequence or narration appointed as a figure of something to come | Reference | **Redefined** |
| narrative | A complete piece of divine communication under HRS analysis | Reference | **Moved** from Mandate and redefined |
| hrs_framework | A collection of principles, concepts and divine patterns making up a construct or system | Reference | **New** |
| mandate | A directive from the Kingdom Mandate: what the network is sent to do | Mandate | Unchanged |
| statement | A formal declaration of position, belief or intent | Mandate | Unchanged |
| framework | A structured governance framework, in the conventional sense | Mandate | Clarified |
| protocol | A defined sequence of steps for a recurring occasion | Mandate | Unchanged |
| procedure | An operational process for recurring tasks | Mandate | Unchanged |
| programme | A structured governance-context programme. Not the same as a Learn programme. | Mandate | Unchanged |
| key | A key symbol or device from the host's Dream or Spirit Journal, interpreted against the Reference Library | Keys | Wording aligned |
| calendar | A time-governed plan of seasons and appointed times | Deferred | Unchanged (deferred) |
| ~~subject~~ | — | — | **Removed as a record type.** Subject becomes a role in HRS analysis (Part 3.5). |
| ~~entity~~ | — | — | **Removed as a record type.** Entity becomes a role in HRS analysis (Part 3.5). |

## 2.6 Journals

Journals live in the community platform's Records Engine, not in the Handbook data domain. They matter to the Handbook because they supply the Keys Library.

| Journal | Purpose | Record type (data contract v11, Part 2.3) |
|---|---|---|
| D.A.R (Daily Analysis Record) | A tracking journal: a dashboard for managing the linkages in the affairs of the host | `dar` |
| My Journal | Collects and records the thoughts and activities of the host | `note` (to be confirmed, Part 10, D7) |
| Dream Journal | Records the host's dreams. Chief source for the Keys Library. | `dream` |
| Prayer Journal | Records and tracks the host's prayer life | `prayer` |
| Spirit Journal | Records what the host receives by the Spirit. Source for the Keys Library. | `spirit` |

All journal records are `record_family: journal`, `record_class: personal`, `visibility: private`. The Journal Privacy Invariant (Part 6.2) governs every place a journal entry can be linked or shown.

---

# Part 3 — The Hierarchy and Relationship System

## 3.1 Divine Communications

**Divine Communications** are messages conveyed by the Most High God, or through any of His appointed agents, to a chosen audience: a person, a people, or the whole of creation.

In the Handbook the term also covers messages conveyed by other spiritual (ethereal) powers and their agents to a targeted audience. The operator must be able to recognise and weigh every communication received, not only those that come from God.

Every divine communication has four parts:

| Part | Description |
|---|---|
| Sender | The Most High God, one of His agents, or another spiritual power |
| Message | The content being conveyed |
| Medium | Person to person, written, or through dreams and visions |
| Receiver | The person, group, or part of creation it is meant for |

## 3.2 What HRS Is

**Management of Divine Communications** is the organising and passing on of divine information. It runs through three stages: capturing and recording; observation and interpretation; application and conveying.

The **Hierarchy and Relationship System (HRS)®** is the method the Handbook uses for this management. It organises and identifies the elements of divine communications.

HRS is not a tagging system or a categorisation scheme. It is the method by which:

- divine communications are captured, and their elements identified by hierarchy and relationship;
- the Reference Library is compiled from Scripture according to the General Signification of Symbols;
- the operator's personal keys are interpreted against that shared vocabulary.

The Handbook product is the digital home of this method. The platform supports HRS; it does not define it. The Introduction to the Prophet's Handbook defines it.

## 3.3 The HRS Method

The method has four steps.

**1. Determine the ruling influence.** Two laws, named in Romans 8:2, govern the thoughts and actions of every person or thing:
- the law of the Spirit of life in Christ Jesus: the tree of **Selflessness**;
- the law of sin and death: the tree of **Self-centeredness**.

These two laws decide the relationship between a subject and its entities in a narration.

**2. Determine the relationship between the subject and the entities.** The elements of a narration are sorted into subjects and entities by hierarchy and relationship. Classes, traits and locations are identified in this step. The Introduction's worked example on Ezekiel 29:3 is the reference case.

**3. Compile the databases.** All information is compiled according to the General Signification of Symbols (G.S.S.) used in the Scriptures. Research records and authorised references support the compilation where case studies are required.

**4. Main categories.** The compiled results become Symbols, Principles, Concepts and Divine Patterns in the Reference Library.

Once identified, elements move on to observation, interpretation and application.

## 3.4 How the Method Maps to the Product

| HRS step | Where it happens in the Handbook |
|---|---|
| Capturing and recording | A **narrative** record is created for the divine communication. It is linked to its Scripture passage (Part 3.8), or, for personal communications, the host's journal supplies the data to a **key** record. |
| Identification (steps 1–2) | The subjects and entities are linked to the narrative with `has_subject` and `has_entity` links (Part 3.5). The analysis (ruling influence, hierarchy, relationship, class, traits, location) is written in the narrative's content. |
| Compilation (step 3) | **Symbol** records are created or updated and linked to their **class**. Principles, concepts and divine patterns are compiled and linked. |
| Main categories (step 4) | The four categories are browsable in the Reference Library. HRS Frameworks gather them. |
| Observation, interpretation, application | Written in the content of the relevant records. Mandate Library records carry the application outward. |

## 3.5 Narrative Analysis

Subject and entity are **roles an element plays within a particular narrative**, not kinds of record. Pharaoh is the subject in Ezekiel 29:3, ruling over his rivers. In another narration the same figure could be an entity. The role therefore lives on the link between the narrative and the element, not on the element's record.

The **proposed model** (Part 10, D3) is as follows:

- A **narrative** record holds the divine communication and its written analysis.
- `has_subject` links the narrative to each record playing the subject role: a symbol, or a person represented as a symbol.
- `has_entity` links the narrative to each record playing the entity role.
- The hierarchy and relationship between them is written in the narrative's analysis. It is not stored as structured fields while the HRS attributes remain retired (Part 3.7).

`has_subject` and `has_entity` were retired in data contract v11 (Part 2.5.4), with existing data retained. v2.0 proposes reinstating them for this purpose only. The retained data must be audited to see whether it can be adopted.

Symbols carry a **general** meaning (their G.S.S. reading and their class) and a **contextual** meaning within a given narrative. For example, a river means a kingdom *in the context of* Ezekiel 29:3. The general meaning lives on the symbol record. The contextual meaning lives in the narrative's analysis.

## 3.6 Record Links

The Handbook uses a controlled set of link types from the Relationships Engine to connect records. These are **record links**: the plumbing of the knowledge graph. They are not HRS relationships in the methodological sense. The seven types built in K.3 are retained unchanged in code; only their labels and examples change.

| Link type | Direction | Meaning | Example (corrected in v2.0) |
|---|---|---|---|
| part_of | directed | A is a member or component of B | symbol part_of class; principle part_of hrs_framework |
| derived_from | directed | A is derived from B | concept derived_from principle; key derived_from journal entry (owner-only, Part 6.2) |
| aligns_with | directed | A is consistent with B | programme aligns_with mandate |
| authorised_by | directed | A is authorised by B | procedure authorised_by mandate |
| references | directed | A cites B | any record references BibleVerse (Part 3.8) |
| has_symbol | bidirectional | A and B share symbolic meaning | key has_symbol symbol |
| matches_pattern | directed | A exemplifies the pattern of B | narrative matches_pattern divine_pattern |
| has_subject | directed | Narrative A has B in the subject role | **Proposed reinstatement** (Part 3.5) |
| has_entity | directed | Narrative A has B in the entity role | **Proposed reinstatement** (Part 3.5) |

v1.0's example "concept derived_from divine_pattern" is withdrawn. A concept derives from a principle.

## 3.7 HRS Attributes — Retired

v1.0 carried six HRS property attributes on Reference Library records: complexity, relationship_position, position, direction, speed, emotional_tone. They are **retired** in v2.0. Their meanings in the underlying research are no longer certain, and fields whose meaning is unclear cannot be filled in consistently.

The rules for retirement:

- The HRS attributes panel is removed from the Properties Sidecar.
- No new values are written to these `custom_fields` keys.
- **Existing values are retained in the database, untouched.** They may help recover the research. They are neither deleted nor migrated.
- Because the attributes were free-text in `custom_fields`, no schema change is needed.

If structured HRS fields return, they will be defined in the Introduction first and brought into this specification by amendment.

## 3.8 The HRS Bible

The HRS Bible is the Bible of the Handbook. The Holy Scriptures are the data source of the Reference Library, so the Scriptures sit inside the Handbook as the first part of the Operator's Toolkit.

The HRS Bible does two things:

- **Reading with links.** The operator reads a passage and sees, beside each verse, the Handbook records linked to it: the narratives analysed from it, and the symbols, principles, concepts, divine patterns and mandates that cite it. Each linked record opens in the Handbook. Only records the reader is permitted to see are shown (Part 5).
- **Scripture mapping.** The Architect and Handbook Stewards link passages to Handbook records from here, as well as from the Scripture tab of the Properties Sidecar. This absorbs what v2.0 called the HRS Scripture Module.

The HRS Bible holds no Scripture text of its own. It calls the Bible Engine for text and adds the Handbook's link layer on top.

**The HRS Bible replaces `app.ichebo.org/bible/`.** That route moves permanently into the Handbook. All other users read Scripture at `bible.ichebo.org`. The migration is set out in Part 8.5.

### The Critical Separation

There are two Bibles in the Ichebo ecosystem, and they must stay separate.

| Surface | Who uses it | What it does |
|---|---|---|
| **Ichebo Bible** (`bible.ichebo.org`) | All users | Personal Scripture engagement: reading, notes, highlights, reading plans. Calls the Bible Engine for text. No HRS functionality. |
| **HRS Bible** (in the Handbook) | Operators with Handbook access | Scripture read with Handbook links, and scripture mapping by the Architect and Handbook Stewards. Version-controlled and audited. Calls the Bible Engine for text and adds the Handbook link layer. |

**The architectural rule.** The Bible Engine provides text to both surfaces and holds no HRS logic. HRS functionality lives only in the Handbook and is never built into the Ichebo Bible. The Ichebo Bible returns text. The Handbook builds meaning.

## 3.9 Scripture Linkage Pattern

A scripture link is a `references` link from a Handbook record to a BibleVerse, with `bible_verse_id` set instead of `to_record_id`. Links can be made from either direction. From a record, the Scripture tab of the Properties Sidecar lets the author find a verse, read it and link it in one workflow. From the HRS Bible, the author selects a verse and links it to an existing record, or starts a new narrative from the passage.

Two examples:
- A narrative record for Ezekiel 29:3 is linked to that verse with `references`. Its subjects and entities are then linked with `has_subject` and `has_entity`.
- A mandate on community formation is linked to Matthew 28:19–20 as its scriptural authority.

---

# Part 4 — The Handbook Workspace

## 4.1 The Desk as Proof of Concept

The Desk, built in Version 2 as part of the Apostolic Command Shell, proved three things:

- Handbook authorship is a distinct discipline and needs its own environment.
- The Handbook's needs (HRS analysis, scripture mapping, versioning, key management) exceed what a community governance app can provide.
- The Options Bar as a metadata sidecar is the right pattern for record properties, links and scripture.

The Handbook workspace is The Desk, completed and given its own home. It was built in K.2.

## 4.2 Product Attributes

| Attribute | Value |
|---|---|
| Product type | Standalone: its own service, data domain and UI surface |
| Access | Invitation only. The Architect appoints Handbook Stewards. |
| Authorship | The Architect and Handbook Stewards. Read access per Part 5. |
| Version control | Full version history on every record (previous_version_id chain) |
| Audit trail | Every write logged: who created, edited, published, locked, superseded |
| Publishing | Published downward to the network via sync |
| Scripture | The HRS Bible (Part 3.8) |
| Isolation | Communities receive the Handbook; they cannot edit it. The Handbook does not receive from communities. |
| Status | Built. Layer 9, K.1–K.6 complete. K.8 required for v2.0 alignment. |
| ADR reference | ADR-020; ADR-023 (proposed) |

## 4.3 Workspace Surface

The workspace uses the Apostolic Command Shell's four-column architecture, tuned for Handbook authorship. All visual decisions are governed by DESIGN.md and design-preview.html.

| Zone | Width | Function |
|---|---|---|
| **Toolkit Navigator** (was Branch Navigator) | 72–120px, Ink | The HRS Bible, then the three Libraries: Reference, Mandate, Keys. The active place is marked with the left red rule. |
| **Knowledge Explorer** | 280px | In the HRS Bible: translation, book and chapter navigation, and passage search. In a Library: browse and search records in the active Library, grouped by record type. In the Reference Library, the four main categories are listed first, then Classes, Narratives and HRS Frameworks. Filter by status, date and author. |
| **Authorship Canvas** | Flexible, Stone | In the HRS Bible: the passage reader, with a link marker beside each verse that has Handbook links. In a Library: the writing surface. Markdown authorship. Record titles in the DESIGN.md display face; 680px max-width, centred. |
| **Properties Sidecar** | 320px | Tabbed: **Properties** (status, lifecycle controls, class membership for symbols) · **Links** (record links, incoming and outgoing) · **Analysis** (narratives only: subjects and entities) · **Scripture** (linked verses) · **History** (version chain). In the HRS Bible, the sidecar lists the Handbook records linked to the selected verse, with actions to link or start a narrative. |

## 4.4 Authorship Canvas

**Record creation flow**

1. The author selects a Library and record type in the Knowledge Explorer.
2. A new record opens in the Authorship Canvas with the title field focused.
3. The author writes in markdown, with live preview available.
4. For a symbol, the author sets its class in the Properties tab.
5. For a narrative, the author links the Scripture passage, then adds subjects and entities in the Analysis tab.
6. The author adds scripture links and record links.
7. The record follows the lifecycle: draft → active → locked → superseded.

**The markdown environment**

- Obsidian-style live preview, with a toggle between edit and preview.
- A floating formatting toolbar: H1–H4, bold, italic, blockquote, link.
- Auto-save on a 3-second debounce, with a "Saved" pulse in the toolbar.
- A 680px writing measure for long-form work.
- The record ID shown in the DESIGN.md monospace face at the top.

**Lifecycle controls**

- Status badge: draft → active → locked → superseded.
- **Publish:** draft to active, with confirmation.
- **Lock:** active to locked. The confirmation reads "Record will be immutable after locking."
- **Create new version:** available on locked records. Creates a new draft with previous_version_id set.
- Superseded records are greyed out in the Knowledge Explorer, with the full chain in the History tab.

Which grants may publish, lock and version is set out in Part 5.1.

---

# Part 5 — Access Model

Authority flows from the Architect and apostolic leadership downward. The Handbook is never democratised.

## 5.1 Access Rules

| Who | Library access | Authorship |
|---|---|---|
| Level 0b–2 (Seeker, Member, Disciple) | No Handbook access | Own journals only (community platform) |
| Level 3 (Functional Minister) | HRS Bible and Reference Library: read | Own journals; own key records in the Keys Library |
| Level 4 (Leader) | HRS Bible, Reference Library and Mandate Library: read | Own journals and keys |
| Level 5 (Apostolic Steward) | HRS Bible and all Libraries: read (Keys: own only) | Own journals and keys. Handbook authorship only if appointed a Handbook Steward. |
| **Handbook Steward** (appointed; Level 5 minimum) | HRS Bible and all Libraries: read (Keys: own only). Scripture mapping in the HRS Bible. | Per HandbookAccess grant: **author** creates and edits drafts; **editor** also publishes, locks and creates new versions. *Confirm against the as-built permission checks.* |
| **The Architect** | HRS Bible and all Libraries: read (Keys: own only). Scripture mapping in the HRS Bible. | Full authorship. Sole authority to appoint and remove Handbook Stewards and to change their grants. |

In the HRS Bible, each reader sees only the links to records their level permits: a Level 3 reader sees Reference Library links but not Mandate Library links. No one's key records or journal links ever appear in another person's view. Access levels for the HRS Bible are proposed in Part 10, D9.

No one, including the Architect, can read another person's key records or journals. See Part 6.

## 5.2 Invitation-Only Access

Handbook access is not granted by competence level alone. Level 5 is the minimum, not the qualification. Access is appointed, not earned by meeting a threshold. This mirrors the KGS: authority is given, not claimed.

The appointment flow:

1. The Architect identifies a Level 5 Apostolic Steward for Handbook work.
2. The Architect grants access through the Handbook's access management panel, not through tenant membership.
3. The new Handbook Steward is notified: "You have been appointed a Handbook Steward."
4. They sign in to the Handbook with their shared platform identity.

The platform enforces this: no user may grant themselves Handbook access.

## 5.3 Keys Library — Personal Access

The Keys Library is the exception to invitation-only access. Level 3+ operators author their own key records.

A key record is a key symbol or device drawn from the host's Dream or Spirit Journal, interpreted through prayerful study and linked to the Reference Library symbol that gives it its vocabulary. This is a personal spiritual discipline, not a governance function. The Keys Library honours it with a private surface.

---

# Part 6 — Privacy Invariants

## 6.1 Keys Library Privacy Invariant (built, K.6)

Key records are owner-only. They are:
- never visible to other users, editors, Handbook Stewards or the Architect;
- never included in the publish feed;
- never subject to the governance lifecycle.

This is enforced through shared helpers in all API and workspace views and covered by 13 passing tests. v2.0 does not change it.

## 6.2 Journal Privacy Invariant (new in v2.0)

Journals are private. The host alone authors and reads them. Journal records are already `record_class: personal`, `visibility: private`, and sync as Local Wins. v2.0 extends that privacy to every Handbook surface that can touch a journal entry:

1. **Links.** Any record link where either end is a journal entry is visible only to the journal's owner. The link is not shown to anyone else, even when the other end is visible to them.
2. **Publish feed.** No link to a journal entry, and no journal content, is ever included in the Handbook publish feed.
3. **Published records.** A record that is published to the network must not carry a link to a journal entry. Data contract v11 documents `mandate derived_from spirit_journal_entry`, which breaks this rule. It must be removed or re-scoped (Part 10, D4).
4. **Tests.** K.8 adds tests matching the Keys pattern: a journal-linked record viewed by another user, by a Handbook Steward, and through the publish feed must reveal nothing of the journal entry.

---

# Part 7 — Publishing

## 7.1 The Publishing Flow

The Handbook publishes downward to the network. When a record is activated, it becomes available to communities according to the access rules, and is included in their sync pull payload.

| Step | What happens |
|---|---|
| 1 | The Architect and Handbook Stewards author and publish records |
| ↓ | Publishes downward |
| 2 | Ichebo Cloud includes active and locked Handbook records in sync pull payloads |
| ↓ | Synced to device |
| 3 | Communities read Handbook content, read-only on Desktop and in the Governance App |

## 7.2 What Gets Published

| Status | Published to the network? |
|---|---|
| draft | No. Visible only in the Handbook workspace. |
| active | Yes, to users with the right level of access |
| locked | Yes. Immutable, authoritative version. |
| superseded | Yes, retained for history. Marked superseded and not featured in browse views. |

Key records and journal links are never published, whatever their status (Part 6).

## 7.3 Conflict Resolution

Per the Sync Engine rules (DOC C, ADR-018), Handbook and Mandate records use **Cloud Wins, always**. A community steward cannot locally override a Handbook record. The Handbook's authority is preserved at the data level: as a sync invariant, not only as a permission rule. Journals, being personal records, remain **Local Wins**.

---

# Part 8 — Migration

## 8.1 Handbook-as-Tenant (Original Production State)

| Attribute | Value |
|---|---|
| Tenant ID | handbook-singleton-uuid (seeded by management command) |
| Path | /global/handbook/ |
| Tier | handbook |
| Access control | Special-cased in the permission algorithm |
| Write access | competence_level ≥ 5 |
| Read, Reference types | competence_level ≥ 3 |
| Read, Mandate types | competence_level ≥ 4 |

## 8.2 Tenant Migration Path (K.7)

1. Audit every record in the Handbook tenant: type, status, links, scripture links.
2. Migrate records into the Handbook product domain, preserving IDs, version chains, links and scripture links.
3. Point Governance App references at the Handbook product API.
4. Source the Sync Engine pull payload from the Handbook product.
5. Remove the `handbook` tier from the Tenant model once everything is confirmed.

**Migration principle.** IDs are preserved. A record's UUID is its permanent identity. This is why UUID primary keys are non-negotiable.

## 8.3 Terminology and HRS Alignment Migration (K.8)

v2.0 changes the meaning or placement of several record types that already exist in production. Existing data must be **audited before it is moved**, because records created under v1.0 meanings may not fit the corrected ones.

| Current data | Action |
|---|---|
| Library discriminator values | Rename to Reference / Mandate / Keys Library in all UI copy. If the model field is named `branch`, rename it to `library` in a migration. |
| `class` records | Audit each one. Records that match the corrected meaning (a grouping of symbols) stay. Others are re-typed (for example to `concept` or `hrs_framework`) with the Architect's approval. |
| `narrative` records (Mandate) | Move to the Reference Library. **Read access widens from Level 4+ to Level 3+**, so each must be reviewed before the move. Any that are really governance precedent or testimony are re-typed within the Mandate Library. |
| `subject` and `entity` records | Audit. Those that are symbols become `symbol` records. Their role in any narrative becomes a `has_subject` or `has_entity` link. Records that fit neither are referred to the Architect. |
| Mandate `framework` records | Review. Those that are HRS Frameworks are re-typed `hrs_framework` and move to the Reference Library. |
| Retired `has_subject` / `has_entity` data | Audit against the proposed model (Part 3.5). Adopt what fits; leave the rest untouched. |
| HRS attribute values in `custom_fields` | Retain untouched (Part 3.7). |
| Journal-linked records | Audit every link to a journal entry and apply the Journal Privacy Invariant (Part 6.2). |

Every re-type is recorded in the audit log, and no record is deleted. Soft delete only, per the platform rule.

## 8.4 Data Contract v12 Amendment

The following changes to data contract v11 are required:

- **Part 2.3:** the Level 5 platform label "Architect" is replaced (Part 10, D2).
- **Part 2.5.3:** the governance type table is replaced with the Part 2.5 registry above.
- **Part 2.5.4 and Part 3:** relationship types relabelled as record links, corrected examples, `has_subject` and `has_entity` reinstated, and the `mandate derived_from spirit_journal_entry` pattern removed or re-scoped.
- **Part 15.4:** the authority matrix is updated to Libraries, the new record types, and Handbook Steward authorship.
- All instances of "Mandate Branch" become "Mandate Library".
- The Handbook-as-tenant section is removed once K.7 completes.
- **Part 13 (Bible):** the Handbook linkage feature is reassigned from the Bible App to the HRS Bible, and the Bible App's route and surfaces are updated per Part 8.5.

---

## 8.5 Bible Route Migration (K.9)

`app.ichebo.org/bible/` moves permanently into the Handbook as the HRS Bible. All other users read Scripture at `bible.ichebo.org`.

| Element at `app.ichebo.org/bible/` today | Where it goes |
|---|---|
| Scripture reader (KJV, ASV, WEB) | HRS Bible for Handbook users; Ichebo Bible for everyone else. Both read from the Bible Engine. |
| Handbook linkages (Level 5) | HRS Bible. This is the core of it. |
| Personal Bible notes (`bible_note`, personal) | Ichebo Bible. They are Records Engine records, so nothing is moved or lost; they are shown at `bible.ichebo.org`. |
| Tenant-scoped Bible notes | Ichebo Bible, with their tenant visibility unchanged |

**Routing.** After K.9, `app.ichebo.org/bible/` no longer serves a reader. A request to it is redirected by who is asking: a user with Handbook read access goes to the HRS Bible; everyone else goes to `bible.ichebo.org`. The same applies to deep links, which keep their book, chapter and verse. Because the destination depends on the user, the redirect must be a temporary (302) redirect issued by the application, not a cached permanent (301) redirect in Nginx.

**Sequencing gate.** The route cannot move until `bible.ichebo.org` is live. Otherwise community users lose Bible access. `bible.ichebo.org` is in the design pipeline (DOC L) and not yet built (Part 10, D10).

# Part 9 — Technical Specification and Build Status

## 9.1 Service Attributes

| Attribute | Value |
|---|---|
| Service type | Standalone Django app, separate from the community apps |
| Language | Python (Django 4.2). Go extraction later if complexity demands it. |
| Data domain | Own tables (`HandbookRecord`, `HandbookRelationship`, `HandbookAccess`) |
| API | DRF endpoints, consumed by the workspace UI and the Sync Engine |
| Authentication | Shared identity service (accounts app): the same user accounts, with separate Handbook access grants |
| Design authority | DESIGN.md and design-preview.html |

## 9.2 Data Model (as built, with v2.0 changes)

| Model | Purpose | v2.0 changes |
|---|---|---|
| **HandbookRecord** | UUID primary key. Library discriminator (Reference / Mandate / Keys). record_type from the Part 2.5 registry. Four-status lifecycle. Version chain fields. | Registry update. Discriminator relabelled. Symbol class membership via `part_of`. |
| **HandbookRelationship** | Record links (seven types) and scripture links (`bible_verse_id`) | Relabelled "record links". `has_subject` and `has_entity` added if D3 is locked. Journal-link privacy enforced. |
| **HandbookAccess** | Access grants: reader / author / editor | The Architect issues and revokes all grants. Grant holders are Handbook Stewards. |

Constraints enforced by the service:

- `record_class: governance` on all Reference and Mandate records.
- `record_type` must be in the registry and valid for the record's Library.
- All writes require an explicit HandbookAccess grant; Level 5 alone is not enough.
- Every write creates an audit entry: who, what, when, and from which status to which status.

## 9.3 Version History Fields

| Field | Purpose |
|---|---|
| previous_version_id | The record this version supersedes. Null for the first version. |
| superseded_by | The record that supersedes this one. Null until superseded. |
| version_number | Human-readable label ("v1", "v2"), set on creation |
| locked_at | Timestamp of locking |
| locked_by | UUID of the user who locked the record |

## 9.4 Core API Endpoints

| Endpoint | Purpose |
|---|---|
| GET /api/handbook/records/ | List records. Filter by library, type, status. |
| GET /api/handbook/records/{id}/ | Full detail, including links and scripture links. Journal links shown only to their owner. |
| POST /api/handbook/records/ | Create. Requires an author grant. |
| PATCH /api/handbook/records/{id}/ | Update. Locked records reject content changes. |
| POST /api/handbook/records/{id}/publish/ | draft → active |
| POST /api/handbook/records/{id}/lock/ | active → locked, with confirmation |
| POST /api/handbook/records/{id}/new-version/ | New draft version of a locked record |
| GET /api/handbook/records/{id}/history/ | Full version chain |
| GET /api/handbook/publish-feed/?since={ts} | Sync feed: active and locked records changed since the timestamp. Excludes keys and journal links. |
| GET /api/handbook/access/ | The requesting user's Handbook access |
| GET /api/handbook/bible/{translation}/{book}/{chapter}/ | HRS Bible passage: verse text from the Bible Engine, with the Handbook links the user is permitted to see, per verse |
| GET /api/handbook/bible/verses/{bible_verse_id}/links/ | All Handbook records linked to one verse that the user is permitted to see |

The v1.0 filter parameter `branch` is replaced by `library`. The old parameter is accepted as an alias until API versioning lands, then removed.

## 9.5 Build Phases and Status

| Phase | What it built | Status |
|---|---|---|
| K.1 — Handbook Foundation | Standalone app, own data domain, core DRF endpoints, invitation-only access grants, shared identity | ✅ Complete |
| K.2 — Workspace UI and The Desk | Four-zone authorship interface, record CRUD, lifecycle controls, version history display | ✅ Complete |
| K.3 — HRS Relationships | Seven link types in the Properties Sidecar; add, remove and traverse | ✅ Complete |
| K.4 — Scripture Linking | Bible Engine integration, verse search, scripture links | ✅ Complete |
| K.5 — Publish Feed | Lifecycle publishing, publish-feed endpoint, Sync Engine integration | ✅ Complete |
| K.6 — Keys Library Privacy | Owner-only key records; invariant enforced with 13 tests | ✅ Complete |
| K.7 — Handbook-as-Tenant Migration | Part 8.2 | ⚠️ Status to be confirmed against the repo roadmap |
| **K.8 — Terminology and HRS Alignment** | Part 8.3 data audit and migration; registry update; relabelling to Libraries, record links and Handbook Steward; Analysis tab and has_subject / has_entity (if D3 locked); HRS attributes panel removed; Journal Privacy Invariant and tests; `library` API parameter; data contract v12 | ⏳ New in v2.0 |

| **K.9 — HRS Bible** | Toolkit Navigator entry; passage reader with per-verse Handbook links; scripture mapping from the HRS Bible; the two Bible endpoints; move of the Handbook linkage feature from the Bible App; per-user redirect of `app.ichebo.org/bible/`; permission tests for per-verse link visibility | ⏳ New in v2.1 |

**K.8 entry requirement:** ADR-023 accepted, the Part 10 decisions locked, and the Part 8.3 audit reviewed by the Architect before any record is re-typed.

**K.9 entry requirement:** K.8 complete and `bible.ichebo.org` live in production (Part 8.5).

## 9.6 Deferred Items

- `calendar` record type: registered, deferred.
- Structured HRS fields: deferred until defined in the Introduction (Part 3.7).
- Full HRS graph visualisation.
- Level 4 tenant-scoped governance records.
- Public Handbook: a read-only public view of selected Reference Library records.
- Handbook API for authorised external integrations.

---

# Part 10 — Decisions Required Before K.8

These decisions surfaced while aligning this document with data contract v11. Each has a recommendation. Once locked, they are recorded in ADR-023.

| # | Decision | Recommendation |
|---|---|---|
| D1 | **"Steward" collision.** Data contract v11 labels Level 3 "Steward" and Level 4 "Senior Steward". The Handbook's appointed workers are now "stewards". | Use **Handbook Steward** in full in all platform contexts. |
| D2 | **Level 5 platform label.** Data contract v11 labels Level 5 "Architect", which contradicts the locked meaning. Separately, Level 2 is labelled "Disciple/Operator", while the Handbook's "operator" means anyone using the Toolkit. | Relabel Level 5 **"Apostolic Steward"**, its KGS name. Relabel Level 2 **"Disciple"** so "operator" keeps its Handbook meaning. |
| D3 | **Reinstate has_subject / has_entity** as HRS analysis links (Part 3.5). | Reinstate, for narrative analysis only. |
| D4 | **mandate derived_from spirit_journal_entry.** A published Mandate linked to a private journal entry breaks the Journal Privacy Invariant. | Remove the pattern. Where a mandate genuinely arose from a journal entry, the author records that in the mandate's content without linking the private entry. |
| D5 | **HRS Framework record type name.** | `hrs_framework`, in the Reference Library. |
| D6 | **Disposition of existing records** whose type changes meaning (Part 8.3). | The Architect reviews the audit before any re-type. No automatic re-typing. |
| D7 | **My Journal record type.** | Confirm that My Journal maps to `note` in the journal family. |
| D8 | **K.7 status.** | Confirm against the repo roadmap whether the tenant migration is complete. |
| D9 | **Who may read the HRS Bible.** | Anyone with Handbook read access (Level 3+), seeing only the links their level permits. Scripture mapping by the Architect and Handbook Stewards only. |
| D10 | **Timing of the Bible route move.** | Move `app.ichebo.org/bible/` only once `bible.ichebo.org` is live. Until then the current Bible App stays in place, and no new features are added to it. |
| D11 | **Personal notes in the HRS Bible.** | Keep personal notes in the Ichebo Bible only. The HRS Bible shows Handbook links, not personal annotations, which keeps the two Bibles cleanly separate. |

---

**Ichebo Christian Services**

_DOC F — Ichebo Handbook Product Specification v2.1 — 29 September 2026_
