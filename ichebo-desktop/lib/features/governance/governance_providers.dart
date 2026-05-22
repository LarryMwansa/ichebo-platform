import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/database/db.dart';
import '../../core/database/schema.dart';

// ── GovernanceRecord ──────────────────────────────────────────────────────────

class GovernanceRecord {
  const GovernanceRecord({
    required this.id,
    required this.recordClass,
    required this.recordFamily,
    required this.recordType,
    required this.title,
    required this.status,
    this.body,
    this.updatedAt,
  });

  final String id;
  final String recordClass;
  final String recordFamily;
  final String recordType;
  final String title;
  final String status;
  final String? body;
  final String? updatedAt;

  factory GovernanceRecord.fromMap(Map<String, dynamic> m) {
    String? body;
    final raw = m['metadata'];
    if (raw != null && raw.toString().isNotEmpty) {
      try {
        final decoded = jsonDecode(raw as String) as Map<String, dynamic>;
        body = decoded['body'] as String?;
      } catch (_) {}
    }
    return GovernanceRecord(
      id:          m[cId] as String,
      recordClass: m[cRecordClass] as String? ?? '',
      recordFamily:m[cRecordFamily] as String? ?? '',
      recordType:  m[cRecordType] as String? ?? '',
      title:       m[cTitle] as String? ?? '(Untitled)',
      status:      m[cStatus] as String? ?? 'active',
      body:        body,
      updatedAt:   m[cUpdatedAt] as String?,
    );
  }

  // Human-readable label for the record_type
  String get typeLabel {
    final words = recordType.replaceAll('_', ' ').split(' ');
    return words.map((w) => w.isEmpty ? '' : '${w[0].toUpperCase()}${w.substring(1)}').join(' ');
  }
}

// ── Providers ─────────────────────────────────────────────────────────────────

// All governance-class records, ordered by family then title
final governanceRecordsProvider = FutureProvider<List<GovernanceRecord>>((ref) async {
  final db = await ref.watch(dbProvider.future);
  final rows = await db.rawQuery(
    "SELECT id, record_class, record_family, record_type, title, status, "
    "       metadata, updated_at "
    "FROM records "
    "WHERE record_class = 'governance' AND (deleted_at IS NULL OR deleted_at = '') "
    "ORDER BY record_family ASC, title ASC",
  );
  return rows.map(GovernanceRecord.fromMap).toList();
});

// Selected record ID for the detail pane
final selectedGovernanceIdProvider = StateProvider<String?>((ref) => null);

// Single record by ID
final governanceByIdProvider =
    FutureProvider.family<GovernanceRecord?, String>((ref, id) async {
  final db = await ref.watch(dbProvider.future);
  final rows = await db.rawQuery(
    "SELECT id, record_class, record_family, record_type, title, status, "
    "       metadata, updated_at "
    "FROM records WHERE id = ?",
    [id],
  );
  if (rows.isEmpty) return null;
  return GovernanceRecord.fromMap(rows.first);
});

// Grouped by record_family
final governanceByFamilyProvider =
    Provider<Map<String, List<GovernanceRecord>>>((ref) {
  final async = ref.watch(governanceRecordsProvider);
  return async.maybeWhen(
    data: (records) {
      final map = <String, List<GovernanceRecord>>{};
      for (final r in records) {
        map.putIfAbsent(r.recordFamily, () => []).add(r);
      }
      return map;
    },
    orElse: () => {},
  );
});

// Search query
final governanceSearchProvider = StateProvider<String>((ref) => '');

// Filtered flat list
final filteredGovernanceProvider = Provider<AsyncValue<List<GovernanceRecord>>>((ref) {
  final search = ref.watch(governanceSearchProvider).toLowerCase();
  return ref.watch(governanceRecordsProvider).whenData((records) {
    if (search.isEmpty) return records;
    return records
        .where((r) =>
            r.title.toLowerCase().contains(search) ||
            r.recordType.toLowerCase().contains(search) ||
            r.recordFamily.toLowerCase().contains(search))
        .toList();
  });
});
