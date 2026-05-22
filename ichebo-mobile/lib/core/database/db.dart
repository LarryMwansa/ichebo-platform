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
      // Go engine creates the full schema on first SyncStart.
      // Bootstrap a minimal settings table so reads don't crash before
      // the engine has initialised (e.g. during first-launch auth flow).
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
