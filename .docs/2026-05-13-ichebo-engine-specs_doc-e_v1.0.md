**ICHEBO**

**Engine Specifications**

_DOC E - Version 1.0 - May 2026_

| **Field**     | **Value**                                                          |
| ------------- | ------------------------------------------------------------------ |
| Document      | DOC E - Engine Specifications                                      |
| Version       | 1.0 - May 2026                                                     |
| Status        | Approved - Canonical Reference                                     |
| ADR reference | ADR-019 (Go engines), ADR-018 (Sync Engine), ADR-016 (local-first) |
| Data contract | data-contract-v11-canonical-2026-05-13.md Parts 3, 4, 11, 13, 22   |
| Depends on    | DOC C (Sync Engine Spec), DOC D (Technical Architecture)           |
| Authors       | Chizola (domain); Claude (technical)                               |

**Purpose**

This document provides the complete, language-agnostic specification for all six Ichebo domain engines. Both the Go implementation (Ichebo Desktop, Layer 5+) and the Python/Django implementation (cloud, current) must conform to the rules defined here. The data contract is the lingua franca - both implementations must produce identical results for identical inputs.

**-- FOUNDATION**

**The Engine Architecture**

Six engines. One interface. One data contract. Two implementations.

## **1.1 The Engine Principle**

The domain engines are the rules layer of the Ichebo ecosystem. They enforce domain logic - the business rules derived from the KGS framework - independently of any web framework, database engine, or deployment context. A domain engine does not know or care whether it is running inside a Flutter Desktop app calling Go via FFI, or inside a Django request-response cycle, or inside a Go microservice behind an API gateway.

This is the architectural property that makes local-first possible: the same rules that govern data on the cloud govern data on the device. There is one specification, two implementations, one truth.

## **1.2 The Engine Interface**

Every engine implements the Engine interface. The Sync Engine calls engines through the Registry - never directly. This decouples the sync transport from domain logic and makes each engine independently testable.

// Go - engines/engine.go

type Engine interface {

// EntityType returns the entity type string this engine handles.

// Must match entity_type values used in the ChangeLog.

EntityType() string

// Apply writes an entity payload to the local store inside a transaction.

// Called by the Sync Engine Puller when a cloud entity arrives locally.

// Must enforce all domain rules from this specification.

// Returns error if validation fails - the Sync Engine will queue the conflict.

Apply(tx store.TxStore, op changelog.Operation, payload json.RawMessage) error

// Extract reads a local entity and returns it as JSON for the push payload.

// Called by the Sync Engine Pusher when building a cloud-bound payload.

Extract(store store.Store, entityID uuid.UUID) (json.RawMessage, error)

// Validate checks a payload conforms to domain rules before Apply.

// Returns a descriptive ValidationError if any rule is violated.

Validate(payload json.RawMessage) error

}

// Registry maps entity types to engines. Built once at startup. Immutable.

type Registry struct { engines map\[string\]Engine }

func (r \*Registry) For(entityType string) Engine // panics if not found

func (r \*Registry) MustFor(entityType string) Engine // same, explicit name

func (r \*Registry) Register(e Engine)

## **1.3 The Four Mandatory Fields**

**Non-negotiable - data contract Part 1.1**

Every entity governed by the engine layer must carry four mandatory fields. Validate() must reject any payload missing any one of them. No exceptions. BibleVerse and CalendarEvent (read-only reference data) are exempt.

// The four mandatory fields - present on every syncable entity

type MandatoryFields struct {

ID uuid.UUID // UUID v4 - generated offline, permanent before cloud contact

TenantID \*uuid.UUID // null for personal-scope and platform-level entities

CreatedBy uuid.UUID // the user who created this record

CreatedAt time.Time // when it was created (HLC timestamp)

}

// Python/Django equivalent (after Phase E.1 UUID migration)

class SyncableMixin(models.Model):

id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

tenant_id = models.UUIDField(null=True, blank=True)

created_by = models.UUIDField()

created_at = models.DateTimeField(auto_now_add=True)

updated_at = models.DateTimeField(auto_now=True)

deleted_at = models.DateTimeField(null=True, blank=True) # soft delete

device_id = models.UUIDField(null=True, blank=True) # originating device

class Meta:

abstract = True

## **1.4 Engine Summary**

| **Engine**           | **EntityType** | **Operation mode**                                       |
| -------------------- | -------------- | -------------------------------------------------------- |
| Records Engine       | record         | Read + Write (Create, Update, Soft-delete)               |
| Activity Engine      | activity       | Read + Write (Create, Update, Soft-delete) + ActivityLog |
| Relationships Engine | relationship   | Read + Write (Create, Soft-delete)                       |
| Bible Engine         | bible_verse    | Read-only. Bundled SQLite. Never pushed to cloud.        |
| Calendar Engine      | calendar_event | Read-only in MVP. Aggregates from Activity.              |
| Sync Engine          | (orchestrator) | Calls all engines. Not a domain engine. See DOC C.       |

