import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/tokens.dart';
import 'member_detail.dart';
import 'member_list.dart';
import 'people_providers.dart';

class PeopleScreen extends ConsumerWidget {
  const PeopleScreen({super.key});

  static const _listPanelWidth = 360.0;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedId = ref.watch(selectedMemberIdProvider);
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final canvasWidth = MediaQuery.of(context).size.width;

    // Narrow canvas: show list OR detail (back button to return to list)
    if (canvasWidth < 700) {
      return _NarrowLayout(selectedId: selectedId, isDark: isDark);
    }

    return Row(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Left: member list panel
        SizedBox(
          width: _listPanelWidth,
          child: Container(
            decoration: BoxDecoration(
              border: Border(
                right: BorderSide(color: isDark ? IcsColors.borderDark : IcsColors.borderLight),
              ),
            ),
            child: const MemberList(),
          ),
        ),
        // Right: detail panel or empty state
        Expanded(
          child: selectedId != null
              ? MemberDetail(memberId: selectedId)
              : _EmptyState(isDark: isDark),
        ),
      ],
    );
  }
}

// ── Narrow layout (< 700px canvas) ───────────────────────────────────────────

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
          // Back bar
          Container(
            height: 44,
            padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.s),
            decoration: BoxDecoration(
              border: Border(bottom: BorderSide(color: isDark ? IcsColors.borderDark : IcsColors.borderLight)),
            ),
            child: Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.arrow_back, size: 18),
                  onPressed: () => ref.read(selectedMemberIdProvider.notifier).state = null,
                  color: isDark ? Colors.white : IcsColors.inkBg,
                ),
                Text(
                  'Members',
                  style: TextStyle(fontSize: 13, color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted),
                ),
              ],
            ),
          ),
          Expanded(child: MemberDetail(memberId: selectedId!)),
        ],
      );
    }
    return const MemberList();
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
            Icons.person_outline,
            size: 48,
            color: isDark ? IcsColors.borderDark : IcsColors.borderLight,
          ),
          const SizedBox(height: IcsSpacing.m),
          Text(
            'Select a member',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w500,
              color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
            ),
          ),
          const SizedBox(height: IcsSpacing.xs),
          Text(
            'Choose from the list to view their profile.',
            style: TextStyle(
              fontSize: 12,
              color: (isDark ? IcsColors.textMutedDark : IcsColors.textMuted).withValues(alpha: 0.6),
            ),
          ),
        ],
      ),
    );
  }
}
