import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/database/db.dart';
import '../../core/database/schema.dart';

// ── GovernanceRecord model ────────────────────────────────────────────────────

class GovernanceRecord {
  const GovernanceRecord({
    required this.id,
    required this.tenantId,
    required this.recordClass,
    required this.recordFamily,
    required this.recordType,
    required this.title,
    required this.status,
    this.metadataRaw,
    this.permissionsRaw,
    required this.updatedAt,
  });

  final String  id;
  final String  tenantId;
  final String  recordClass;
  final String  recordFamily;
  final String  recordType;
  final String  title;
  final String  status;
  final String? metadataRaw;
  final String? permissionsRaw;
  final String  updatedAt;

  Map<String, dynamic> get metadata {
    if (metadataRaw == null || metadataRaw!.isEmpty) return {};
    try { return jsonDecode(metadataRaw!) as Map<String, dynamic>; }
    catch (_) { return {}; }
  }

  String? get summary     => metadata['summary']     as String?;
  String? get effectiveAt => metadata['effective_at'] as String?;

  factory GovernanceRecord.fromMap(Map<String, dynamic> m) => GovernanceRecord(
    id:             m[cId]           as String,
    tenantId:       m[cTenantId]     as String? ?? '',
    recordClass:    m[cRecordClass]  as String? ?? '',
    recordFamily:   m[cRecordFamily] as String? ?? '',
    recordType:     m[cRecordType]   as String? ?? '',
    title:          m[cTitle]        as String? ?? '(Untitled)',
    status:         m[cStatus]       as String? ?? 'active',
    metadataRaw:    m[cMetadata]     as String?,
    permissionsRaw: m[cPermissions]  as String?,
    updatedAt:      m[cUpdatedAt]    as String? ?? '',
  );
}

// ── All governance records for this tenant ────────────────────────────────────

final governanceRecordsProvider =
    FutureProvider<List<GovernanceRecord>>((ref) async {
  final db     = await ref.watch(dbProvider.future);
  final prefs  = await SharedPreferences.getInstance();
  final tenant = prefs.getString('ics_tenant_id') ?? '';

  final rows = await db.query(
    tRecords,
    where:    '$cTenantId = ? AND $cRecordClass = \'governance\' '
              'AND ($cDeletedAt IS NULL OR $cDeletedAt = \'\')',
    whereArgs: [tenant],
    orderBy:  '$cRecordFamily ASC, $cTitle ASC',
  );
  return rows.map(GovernanceRecord.fromMap).toList();
});

// ── Single record by id ───────────────────────────────────────────────────────

final governanceByIdProvider =
    FutureProvider.family<GovernanceRecord?, String>((ref, id) async {
  final db   = await ref.watch(dbProvider.future);
  final rows = await db.query(
    tRecords,
    where:    '$cId = ?',
    whereArgs: [id],
    limit:    1,
  );
  if (rows.isEmpty) return null;
  return GovernanceRecord.fromMap(rows.first);
});

// ── Grouped by family ─────────────────────────────────────────────────────────

final governanceByFamilyProvider =
    Provider<AsyncValue<Map<String, List<GovernanceRecord>>>>((ref) {
  final all    = ref.watch(governanceRecordsProvider);
  final query  = ref.watch(governanceSearchProvider).toLowerCase();

  return all.whenData((list) {
    final filtered = query.isEmpty
        ? list
        : list.where((r) =>
            r.title.toLowerCase().contains(query) ||
            r.recordFamily.toLowerCase().contains(query) ||
            r.recordType.toLowerCase().contains(query)).toList();

    final map = <String, List<GovernanceRecord>>{};
    for (final r in filtered) {
      (map[r.recordFamily] ??= []).add(r);
    }
    return map;
  });
});

// ── Search + selection state ──────────────────────────────────────────────────

final governanceSearchProvider     = StateProvider<String>((_) => '');
final selectedGovernanceIdProvider = StateProvider<String?>((_) => null);
