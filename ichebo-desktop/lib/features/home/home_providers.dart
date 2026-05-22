import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/database/db.dart';
import '../../sync/sync_state.dart';

// ── Upcoming gatherings (next 3 scheduled, activity_type='gathering') ─────────

class UpcomingGathering {
  const UpcomingGathering({
    required this.id,
    required this.title,
    required this.scheduledAt,
    this.attendanceCount = 0,
  });
  final String id;
  final String title;
  final String scheduledAt;
  final int attendanceCount;
}

final upcomingGatheringsProvider = FutureProvider<List<UpcomingGathering>>((ref) async {
  final db  = await ref.watch(dbProvider.future);
  final now = DateTime.now().toIso8601String();
  final rows = await db.rawQuery(
    "SELECT a.id, a.title, a.scheduled_at, "
    "       (SELECT COUNT(*) FROM activity_log l "
    "        WHERE l.activity_id = a.id AND l.to_status = 'attendance') AS att "
    "FROM activities a "
    "WHERE a.activity_type = 'gathering' "
    "  AND a.status != 'cancelled' "
    "  AND a.scheduled_at >= ? "
    "  AND (a.deleted_at IS NULL OR a.deleted_at = '') "
    "ORDER BY a.scheduled_at ASC LIMIT 3",
    [now],
  );
  return rows.map((m) => UpcomingGathering(
    id:             m['id'] as String,
    title:          m['title'] as String? ?? '(Untitled)',
    scheduledAt:    m['scheduled_at'] as String? ?? '',
    attendanceCount: (m['att'] as int?) ?? 0,
  )).toList();
});

// ── Recent activity log (last 5 events across all activities) ─────────────────

class RecentEvent {
  const RecentEvent({
    required this.activityTitle,
    required this.toStatus,
    required this.changedAt,
    this.note,
  });
  final String activityTitle;
  final String toStatus;
  final String changedAt;
  final String? note;
}

final recentEventsProvider = FutureProvider<List<RecentEvent>>((ref) async {
  final db = await ref.watch(dbProvider.future);
  final rows = await db.rawQuery(
    "SELECT a.title, l.to_status, l.changed_at, l.note "
    "FROM activity_log l "
    "JOIN activities a ON a.id = l.activity_id "
    "WHERE l.to_status != 'attendance' "
    "ORDER BY l.changed_at DESC LIMIT 5",
  );
  return rows.map((m) => RecentEvent(
    activityTitle: m['title'] as String? ?? '(Untitled)',
    toStatus:      m['to_status'] as String? ?? '',
    changedAt:     m['changed_at'] as String? ?? '',
    note:          m['note'] as String?,
  )).toList();
});

// ── Community snapshot ────────────────────────────────────────────────────────

class CommunitySnapshot {
  const CommunitySnapshot({
    required this.totalMembers,
    required this.activeThisMonth,
    required this.formationInProgress,
  });
  final int totalMembers;
  final int activeThisMonth;
  final int formationInProgress;
}

final communitySnapshotProvider = FutureProvider<CommunitySnapshot>((ref) async {
  final db = await ref.watch(dbProvider.future);

  final totalRow = await db.rawQuery(
    "SELECT COUNT(*) AS c FROM members "
    "WHERE is_active = 1 AND (deleted_at IS NULL OR deleted_at = '')",
  );
  final total = (totalRow.first['c'] as int?) ?? 0;

  final monthStart = DateTime.now()
      .copyWith(day: 1, hour: 0, minute: 0, second: 0, millisecond: 0)
      .toIso8601String();
  final activeRow = await db.rawQuery(
    "SELECT COUNT(DISTINCT l.changed_by) AS c "
    "FROM activity_log l WHERE l.changed_at >= ?",
    [monthStart],
  );
  final active = (activeRow.first['c'] as int?) ?? 0;

  final formationRow = await db.rawQuery(
    "SELECT COUNT(*) AS c FROM members "
    "WHERE competence_level BETWEEN 1 AND 4 "
    "  AND is_active = 1 "
    "  AND (deleted_at IS NULL OR deleted_at = '')",
  );
  final formation = (formationRow.first['c'] as int?) ?? 0;

  return CommunitySnapshot(
    totalMembers: total,
    activeThisMonth: active,
    formationInProgress: formation,
  );
});

// Re-export sync state for Home to use without extra import
final homeSyncStatusProvider = Provider((ref) => ref.watch(syncStateProvider));
