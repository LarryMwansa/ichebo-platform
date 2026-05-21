import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/state/shell_state.dart';
import '../core/theme/tokens.dart';

class StageTopBar extends ConsumerWidget implements PreferredSizeWidget {
  const StageTopBar({super.key});

  @override
  Size get preferredSize => const Size.fromHeight(IcsDimensions.topBarHeight);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final shell = ref.watch(shellProvider);
    final notifier = ref.read(shellProvider.notifier);
    final isDark = shell.themeMode == ThemeMode.dark;

    final bgColor = isDark ? IcsColors.darkStoneBg : IcsColors.stoneBg;
    final borderColor = isDark ? IcsColors.borderDark : IcsColors.borderLight;
    final textColor = isDark ? IcsColors.textDark : IcsColors.textInk;
    final mutedColor = isDark ? IcsColors.textMutedDark : IcsColors.textMuted;

    return Container(
      height: IcsDimensions.topBarHeight,
      decoration: BoxDecoration(
        color: bgColor,
        border: Border(bottom: BorderSide(color: borderColor, width: 1)),
      ),
      padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.s),
      child: Row(
        children: [
          // ── Left cluster ─────────────────────────────────────────────
          _IconBtn(
            icon: Icons.dock_outlined,
            active: shell.contextOpen,
            onTap: notifier.toggleContext,
            isDark: isDark,
          ),
          const SizedBox(width: IcsSpacing.s),
          // Breadcrumb
          Text(
            shell.activeSection.label,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w500,
              color: mutedColor,
            ),
          ),

          const Spacer(),

          // ── Right cluster ─────────────────────────────────────────────
          // Search trigger
          GestureDetector(
            onTap: () => ref.read(shellProvider.notifier).openCommandPalette(),
            child: Container(
              height: 36,
              width: IcsDimensions.searchBarWidth,
              decoration: BoxDecoration(
                color: isDark ? IcsColors.ink2 : IcsColors.stone2,
                border: Border.all(color: borderColor),
                borderRadius: BorderRadius.all(IcsRadius.m),
              ),
              padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m),
              child: Row(
                children: [
                  Icon(Icons.search, size: 16, color: mutedColor),
                  const SizedBox(width: IcsSpacing.xs),
                  Text(
                    'Search  ( / )',
                    style: TextStyle(fontSize: 12, color: mutedColor),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(width: IcsSpacing.s),

          // Notifications
          _IconBtn(
            icon: Icons.notifications_outlined,
            onTap: () {},
            isDark: isDark,
          ),
          const SizedBox(width: IcsSpacing.xs),

          // Theme toggle
          _IconBtn(
            icon: shell.themeMode == ThemeMode.dark
                ? Icons.light_mode_outlined
                : Icons.dark_mode_outlined,
            onTap: notifier.toggleTheme,
            isDark: isDark,
          ),
          const SizedBox(width: IcsSpacing.xs),

          // Divider
          Container(
            width: 1,
            height: 24,
            color: borderColor,
            margin: const EdgeInsets.symmetric(horizontal: IcsSpacing.xs2),
          ),

          // Level badge
          Container(
            width: IcsDimensions.levelBadgeSize,
            height: IcsDimensions.levelBadgeSize,
            decoration: BoxDecoration(
              color: IcsColors.accentRed,
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white.withValues(alpha: 0.2), width: 1.5),
            ),
            alignment: Alignment.center,
            child: const Text(
              '1',
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w800,
                color: Colors.white,
              ),
            ),
          ),
          const SizedBox(width: IcsSpacing.xs),

          // Avatar
          Container(
            width: IcsDimensions.avatarSize,
            height: IcsDimensions.avatarSize,
            decoration: BoxDecoration(
              color: isDark ? IcsColors.darkStone2 : IcsColors.stone2,
              shape: BoxShape.circle,
              border: Border.all(color: borderColor),
            ),
            alignment: Alignment.center,
            child: Text(
              'A',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: textColor,
              ),
            ),
          ),
          const SizedBox(width: IcsSpacing.xs),

          // Settings
          _IconBtn(
            icon: Icons.settings_outlined,
            onTap: () {},
            isDark: isDark,
          ),
          const SizedBox(width: IcsSpacing.xs),

          // Options toggle
          _IconBtn(
            icon: Icons.dock_outlined,
            active: shell.optionsOpen,
            onTap: notifier.toggleOptions,
            isDark: isDark,
          ),
        ],
      ),
    );
  }
}

class _IconBtn extends StatefulWidget {
  const _IconBtn({
    required this.icon,
    required this.onTap,
    required this.isDark,
    this.active = false,
  });
  final IconData icon;
  final VoidCallback onTap;
  final bool isDark;
  final bool active;

  @override
  State<_IconBtn> createState() => _IconBtnState();
}

class _IconBtnState extends State<_IconBtn> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    final borderColor = widget.isDark ? IcsColors.borderDark : IcsColors.borderLight;
    final bgColor = widget.active
        ? IcsColors.accentRedAlpha15
        : _hovered
            ? (widget.isDark ? IcsColors.ink2 : IcsColors.stone2)
            : (widget.isDark ? IcsColors.darkStone2 : IcsColors.stone2);
    final iconColor = widget.active
        ? IcsColors.accentRed
        : widget.isDark
            ? IcsColors.textMutedDark
            : IcsColors.textMuted;

    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedContainer(
          duration: IcsDuration.fast,
          width: 30,
          height: 30,
          decoration: BoxDecoration(
            color: bgColor,
            borderRadius: BorderRadius.all(IcsRadius.s),
            border: Border.all(color: borderColor),
          ),
          child: Icon(widget.icon, size: 16, color: iconColor),
        ),
      ),
    );
  }
}
