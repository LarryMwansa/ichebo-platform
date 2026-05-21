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
    onCreate: (db, _) async {
      // The Go engine creates the schema on first SyncStart.
      // If Flutter opens the DB before the engine has run (e.g. in tests),
      // we create a minimal settings table so reads don't crash.
      await db.execute('''
        CREATE TABLE IF NOT EXISTS settings (
          key   TEXT PRIMARY KEY,
          value TEXT NOT NULL
        )
      ''');
    },
    onOpen: (db) async {
      await db.execute('PRAGMA journal_mode=WAL');
      await db.execute('PRAGMA foreign_keys=ON');
      await db.execute('PRAGMA busy_timeout=5000');
    },
  );
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