## **1.5 How Django Implements the Specification**

The Python/Django implementation does not use the Go Engine interface literally - it uses the same specification expressed in Django models, DRF serializers, and service modules. The rules are identical; the syntax is different.

| **Go implementation**         | **Django/Python implementation**                          |
| ----------------------------- | --------------------------------------------------------- |
| Engine.Apply(tx, op, payload) | DRF ViewSet.create() / .update() calling a service module |
| Engine.Validate(payload)      | DRF Serializer.validate() methods                         |
| Engine.Extract(store, id)     | DRF Serializer.to_representation()                        |
| store.TxStore atomic write    | django.db.transaction.atomic()                            |
| changelog.Writer.Append()     | ActivityLog signal / SyncChangelog model (Phase E.1)      |
| uuid.New()                    | uuid.uuid4() via models.UUIDField(default=uuid.uuid4)     |

**Records Engine**

EntityType: "record" | Table: records | Operation: Read + Write

_ADR: ADR-019, ADR-003, ADR-006 | Source: data-contract-v11 Parts 3, 7, 22.1_

## **2.1 Responsibility**

The Records Engine is the data spine of the Ichebo ecosystem. Every piece of institutional content - journal entries, governance documents, Bible notes, gathering records, learning content, file references - is a Record. The engine enforces the classification taxonomy and the permission gate that governs access to every piece of content on the platform.

## **2.2 The Single Table Constraint**

**Non-negotiable - ADR-003**

All content lives in one records table. No new model tables for new content types. The record_class / record_family / record_type discriminator is how content is classified. If a new content type is needed, it is a new record_type within an existing record_family - never a new table.

## **2.3 Record Classification Taxonomy**

Three fields classify every record. All three must be validated by the engine.

**record_class - the permission gate (checked first, always)**

| **record_class** | **Who creates it**   |
| ---------------- | -------------------- |
| personal         | Any user (Level 0b+) |
| organizational   | Level 2+             |
| governance       | Level 4+ (write)     |

**record_family + record_type - the full taxonomy**

| **record_family** | **record_type values**                                                                                                               | **record_class**          |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------- |
| journal           | prayer, spirit, dream, dar, note                                                                                                     | personal                  |
| governance        | class, principle, concept, divine_pattern, narrative, subject, entity, mandate, statement, programme, framework, protocol, procedure | governance                |
| activity          | event, campaign, project, habit, task, skill                                                                                         | organizational            |
| learning          | programme, course, lesson, assignment, quiz, certification                                                                           | organizational            |
| reference         | key, property, attachment                                                                                                            | personal / organizational |
| bible             | bible_note                                                                                                                           | personal                  |
| community         | announcement, gathering                                                                                                              | organizational            |

## **2.4 Validate() - Rules Enforced**

**Mandatory field validation**

- id: must be present, must be valid UUID v4
- created_by: must be present, must be valid UUID
- created_at: must be present, must be valid ISO-8601 timestamp
- tenant_id: may be null only for personal-scope records (record_class: personal with visibility: private)

**Classification validation**

- record_class must be one of: personal | organizational | governance
- record_family must be registered: journal | governance | activity | learning | reference | bible | community
- record_type must be valid for the given record_family - cross-reference the taxonomy table
- record_type and record_family mismatch: reject with descriptive error

**Governance record special rules**

- record_class: governance requires created_by user to have competence_level >= 4 (write) - enforce in Apply(), not just Validate()
- status must be one of: draft | active | locked | superseded
- locked records: Apply() must reject any payload that modifies content fields - only previous_version_id and superseded_by may be set on a locked record
- versioning fields: if previous_version_id is set, the referenced record must exist and must be in locked or superseded status

**Soft delete validation**

- deleted_at: if set, must be valid ISO-8601 timestamp
- deleted records: Apply() with OpDelete must set deleted_at only - it must not remove the row

## **2.5 Apply() - Domain Rules Enforced**

// Go pseudocode - records engine Apply()

