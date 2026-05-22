import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/tokens.dart';
import 'activity_detail.dart';
import 'activity_list.dart';
import 'activity_providers.dart';

class ActivityScreen extends ConsumerWidget {
  const ActivityScreen({super.key});

  static const _listPanelWidth = 380.0;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedId  = ref.watch(selectedActivityIdProvider);
    final isDark      = Theme.of(context).brightness == Brightness.dark;
    final canvasWidth = MediaQuery.of(context).size.width;

    if (canvasWidth < 700) {
      return _NarrowLayout(selectedId: selectedId, isDark: isDark);
    }

    return Row(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SizedBox(
          width: _listPanelWidth,
          child: Container(
            decoration: BoxDecoration(
              border: Border(
                right: BorderSide(
                  color: isDark ? IcsColors.borderDark : IcsColors.borderLight,
                ),
              ),
            ),
            child: const ActivityList(),
          ),
        ),
        Expanded(
          child: selectedId != null
              ? ActivityDetail(activityId: selectedId)
              : _EmptyState(isDark: isDark),
        ),
      ],
    );
  }
}

// ── Narrow layout ─────────────────────────────────────────────────────────────

class _NarrowLayout extends ConsumerWidget {
  const _NarrowLayout({required this.selectedId, required this.isDark});
  final String? selectedId;
  final bool isDark;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (selectedId != null) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            height: 44,
            padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.s),
            decoration: BoxDecoration(
              border: Border(
                bottom: BorderSide(
                  color: isDark ? IcsColors.borderDark : IcsColors.borderLight,
                ),
              ),
            ),
            child: Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.arrow_back, size: 18),
                  onPressed: () =>
                      ref.read(selectedActivityIdProvider.notifier).state = null,
                  color: isDark ? Colors.white : IcsColors.inkBg,
                ),
                Text(
                  'Activities',
                  style: TextStyle(
                    fontSize: 13,
                    color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
                  ),
                ),
              ],
            ),
          ),
          Expanded(child: ActivityDetail(activityId: selectedId!)),
        ],
      );
    }
    return const ActivityList();
  }
}

// ── Empty state ───────────────────────────────────────────────────────────────

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
            Icons.event_note_outlined,
            size: 48,
            color: isDark ? IcsColors.borderDark : IcsColors.borderLight,
          ),
          const SizedBox(height: IcsSpacing.m),
          Text(
            'Select an activity',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w500,
              color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
            ),
          ),
          const SizedBox(height: IcsSpacing.xs),
          Text(
            'Choose from the list to view details.',
            style: TextStyle(
              fontSize: 12,
              color: (isDark ? IcsColors.textMutedDark : IcsColors.textMuted)
                  .withValues(alpha: 0.6),
            ),
          ),
        ],
      ),
    );
  }
}
