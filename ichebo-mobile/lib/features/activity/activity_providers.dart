import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/database/db.dart';
import '../../core/database/schema.dart';

// ── ActivityModel ─────────────────────────────────────────────────────────────

class ActivityModel {
  const ActivityModel({
    required this.id,
    required this.tenantId,
    required this.activityType,
    required this.title,
    required this.description,
    required this.status,
    required this.progress,
    this.assignedTo,
    this.linkedRecordId,
    this.parentActivityId,
    this.dueAt,
    this.scheduledAt,
    this.completedAt,
    this.metadataRaw,
    required this.updatedAt,
  });

  final String  id;
  final String  tenantId;
  final String  activityType;
  final String  title;
  final String  description;
  final String  status;
  final int     progress;
  final String? assignedTo;
  final String? linkedRecordId;
  final String? parentActivityId;
  final String? dueAt;
  final String? scheduledAt;
  final String? completedAt;
  final String? metadataRaw;
  final String  updatedAt;

  Map<String, dynamic> get metadataMap {
    if (metadataRaw == null || metadataRaw!.isEmpty) return {};
    try { return jsonDecode(metadataRaw!) as Map<String, dynamic>; }
    catch (_) { return {}; }
  }

  String? get location      => metadataMap['location'] as String?;
  String? get format        => metadataMap['format']   as String?;
  int?    get durationMinutes {
    final v = metadataMap['duration_minutes'];
    if (v is int) return v;
    if (v is String) return int.tryParse(v);
    return null;
  }

  bool get isGathering  => activityType == 'gathering';
  bool get isCompleted  => status == 'completed' || completedAt != null;

  static const _typeLabels = {
    'gathering': 'Gathering',
    'event':     'Event',
    'task':      'Task',
    'campaign':  'Campaign',
    'goal':      'Goal',
    'habit':     'Habit',
  };
  String get typeLabel => _typeLabels[activityType] ?? activityType;

  factory ActivityModel.fromMap(Map<String, dynamic> m) => ActivityModel(
    id:               m[cId]               as String,
    tenantId:         m[cTenantId]         as String? ?? '',
    activityType:     m[cActivityType]     as String? ?? 'task',
    title:            m[cTitle]            as String? ?? '(Untitled)',
    description:      m[cDescription]      as String? ?? '',
    status:           m[cStatus]           as String? ?? 'active',
    progress:         m[cProgress]         as int?    ?? 0,
    assignedTo:       m[cAssignedTo]       as String?,
    linkedRecordId:   m[cLinkedRecordId]   as String?,
    parentActivityId: m[cParentActivityId] as String?,
    dueAt:            m[cDueAt]            as String?,
    scheduledAt:      m[cScheduledAt]      as String?,
    completedAt:      m[cCompletedAt]      as String?,
    metadataRaw:      m[cMetadata]         as String?,
    updatedAt:        m[cUpdatedAt]        as String? ?? '',
  );
}

// ── All activities for this tenant ────────────────────────────────────────────

final activitiesProvider = FutureProvider<List<ActivityModel>>((ref) async {
  final db     = await ref.watch(dbProvider.future);
  final prefs  = await SharedPreferences.getInstance();
  final tenant = prefs.getString('ics_tenant_id') ?? '';

  final rows = await db.query(
    tActivities,
    where:    '$cTenantId = ? AND ($cDeletedAt IS NULL OR $cDeletedAt = \'\')',
    whereArgs: [tenant],
    orderBy:  '$cScheduledAt DESC, $cDueAt DESC, $cUpdatedAt DESC',
  );
  return rows.map(ActivityModel.fromMap).toList();
});

// ── Single activity by id ─────────────────────────────────────────────────────

final activityByIdProvider =
    FutureProvider.family<ActivityModel?, String>((ref, id) async {
  final db   = await ref.watch(dbProvider.future);
  final rows = await db.query(
    tActivities,
    where:    '$cId = ?',
    whereArgs: [id],
    limit:    1,
  );
  if (rows.isEmpty) return null;
  return ActivityModel.fromMap(rows.first);
});

// ── Attendance count for a gathering ─────────────────────────────────────────

final attendanceCountProvider =
    FutureProvider.family<int, String>((ref, activityId) async {
  final db   = await ref.watch(dbProvider.future);
  final rows = await db.rawQuery(
    'SELECT COUNT(*) AS c FROM $tActivityLog '
    'WHERE $cActivityId = ? AND $cToStatus = \'attendance\'',
    [activityId],
  );
  return (rows.first['c'] as int?) ?? 0;
});

// ── Attendance member ids for a gathering ─────────────────────────────────────

final attendanceMemberIdsProvider =
    FutureProvider.family<List<String>, String>((ref, activityId) async {
  final db   = await ref.watch(dbProvider.future);
  final rows = await db.query(
    tActivityLog,
    columns:   [cChangedBy],
    where:     '$cActivityId = ? AND $cToStatus = \'attendance\'',
    whereArgs: [activityId],
    orderBy:   '$cChangedAt ASC',
  );
  return rows.map((r) => r[cChangedBy] as String).toList();
});

// ── Search + filter state ─────────────────────────────────────────────────────

final activitySearchProvider     = StateProvider<String>((_) => '');
final activityFilterTypeProvider = StateProvider<String?>((_) => null);
final selectedActivityIdProvider = StateProvider<String?>((_) => null);

// ── Derived filtered list ─────────────────────────────────────────────────────

final filteredActivitiesProvider =
    Provider<AsyncValue<List<ActivityModel>>>((ref) {
  final all   = ref.watch(activitiesProvider);
  final query = ref.watch(activitySearchProvider).toLowerCase();
  final type  = ref.watch(activityFilterTypeProvider);

  return all.whenData((list) => list.where((a) {
    if (query.isNotEmpty) {
      final hit = a.title.toLowerCase().contains(query) ||
          a.description.toLowerCase().contains(query);
      if (!hit) return false;
    }
    if (type != null && a.activityType != type) return false;
    return true;
  }).toList());
});