func (e \*RecordsEngine) Apply(tx store.TxStore, op changelog.Operation, payload json.RawMessage) error {

// 1. Validate payload against all rules

if err := e.Validate(payload); err != nil {

return err

}

var record Record

json.Unmarshal(payload, &record)

switch op {

case changelog.OpCreate:

// Enforce: record does not already exist (idempotency check)

existing, \_ := tx.Records().FindByID(record.ID)

if existing != nil {

return nil // idempotent - already applied

}

return tx.Records().Insert(record)

case changelog.OpUpdate:

existing, err := tx.Records().FindByID(record.ID)

if err != nil { return err }

// Enforce: locked records cannot be content-edited

if existing.Status == "locked" {

if contentFieldsChanged(existing, record) {

return ErrLockedRecordContentEdit

}

}

return tx.Records().Update(record)

case changelog.OpDelete:

// Soft delete only - set deleted_at, never remove row

return tx.Records().SoftDelete(record.ID, record.DeletedAt)

}

return nil

}

## **2.6 The Permission Algorithm**

Apply() enforces classification rules. The permission algorithm (who can read a record) is applied by query layer, not by Apply() - it governs reads, not writes.

// Canonical permission check - Go

func CanAccess(user User, record Record) bool {

// 1. Handbook short-circuit (current production implementation)

if record.Tenant != nil && record.Tenant.Tier == "handbook" {

refLibTypes := map\[string\]bool{"class":true,"principle":true,"concept":true,"divine_pattern":true}

if refLibTypes\[record.RecordType\] {

return user.CompetenceLevel >= 3

}

return user.CompetenceLevel >= 4

// Write access always requires Level 5 - enforced at Apply() level

}

// 2. record_class gate - FIRST

if record.RecordClass == "governance" && user.CompetenceLevel < 4 {

return false

}

// 3. Visibility scope

switch record.Visibility {

case "private":

return record.CreatedBy == user.ID

case "tenant":

return userHasPermissionForTenant(user, record.TenantID)

case "collective":

return userHasPermissionForCollective(user, record.TenantID)

case "public":

return user.CompetenceLevel >= 1

}

// 4. Level gate

return user.CompetenceLevel >= record.RequiredLevel

}

## **2.7 Record Lifecycle - Governance Records**

State machine: draft → active → locked → superseded

Transitions:

draft → active: Level 5 only. Record is published.

active → locked: Level 5 only. Record is finalised.

locked → superseded: Level 5 only. A new version supersedes this one.

Version chain:

When creating a new version of a locked record:

1\. Lock the old record (status → locked)

2\. Create new record with previous_version_id = old_record.id

3\. PATCH old record: superseded_by = new_record.id, status = superseded

The engine must validate:

\- previous_version_id: if set, referenced record must exist and be locked or superseded

\- superseded_by: if set, referenced record must exist and have previous_version_id pointing back

**Activity Engine**

EntityType: "activity" | Table: activities + activity_log | Operation: Read + Write + ActivityLog

_ADR: ADR-019, ADR-006 | Source: data-contract-v11 Parts 4, 10, 22.2_

## **3.1 Responsibility**

The Activity Engine manages the operational record of the community. Everything that happens - gatherings, tasks, habits, goals, participation, service, ministry campaigns - is an Activity. The engine enforces the activity taxonomy, the assignment rules, and the critical invariant: every status transition generates an immutable ActivityLog entry.

## **3.2 Activity Type Taxonomy**

| **activity_type** | **Context**                         |
| ----------------- | ----------------------------------- |
| task              | Personal (My Activities) + Ministry |
| habit             | Personal only                       |
| goal              | Personal only                       |
| skill             | Personal only                       |
| reminder          | Personal + Ministry                 |
| event             | Ministry + Community (gatherings)   |
| campaign          | Ministry only                       |
| project           | Ministry only                       |
| programme         | Learning only                       |

## **3.3 The ActivityLog Invariant**

**Non-negotiable**

Every status transition on an Activity must generate an ActivityLog entry, atomically in the same transaction. The ActivityLog is immutable - entries are never updated or deleted. This is the audit trail for the entire operational record of the community.

// Go - the atomic write pattern

func (e \*ActivityEngine) Apply(tx store.TxStore, op changelog.Operation, payload json.RawMessage) error {

var activity Activity

json.Unmarshal(payload, &activity)

if err := e.Validate(payload); err != nil { return err }

switch op {

case changelog.OpCreate:

existing, \_ := tx.Activities().FindByID(activity.ID)

if existing != nil { return nil } // idempotent

if err := tx.Activities().Insert(activity); err != nil { return err }

// Write ActivityLog entry for creation

return tx.ActivityLog().Append(ActivityLogEntry{

ID: uuid.New(),

ActivityID: activity.ID,

EventType: "created",

PreviousValue: nil,

NewValue: activity.Status,

CreatedAt: time.Now(),

})

case changelog.OpUpdate:

existing, err := tx.Activities().FindByID(activity.ID)

if err != nil { return err }

statusChanged := existing.Status != activity.Status

if err := tx.Activities().Update(activity); err != nil { return err }

// Write ActivityLog entry ONLY on status transition

if statusChanged {

return tx.ActivityLog().Append(ActivityLogEntry{

ID: uuid.New(),

ActivityID: activity.ID,

EventType: "status_changed",

PreviousValue: existing.Status,

NewValue: activity.Status,

CreatedAt: time.Now(),

})

}

return nil

case changelog.OpDelete:

return tx.Activities().SoftDelete(activity.ID, activity.DeletedAt)

}

return nil

}

