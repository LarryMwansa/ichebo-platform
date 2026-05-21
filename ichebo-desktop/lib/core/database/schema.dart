// DDL that mirrors ichebo-sync/pkg/store/store.go migrate().
// Flutter never runs migrations — the Go engine creates and owns the schema.
// This file exists so Flutter code can reference column names as constants
// and so the schema is documented on the Dart side.

const kDbVersion = 1;

// Table names
const tChangelog = 'changelog';
const tConflictQueue = 'conflict_queue';
const tSettings = 'settings';
const tMembers = 'members';
const tRecords = 'records';
const tActivities = 'activities';
const tActivityLog = 'activity_log';
const tRelationships = 'relationships';

// ── members columns ───────────────────────────────────────────────────────────
const cId = 'id';
const cTenantId = 'tenant_id';
const cEmail = 'email';
const cDisplayName = 'display_name';
const cFirstName = 'first_name';
const cLastName = 'last_name';
const cPhone = 'phone';
const cAvatarUrl = 'avatar_url';
const cCompetenceLevel = 'competence_level';
const cIsActive = 'is_active';
const cShepherdId = 'shepherd_id';
const cCustomFields = 'custom_fields';
const cCreatedBy = 'created_by';
const cCreatedAt = 'created_at';
const cUpdatedAt = 'updated_at';
const cDeletedAt = 'deleted_at';

// ── records columns ───────────────────────────────────────────────────────────
const cRecordClass = 'record_class';
const cRecordFamily = 'record_family';
const cRecordType = 'record_type';
const cTitle = 'title';
const cStatus = 'status';
const cMetadata = 'metadata';
const cPermissions = 'permissions';

// ── activities columns ────────────────────────────────────────────────────────
const cActivityType = 'activity_type';
const cDescription = 'description';
const cProgress = 'progress';
const cAssignedTo = 'assigned_to';
const cLinkedRecordId = 'linked_record_id';
const cParentActivityId = 'parent_activity_id';
const cDueAt = 'due_at';
const cScheduledAt = 'scheduled_at';
const cCompletedAt = 'completed_at';
const cSourceApp = 'source_app';

// ── activity_log columns ──────────────────────────────────────────────────────
const cActivityId = 'activity_id';
const cFromStatus = 'from_status';
const cToStatus = 'to_status';
const cNote = 'note';
const cChangedBy = 'changed_by';
const cChangedAt = 'changed_at';

// ── relationships columns ─────────────────────────────────────────────────────
const cFromRecordId = 'from_record_id';
const cToRecordId = 'to_record_id';
const cBibleVerseId = 'bible_verse_id';
const cRelationshipType = 'relationship_type';
const cDirection = 'direction';
const cStrength = 'strength';

// ── changelog columns ─────────────────────────────────────────────────────────
const cEntityType = 'entity_type';
const cEntityId = 'entity_id';
const cOperation = 'operation';
const cChangedAtHlc = 'changed_at'; // HLC string
const cSyncedAt = 'synced_at';
const cDeviceId = 'device_id';
const cPayloadHash = 'payload_hash';
