import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/database/db.dart';
import '../../core/database/schema.dart';
import '../../sync/sync_state.dart';

// ── Upcoming gatherings (next 3) ──────────────────────────────────────────────

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
  final int    attendanceCount;
}

final upcomingGatheringsProvider = FutureProvider<List<UpcomingGathering>>((ref) async {
  final db  = await ref.watch(dbProvider.future);
  final now = DateTime.now().toIso8601String();
  final rows = await db.rawQuery(
    'SELECT a.id, a.title, a.scheduled_at, '
    '       (SELECT COUNT(*) FROM $tActivityLog l '
    '        WHERE l.$cActivityId = a.$cId AND l.$cToStatus = \'attendance\') AS att '
    'FROM $tActivities a '
    'WHERE a.$cActivityType = \'gathering\' '
    '  AND a.$cStatus != \'cancelled\' '
    '  AND a.$cScheduledAt >= ? '
    '  AND (a.$cDeletedAt IS NULL OR a.$cDeletedAt = \'\') '
    'ORDER BY a.$cScheduledAt ASC LIMIT 3',
    [now],
  );
  return rows.map((m) => UpcomingGathering(
    id:             m[cId]          as String,
    title:          m[cTitle]       as String? ?? '(Untitled)',
    scheduledAt:    m[cScheduledAt] as String? ?? '',
    attendanceCount: (m['att']      as int?)   ?? 0,
  )).toList();
});

// ── Recent activity log (last 5 events) ──────────────────────────────────────

class RecentEvent {
  const RecentEvent({
    required this.activityTitle,
    required this.toStatus,
    required this.changedAt,
    this.note,
  });
  final String  activityTitle;
  final String  toStatus;
  final String  changedAt;
  final String? note;
}

final recentEventsProvider = FutureProvider<List<RecentEvent>>((ref) async {
  final db = await ref.watch(dbProvider.future);
  final rows = await db.rawQuery(
    'SELECT a.$cTitle, l.$cToStatus, l.$cChangedAt, l.$cNote '
    'FROM $tActivityLog l '
    'JOIN $tActivities a ON a.$cId = l.$cActivityId '
    'WHERE l.$cToStatus != \'attendance\' '
    'ORDER BY l.$cChangedAt DESC LIMIT 5',
  );
  return rows.map((m) => RecentEvent(
    activityTitle: m[cTitle]     as String? ?? '(Untitled)',
    toStatus:      m[cToStatus]  as String? ?? '',
    changedAt:     m[cChangedAt] as String? ?? '',
    note:          m[cNote]      as String?,
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
    'SELECT COUNT(*) AS c FROM $tMembers '
    'WHERE $cIsActive = 1 AND ($cDeletedAt IS NULL OR $cDeletedAt = \'\')',
  );
  final total = (totalRow.first['c'] as int?) ?? 0;

  final monthStart = DateTime.now()
      .copyWith(day: 1, hour: 0, minute: 0, second: 0, millisecond: 0)
      .toIso8601String();
  final activeRow = await db.rawQuery(
    'SELECT COUNT(DISTINCT l.$cChangedBy) AS c '
    'FROM $tActivityLog l WHERE l.$cChangedAt >= ?',
    [monthStart],
  );
  final active = (activeRow.first['c'] as int?) ?? 0;

  final formationRow = await db.rawQuery(
    'SELECT COUNT(*) AS c FROM $tMembers '
    'WHERE $cCompetenceLevel BETWEEN 1 AND 4 '
    '  AND $cIsActive = 1 '
    '  AND ($cDeletedAt IS NULL OR $cDeletedAt = \'\')',
  );
  final formation = (formationRow.first['c'] as int?) ?? 0;

  return CommunitySnapshot(
    totalMembers:       total,
    activeThisMonth:    active,
    formationInProgress: formation,
  );
});

// Re-export sync state — Home reads sync status without an extra import.
final homeSyncStatusProvider = Provider((ref) => ref.watch(syncStateProvider));