## **3.4 Validate() - Rules Enforced**

**Mandatory fields**

- id, created_by, created_at: always required
- tenant_id: required for organizational activities (ministry, campaign, event, programme). Null only for personal activities (task, habit, goal, skill, reminder with no tenant context).

**activity_type validation**

- Must be one of: task | habit | goal | event | campaign | project | programme | reminder | skill
- programme activities are system-generated by the certification signal - Validate() rejects manual creation of programme activities from client payloads

**status validation**

- Must be one of: pending | in_progress | completed | cancelled | deferred
- progress: integer 0-100 inclusive
- progress == 100 must accompany status == completed - and vice versa (enforce in both directions)

**Assignment validation**

- assigned_to: if set, must be a valid user UUID
- Level 1-2 users: assigned_to must equal created_by (personal activities only - cannot assign to others)
- Level 3+ stewards: assigned_to may be any user within their tenant scope

**Nesting validation**

- parent_activity_id: if set, must reference an existing activity of type campaign or project
- campaign and project activities may not themselves have a parent_activity_id (two levels maximum - no deep nesting)

## **3.5 The Skill Activity Type**

The skill activity type records a member's gifts and ministry capabilities. It is personal - not assigned by a steward.

| **Field**              | **Skill-specific usage**                                                        |
| ---------------------- | ------------------------------------------------------------------------------- |
| title                  | Name of the gift or skill (e.g. "Teaching", "Administration")                   |
| description            | How this gift manifests in ministry context                                     |
| progress               | Self-assessed competence: 0-100                                                 |
| kgs_pathway            | Which Kingdom Pathway this gift primarily serves                                |
| metadata.service_order | KGS Service Order this gift aligns with (validated against ServiceOrder table)  |
| status                 | active = current gift; completed = fully developed; archived = no longer active |
| tenant_id              | null = personal register; set = visible to community steward                    |

## **3.6 The certification Signal**

When a programme Activity reaches progress: 100, the Activity Engine must emit a certification signal. In Django this is a Django signal. In Go this is a callback registered on the engine at startup.

// Go - certification signal

type CertificationSignal struct {

ProgrammeActivityID uuid.UUID

LearnerID uuid.UUID

ProgrammeRecordID uuid.UUID

CompletedAt time.Time

}

// Engine fires this when programme activity progress reaches 100

type CertificationSignalHandler func(signal CertificationSignal)

// Registered at startup:

engine := activity.NewEngine(store, certificationHandler)

// Python/Django equivalent:

from django.db.signals import post_save

@receiver(post_save, sender=Activity)

def on_programme_completion(sender, instance, \*\*kwargs):

if instance.activity_type == 'programme' and instance.progress == 100:

create_certification_record(instance)

**Relationships Engine**

EntityType: "relationship" | Table: relationships | Operation: Read + Write

_ADR: ADR-019 | Source: data-contract-v11 Parts 3.3, 3.4, 22.3_

## **4.1 Responsibility**

The Relationships Engine manages typed, directed or bidirectional links between Records and between Records and Bible Verses. It is the technical implementation of the Hierarchy and Relationship System (HRS) methodology. It provides the graph layer that connects the institutional knowledge base - every governance document, every scripture reference, every relationship between concepts and mandates.

## **4.2 The Critical Constraint**

**Non-negotiable**

Exactly one of to_record_id or bible_verse_id must be non-null on every Relationship. Both null and both set are invalid. Validate() must enforce this as a hard rejection with a clear error message.

// Go validation

func validateRelationship(r Relationship) error {

bothNull := r.ToRecordID == nil && r.BibleVerseID == nil

bothSet := r.ToRecordID != nil && r.BibleVerseID != nil

if bothNull || bothSet {

return ErrRelationshipTargetConstraint(

"exactly one of to_record_id or bible_verse_id must be non-null")

}

return nil

}

// Python/Django equivalent - in Relationship.clean():

def clean(self):

if (self.to_record_id is None) == (self.bible_verse_id is None):

raise ValidationError(

"exactly one of to_record_id or bible_verse_id must be non-null")

## **4.3 Relationship Type Vocabulary - Controlled**

The relationship_type field is controlled vocabulary. The engine must reject any type not in this list.

