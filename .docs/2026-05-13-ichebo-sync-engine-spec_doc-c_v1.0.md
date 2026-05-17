**ICHEBO**

**Sync Engine Specification**

_DOC C - Version 1.0_

May 2026 - Ichebo Christian Services

| **Field**        | **Value**                                            |
| ---------------- | ---------------------------------------------------- |
| Document         | DOC C - Sync Engine Specification                    |
| Version          | 1.0 - May 2026                                       |
| Status           | Approved - Canonical Reference                       |
| ADR reference    | ADR-018, ADR-016, ADR-019                            |
| Data contract    | data-contract-v11-canonical-2026-05-13.md Part 21    |
| Sketch reference | 2026-05-13-ichebo-sync-engine-modules-sketch_v0.1.md |
| Authors          | Chizola (domain); Claude (technical)                 |

This document is the complete, canonical specification for the Ichebo Sync Engine - the strategic core of the Ichebo ecosystem. It supersedes the sketch (v0.1) and all partial descriptions in the ecosystem architecture document. Every detail required to implement the engine from scratch is here.

**The architectural centre of gravity**

_The Sync Engine does not sync data. It syncs facts about what happened on a device. The ChangeLog is a journal of facts. The domain engines apply those facts. The Sync Engine is transport and arbitration only. This separation is the decision that makes everything else clean._

# **Part 1 - Strategic Position**

## **1.1 What the Sync Engine Is**

The Sync Engine is a standalone Go binary that enables Ichebo Desktop to operate as a local-first, offline-capable community platform while remaining connected to the Ichebo Cloud network when internet is available. It is embedded inside the Ichebo Desktop Flutter application and runs as a background daemon - invisible to the user except through the sync status bar.

It is the most strategically significant component in the Ichebo ecosystem:

- It is owned entirely by Ichebo - not a third-party library, not a SaaS dependency
- It cannot be bought, licensed away, or price-increased by a vendor
- It is the infrastructure that makes local-first possible across all Ichebo products
- Over time it may be published as the Ichebo Sync Protocol - a standard for KGS-compliant community data synchronisation

## **1.2 What the Sync Engine Is Not**

- It is not a database - SQLite is the database
- It is not a domain engine - it does not know the schema of members, activities, or records
- It is not an API server - it is a client that calls the Ichebo Cloud DRF API
- It is not responsible for the UI - Flutter reads SQLite directly for all display data
- It is not a replacement for the delta sync endpoint (GET /api/sync/changes/) - that endpoint serves Flutter mobile; this engine serves Ichebo Desktop

## **1.3 Relationship to Other Components**

| **Component**                                     | **Relationship**                                                                    |
| ------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Ichebo Cloud DRF API                              | The sync engine calls these endpoints. The cloud is the coordination layer.         |
| Domain Engines (Records, Activity, Relationships) | The sync engine orchestrates them during sync. They apply facts to the local store. |
| Local SQLite Database                             | The sync engine writes through domain engines. Flutter reads directly.              |
| Flutter Desktop App                               | Flutter calls the sync engine via FFI for control. Reads SQLite for data.           |
| Delta Sync Endpoint                               | Separate mechanism for Flutter mobile. Both coexist. Not replaced.                  |
| ConflictQueue                                     | The sync engine writes to it. The Flutter UI reads and resolves from it.            |

# **Part 2 - Architecture Overview**

## **2.1 Repository Structure**

The Sync Engine lives in a standalone Go repository: ichebo-sync. It is built as both a shared library (embedded in Flutter Desktop via FFI) and a standalone binary (for development and testing).

ichebo-sync/

├── cmd/

│ └── syncd/

│ └── main.go ← standalone binary entry point (dev + testing)

│

├── pkg/

│ ├── device/ ← device identity and licence validation

│ ├── changelog/ ← append-only change log - the engine's memory

│ ├── clock/ ← Hybrid Logical Clock for event ordering

│ ├── store/ ← local SQLite abstraction layer

│ ├── transport/ ← HTTP client for Ichebo Cloud API

│ ├── push/ ← push: local changes → cloud

│ ├── pull/ ← pull: cloud changes → local

│ ├── resolve/ ← conflict resolution - policy table

│ ├── queue/ ← ConflictQueue - user-facing conflict management

│ └── status/ ← sync status - the four states

│

├── engines/

│ ├── records/ ← Records Engine

│ ├── activity/ ← Activity Engine

│ ├── relationships/ ← Relationships Engine

│ ├── bible/ ← Bible Engine (pull-only, bundled SQLite)

│ └── calendar/ ← Calendar Engine (pull-only)

│

├── ffi/

│ └── bridge.go ← six exported functions for dart:ffi

│

└── go.mod

## **2.2 Two Deployment Modes**

| **Mode**                        | **Description**                                                                                                                                                                                   |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Embedded library (production)   | Compiled as a shared library (.so on Linux/Android, .dylib on macOS, .dll on Windows). Flutter loads it at app startup via dart:ffi. The sync daemon runs in a Go goroutine. No separate process. |
| Standalone binary (development) | Compiled as a CLI binary. Runs independently of Flutter. Accepts keyboard commands (s=sync now, q=quit). Outputs sync status to stdout. Used for testing sync behaviour in isolation.             |

## **2.3 The Full Data Flow**

Tracing one member creation from user action to cloud confirmation:

1\. USER taps "Add member" in Flutter UI

|

2\. Flutter calls engines/records.CreateMember() via SQLite write

|

3\. engines/records validates: mandatory fields, record_class rules

|

4\. store.Tx opens SQLite transaction

├── writes member row to members table

└── appends ChangeLog entry {

entity_type: "member",

entity_id: &lt;new UUID&gt;,

operation: CREATE,

changed_at: clock.HLC.Now(),

synced_at: nil,

payload_hash: sha256(memberJSON)

}

|

5\. store.Tx commits atomically - both writes or neither

|

6\. Flutter UI reads SQLite directly - member appears instantly

|

