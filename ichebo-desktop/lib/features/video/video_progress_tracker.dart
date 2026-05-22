import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/database/db.dart';

// VideoProgressTracker fires milestone Activity progress updates at 25/50/75/100%.
// Each milestone fires exactly once per tracker instance (idempotent via _firedMilestones).
//
// This writes directly to the activities table — the Go sync engine will pick up the
// change on next sync and propagate it to the server via the ChangeLog.
class VideoProgressTracker {
  VideoProgressTracker({
    required this.ref,
    required this.activityId,
    required this.videoRecordId,
    required this.totalSeconds,
  });

  final WidgetRef ref;
  final String activityId;
  final String videoRecordId;
  final int totalSeconds;

  final Set<int> _firedMilestones = {};

  Future<void> onProgress(int watchedSeconds) async {
    if (totalSeconds <= 0) return;
    final pct = (watchedSeconds / totalSeconds * 100).round().clamp(0, 100);

    for (final milestone in [25, 50, 75, 100]) {
      if (pct >= milestone && !_firedMilestones.contains(milestone)) {
        _firedMilestones.add(milestone);
        await _emitMilestone(milestone, watchedSeconds);
      }
    }
  }

  Future<void> _emitMilestone(int milestone, int watchedSeconds) async {
    final db = await ref.read(dbProvider.future);

    // Update the activity's progress field and metadata in SQLite.
    // The sync engine will detect the update via updated_at and sync it upstream.
    final now = DateTime.now().toUtc().toIso8601String();
    await db.update(
      'activities',
      {
        'progress': milestone,
        'status': milestone == 100 ? 'completed' : 'in_progress',
        if (milestone == 100) 'completed_at': now,
        'updated_at': now,
        // Store watcher metadata as a metadata JSON merge — the sync engine
        // treats metadata as an opaque JSON column, no schema change needed.
      },
      where: 'id = ?',
      whereArgs: [activityId],
    );
  }
}