| **relationship_type** | **Canonical usage**                                        |
| --------------------- | ---------------------------------------------------------- |
| relates_to            | General association - use sparingly; prefer specific types |
| derived_from          | B is derived from or inspired by A                         |
| references            | A references or cites B (including scripture)              |
| answers               | A provides the answer or response to B                     |
| fulfills              | A fulfills the mandate or requirement of B                 |
| requests              | A requests or depends on B                                 |
| has_symbol            | A has B as a symbol or emblem                              |
| matches_pattern       | A matches or exemplifies the pattern of B                  |
| assigned_to           | A (activity) is assigned to B (member record)              |
| tracks                | A (activity) tracks progress toward B (goal or record)     |
| completes             | A (activity) completes B (task or record requirement)      |
| part_of               | A is a component of B (governance structure)               |
| aligns_with           | A is aligned with or supports B                            |
| authorised_by         | A is authorised or governed by B                           |
| tagged_in             | A appears in or is tagged in B                             |
| community_ref         | A (community record) references B (governance record)      |

## **4.4 Direction**

| **direction value** | **Meaning**                                                                                     |
| ------------------- | ----------------------------------------------------------------------------------------------- |
| directed            | from_record → to_record/bible_verse. Traversal is one-way. Most HRS relationships are directed. |
| bidirectional       | The relationship applies in both directions. Use for relates_to and has_symbol in most cases.   |

## **4.5 Validate() - Rules Enforced**

- from_record_id: required, must be valid UUID
- to_record_id XOR bible_verse_id: exactly one must be non-null (see 4.2)
- relationship_type: must be in the controlled vocabulary (see 4.3)
- direction: must be directed or bidirectional
- strength: if set, must be weak | medium | strong - not a float, not any other string
- tenant_id: may be null for personal relationships (personal record → personal record). Must match from_record tenant context for organizational and governance relationships.

## **4.6 Traversal**

The engine must provide traversal from any record - returning all relationships where it is either the source or the target.

// Go

func (e \*RelationshipsEngine) TraverseFrom(store store.Store, recordID uuid.UUID) (\[\]Relationship, error) {

// Returns all non-deleted relationships where from_record_id OR to_record_id = recordID

return store.Relationships().FindByRecord(recordID)

}

func (e \*RelationshipsEngine) TraverseDirected(store store.Store, recordID uuid.UUID) (\[\]Relationship, error) {

// Returns only outbound directed relationships (from_record_id = recordID, direction = "directed")

return store.Relationships().FindOutbound(recordID)

}

// Django/Python equivalent:

def traverse_from(record_id):

return Relationship.objects.filter(

Q(from_record_id=record_id) | Q(to_record_id=record_id),

deleted*at*\_isnull=True

)

**Bible Engine**

EntityType: "bible_verse" | Table: bible_verses (bundled SQLite) | Operation: Read-only

_ADR: ADR-019, ADR-018 Q3 | Source: data-contract-v11 Parts 13, 22.4_

## **5.1 Responsibility**

The Bible Engine provides scripture text to all Ichebo products. It returns verse text - nothing more. No HRS logic, no relationship management, no annotation handling. The HRS scripture module (linking verses to governance documents) lives in the Ichebo Handbook product. Personal Bible notes live in the Records Engine (record_family: "bible", record_type: "bible_note"). The Bible Engine is the pure text provider.

## **5.2 The Bundled SQLite Decision**

**Locked - Q3 answer (DOC C)**

Bible data (KJV, ASV, WEB - approximately 30MB) is bundled with the Ichebo Desktop installer as a pre-populated read-only SQLite file. No network required for scripture. The word of God is available offline from minute one. This is what local-first means in practice.

| **Translation**           | **Code** |
| ------------------------- | -------- |
| King James Version        | KJV      |
| American Standard Version | ASV      |
| World English Bible       | WEB      |

BibleVerse records are exempt from the four mandatory fields rule (data contract Part 1.1). They are read-only reference data loaded by management command - not governed platform entities.

## **5.3 Data Model**

// Bible data model - both Go (SQLite) and Django (PostgreSQL)

BibleTranslation {

id: uuid (or integer - exempt from UUID requirement)

code: string // "KJV", "ASV", "WEB"

name: string // "King James Version"

language: string // "en"

is_default: boolean // true for KJV

}

BibleBook {

id: integer // exempt from UUID requirement - sequential by canonical order

code: string // "GEN", "EXO", "MAT", "JHN", etc. (3-letter OSIS codes)

name: string // "Genesis", "Exodus", "Matthew", "John"

testament: string // "OT" | "NT"

order: integer // canonical ordering (1-66)

}