7\. pkg/status - PendingCount increments

Status bar: "○ Offline - 1 change pending" (if offline)

or begins sync cycle immediately (if online)

|

(when online - background goroutine)

|

8\. pkg/push reads pending ChangeLog entries (synced_at IS NULL)

|

9\. pkg/push calls engines/records.Extract(memberID) → full member JSON

|

10\. pkg/push builds PushPayload, POSTs to POST /api/sync/push/

|

11\. Cloud (Django) validates, writes to PostgreSQL, returns PushResult

|

12\. On success: changelog.MarkSynced(\[entryID\])

|

13\. pkg/status - PendingCount decrements

Status bar: "● Synced - just now"

The user never waits for the cloud. Step 6 happens before step 8. All local. All fast.

# **Part 3 - Package Specifications**

## **3.1 pkg/device - Device Identity**

One job: know who this device is. Generate and persist a stable UUID on first run. This UUID is the fingerprint of the installation - it never changes for the lifetime of the app.

**Identity struct**

type Identity struct {

DeviceID uuid.UUID // generated once on first run, never changes

TenantID uuid.UUID // the Sceptre Community this device serves

LicenceKey string // issued by Ichebo Cloud at KGS onboarding

CreatedAt time.Time

ValidatedAt time.Time // last time the licence was confirmed with cloud

}

// Load retrieves identity from local SQLite settings table.

// If no identity exists, returns ErrNotInitialised.

func Load(store store.Store) (\*Identity, error)

// Init generates a new DeviceID, writes it to the store.

// Called exactly once - on first run after licence activation.

func Init(store store.Store, tenantID uuid.UUID, licenceKey string) (\*Identity, error)

// Validate confirms the licence key is accepted by Ichebo Cloud.

// Called on first run and monthly thereafter.

// On failure: status transitions to Blocked.

func Validate(identity \*Identity, transport transport.Client) error

**Invariants**

- DeviceID is generated with uuid.NewRandom() - cryptographically random, no sequential pattern
- DeviceID is written to the SQLite settings table on first run and never modified
- DeviceID is sent as the X-Device-ID header on every cloud API call
- LicenceKey validation happens on first run. If validation fails, the engine enters Blocked state and no sync occurs

## **3.2 pkg/changelog - The Engine's Memory**

One job: record every local write as an immutable fact. Be the single authoritative log of what this device has done and what has not yet been synchronised.

**Entry struct - maps to the ChangeLog SQLite table**

type Operation string

const (

OpCreate Operation = "CREATE"

OpUpdate Operation = "UPDATE"

OpDelete Operation = "DELETE"

)

type Entry struct {

ID uuid.UUID // unique ID for this change event

EntityType string // "member" | "activity" | "record" | "relationship"

EntityID uuid.UUID // the entity that changed

Operation Operation // what happened

ChangedAt hlc.Timestamp // Hybrid Logical Clock timestamp (see pkg/clock)

SyncedAt \*time.Time // nil until successfully acknowledged by cloud

DeviceID uuid.UUID // which installation made this change

PayloadHash string // SHA-256 of the entity JSON at time of change

}

// SQLite DDL

// CREATE TABLE changelog (

// id TEXT PRIMARY KEY,

// entity_type TEXT NOT NULL,

// entity_id TEXT NOT NULL,

// operation TEXT NOT NULL CHECK(operation IN ('CREATE','UPDATE','DELETE')),

// changed_at TEXT NOT NULL, -- HLC timestamp serialised as string

// synced_at TEXT, -- NULL until synced

// device_id TEXT NOT NULL,

// payload_hash TEXT NOT NULL

// );

// CREATE INDEX idx_changelog_synced_at ON changelog(synced_at);

// CREATE INDEX idx_changelog_entity ON changelog(entity_id, entity_type);

**Log interface**

// Log is the interface all packages use to interact with the ChangeLog.

type Log interface {

// Append adds a new entry. Called inside every store transaction.

// Never called directly by application code - called by domain engines.

Append(entry Entry) error

// Pending returns all entries where synced_at IS NULL,

// ordered by changed_at ASC (oldest first - preserve causality).

Pending(deviceID uuid.UUID) (\[\]Entry, error)

// MarkSynced sets synced_at = now() on the given entry IDs.

// Called by push.Pusher after cloud acknowledges receipt.

MarkSynced(ids \[\]uuid.UUID) error

// LastSyncedAt returns the most recent synced_at timestamp.

// Used as the since= parameter in pull requests.

LastSyncedAt(deviceID uuid.UUID) (\*time.Time, error)

// Count returns the number of pending (unsynced) entries.

// Used by pkg/status to populate PendingCount.

Count(deviceID uuid.UUID) (int, error)

}

**Non-negotiable invariants**

- **The ChangeLog is append-only. Entries are never updated or deleted.**
- **PayloadHash is computed by the changelog package - not by the caller. SHA-256 of the JSON-serialised entity at the moment of the write.**
- **Every store.Tx that writes an entity also writes a ChangeLog entry. Atomically. If either write fails, both are rolled back.**
- **ChangedAt uses pkg/clock HLC timestamps - never time.Now() directly.**

## **3.3 pkg/clock - Event Ordering**

One job: assign meaningful, globally comparable timestamps to change events so conflict resolution can determine which change happened "later" across devices with different wall clocks.

**Why not time.Now()?**

_If device A and device B both edit the same member record while offline and both happen to record the edit at 14:00:00.000, wall clock alone cannot determine which was later. The Hybrid Logical Clock adds a logical counter that resolves this: 14:00:00.000+0 vs 14:00:00.000+1. HLC gives us: monotonically increasing, globally comparable timestamps, even when device clocks drift or when events happen in the same millisecond._

// HLCTimestamp is a hybrid logical timestamp.

// Serialised as "{unix_nano}\_{logical}" for storage and comparison.

type HLCTimestamp struct {

Physical time.Time // wall clock component

Logical uint32 // counter for same-millisecond ordering

}

