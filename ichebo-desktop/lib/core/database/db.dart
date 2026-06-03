import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

// ── Database initialisation ───────────────────────────────────────────────────

// Call once at app startup, before ProviderScope.
void initSqfliteForDesktop() {
  sqfliteFfiInit();
  databaseFactory = databaseFactoryFfi;
}

Future<String> _dbPath() async {
  final dir = await getApplicationSupportDirectory();
  return p.join(dir.path, 'ichebo.db');
}

// Opens the database with WAL mode and the correct pragmas.
// The Go sync engine also opens this same file — Flutter is a read-only
// consumer except for settings written before SyncStart is called.
Future<Database> _openDb() async {
  final path = await _dbPath();
  return openDatabase(
    path,
    version: 1,
    onCreate: (db, _) => _createSchema(db),
    onUpgrade: (db, oldV, newV) => _createSchema(db),
    onOpen: (db) async {
      await db.execute('PRAGMA journal_mode=WAL');
      await db.execute('PRAGMA foreign_keys=ON');
      await db.execute('PRAGMA busy_timeout=5000');
    },
  );
}

// Creates all tables using IF NOT EXISTS — safe to call whether the Go engine
// has already run or not. Mirrors ichebo-sync/pkg/store/store.go migrate().
Future<void> _createSchema(Database db) async {
  await db.execute('''
    CREATE TABLE IF NOT EXISTS settings (
      key   TEXT PRIMARY KEY,
      value TEXT NOT NULL
    )
  ''');
  await db.execute('''
    CREATE TABLE IF NOT EXISTS members (
      id                TEXT PRIMARY KEY,
      tenant_id         TEXT NOT NULL,
      email             TEXT NOT NULL DEFAULT '',
      display_name      TEXT NOT NULL DEFAULT '',
      first_name        TEXT NOT NULL DEFAULT '',
      last_name         TEXT NOT NULL DEFAULT '',
      phone             TEXT NOT NULL DEFAULT '',
      avatar_url        TEXT NOT NULL DEFAULT '',
      competence_level  INTEGER NOT NULL DEFAULT 0,
      is_active         INTEGER NOT NULL DEFAULT 1,
      shepherd_id       TEXT,
      service_order     TEXT,
      custom_fields     TEXT NOT NULL DEFAULT '{}',
      created_by        TEXT NOT NULL DEFAULT '',
      created_at        TEXT NOT NULL DEFAULT '',
      updated_at        TEXT NOT NULL DEFAULT '',
      deleted_at        TEXT
    )
  ''');
  await db.execute('''
    CREATE TABLE IF NOT EXISTS records (
      id            TEXT PRIMARY KEY,
      tenant_id     TEXT NOT NULL,
      record_class  TEXT NOT NULL DEFAULT '',
      record_family TEXT NOT NULL DEFAULT '',
      record_type   TEXT NOT NULL DEFAULT '',
      title         TEXT NOT NULL DEFAULT '',
      status        TEXT NOT NULL DEFAULT 'active',
      custom_fields TEXT NOT NULL DEFAULT '{}',
      metadata      TEXT NOT NULL DEFAULT '{}',
      permissions   TEXT NOT NULL DEFAULT '{}',
      created_by    TEXT NOT NULL DEFAULT '',
      created_at    TEXT NOT NULL DEFAULT '',
      updated_at    TEXT NOT NULL DEFAULT '',
      deleted_at    TEXT
    )
  ''');
  await db.execute('''
    CREATE TABLE IF NOT EXISTS activities (
      id                  TEXT PRIMARY KEY,
      tenant_id           TEXT NOT NULL,
      activity_type       TEXT NOT NULL DEFAULT 'task',
      title               TEXT NOT NULL DEFAULT '',
      description         TEXT NOT NULL DEFAULT '',
      status              TEXT NOT NULL DEFAULT 'pending',
      progress            INTEGER NOT NULL DEFAULT 0,
      assigned_to         TEXT,
      linked_record_id    TEXT,
      parent_activity_id  TEXT,
      scheduled_at        TEXT,
      due_at              TEXT,
      completed_at        TEXT,
      source_app          TEXT NOT NULL DEFAULT '',
      custom_fields       TEXT NOT NULL DEFAULT '{}',
      metadata            TEXT NOT NULL DEFAULT '{}',
      created_by          TEXT NOT NULL DEFAULT '',
      created_at          TEXT NOT NULL DEFAULT '',
      updated_at          TEXT NOT NULL DEFAULT '',
      deleted_at          TEXT
    )
  ''');
  await db.execute('''
    CREATE TABLE IF NOT EXISTS activity_log (
      id          TEXT PRIMARY KEY,
      activity_id TEXT NOT NULL,
      from_status TEXT NOT NULL DEFAULT '',
      to_status   TEXT NOT NULL DEFAULT '',
      note        TEXT,
      changed_by  TEXT NOT NULL DEFAULT '',
      changed_at  TEXT NOT NULL DEFAULT ''
    )
  ''');
  await db.execute('''
    CREATE TABLE IF NOT EXISTS relationships (
      id                TEXT PRIMARY KEY,
      tenant_id         TEXT NOT NULL,
      from_record_id    TEXT NOT NULL,
      to_record_id      TEXT,
      bible_verse_id    TEXT,
      relationship_type TEXT NOT NULL DEFAULT '',
      direction         TEXT NOT NULL DEFAULT 'undirected',
      strength          INTEGER NOT NULL DEFAULT 1,
      created_at        TEXT NOT NULL DEFAULT '',
      deleted_at        TEXT
    )
  ''');
  await db.execute('''
    CREATE TABLE IF NOT EXISTS changelog (
      id           TEXT PRIMARY KEY,
      tenant_id    TEXT NOT NULL,
      device_id    TEXT NOT NULL,
      entity_type  TEXT NOT NULL,
      entity_id    TEXT NOT NULL,
      operation    TEXT NOT NULL,
      payload      TEXT NOT NULL DEFAULT '{}',
      payload_hash TEXT NOT NULL DEFAULT '',
      changed_at   TEXT NOT NULL DEFAULT '',
      synced_at    TEXT
    )
  ''');
  await db.execute('''
    CREATE TABLE IF NOT EXISTS conflict_queue (
      id             TEXT PRIMARY KEY,
      entity_type    TEXT NOT NULL,
      entity_id      TEXT NOT NULL,
      local_version  TEXT NOT NULL DEFAULT '{}',
      cloud_version  TEXT NOT NULL DEFAULT '{}',
      created_at     TEXT NOT NULL DEFAULT '',
      resolved_at    TEXT
    )
  ''');
}

// ── Riverpod provider ─────────────────────────────────────────────────────────

// Async provider — resolves once the DB file is open.
// Usage: ref.watch(dbProvider)
final dbProvider = FutureProvider<Database>((ref) async {
  final db = await _openDb();
  ref.onDispose(db.close);
  return db;
});

// Convenience: returns DB path (for passing to SyncStart).
final dbPathProvider = FutureProvider<String>((ref) => _dbPath());