BibleVerse {

id: uuid // unique per translation + book + chapter + verse

translation: FK → BibleTranslation

book: FK → BibleBook

chapter: integer

verse: integer

text: string // the verse text

// unique_together: (translation, book, chapter, verse)

}

## **5.4 Engine Operations - Read-Only**

// Go - Bible Engine interface

type BibleEngine interface {

// GetVerse returns a single verse by reference.

GetVerse(translationCode, bookCode string, chapter, verse int) (\*BibleVerse, error)

// GetChapter returns all verses for a chapter, ordered by verse number.

GetChapter(translationCode, bookCode string, chapter int) (\[\]BibleVerse, error)

// ResolveReference parses a reference string and returns the verse.

// Supported formats: "JHN 3:16", "John 3:16", "JHN 3:16-18" (returns first verse of range)

ResolveReference(translationCode, ref string) (\*BibleVerse, error)

// ListTranslations returns all available translations.

ListTranslations() (\[\]BibleTranslation, error)

// ListBooks returns all books in canonical order.

ListBooks() (\[\]BibleBook, error)

}

// Django/Python equivalent - DRF endpoints:

GET /api/bible/translations/

GET /api/bible/books/

GET /api/bible/verses/?book_code=JHN&chapter=3

GET /api/bible/verse-context/{verse_id}/ // returns verse + surrounding context

## **5.5 No-Write Invariant**

The Bible Engine has no Apply(), no Validate() for writes, and no Extract(). It is read-only. The Sync Engine never pushes or pulls BibleVerse records - they are bundled, not synced. Any attempt to write to the bible_verses table through the engine layer must be rejected.

The only write path for bible data is the management command that loads the bundled SQLite file on first run. This happens once, outside of the normal engine write path.

**Calendar Engine**

EntityType: "calendar_event" | Table: (aggregated from activities) | Operation: Read-only in MVP

_ADR: ADR-019 | Source: data-contract-v11 Parts 11, 22.5_

## **6.1 Responsibility**

The Calendar Engine is an aggregation service. It does not have its own storage table - it reads from the Activity table and produces a CalendarEvent view sorted by time. Events are expressions of the KGS operational rhythm - not standalone records.

In the Sync Engine context, the Calendar Engine receives calendar event snapshots from the cloud during pull operations and caches them for the Flutter UI. In the cloud context, it serves as the aggregation layer behind the /api/calendar/events/ endpoint.

## **6.2 CalendarEvent - The Output Shape**

// CalendarEvent is produced by the engine - it is not stored as a table row.

type CalendarEvent struct {

ID uuid.UUID // source entity ID (activity.ID or record.ID)

SourceType string // "activity" | "record"

SourceApp string // "activity" | "learn" | "governance" | "community"

Title string

ScheduledAt \*time.Time

DueAt \*time.Time

ActivityType string // from Activity.activity_type (if source is activity)

RecordType string // from Record.record_type (if source is record)

TenantID \*uuid.UUID

Status string

KGSPillar string

KGSPathway string

}

// Python/Django equivalent - CalendarEvent dataclass or serializer output:

@dataclass

class CalendarEvent:

id: str

source_type: str # "activity" | "record"

source_app: str

title: str

scheduled_at: Optional\[datetime\]

due_at: Optional\[datetime\]

activity_type: Optional\[str\]

record_type: Optional\[str\]

tenant_id: Optional\[str\]

status: str

kgs_pillar: Optional\[str\]

kgs_pathway: Optional\[str\]

## **6.3 Aggregation Query**

// Go - Calendar Engine Aggregate()

func (e \*CalendarEngine) Aggregate(

store store.Store,

tenantID uuid.UUID,

from, to time.Time,

filters CalendarFilters,

) (\[\]CalendarEvent, error) {

// Query activities in date range for this tenant

activities, err := store.Activities().FindInRange(tenantID, from, to, filters.ActivityTypes)

if err != nil { return nil, err }

// Convert to CalendarEvent

events := make(\[\]CalendarEvent, 0, len(activities))

for \_, a := range activities {

events = append(events, calendarEventFromActivity(a))

}

// Sort by scheduled_at ASC, then due_at ASC

sort.Slice(events, func(i, j int) bool {

return compareEventTimes(events\[i\], events\[j\])

})

return events, nil

}

// Django/Python equivalent - calendar_app/services.py:

def aggregate_events(tenant_id, from_date, to_date, filters=None):

activities = Activity.objects.filter(

tenant_id=tenant_id,

deleted*at*\_isnull=True,

scheduled*at*\_range=(from_date, to_date)

).order_by('scheduled_at', 'due_at')

return \[calendar_event_from_activity(a) for a in activities\]

## **6.4 Version 3 Extension - KGS Annual Rhythm**