// HybridClock maintains the local HLC state.

type HybridClock struct {

mu sync.Mutex

physNow func() time.Time // injectable for testing

lastTS HLCTimestamp

}

// Now returns the current HLC timestamp, advancing logical if physical has not.

func (c \*HybridClock) Now() HLCTimestamp

// Receive updates the local clock when a remote timestamp is observed.

// Ensures the local clock is always at least as advanced as any remote clock seen.

// Called by the Puller when processing cloud responses.

func (c \*HybridClock) Receive(remote HLCTimestamp) HLCTimestamp

// Compare returns -1, 0, or 1 for a &lt; b, a == b, a &gt; b.

// Used by pkg/resolve for LastWriteWins rule.

func Compare(a, b HLCTimestamp) int

Why HLC and not vector clocks: vector clocks track causality between every pair of devices and grow in size with the number of devices. For Ichebo - single community, one device per installation - HLC is the correct trade-off: simple, small, deterministic, and correct for the conflict resolution rules used.

## **3.4 pkg/store - Local SQLite Abstraction**

One job: provide a clean interface to the local SQLite database. Hide all SQL. Be the only place in the codebase that holds a database connection.

**SQLite configuration (non-negotiable)**

// SQLite must be opened with these pragmas on every connection:

PRAGMA journal_mode=WAL; -- enables concurrent reads + one writer

PRAGMA busy_timeout=5000; -- wait 5s before failing on lock

PRAGMA foreign_keys=ON; -- enforce FK constraints

PRAGMA synchronous=NORMAL; -- safe + fast (WAL mode makes FULL unnecessary)

**Store interface**

// Store is the interface every package uses to read and write local data.

// Production: SQLite. Tests: in-memory store.

type Store interface {

Members() MemberStore

Activities() ActivityStore

Records() RecordStore

Settings() SettingsStore

ChangeLog() changelog.Log

// Tx begins a transaction. All writes within fn are atomic.

// CRITICAL: domain engines MUST use Tx for all writes.

// This guarantees that entity write + ChangeLog.Append are always atomic.

Tx(fn func(tx TxStore) error) error

}

// TxStore is the write-only view inside a transaction.

// Deliberately does not expose ChangeLog.Reader - reads outside transactions only.

type TxStore interface {

Members() MemberStore // write operations only

Activities() ActivityStore // write operations only

Records() RecordStore // write operations only

ChangeLog() changelog.Writer // append only

}

The design intent: TxStore does not allow reads inside a transaction. This prevents the common pattern of read-modify-write inside a transaction leading to phantom reads. Domain engines read first (outside Tx), then write (inside Tx).

## **3.5 pkg/transport - Cloud HTTP Client**

One job: talk to the Ichebo Cloud DRF API. Handle authentication, retries, timeouts, and connectivity detection.

type Client interface {

// Post sends a JSON payload. Handles: auth token, timeout (30s), retry (3x, exponential backoff).

Post(ctx context.Context, path string, body interface{}) (\[\]byte, error)

// Get sends a GET request with query parameters.

Get(ctx context.Context, path string, params map\[string\]string) (\[\]byte, error)

// IsOnline checks connectivity via HEAD /api/health/. Cached 10 seconds.

IsOnline(ctx context.Context) bool

}

type Config struct {

BaseURL string // "<https://app.ichebo.org>"

AuthToken string // DRF token for this device's user account

DeviceID string // sent as X-Device-ID header on every request

Timeout time.Duration // default 30s

MaxRetries int // default 3

}

// Error types

type AuthError struct { StatusCode int; Message string } // 401 or 403 → Blocked state

type NetworkError struct { Cause error } // no connection → Offline state

type ServerError struct { StatusCode int; Message string } // 5xx → retry with backoff

## **3.6 pkg/push - Local → Cloud**

One job: take pending ChangeLog entries and deliver them to the cloud, in order, reliably, idempotently.

**Pusher**

type Pusher struct {

log changelog.Log

store store.Store

transport transport.Client

engines engines.Registry

device \*device.Identity

status \*status.Monitor

batchSize int // default 50

}

// Run executes one complete push cycle.

func (p \*Pusher) Run(ctx context.Context) error {

// 1. Read all pending ChangeLog entries, ordered by changed_at ASC

pending, err := p.log.Pending(p.device.DeviceID)

if err != nil { return err }

if len(pending) == 0 { return nil }

// 2. Batch into groups of p.batchSize

for \_, batch := range batchEntries(pending, p.batchSize) {

// 3. Build PushPayload: resolve entity data for each entry

payload, err := p.buildPayload(batch)

if err != nil { return err }

// 4. POST to cloud

p.status.SetState(status.Syncing, status.WithProgress(len(batch), len(pending)))

results, err := p.postBatch(ctx, payload)

if err != nil {

// NetworkError → transition to Offline, stop

// AuthError → transition to Blocked, stop

return err

}

// 5. Process results

var synced, conflicted \[\]uuid.UUID

for \_, result := range results {

switch result.Status {

case "success": synced = append(synced, result.EntityID)

case "conflict": conflicted = append(conflicted, result.EntityID)

case "rejected": p.logRejection(result) // permissions issue - log, skip

}

}

// 6. Mark synced entries

if err := p.log.MarkSynced(synced); err != nil { return err }

// 7. Handle conflicts

for \_, id := range conflicted {

p.handOffConflict(ctx, id)

}

}

return nil

}

