import 'package:flutter/foundation.dart';

import '../../core/api/api_client.dart';

/// Fires progress milestone PATCHes to activities/{activityId}/ at 25/50/75/100%.
/// Each milestone fires exactly once per player session.
class VideoProgressTracker {
  VideoProgressTracker({
    required this.activityId,
    required this.videoRecordId,
    required this.totalSeconds,
    required this.apiClient,
    this.onComplete,
  });

  final String activityId;
  final String videoRecordId;
  final int totalSeconds;
  final ApiClient apiClient;
  final VoidCallback? onComplete;

  final Set<int> _firedMilestones = {};

  static const _milestones = [25, 50, 75, 100];

  void onProgress(int watchedSeconds) {
    if (totalSeconds <= 0) return;
    final pct = (watchedSeconds * 100) ~/ totalSeconds;

    for (final milestone in _milestones) {
      if (pct >= milestone && !_firedMilestones.contains(milestone)) {
        _firedMilestones.add(milestone);
        _report(milestone, watchedSeconds);
        if (milestone == 100) onComplete?.call();
      }
    }
  }

  Future<void> _report(int progress, int watchedSeconds) async {
    try {
      await apiClient.patch<void>(
        'activities/$activityId/',
        data: {
          'progress': progress,
          'metadata': {
            'source_app': 'learn',
            'video_record_id': videoRecordId,
            'watched_seconds': watchedSeconds,
            'total_seconds': totalSeconds,
          },
        },
      );
    } catch (_) {
      // Progress reporting is best-effort — never surface to user.
    }
  }
}
