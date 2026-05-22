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
    this.scheduledAt,
    this.dueAt,
    this.completedAt,
    required this.metadata,
    required this.createdBy,
    required this.createdAt,
    required this.updatedAt,
  });

  final String id;
  final String tenantId;
  final String activityType;
  final String title;
  final String description;
  final String status;
  final int progress;
  final String? assignedTo;
  final String? linkedRecordId;
  final String? scheduledAt;
  final String? dueAt;
  final String? completedAt;
  final String metadata; // JSON — includes location, duration_minutes, format etc.
  final String createdBy;
  final String createdAt;
  final String updatedAt;

  factory ActivityModel.fromMap(Map<String, dynamic> m) => ActivityModel(
        id: m[cId] as String,
        tenantId: m[cTenantId] as String,
        activityType: m[cActivityType] as String? ?? 'task',
        title: m[cTitle] as String? ?? '',
        description: m[cDescription] as String? ?? '',
        status: m[cStatus] as String? ?? 'pending',
        progress: m[cProgress] as int? ?? 0,
        assignedTo: m[cAssignedTo] as String?,
        linkedRecordId: m[cLinkedRecordId] as String?,
        scheduledAt: m[cScheduledAt] as String?,
        dueAt: m[cDueAt] as String?,
        completedAt: m[cCompletedAt] as String?,
        metadata: m[cMetadata] as String? ?? '{}',
        createdBy: m[cCreatedBy] as String,
        createdAt: m[cCreatedAt] as String,
        updatedAt: m[cUpdatedAt] as String,
      );

  // Convenience: parse metadata JSON once.
  Map<String, dynamic> get metadataMap {
    try {
      return jsonDecode(metadata) as Map<String, dynamic>;
    } catch (_) {
      return {};
    }
  }

  String? get location => metadataMap['location'] as String?;
  String? get format => metadataMap['format'] as String?;
  int? get durationMinutes => metadataMap['duration_minutes'] as int?;

  // Attendance count: number of activity_log rows with to_status='attendance'.
  // Stored separately via attendanceCountProvider.

  ActivityModel copyWith({
    String? title,
    String? description,
    String? status,
    int? progress,
    String? assignedTo,
    String? scheduledAt,
    String? dueAt,
    String? completedAt,
    String? metadata,
  }) {
    return ActivityModel(
      id: id,
      tenantId: tenantId,
      activityType: activityType,
      title: title ?? this.title,
      description: description ?? this.description,
      status: status ?? this.status,
      progress: progress ?? this.progress,
      assignedTo: assignedTo ?? this.assignedTo,
      linkedRecordId: linkedRecordId,
      scheduledAt: scheduledAt ?? this.scheduledAt,
      dueAt: dueAt ?? this.dueAt,
      completedAt: completedAt ?? this.completedAt,
      metadata: metadata ?? this.metadata,
      createdBy: createdBy,
      createdAt: createdAt,
      updatedAt: updatedAt,
    );
  }
}

// ── Raw list from SQLite ──────────────────────────────────────────────────────

final activitiesProvider = FutureProvider<List<ActivityModel>>((ref) async {
  final db = await ref.watch(dbProvider.future);
  final prefs = await SharedPreferences.getInstance();
  final tenantId = prefs.getString('ics_tenant_id') ?? '';

  final rows = await db.query(
    tActivities,
    where: '$cTenantId = ? AND $cDeletedAt IS NULL',
    whereArgs: [tenantId],
    orderBy: 'COALESCE($cScheduledAt, $cCreatedAt) DESC',
  );
  return rows.map(ActivityModel.fromMap).toList();
});

// ── Single activity ───────────────────────────────────────────────────────────

final activityByIdProvider =
    FutureProvider.family<ActivityModel?, String>((ref, id) async {
  final db = await ref.watch(dbProvider.future);
  final rows = await db.query(
    tActivities,
    where: '$cId = ?',
    whereArgs: [id],
    limit: 1,
  );
  if (rows.isEmpty) return null;
  return ActivityModel.fromMap(rows.first);
});

// ── Attendance count for a gathering ─────────────────────────────────────────

final attendanceCountProvider =
    FutureProvider.family<int, String>((ref, activityId) async {
  final db = await ref.watch(dbProvider.future);
  final rows = await db.query(
    tActivityLog,
    columns: ['COUNT(*) as cnt'],
    where: '$cActivityId = ? AND $cToStatus = ?',
    whereArgs: [activityId, 'attendance'],
  );
  return (rows.first['cnt'] as int?) ?? 0;
});

// ── Attendance member IDs for a gathering (for pre-populating the flow) ───────

final attendanceMembersProvider =
    FutureProvider.family<Set<String>, String>((ref, activityId) async {
  final db = await ref.watch(dbProvider.future);
  final rows = await db.query(
    tActivityLog,
    columns: [cNote],
    where: '$cActivityId = ? AND $cToStatus = ?',
    whereArgs: [activityId, 'attendance'],
  );
  return rows.map((r) => r[cNote] as String).toSet();
});

// ── Search + filter state ─────────────────────────────────────────────────────

final activitySearchProvider = StateProvider<String>((_) => '');
final activityFilterTypeProvider = StateProvider<String?>((_) => null);
final selectedActivityIdProvider = StateProvider<String?>((_) => null);

// ── Derived filtered list ─────────────────────────────────────────────────────

final filteredActivitiesProvider =
    Provider<AsyncValue<List<ActivityModel>>>((ref) {
  final all = ref.watch(activitiesProvider);
  final query = ref.watch(activitySearchProvider).toLowerCase();
  final typeFilter = ref.watch(activityFilterTypeProvider);

  return all.whenData((list) {
    return list.where((a) {
      if (query.isNotEmpty && !a.title.toLowerCase().contains(query)) {
        return false;
      }
      if (typeFilter != null && a.activityType != typeFilter) {
        return false;
      }
      return true;
    }).toList();
  });
});