**PushPayload - request body for POST /api/sync/push/**

type PushPayload struct {

DeviceID string \`json:"device_id"\`

Changes \[\]PushChange \`json:"changes"\`

}

type PushChange struct {

EntityType string \`json:"entity_type"\`

EntityID string \`json:"entity_id"\`

Operation string \`json:"operation"\` // CREATE | UPDATE | DELETE

ChangedAt string \`json:"changed_at"\` // HLC timestamp serialised

PayloadHash string \`json:"payload_hash"\`

Payload json.RawMessage \`json:"payload"\` // full entity JSON

}

type PushResult struct {

EntityID string \`json:"entity_id"\`

Status string \`json:"status"\` // "success" | "conflict" | "rejected"

Reason string \`json:"reason,omitempty"\`

}

**Idempotency guarantee**

The cloud identifies duplicates by the tuple (device_id, entity_id, operation, changed_at). If a push is retried because the network dropped after the cloud processed but before it responded - the duplicate is silently ignored. The ChangeLog entry remains unsynced locally until the cloud confirms, so the retry is always safe. UUID primary keys make this reliable - no sequential ID collision is possible.

## **3.7 pkg/pull - Cloud → Local**

One job: ask the cloud what has changed since the last sync, receive the response, and apply it to the local store through the appropriate domain engine.

**Puller**

type Puller struct {

log changelog.Log

store store.Store

transport transport.Client

engines engines.Registry

resolver resolve.Resolver

clock \*clock.HybridClock

device \*device.Identity

status \*status.Monitor

}

// Run executes one complete pull cycle.

func (p \*Puller) Run(ctx context.Context) error {

since, err := p.log.LastSyncedAt(p.device.DeviceID)

if err != nil { return err }

for {

resp, err := p.fetch(ctx, since)

if err != nil { return err }

// Update HLC with the cloud's retrieved_at timestamp

p.clock.Receive(hlc.Parse(resp.RetrievedAt))

// Process each entity type

for \_, entityType := range \[\]string{"members", "activities", "records", "governance"} {

for \_, raw := range resp.EntitiesFor(entityType) {

if err := p.applyOrConflict(ctx, entityType, raw); err != nil {

return err

}

}

}

if !resp.HasMore { break }

since = &resp.RetrievedAt

}

return nil

}

// applyOrConflict determines whether to apply a cloud entity or send to resolve.

func (p \*Puller) applyOrConflict(ctx context.Context, entityType string, raw json.RawMessage) error {

entityID := extractID(raw)

// Check if this entity has pending local changes

pending, \_ := p.log.Pending(p.device.DeviceID)

hasPendingLocal := containsEntity(pending, entityID)

if !hasPendingLocal {

// No conflict - apply directly through the domain engine

return p.store.Tx(func(tx store.TxStore) error {

return p.engines.For(entityType).Apply(tx, changelog.OpUpdate, raw)

})

}

// Conflict detected - send to resolve.Resolver

localVersion, \_ := p.engines.For(entityType).Extract(p.store, entityID)

p.resolver.Resolve(ctx, resolve.Conflict{

EntityType: entityType,

EntityID: entityID,

LocalVersion: localVersion,

CloudVersion: raw,

})

return nil

}

**PullResponse - cloud API response**

// GET /api/sync/pull/?since={ts}&device_id={id}&tenant_id={id}

type PullResponse struct {

Since string \`json:"since"\`

RetrievedAt string \`json:"retrieved_at"\`

HasMore bool \`json:"has_more"\`

Members \[\]json.RawMessage \`json:"members"\`

Activities \[\]json.RawMessage \`json:"activities"\`

Records \[\]json.RawMessage \`json:"records"\`

Governance \[\]json.RawMessage \`json:"governance"\`

}

## **3.8 pkg/resolve - Conflict Resolution**

One job: apply the conflict resolution policy table to determine what wins when local and cloud have different versions of the same entity. This is the policy enforcer - every conflict resolution decision flows through here.

**Conflict resolution rules (policy table)**

| **Entity type**                            | **Rule**              | **Reason**                                                                 |
| ------------------------------------------ | --------------------- | -------------------------------------------------------------------------- |
| governance_record, handbook_record         | Cloud wins always     | Authority flows from apostolic leadership downward. Local cannot override. |
| permission, role                           | Cloud wins always     | Authority flows downward, never upward.                                    |
| community_settings                         | Cloud wins always     | Set at onboarding, controlled by network.                                  |
| member                                     | Last write wins (HLC) | Steward updates are legitimate from both device and cloud.                 |
| activity_log                               | Merge - both kept     | Both events are real. Neither overwrites the other.                        |
| personal_record, bible_note, journal_entry | Local wins always     | Personal and private to the device.                                        |
| anything else                              | Queue                 | Goes to ConflictQueue for user review.                                     |

type Rule int

const (

CloudWins Rule = iota // cloud version replaces local

LocalWins // local version is pushed, cloud updated

LastWriteWins // HLC comparison - later timestamp wins

Merge // both versions kept as separate records

Queue // ConflictQueue - user decides

)

// RuleFor is the single authoritative location for conflict resolution policy.

// Changing this function changes the policy everywhere.

// This is intentional - conflict rules are architectural decisions,

// not configuration values.

func RuleFor(entityType string) Rule {

switch entityType {

case "governance_record", "handbook_record":

return CloudWins

case "permission", "role", "community_settings":

return CloudWins

case "personal_record", "bible_note", "journal_entry":

return LocalWins

case "member":

return LastWriteWins

case "activity_log":

return Merge

default:

return Queue

}

}

type Conflict struct {

EntityType string

EntityID uuid.UUID

LocalVersion json.RawMessage

CloudVersion json.RawMessage

LocalChangedAt hlc.Timestamp

CloudChangedAt hlc.Timestamp

Rule Rule

}

type Resolver interface {

Resolve(ctx context.Context, conflict Conflict) error

}

**Why policy is in code, not config**

_Policy tables in config files get edited incorrectly, parsed incorrectly, and silently ignored. Conflict resolution rules are a core architectural decision (ADR-018). They belong in code, under version control, reviewed as code changes. Changing a conflict rule is significant - it should require a pull request, not a config edit._

## **3.9 pkg/queue - ConflictQueue**

One job: hold conflicts that could not be auto-resolved, surface them to the user calmly, and apply their resolution.

// ConflictEntry is one pending conflict awaiting user resolution.

type ConflictEntry struct {

ID uuid.UUID // unique ID for this conflict event

EntityType string

EntityID uuid.UUID

LocalVersion json.RawMessage

CloudVersion json.RawMessage

CreatedAt time.Time

ResolvedAt \*time.Time // nil until user resolves

Resolution \*string // "local" | "cloud" - set on resolution

}

// SQLite DDL

// CREATE TABLE conflict_queue (

// id TEXT PRIMARY KEY,

// entity_type TEXT NOT NULL,

// entity_id TEXT NOT NULL,

// local_version TEXT NOT NULL,

// cloud_version TEXT NOT NULL,

// created_at TEXT NOT NULL,

// resolved_at TEXT,

// resolution TEXT

// );

type Queue interface {

Add(entry ConflictEntry) error

Pending() (\[\]ConflictEntry, error)

Count() (int, error) // drives status bar conflict count

// Resolve applies user's choice:

// "local" → write local version to store, push to cloud

// "cloud" → write cloud version to store, mark local ChangeLog entry synced

Resolve(id uuid.UUID, choice string, store store.Store, engines engines.Registry) error

}

User experience contract: the ConflictQueue is not an error state. It is a normal, occasional part of running a community. The status bar shows the conflict state calmly. The review UI presents each conflict as two versions side by side with two buttons: Keep mine / Keep cloud. Most users will see this rarely if ever.

## **3.10 pkg/status - The Four States**

One job: be the single source of truth for the current sync state. Broadcast changes to Flutter. Never block.

| **State** | **Display text**                            |
| --------- | ------------------------------------------- |
| Synced    | ● Synced - 2 minutes ago \[Sync now\]       |
| Offline   | ○ Offline - 47 changes pending              |
| Syncing   | ⟳ Syncing - 23 of 47 changes...             |
| Conflict  | ⚠ 3 records need attention \[Review\]       |
| Blocked   | ✕ Sync blocked - contact your administrator |

type State int

const (

Synced State = iota

Offline

Syncing

Conflict

Blocked

)

type StateUpdate struct {

State State

PendingCount int

SyncedCount int

TotalCount int

LastSyncedAt \*time.Time

ConflictCount int

Message string // pre-formatted display string

}

type Monitor struct {

current State

mu sync.RWMutex

subscribers \[\]chan StateUpdate

}

// Subscribe returns a channel that receives StateUpdate on every state change.

// Flutter polls this via FFI or listens via callback.

func (m \*Monitor) Subscribe() <-chan StateUpdate

// SetState transitions state and broadcasts to all subscribers.

func (m \*Monitor) SetState(s State, opts ...Option)

// Options

func WithPending(count int) Option

func WithProgress(synced, total int) Option

func WithConflicts(count int) Option

func WithLastSynced(t time.Time) Option

# **Part 4 - Domain Engine Specifications**

Each domain engine implements the Engine interface. The Sync Engine calls engines through the Registry - it never calls engine packages directly. Engines enforce all domain rules from the data contract.

// The Engine interface - every domain engine implements this.

type Engine interface {

EntityType() string // "member" | "activity" | "record" | "relationship"

// Apply writes a cloud-sourced entity to the local store inside a transaction.

// Enforces all domain rules from data-contract-v11.

Apply(tx store.TxStore, op changelog.Operation, payload json.RawMessage) error

// Extract reads a local entity and returns it as JSON for the push payload.

Extract(store store.Store, entityID uuid.UUID) (json.RawMessage, error)

// Validate checks a payload conforms to domain rules before Apply.

// Returns a descriptive error if validation fails.

Validate(payload json.RawMessage) error

}

// Registry maps entity types to engines.

type Registry struct { engines map\[string\]Engine }

func (r \*Registry) For(entityType string) Engine

func (r \*Registry) Register(e Engine)

func (r \*Registry) MustFor(entityType string) Engine // panics if not found

## **4.1 Records Engine**

| **Property** | **Value**                           |
| ------------ | ----------------------------------- |
| EntityType   | record                              |
| SQLite table | records                             |
| Source       | data-contract-v11 Part 3, Part 22.1 |

**Apply - domain rules enforced**

- Four mandatory fields: id (UUID), tenant_id, created_by, created_at - all must be present or Apply returns error
- record_class must be one of: personal | organizational | governance
- record_family must be registered: journal | governance | activity | learning | reference | bible | community
- record_type must be valid for the given record_family (see data contract Part 3.2 registry)
- Governance records (record_class: governance): Apply only if the source is a cloud-authoritative push (CloudWins rule). Local governance record edits go through The Desk on the web - not through Desktop in MVP.
- Soft delete: deleted_at field respected - deleted records are kept in the table, filtered from queries

**Extract - fields included in push payload**

All fields from the record row including custom_fields and metadata JSONField. PayloadHash computed over the full serialised JSON.

## **4.2 Activity Engine**

| **Property**  | **Value**                           |
| ------------- | ----------------------------------- |
| EntityType    | activity                            |
| SQLite tables | activities, activity_log            |
| Source        | data-contract-v11 Part 4, Part 22.2 |

**Apply - domain rules enforced**

- Four mandatory fields enforced
- activity_type must be valid: task | habit | goal | event | campaign | project | programme | reminder | skill
- status must be valid: pending | in_progress | completed | cancelled | deferred
- On every status transition: ActivityLog entry written atomically in the same Tx. ActivityLog entries are immutable - never updated, never deleted.
- linked_record_id: if set, must reference a valid record UUID in the local records table
- Soft delete: deleted_at respected

## **4.3 Relationships Engine**

| **Property** | **Value**                             |
| ------------ | ------------------------------------- |
| EntityType   | relationship                          |
| SQLite table | relationships                         |
| Source       | data-contract-v11 Part 3.3, Part 22.3 |

**Apply - domain rules enforced**

- Exactly one of to_record_id or bible_verse_id must be non-null - both null or both set is rejected
- relationship_type must be in the controlled vocabulary (data contract Part 3.4)
- direction must be directed or bidirectional
- strength must be weak | medium | strong | null - not a float
- Soft delete: deleted_at respected

## **4.4 Bible Engine**

| **Property** | **Value**                                   |
| ------------ | ------------------------------------------- |
| EntityType   | bible_verse                                 |
| Operation    | Pull only - never pushed to cloud           |
| Source       | Bundled SQLite file (30MB, KJV + ASV + WEB) |
| Source spec  | data-contract-v11 Part 13, Part 22.4        |

**Bundled database - locked decision**

**Locked - Q3 answer**

_Bible data (KJV, ASV, WEB - approximately 30MB) is bundled with the Ichebo Desktop installer as a pre-populated SQLite file. No network required for scripture. The word of God is available offline from minute one. This is what local-first means in practice._

**Apply - domain rules enforced**

- Bible Engine is pull-only - Apply only handles receiving cloud-side bible_note records (personal annotations), not the scripture verses themselves
- Scripture verse data is read-only - never pushed, never modified by the engine
- BibleVerse records are exempt from the four mandatory fields rule (data contract Part 1.1)

## **4.5 Calendar Engine**

| **Property** | **Value**                                |
| ------------ | ---------------------------------------- |
| EntityType   | calendar_event                           |
| Operation    | Pull only - aggregation of Activity data |
| Source       | data-contract-v11 Part 11, Part 22.5     |

The Calendar Engine aggregates events from the Activity table filtered by date range and source app. It does not have its own storage - it reads from the activities table. In the Sync Engine context it receives calendar event snapshots from the cloud during pull operations and caches them for the Flutter UI.

# **Part 5 - FFI Bridge**

The FFI bridge is the minimal interface between Flutter (Dart) and the Sync Engine (Go). Six functions exported. No more.

**FFI is for control. SQLite is for data.**

_Flutter calls six FFI functions to control the sync engine. All actual data for the UI - member lists, activity feeds, records - is read directly from SQLite by Flutter using the sqflite package. No data passes through the FFI boundary. This keeps the boundary minimal, fast, and stable._

// ffi/bridge.go - exported functions callable from dart:ffi

// SyncStart starts the sync engine daemon.

// configJSON: JSON string containing Config (baseURL, authToken, deviceID, tenantID).

// Returns 0 on success, non-zero on error.

// Call once on app initialisation. The daemon runs in a background goroutine.

//export SyncStart

func SyncStart(configJSON \*C.char) C.int

// SyncStop gracefully shuts down the sync engine.

// Flushes pending operations, closes SQLite connections, stops goroutines.

// Call on app termination.

//export SyncStop

func SyncStop()

// SyncNow triggers an immediate sync cycle (push + pull).

// Returns immediately - the cycle runs in the background.

// Call when user taps "Sync now" in the status bar.

//export SyncNow

func SyncNow()

// SyncStatus returns the current status as a JSON string.

// Dart decodes this to a StatusUpdate struct.

// {"state":"synced","pending":0,"last_synced_at":"2026-05-13T14:00:00Z","conflict_count":0}

//export SyncStatus

func SyncStatus() \*C.char

// SyncConflictCount returns the number of pending conflicts in the ConflictQueue.

// Dart uses this to show/hide the conflict badge in the status bar.

//export SyncConflictCount

func SyncConflictCount() C.int

// SyncResolveConflict applies the user's resolution to a specific conflict.

// conflictID: UUID string of the ConflictEntry.

// choice: 0 = keep local version, 1 = keep cloud version.

// Returns 0 on success.

//export SyncResolveConflict

func SyncResolveConflict(conflictID \*C.char, choice C.int) C.int

**Dart-side wrapper (Flutter)**

// In Flutter: lib/sync/sync_engine.dart

import 'dart:ffi';

import 'package:ffi/ffi.dart';

class SyncEngine {

static final DynamicLibrary \_lib = DynamicLibrary.open('libichebo_sync.so');

static late final \_syncStart = \_lib

.lookup&lt;NativeFunction<Int32 Function(Pointer<Utf8&gt;)>>('SyncStart')

.asFunction&lt;int Function(Pointer<Utf8&gt;)>();

static void start(SyncConfig config) {

final json = jsonEncode(config.toJson());

final ptr = json.toNativeUtf8();

\_syncStart(ptr);

malloc.free(ptr);

}

static void syncNow() { /\* ... \*/ }

