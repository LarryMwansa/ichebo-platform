import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/tokens.dart';
import 'video_models.dart';
import 'video_providers.dart';

class VideoLibrary extends ConsumerWidget {
  const VideoLibrary({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(videoLibraryProvider);
    final selectedId = ref.watch(selectedVideoIdProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _Header(isDark: isDark),
        Expanded(
          child: async.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => Center(child: Text('Error: $e')),
            data: (videos) => videos.isEmpty
                ? _EmptyLibrary(isDark: isDark)
                : ListView.builder(
                    itemCount: videos.length,
                    itemBuilder: (context, i) => _VideoTile(
                      video: videos[i],
                      isSelected: videos[i].id == selectedId,
                      isDark: isDark,
                      onTap: () => ref.read(selectedVideoIdProvider.notifier).state = videos[i].id,
                    ),
                  ),
          ),
        ),
      ],
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.isDark});
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    final border = isDark ? IcsColors.borderDark : IcsColors.borderLight;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: border)),
      ),
      child: Text(
        'Library',
        style: Theme.of(context).textTheme.titleMedium,
      ),
    );
  }
}

class _VideoTile extends StatelessWidget {
  const _VideoTile({
    required this.video,
    required this.isSelected,
    required this.isDark,
    required this.onTap,
  });

  final VideoRecord video;
  final bool isSelected;
  final bool isDark;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final border = isDark ? IcsColors.borderDark : IcsColors.borderLight;
    final bg = isSelected
        ? (isDark ? IcsColors.accentRedAlpha15 : IcsColors.accentRedAlpha5)
        : Colors.transparent;

    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: bg,
          border: Border(bottom: BorderSide(color: border)),
        ),
        child: Row(
          children: [
            _TypeBadge(recordType: video.recordType),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    video.title,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                        ),
                  ),
                  if (video.durationSeconds != null) ...[
                    const SizedBox(height: 2),
                    Text(
                      _formatDuration(video.durationSeconds!),
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
                          ),
                    ),
                  ],
                ],
              ),
            ),
            if (video.isOfflineAvailable)
              Padding(
                padding: const EdgeInsets.only(left: 6),
                child: Icon(
                  Icons.offline_pin_outlined,
                  size: 14,
                  color: IcsColors.success,
                ),
              ),
          ],
        ),
      ),
    );
  }

  String _formatDuration(int seconds) {
    final h = seconds ~/ 3600;
    final m = (seconds % 3600) ~/ 60;
    final s = seconds % 60;
    if (h > 0) return '${h}h ${m}m';
    if (m > 0) return '${m}m ${s}s';
    return '${s}s';
  }
}

class _TypeBadge extends StatelessWidget {
  const _TypeBadge({required this.recordType});
  final String recordType;

  @override
  Widget build(BuildContext context) {
    final (label, color) = switch (recordType) {
      'learning_video' => ('Learn', IcsColors.info),
      'broadcast' => ('Live', IcsColors.error),
      _ => ('Video', IcsColors.textMuted),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(3),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w600,
          color: color,
          letterSpacing: 0.4,
        ),
      ),
    );
  }
}

class _EmptyLibrary extends StatelessWidget {
  const _EmptyLibrary({required this.isDark});
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Text(
        'No videos yet.',
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
            ),
      ),
    );
  }
}
