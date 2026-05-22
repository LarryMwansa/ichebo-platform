import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/database/db.dart';
import '../../sync/sync_state.dart';

// ── ConflictEntry ─────────────────────────────────────────────────────────────

class ConflictEntry {
  const ConflictEntry({
    required this.id,
    required this.entityType,
    required this.entityId,
    required this.localVersion,
    required this.cloudVersion,
    required this.createdAt,
  });

  final String id;
  final String entityType;
  final String entityId;
  final Map<String, dynamic> localVersion;
  final Map<String, dynamic> cloudVersion;
  final DateTime createdAt;

  static Map<String, dynamic> _parseJson(dynamic v) {
    if (v == null) return {};
    if (v is Map<String, dynamic>) return v;
    try { return jsonDecode(v as String) as Map<String, dynamic>; } catch (_) { return {}; }
  }

  factory ConflictEntry.fromMap(Map<String, dynamic> m) {
    return ConflictEntry(
      id:           m['id'] as String,
      entityType:   m['entity_type'] as String? ?? 'unknown',
      entityId:     m['entity_id'] as String? ?? '',
      localVersion: _parseJson(m['local_version']),
      cloudVersion: _parseJson(m['cloud_version']),
      createdAt:    DateTime.tryParse(m['created_at'] as String? ?? '') ?? DateTime.now(),
    );
  }

  // Returns a readable one-line summary of a version map.
  static String summarise(Map<String, dynamic> v) {
    if (v.isEmpty) return '—';
    final interesting = ['display_name', 'name', 'title', 'service_order',
        'competence_level', 'status', 'email', 'format'];
    final parts = <String>[];
    for (final k in interesting) {
      if (v.containsKey(k) && v[k] != null && v[k].toString().isNotEmpty) {
        parts.add('${_label(k)}: ${v[k]}');
      }
    }
    return parts.isEmpty ? v.values.first.toString() : parts.join(' · ');
  }

  static String _label(String k) => switch (k) {
        'display_name'     => 'Name',
        'service_order'    => 'Role',
        'competence_level' => 'Level',
        'status'           => 'Status',
        'format'           => 'Format',
        'title'            => 'Title',
        _                  => k,
      };
}

// ── Providers ─────────────────────────────────────────────────────────────────

final conflictsProvider = FutureProvider<List<ConflictEntry>>((ref) async {
  final db = await ref.watch(dbProvider.future);
  final rows = await db.rawQuery(
    'SELECT id, entity_type, entity_id, local_version, cloud_version, created_at '
    'FROM conflict_queue WHERE resolved_at IS NULL ORDER BY created_at ASC',
  );
  return rows.map(ConflictEntry.fromMap).toList();
});

// Expose the SyncStateNotifier's triggerSync through a provider so widgets
// only need to watch syncStateProvider — they don't need to read SyncEngine directly.
final syncActionProvider = Provider<SyncStateNotifier>((ref) {
  return ref.read(syncStateProvider.notifier);
});