static SyncStatus getStatus() { /\* ... \*/ }

static int getConflictCount() { /\* ... \*/ }

static void resolveConflict(String id, bool keepLocal) { /\* ... \*/ }

}

# **Part 6 - Sync Cycle Specification**

## **6.1 Sync Triggers**

| **Trigger**                 | **When**                                             | **Who initiates**       | **Priority**                                |
| --------------------------- | ---------------------------------------------------- | ----------------------- | ------------------------------------------- |
| App open                    | Every time the Flutter app starts                    | Automatic               | High - run before UI is fully rendered      |
| Connectivity restored       | Network transitions from offline to online           | pkg/transport monitors  | High - run within 2 seconds of detection    |
| User-triggered              | User taps "Sync now" in status bar                   | FFI SyncNow()           | Immediate - highest priority                |
| Periodic (online)           | Every 5 minutes while the app is in the foreground   | Internal ticker         | Normal - background priority                |
| Throttle during UI activity | Suppress periodic trigger if user is actively typing | Flutter signals via FFI | Courtesy - prevent interrupting active work |

## **6.2 Sync Cycle Sequence**

Every sync cycle runs the same sequence regardless of trigger:

- Check IsOnline - if false, transition to Offline state and abort
- Validate device identity - if expired, call device.Validate(). If fails, transition to Blocked and abort
- Set status to Syncing
- Run push.Pusher.Run() - push all pending local changes to cloud
- Run pull.Puller.Run() - pull all cloud changes since LastSyncedAt
- Check ConflictQueue.Count() - if > 0, set status to Conflict
- If ConflictQueue.Count() == 0 and no errors, set status to Synced
- Update LastSyncedAt

