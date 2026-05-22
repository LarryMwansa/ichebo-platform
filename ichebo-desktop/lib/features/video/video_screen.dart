import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/tokens.dart';
import 'video_detail.dart';
import 'video_library.dart';
import 'video_providers.dart';

class VideoScreen extends ConsumerWidget {
  const VideoScreen({super.key});

  static const _listPanelWidth = 360.0;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedId = ref.watch(selectedVideoIdProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final border = isDark ? IcsColors.borderDark : IcsColors.borderLight;

    return Row(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SizedBox(
          width: _listPanelWidth,
          child: Container(
            decoration: BoxDecoration(
              border: Border(right: BorderSide(color: border)),
            ),
            child: const VideoLibrary(),
          ),
        ),
        Expanded(
          child: selectedId != null
              ? VideoDetail(videoId: selectedId)
              : _EmptyState(isDark: isDark),
        ),
      ],
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.isDark});
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.live_tv_outlined,
            size: 48,
            color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.3),
          ),
          const SizedBox(height: 16),
          Text('Video & Broadcast', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 8),
          Text(
            'Select a video from the library.',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
                ),
          ),
        ],
      ),
    );
  }
}