In Version 3, the Calendar Engine is extended to produce KGS Annual Rhythm events - governance cycles, programme milestones from the Seven-Year Programme, and the Annual Operational Rhythm defined in the KGS framework. These are not stored as Activity rows - they are computed from the KGS calendar specification.

This extension is deferred from Desktop MVP. The engine's Aggregate() interface is designed to accommodate it without breaking changes - governance cycle events are simply additional CalendarEvent objects returned alongside activity-sourced events.

**-- CROSS-ENGINE**

**Cross-Engine Patterns**

Dual-write, certification signal, HRS linkage, competence_level write constraint.

## **7.1 The Dual-Write Pattern**

The dual-write pattern creates two entities atomically in a single transaction. It is used by the Community App (gathering) and the Learn App (enrolment). The engines cooperate - both writes must succeed or neither is committed.

// Go - dual-write: gathering Record + event Activity

func CreateGathering(store store.Store, recordEngine Engine, activityEngine Engine,

gatheringPayload, activityPayload json.RawMessage) error {

return store.Tx(func(tx store.TxStore) error {

// Write 1 - the gathering Record

if err := recordEngine.Apply(tx, changelog.OpCreate, gatheringPayload); err != nil {

return err // transaction rolls back

}

// Write 2 - the event Activity (linked to the gathering Record)

if err := activityEngine.Apply(tx, changelog.OpCreate, activityPayload); err != nil {

return err // transaction rolls back - both writes undone

}

// Write 3 - the Relationship linking Record to Activity

return relationshipsEngine.Apply(tx, changelog.OpCreate, linkPayload)

// All three committed atomically, or none

})

}

// Python/Django equivalent - in community/services.py:

from django.db import transaction

@transaction.atomic

def create_gathering(gathering_data, activity_data):

record = Record.objects.create(\*\*gathering_data)

activity = Activity.objects.create(linked_record=record, \*\*activity_data)

Relationship.objects.create(

from_record=record, to_record_id=activity.linked_record_id,

relationship_type='aligns_with', direction='directed'

)

return record, activity

## **7.2 The competence_level Write Constraint**

**Absolute constraint - ADR-006**

competence_level may only be written by one code path: the certification confirmation service. No engine, no endpoint, no signal, no management command may write to competence_level through any other path. This constraint is enforced at the service layer - not at the model layer - so it is visible and auditable.

// Python/Django - learn/services.py (the sole authorised write path)

def confirm_certification_record(certification_id, confirmed_by_user_id, notes=None, placement_tenant_id=None):

"""

THE SOLE AUTHORISED WRITE PATH for competence_level.

Called only by POST /api/learn/certifications/{id}/confirm/

"""

with transaction.atomic():

cert = Record.objects.select_for_update().get(

id=certification_id,

record_family='learning',

record_type='certification'

)

learner = User.objects.select_for_update().get(id=cert.created_by)

previous_level = learner.competence_level

new_level = previous_level + 1

\# THE ONLY PLACE THIS WRITE IS AUTHORISED

learner.competence_level = new_level

learner.save(update_fields=\['competence_level', 'updated_at'\])

CertificationConfirmation.objects.create(

certification_record=cert,

confirmed_by_id=confirmed_by_user_id,

learner_id=learner.id,

previous_competence_level=previous_level,

new_competence_level=new_level,

notes=notes,

placement_tenant_id=placement_tenant_id

)

\# ... email notification, activity log, etc.

## **7.3 HRS Scripture Linkage**

The Relationships Engine handles the linkage between governance records and Bible verses. This is the technical implementation of the HRS methodology. The relationship is created through the standard Relationships Engine path - the only HRS-specific aspect is that bible_verse_id is set instead of to_record_id.

// Creating an HRS scripture link

Relationship {

from_record_id: governance_record.id, // the mandate, principle, or concept

to_record_id: null, // not used for scripture links

bible_verse_id: verse.id, // the BibleVerse being referenced

relationship_type: "references",

direction: "directed",

notes: "This mandate derives its authority from this passage"

}

// The Bible Engine provides the verse text when the relationship is traversed.

// The HRS Handbook module (Ichebo Handbook product, Version 3+) builds the

// full scripture-governance mapping layer on top of these raw relationships.

## **7.4 Engine-to-App Mapping**

Each Ichebo app surface calls specific engines. No app calls engines outside its mapping.

