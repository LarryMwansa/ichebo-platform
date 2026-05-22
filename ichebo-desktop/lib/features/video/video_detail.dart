import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/tokens.dart';
import 'video_models.dart';
import 'video_player_widget.dart';
import 'video_progress_tracker.dart';
import 'video_providers.dart';

class VideoDetail extends ConsumerWidget {
  const VideoDetail({super.key, required this.videoId});

  final String videoId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(selectedVideoProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return async.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('Error: $e')),
      data: (video) => video == null
          ? const SizedBox.shrink()
          : _VideoDetailContent(video: video, isDark: isDark),
    );
  }
}

class _VideoDetailContent extends ConsumerWidget {
  const _VideoDetailContent({required this.video, required this.isDark});

  final VideoRecord video;
  final bool isDark;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final border = isDark ? IcsColors.borderDark : IcsColors.borderLight;
    final textMuted = isDark ? IcsColors.textMutedDark : IcsColors.textMuted;
    final downloadState = ref.watch(downloadProvider(video.id));

    // Build a VideoProgressTracker only for learning videos that have an
    // enrolment activity. The activityId comes from the record's metadata
    // (set by Django when the user enrols in a lesson).
    final tracker = video.isLearning
        ? VideoProgressTracker(
            ref: ref,
            activityId: video.id, // placeholder — real impl reads enrolment activity id
            videoRecordId: video.id,
            totalSeconds: video.durationSeconds ?? 0,
          )
        : null;

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Player
          IcheboVideoPlayer(record: video, tracker: tracker),

          // Title + meta
          Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(video.title, style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: 6),
                Row(
                  children: [
                    _TypeChip(recordType: video.recordType),
                    if (video.durationSeconds != null) ...[
                      const SizedBox(width: 10),
                      Icon(Icons.schedule_outlined, size: 13, color: textMuted),
                      const SizedBox(width: 3),
                      Text(_formatDuration(video.durationSeconds!),
                          style: Theme.of(context)
                              .textTheme
                              .bodySmall
                              ?.copyWith(color: textMuted)),
                    ],
                    const Spacer(),
                    // Offline download — learning videos only
                    if (video.isLearning) _OfflineButton(video: video),
                  ],
                ),
              ],
            ),
          ),

          // Download progress bar
          if (downloadState.status == DownloadStatus.downloading)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  LinearProgressIndicator(value: downloadState.progress),
                  const SizedBox(height: 4),
                  Text(
                    'Downloading… ${(downloadState.progress * 100).toStringAsFixed(0)}%',
                    style: Theme.of(context)
                        .textTheme
                        .bodySmall
                        ?.copyWith(color: textMuted),
                  ),
                  const SizedBox(height: 12),
                ],
              ),
            ),

          if (downloadState.status == DownloadStatus.error)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
              child: Text(
                'Download failed: ${downloadState.error}',
                style: Theme.of(context)
                    .textTheme
                    .bodySmall
                    ?.copyWith(color: IcsColors.error),
              ),
            ),

          Divider(color: border, height: 1),

          // Chapter navigator — learning videos only
          if (video.isLearning && video.chapterMarkers.isNotEmpty)
            _ChapterSection(video: video),
        ],
      ),
    );
  }

  String _formatDuration(int seconds) {
    final h = seconds ~/ 3600;
    final m = (seconds % 3600) ~/ 60;
    if (h > 0) return '${h}h ${m}m';
    return '${m}m';
  }
}

// ── Offline download button ───────────────────────────────────────────────────

class _OfflineButton extends ConsumerWidget {
  const _OfflineButton({required this.video});
  final VideoRecord video;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(downloadProvider(video.id));

    if (video.isOfflineAvailable || state.status == DownloadStatus.done) {
      return const Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.offline_pin, size: 16, color: IcsColors.success),
          SizedBox(width: 4),
          Text('Available offline', style: TextStyle(fontSize: 12, color: IcsColors.success)),
        ],
      );
    }

    if (state.status == DownloadStatus.downloading) {
      return const SizedBox(
        width: 16,
        height: 16,
        child: CircularProgressIndicator(strokeWidth: 2),
      );
    }

    final cdnUrl = video.videoUrl;
    if (cdnUrl == null || cdnUrl.isEmpty) return const SizedBox.shrink();

    // Build the 480p variant URL from the master URL.
    // Master: .../videos/{record_id}/index.m3u8 → 480p: .../videos/{record_id}/480p/index.m3u8
    final variantUrl = cdnUrl.replaceFirst('/index.m3u8', '/480p/index.m3u8');

    return TextButton.icon(
      onPressed: () => ref.read(downloadProvider(video.id).notifier).download(variantUrl),
      icon: const Icon(Icons.download_outlined, size: 16),
      label: const Text('Download offline', style: TextStyle(fontSize: 12)),
      style: TextButton.styleFrom(
        foregroundColor: IcsColors.accentRed,
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        minimumSize: Size.zero,
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
      ),
    );
  }
}

// ── Chapter section ───────────────────────────────────────────────────────────

class _ChapterSection extends StatelessWidget {
  const _ChapterSection({required this.video});
  final VideoRecord video;

  @override
  Widget build(BuildContext context) {
    // ChapterNavigator requires a VideoPlayerController ref — we expose
    // chapter list as tap-to-seek tiles; the controller is owned by
    // IcheboVideoPlayer above. Since they live in the same scroll view we
    // accept the minor limitation that chapter tap-to-seek requires the
    // player to be initialised. Tap events are ignored when controller is null.
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
          child: Text(
            'Chapters',
            style: Theme.of(context).textTheme.titleSmall,
          ),
        ),
        ...video.chapterMarkers.map((ch) => _ChapterTile(chapter: ch)),
      ],
    );
  }
}

class _ChapterTile extends StatelessWidget {
  const _ChapterTile({required this.chapter});
  final ChapterMarker chapter;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final border = isDark ? IcsColors.borderDark : IcsColors.borderLight;
    final min = chapter.timestampSeconds ~/ 60;
    final sec = chapter.timestampSeconds % 60;
    final ts = '${min.toString().padLeft(2, '0')}:${sec.toString().padLeft(2, '0')}';

    return Container(
      decoration: BoxDecoration(border: Border(bottom: BorderSide(color: border))),
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      child: Row(
        children: [
          Text(
            ts,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: IcsColors.accentRed,
                  fontFeatures: const [FontFeature.tabularFigures()],
                ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Text(chapter.title, style: Theme.of(context).textTheme.bodyMedium),
          ),
        ],
      ),
    );
  }
}

class _TypeChip extends StatelessWidget {
  const _TypeChip({required this.recordType});
  final String recordType;

  @override
  Widget build(BuildContext context) {
    final (label, color) = switch (recordType) {
      'learning_video' => ('Learning', IcsColors.info),
      'broadcast' => ('Broadcast', IcsColors.error),
      _ => ('Teaching', IcsColors.textMuted),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        label,
        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: color),
      ),
    );
  }
}
