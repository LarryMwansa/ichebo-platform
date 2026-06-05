import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:sqflite/sqflite.dart';

Future<String> _dbPath() async {
  final dir = await getApplicationSupportDirectory();
  return p.join(dir.path, 'ichebo.db');
}

// Opens the database with WAL mode and mandatory pragmas.
// The Go sync engine also opens this same file — Flutter is a read consumer.
// Writes go through SyncEngine (FFI) to keep the changelog intact.
Future<Database> _openDb() async {
  final path = await _dbPath();
  return openDatabase(
    path,
    version: 1,
    onCreate: (db, _) async {
      // Mirror of ichebo-sync/pkg/store/store.go migrate().
      // The Go engine will also call CREATE TABLE IF NOT EXISTS on SyncStart,
      // so this is idempotent — Flutter just ensures the schema exists before
      // any reads happen (pre-Layer-5 / sync-engine-not-yet-loaded builds).
      final batch = db.batch();
      batch.execute('''
        CREATE TABLE IF NOT EXISTS changelog (
          id           TEXT PRIMARY KEY,
          entity_type  TEXT NOT NULL,
          entity_id    TEXT NOT NULL,
          operation    TEXT NOT NULL,
          changed_at   TEXT NOT NULL,
          synced_at    TEXT,
          device_id    TEXT NOT NULL,
          payload_hash TEXT NOT NULL
        )''');
      batch.execute('CREATE INDEX IF NOT EXISTS idx_changelog_synced_at ON changelog(synced_at)');
      batch.execute('CREATE INDEX IF NOT EXISTS idx_changelog_entity ON changelog(entity_id, entity_type)');
      batch.execute('''
        CREATE TABLE IF NOT EXISTS conflict_queue (
          id             TEXT PRIMARY KEY,
          entity_type    TEXT NOT NULL,
          entity_id      TEXT NOT NULL,
          local_version  TEXT NOT NULL,
          cloud_version  TEXT NOT NULL,
          created_at     TEXT NOT NULL,
          resolved_at    TEXT,
          resolution     TEXT
        )''');
      batch.execute('''
        CREATE TABLE IF NOT EXISTS settings (
          key   TEXT PRIMARY KEY,
          value TEXT NOT NULL
        )''');
      batch.execute('''
        CREATE TABLE IF NOT EXISTS members (
          id               TEXT PRIMARY KEY,
          tenant_id        TEXT NOT NULL,
          email            TEXT,
          display_name     TEXT,
          first_name       TEXT,
          last_name        TEXT,
          phone            TEXT,
          avatar_url       TEXT,
          competence_level INTEGER NOT NULL DEFAULT 0,
          is_active        INTEGER NOT NULL DEFAULT 1,
          shepherd_id      TEXT,
          service_order    TEXT,
          custom_fields    TEXT NOT NULL DEFAULT "{}",
          created_by       TEXT NOT NULL,
          created_at       TEXT NOT NULL,
          updated_at       TEXT NOT NULL,
          deleted_at       TEXT
        )''');
      batch.execute('CREATE INDEX IF NOT EXISTS idx_members_tenant_id ON members(tenant_id)');
      batch.execute('CREATE INDEX IF NOT EXISTS idx_members_email ON members(email)');
      batch.execute('CREATE INDEX IF NOT EXISTS idx_members_deleted_at ON members(deleted_at)');
      batch.execute('''
        CREATE TABLE IF NOT EXISTS records (
          id            TEXT PRIMARY KEY,
          tenant_id     TEXT NOT NULL,
          record_class  TEXT NOT NULL,
          record_family TEXT NOT NULL,
          record_type   TEXT NOT NULL,
          title         TEXT NOT NULL DEFAULT "",
          status        TEXT NOT NULL DEFAULT "active",
          custom_fields TEXT NOT NULL DEFAULT "{}",
          metadata      TEXT NOT NULL DEFAULT "{}",
          permissions   TEXT NOT NULL DEFAULT "{}",
          created_by    TEXT NOT NULL,
          created_at    TEXT NOT NULL,
          updated_at    TEXT NOT NULL,
          deleted_at    TEXT
        )''');
      batch.execute('CREATE INDEX IF NOT EXISTS idx_records_tenant_id ON records(tenant_id)');
      batch.execute('CREATE INDEX IF NOT EXISTS idx_records_class ON records(record_class)');
      batch.execute('CREATE INDEX IF NOT EXISTS idx_records_family ON records(record_family)');
      batch.execute('CREATE INDEX IF NOT EXISTS idx_records_deleted_at ON records(deleted_at)');
      batch.execute('''
        CREATE TABLE IF NOT EXISTS activities (
          id                 TEXT PRIMARY KEY,
          tenant_id          TEXT NOT NULL,
          activity_type      TEXT NOT NULL,
          title              TEXT NOT NULL DEFAULT "",
          description        TEXT,
          status             TEXT NOT NULL DEFAULT "pending",
          progress           INTEGER NOT NULL DEFAULT 0,
          assigned_to        TEXT,
          linked_record_id   TEXT,
          parent_activity_id TEXT,
          due_at             TEXT,
          scheduled_at       TEXT,
          completed_at       TEXT,
          source_app         TEXT,
          metadata           TEXT NOT NULL DEFAULT "{}",
          created_by         TEXT NOT NULL,
          created_at         TEXT NOT NULL,
          updated_at         TEXT NOT NULL,
          deleted_at         TEXT
        )''');
      batch.execute('CREATE INDEX IF NOT EXISTS idx_activities_tenant_id ON activities(tenant_id)');
      batch.execute('CREATE INDEX IF NOT EXISTS idx_activities_type ON activities(activity_type)');
      batch.execute('CREATE INDEX IF NOT EXISTS idx_activities_status ON activities(status)');
      batch.execute('CREATE INDEX IF NOT EXISTS idx_activities_deleted_at ON activities(deleted_at)');
      batch.execute('''
        CREATE TABLE IF NOT EXISTS activity_log (
          id          TEXT PRIMARY KEY,
          activity_id TEXT NOT NULL REFERENCES activities(id),
          from_status TEXT,
          to_status   TEXT NOT NULL,
          note        TEXT,
          changed_by  TEXT NOT NULL,
          changed_at  TEXT NOT NULL
        )''');
      batch.execute('CREATE INDEX IF NOT EXISTS idx_activity_log_activity ON activity_log(activity_id)');
      batch.execute('''
        CREATE TABLE IF NOT EXISTS relationships (
          id                TEXT PRIMARY KEY,
          tenant_id         TEXT NOT NULL,
          from_record_id    TEXT NOT NULL REFERENCES records(id),
          to_record_id      TEXT,
          bible_verse_id    TEXT,
          relationship_type TEXT NOT NULL,
          direction         TEXT NOT NULL DEFAULT "directed",
          strength          TEXT,
          note              TEXT,
          metadata          TEXT NOT NULL DEFAULT "{}",
          created_by        TEXT NOT NULL,
          created_at        TEXT NOT NULL,
          updated_at        TEXT NOT NULL,
          deleted_at        TEXT
        )''');
      batch.execute('CREATE INDEX IF NOT EXISTS idx_relationships_from ON relationships(from_record_id)');
      batch.execute('CREATE INDEX IF NOT EXISTS idx_relationships_to ON relationships(to_record_id)');
      batch.execute('CREATE INDEX IF NOT EXISTS idx_relationships_deleted ON relationships(deleted_at)');
      await batch.commit(noResult: true);
    },
    onOpen: (db) async {
      await db.execute('PRAGMA journal_mode=WAL');
      await db.execute('PRAGMA foreign_keys=ON');
      await db.execute('PRAGMA busy_timeout=5000');
      await db.execute('PRAGMA synchronous=NORMAL');
    },
  );
}

// Resolves once the DB file is open. Dispose closes the connection.
final dbProvider = FutureProvider<Database>((ref) async {
  final db = await _openDb();
  ref.onDispose(db.close);
  return db;
});

// DB path string — passed to SyncStart so the Go engine opens the same file.
final dbPathProvider = FutureProvider<String>((ref) => _dbPath());