| **App / Product**         | **Engines called**                                                                                                                                              |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Bible App (Ichebo Bible)  | Bible Engine (text only). Records Engine (bible_note records).                                                                                                  |
| Learn App / Formation     | Records Engine (programme, course, lesson records). Activity Engine (programme enrolment activity, progress). Relationships Engine (curriculum part_of chains). |
| Activity App              | Activity Engine (all activity types). Records Engine (linked records). Calendar Engine (event aggregation).                                                     |
| Community App             | Records Engine (announcement, gathering records). Activity Engine (gathering event, attendance). Relationships Engine (aligns_with links).                      |
| Governance App / Handbook | Records Engine (all governance record types). Relationships Engine (HRS graph). Bible Engine (verse text for HRS scripture links).                              |
| Paraclete                 | All engines - read-only. Never writes. Intelligence layer only.                                                                                                 |
| Sync Engine               | Orchestrates Records, Activity, and Relationships engines during sync. Calls Bible Engine for initial scripture cache load.                                     |

**-- IMPLEMENTATION**

**Implementation Guide**

How to build a conforming engine. Go first. Django aligned.

## **8.1 Go Implementation Checklist**

For each engine built in Go, verify every item before marking the engine complete:

**Records Engine**

- Validate() rejects payloads missing any of the four mandatory fields
- Validate() rejects invalid record_family / record_type combinations
- Apply(OpCreate) is idempotent - duplicate entity ID silently ignored
- Apply(OpUpdate) rejects content edits on locked governance records
- Apply(OpDelete) sets deleted_at - never removes the row
- CanAccess() permission algorithm matches the canonical specification exactly
- Governance records: Create requires competence_level >= 4 in the user context
- Version chain validation: previous_version_id references must exist and be locked/superseded

**Activity Engine**

- Every status transition writes an ActivityLog entry atomically in the same Tx
- ActivityLog entries are never updated or deleted
- progress == 100 and status == completed are enforced together
- programme activity type: Validate() rejects manual creation from client payloads
- Certification signal fires when programme activity progress reaches 100
- Assignment rules: Level 1-2 may only assign to self
- Nesting rules: parent_activity_id must reference campaign or project; those types may not have parents

**Relationships Engine**

- Validate() rejects: both to_record_id and bible_verse_id null
- Validate() rejects: both to_record_id and bible_verse_id non-null
- relationship_type must be in the controlled vocabulary - any other value is rejected
- direction must be directed or bidirectional - no other values
- strength must be null, weak, medium, or strong - no floats, no other strings
- TraverseFrom() returns relationships where record is either source or target

**Bible Engine**

- GetVerse() returns nil, not an error, when verse does not exist
- GetChapter() returns empty slice, not an error, when chapter does not exist
- ResolveReference() handles both short codes (JHN) and full names (John)
- No write operations exist on this engine - any write attempt panics
- Bundled SQLite file opened read-only - PRAGMA query_only=ON

**Calendar Engine**

- Aggregate() returns CalendarEvent slice sorted by scheduled_at ASC, then due_at ASC
- Null scheduled_at events appear at the end of the sorted list
- Empty result: returns empty slice, not an error
- Filters: tenant_id scoping applied at query level, not post-filter

## **8.2 Django Conformance Checklist**

The Django implementation must produce the same results as the Go specification for every rule above. Use this checklist when auditing Django apps for conformance:

- All model PKs are UUIDField(primary_key=True, default=uuid.uuid4) - after Phase E.1
- All models carry deleted_at DateTimeField(null=True) - after Phase E.2
- All default querysets filter deleted*at*\_isnull=True
- Record.clean() enforces record_family / record_type taxonomy
- Relationship.clean() enforces the to_record_id XOR bible_verse_id constraint
- Activity status transitions write ActivityLog entries via Django signal (post_save)
- competence_level writes only through learn/services.py::confirm_certification_record()
- All governance record writes require competence_level >= 4 in the view permission check
- Locked governance records reject content edits in the DRF serializer update() method

## **8.3 Build and Test Order**

Build the Go engines in this order. Each engine's tests must pass before the next engine begins.

- pkg/store - SQLite abstraction layer, TxStore interface, WAL mode, FK enforcement
- pkg/changelog - ChangeLog table, append-only invariant, Log interface
- engines/bible - Read-only. Bundled SQLite. Simplest engine - good warm-up.
- engines/records - Most complex. All validation rules. Permission algorithm.
- engines/activity - ActivityLog atomicity. Certification signal.
- engines/relationships - Constraint validation. Traversal.
- engines/calendar - Aggregation. Sorting. Filter correctness.
- Sync Engine (DOC C build sequence) - builds on all engines above.

**Test principle**

Each engine is independently testable. Engine tests use an in-memory store (store.NewMemoryStore()) - no SQLite file, no network, no other engine. If an engine test requires another engine, the test is wrong. Decompose it.

**Ichebo Christian Services**

_DOC E - Engine Specifications v1.0 - May 2026 - Canonical Reference_