## **6.3 Sync Frequency**

| **Situation**             | **Frequency**                                                     |
| ------------------------- | ----------------------------------------------------------------- |
| App open                  | Immediate, every launch                                           |
| Connectivity restored     | Within 2 seconds of detection                                     |
| User-triggered            | Immediate                                                         |
| App in foreground, online | Every 5 minutes                                                   |
| App in background         | No sync - OS may restrict background execution                    |
| User actively typing      | Suppress 5-minute trigger; resume 30 seconds after last keystroke |

## **6.4 Initial Sync (First Activation)**

When Ichebo Desktop activates for the first time with a new licence key, the initial sync payload is downloaded from the cloud. This is a one-time operation that establishes the local database.

**Initial sync payload - minimum viable set**

- Tenant settings - name, tier, path, settings fields
- All current members - the full member roster of the community
- Last 90 days of activities - attendance, service, participation logs
- Governance snapshot - active mandates and reference library records (read-only)

What is NOT in the initial sync:

- Full activity history beyond 90 days - synced on demand if user scrolls back
- Bible data - bundled with the installer, not synced
- Learn programme content - not in Desktop MVP scope

**Design principle**

_The initial sync must complete in under 60 seconds on a 5 Mbps connection for a community of 500 members. If the payload would exceed this, paginate. Never block the first-run experience._

