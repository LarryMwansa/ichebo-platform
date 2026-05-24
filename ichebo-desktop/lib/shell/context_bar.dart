import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import '../core/state/shell_state.dart';
import '../core/theme/tokens.dart';

class ContextBar extends ConsumerWidget {
  const ContextBar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final shell = ref.watch(shellProvider);
    final isDark = shell.themeMode == ThemeMode.dark;

    final bgColor = isDark ? IcsColors.ink2 : Colors.white;
    final borderColor = isDark
        ? IcsColors.inkBorder
        : Theme.of(context).dividerColor;
    final headerTextColor = isDark ? Colors.white : Theme.of(context).textTheme.bodyLarge?.color;

    return AnimatedContainer(
      duration: IcsDuration.shell,
      curve: shellCurve,
      width: shell.contextOpen ? IcsDimensions.contextBarWidth : 0,
      child: shell.contextOpen
          ? Container(
              decoration: BoxDecoration(
                color: bgColor,
                border: Border(
                  right: BorderSide(color: borderColor, width: 1),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Header
                  Container(
                    height: IcsDimensions.topBarHeight,
                    padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.s),
                    decoration: BoxDecoration(
                      border: Border(
                        bottom: BorderSide(color: borderColor, width: 1),
                      ),
                    ),
                    alignment: Alignment.centerLeft,
                    child: Text(
                      shell.activeSection.label,
                      style: GoogleFonts.playfairDisplay(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                        color: headerTextColor,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ),
                  // Content slot — filled by each section in future phases
                  Expanded(
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.symmetric(
                        horizontal: IcsSpacing.s,
                        vertical: IcsSpacing.m,
                      ),
                      child: _ContextBarPlaceholder(section: shell.activeSection, isDark: isDark),
                    ),
                  ),
                ],
              ),
            )
          : const SizedBox.shrink(),
    );
  }
}

class _ContextBarPlaceholder extends StatelessWidget {
  const _ContextBarPlaceholder({required this.section, required this.isDark});
  final ShellSection section;
  final bool isDark;

  @override
  Widget build(BuildContext context) {
    final mutedColor = isDark
        ? IcsColors.textMutedDark.withValues(alpha: 0.5)
        : IcsColors.textMuted.withValues(alpha: 0.5);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _sectionLink('Overview', isDark),
        _sectionLink('Recent', isDark),
        _sectionLink('Favourites', isDark),
        const SizedBox(height: IcsSpacing.l),
        Text(
          'FILTERS',
          style: TextStyle(
            fontSize: 9,
            fontWeight: FontWeight.w700,
            letterSpacing: 0.08,
            color: mutedColor,
          ),
        ),
        const SizedBox(height: IcsSpacing.xs),
        _sectionLink('All', isDark),
        _sectionLink('Mine', isDark),
        _sectionLink('Shared', isDark),
      ],
    );
  }

  Widget _sectionLink(String label, bool isDark) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: IcsSpacing.xs2),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.w500,
          color: isDark
              ? IcsColors.textMutedDark
              : IcsColors.textMuted,
        ),
      ),
    );
  }
}
