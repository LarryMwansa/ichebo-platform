import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';

import '../tokens/tokens.dart';

class ChapterMarker {
  const ChapterMarker({required this.timestampSeconds, required this.title});
  final int timestampSeconds;
  final String title;

  factory ChapterMarker.fromJson(Map<String, dynamic> j) => ChapterMarker(
        timestampSeconds: j['timestamp_seconds'] as int,
        title: j['title'] as String,
      );
}

class ChapterNavigator extends StatelessWidget {
  const ChapterNavigator({
    super.key,
    required this.chapters,
    required this.controller,
    required this.currentPositionSeconds,
  });

  final List<ChapterMarker> chapters;
  final VideoPlayerController controller;
  final int currentPositionSeconds;

  bool _isActive(int i) {
    final start = chapters[i].timestampSeconds;
    final end = i + 1 < chapters.length ? chapters[i + 1].timestampSeconds : null;
    if (currentPositionSeconds < start) return false;
    if (end != null && currentPositionSeconds >= end) return false;
    return true;
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 36,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: IcheboSpacing.xs),
        itemCount: chapters.length,
        separatorBuilder: (_, _) => const SizedBox(width: IcheboSpacing.xs3),
        itemBuilder: (context, i) {
          final active = _isActive(i);
          return GestureDetector(
            onTap: () => controller.seekTo(
              Duration(seconds: chapters[i].timestampSeconds),
            ),
            child: Container(
              padding: const EdgeInsets.symmetric(
                horizontal: IcheboSpacing.xs,
                vertical: 6,
              ),
              decoration: BoxDecoration(
                color: active
                    ? IcheboColors.primaryLight
                    : Theme.of(context).colorScheme.surfaceContainerHighest,
                borderRadius: IcheboRadius.pill,
                border: Border.all(
                  color: active ? IcheboColors.primary : Colors.transparent,
                ),
              ),
              child: Text(
                chapters[i].title,
                style: IcheboTextStyles.bodySmall.copyWith(
                  color: active ? IcheboColors.primary : IcheboColors.muted,
                  fontSize: 11,
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