# **Part 7 - Cloud API Endpoints Required**

The following endpoints must exist on the Ichebo Cloud DRF API to support the Sync Engine. They are additions to the existing API - no existing endpoints are modified.

## **7.1 Push Endpoint**

POST /api/sync/push/

// Request headers:

// Authorization: Token {drf_token}

// X-Device-ID: {device_uuid}

// Content-Type: application/json

// Request body: PushPayload (see Part 3.6)

// Response: 200 OK

{

"processed": 47,

"results": \[

{ "entity_id": "uuid", "status": "success" },

{ "entity_id": "uuid", "status": "conflict", "reason": "newer_version_exists" },

{ "entity_id": "uuid", "status": "rejected", "reason": "permission_denied" }

\]

}

// Idempotency: duplicate (device_id, entity_id, operation, changed_at) tuples

// are silently ignored. Returns status: "success" for the duplicate.

// Cloud-side conflict detection:

// For each incoming entity:

// 1. Look up the current cloud version by entity_id

// 2. Compare cloud updated_at with incoming changed_at

// 3. If cloud version is newer AND payload_hash differs → return status: "conflict"

// 4. If cloud version is same or older → apply the change → return status: "success"

## **7.2 Pull Endpoint**

GET /api/sync/pull/

?since={hlc_timestamp} // HLC timestamp of last successful sync

&device_id={uuid} // for audit - not used for filtering

&tenant_id={uuid} // scope pull to this tenant

// Request headers:

// Authorization: Token {drf_token}

// X-Device-ID: {device_uuid}

// Response: 200 OK - PullResponse (see Part 3.7)

{

"since": "2026-05-13T14:00:00.000_0",

"retrieved_at": "2026-05-13T14:05:00.000_0",

"has_more": false,

"members": \[ /\* full member JSON objects \*/ \],

"activities": \[ /\* full activity JSON objects \*/ \],

"records": \[ /\* governance + community records in tenant scope \*/ \],

"governance": \[ /\* handbook and mandate records if Level 3+ \*/ \]

}

// Scoping rules:

// - members: UserPermission rows for the tenant_id

// - activities: Activity rows for the tenant_id where updated_at > since

// - records: Record rows where tenant_id matches AND visibility permits

// - governance: Handbook records if user.competence_level >= 3

// Pagination: max 500 items per type per response.

// If has_more: true, Puller calls again with since = retrieved_at

## **7.3 Licence Validation Endpoint**

POST /api/sync/validate-licence/

// Request body:

{ "device_id": "uuid", "licence_key": "string", "tenant_id": "uuid" }

// Response: 200 OK

{ "valid": true, "tenant_name": "string", "expires_at": "ISO-8601 | null" }

// Response: 403 Forbidden

{ "valid": false, "reason": "revoked | expired | not_found" }

// Called by pkg/device.Validate() on first run and monthly thereafter.

# **Part 8 - Non-Negotiable Data Rules**

These rules govern both the local SQLite database and the cloud PostgreSQL database. They are the foundation of the sync engine's correctness guarantees. None may be relaxed without a new ADR.

## **8.1 UUID Primary Keys Everywhere**

**Non-negotiable**

_All model primary keys in both SQLite (local) and PostgreSQL (cloud) are UUID v4 fields. No auto-increment integers. No composite keys as primary identifiers. A record created offline must have a permanent UUID identity before it ever reaches the cloud. This is what makes idempotent push possible._

// SQLite - every table

id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' ||

lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) ||

'-' || substr('89ab',abs(random()) % 4 + 1, 1) ||

substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6))))

// Go - using github.com/google/uuid

id := uuid.New() // crypto/rand based, RFC 4122 compliant

// Django (cloud) - after UUID migration (Phase E.1)

id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

## **8.2 Soft Deletes Everywhere**

**Non-negotiable**

_No hard deletes anywhere in the system - neither locally nor on the cloud. Every entity carries a deleted_at field (null until soft-deleted). All default querysets filter to deleted_at IS NULL. Hard deletion via DELETE HTTP verb or ORM .delete() is prohibited. The Sync Engine cannot reconcile hard deletes across devices._

// SQLite - every entity table

deleted_at TEXT -- ISO-8601 timestamp, NULL until soft-deleted

// All queries include:

WHERE deleted_at IS NULL

// Soft delete operation (via domain engine):

UPDATE {table} SET deleted_at = ? WHERE id = ?

\-- Plus ChangeLog entry with operation = 'DELETE'

// Django (cloud)

deleted_at = models.DateTimeField(null=True, blank=True)

\# Default queryset manager filters deleted_at IS NULL

## **8.3 SQLite WAL Mode**

\-- Applied once on first open, persists to database file:

PRAGMA journal_mode=WAL;

PRAGMA busy_timeout=5000;

PRAGMA foreign_keys=ON;

PRAGMA synchronous=NORMAL;

\-- WAL mode allows: many concurrent readers + one writer

\-- This is required because:

\-- The Flutter UI reads SQLite constantly (for display data)

\-- The sync engine's background goroutine writes to SQLite

\-- Without WAL mode these would block each other

## **8.4 Atomic Writes - Entity + ChangeLog**

Every entity write and its corresponding ChangeLog entry must be committed atomically. If either fails, both are rolled back. This is the invariant that makes the ChangeLog a reliable journal.

// The TxStore interface enforces this at the type level.

// Domain engines receive a TxStore - they cannot write an entity

// without also being able to write to the ChangeLog.

// This makes it structurally impossible to write an entity without logging it.

store.Tx(func(tx TxStore) error {

// Both of these must succeed or neither is committed

if err := tx.Members().Create(member); err != nil { return err }

if err := tx.ChangeLog().Append(entry); err != nil { return err }

return nil // commits only if both succeed

})

# **Part 9 - Build Sequence**

This sequence is non-negotiable. The UI of every Ichebo Desktop feature is built after the data layer is solid. Every step has a clear exit criterion.

| **Step**                     | **What it builds and its exit criterion**                                                                                                                    |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| E.1 - UUID migration         | All Django model PKs migrated to UUIDField. Exit: all existing records have UUID PKs. All API responses return UUID strings. No auto-increment IDs anywhere. |
| E.2 - Soft delete pattern    | deleted_at field on all Django models. Default querysets filter it. Exit: no hard deletes possible via any API endpoint.                                     |
| E.3a - pkg/device            | Device identity package with SQLite persistence. Exit: device.Init() and device.Load() pass all unit tests including concurrency tests.                      |
| E.3b - pkg/clock             | Hybrid Logical Clock implementation. Exit: Compare() correctly orders events from two devices with identical wall clock times.                               |
| E.3c - pkg/store             | SQLite abstraction with WAL mode, TxStore interface. Exit: Tx() correctly rolls back both writes if either fails.                                            |
| E.3d - pkg/changelog         | ChangeLog table, Log interface, append-only invariant. Exit: ChangeLog cannot be written outside a Tx (type system enforces this).                           |
| E.3e - engines/records       | Records Engine: Apply() and Extract(). Exit: Apply() rejects payloads missing mandatory fields. Apply() enforces record_class rules.                         |
| E.3f - engines/activity      | Activity Engine: Apply() and Extract(). Exit: ActivityLog entry written atomically with every status transition.                                             |
| E.3g - engines/relationships | Relationships Engine: Apply() and Extract(). Exit: Apply() rejects payloads with both to_record_id and bible_verse_id set.                                   |
| E.3h - engines/bible         | Bible Engine bundled SQLite file. Exit: KJV, ASV, WEB all readable offline from minute one. No network call for scripture.                                   |
| E.4a - POST /api/sync/push/  | Cloud endpoint. Exit: idempotency test - sending the same payload twice returns "success" both times with no duplicate data.                                 |
| E.4b - GET /api/sync/pull/   | Cloud endpoint. Exit: returns only data scoped to the requesting tenant. has_more pagination works correctly.                                                |
| E.4c - pkg/transport         | HTTP client with retry, auth, offline detection. Exit: NetworkError returned (not panic) when server unreachable.                                            |
| E.4d - pkg/push              | Push cycle. Exit: 7-day offline test - make 1000 changes offline, push all, cloud has all 1000 with correct data.                                            |
| E.4e - pkg/pull              | Pull cycle. Exit: pull after cloud-side change with no local pending changes applies correctly with no conflict.                                             |
| E.4f - pkg/resolve           | Conflict resolution. Exit: CloudWins, LocalWins, LastWriteWins, Merge all tested with deterministic outcomes.                                                |
| E.4g - pkg/queue             | ConflictQueue. Exit: Queue conflict, count returns 1, resolve with "cloud" writes cloud version, count returns 0.                                            |
| E.4h - pkg/status            | Status Monitor. Exit: all four state transitions broadcast to subscribers within 100ms.                                                                      |
| E.4i - ffi/bridge            | FFI bridge. Exit: Flutter calls SyncStart() and SyncStatus() correctly from Dart without memory leaks.                                                       |
| E.4j - Integration test      | End-to-end test: offline for 7 days, 500 changes, reconnect, full sync, zero conflicts, all data correct on both sides.                                      |

# **Part 10 - Open Questions Resolved**

Five questions surfaced during the module sketch session (May 2026). All are now locked.

| **Question**                   | **Locked answer**                                                                                                                                                                                                                                  |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Q1 - Conflict detection timing | Both sides. Cloud detects at push time via payload_hash comparison. Local Puller detects at pull time if entity has pending ChangeLog entries. Double detection. Belt and braces.                                                                  |
| Q2 - Initial sync payload      | Minimum viable set: tenant settings, full member roster, last 90 days of activities, governance snapshot. Everything else on demand. First-run target: complete in under 60 seconds on 5 Mbps for 500-member community.                            |
| Q3 - Bible data loading        | Bundled with the Ichebo Desktop installer as a pre-populated 30MB SQLite file (KJV, ASV, WEB). No network dependency for scripture. Available offline from minute one.                                                                             |
| Q4 - FFI vs gRPC               | FFI for the control plane (six functions: start, stop, sync-now, status, conflict-count, resolve). Flutter reads SQLite directly for all data. gRPC deferred to Version 3 Phase 2 if business logic queries from Go engines are needed by Flutter. |
| Q5 - Sync frequency            | Every 5 minutes passively when online. Immediately on: app open, connectivity restored, user-triggered. Suppressed during active UI typing (30-second cooldown after last keystroke).                                                              |

**Ichebo Christian Services**

_DOC C - Sync Engine Specification v1.0 - May 2026 - Canonical Reference_