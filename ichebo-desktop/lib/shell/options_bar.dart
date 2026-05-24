import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/state/shell_state.dart';
import '../core/theme/tokens.dart';

class OptionsBar extends ConsumerStatefulWidget {
  const OptionsBar({super.key});

  @override
  ConsumerState<OptionsBar> createState() => _OptionsBarState();
}

class _OptionsBarState extends ConsumerState<OptionsBar> {
  int _activeTab = 0;
  static const _tabs = ['Relations', 'Details', 'History'];

  @override
  Widget build(BuildContext context) {
    final shell = ref.watch(shellProvider);
    final notifier = ref.read(shellProvider.notifier);
    final isDark = shell.themeMode == ThemeMode.dark;

    final bgColor = isDark ? IcsColors.darkStone2 : IcsColors.stone2;
    final headerBgColor = isDark ? IcsColors.darkStoneBg : IcsColors.stoneBg;
    final borderColor = isDark ? IcsColors.borderDark : IcsColors.borderLight;
    final textColor = isDark ? IcsColors.textDark : IcsColors.textInk;
    final mutedColor = isDark ? IcsColors.textMutedDark : IcsColors.textMuted;

    return AnimatedContainer(
      duration: IcsDuration.shell,
      curve: shellCurve,
      width: shell.optionsOpen ? IcsDimensions.optionsBarWidth : 0,
      child: shell.optionsOpen
          ? Container(
              decoration: BoxDecoration(
                color: bgColor,
                border: Border(
                  left: BorderSide(color: borderColor, width: 1),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // ── Header ────────────────────────────────────────────
                  Container(
                    height: IcsDimensions.topBarHeight,
                    padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.s),
                    decoration: BoxDecoration(
                      color: headerBgColor,
                      border: Border(
                        bottom: BorderSide(color: borderColor, width: 1),
                      ),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'DETAILS & RELATIONS',
                          style: TextStyle(
                            fontSize: 9,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 0.08,
                            color: mutedColor,
                          ),
                        ),
                        GestureDetector(
                          onTap: notifier.toggleOptions,
                          child: Icon(Icons.close, size: 16, color: mutedColor),
                        ),
                      ],
                    ),
                  ),

                  // ── Tabs ──────────────────────────────────────────────
                  Container(
                    decoration: BoxDecoration(
                      color: headerBgColor,
                      border: Border(
                        bottom: BorderSide(color: borderColor, width: 1),
                      ),
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.xs),
                    child: Row(
                      children: List.generate(_tabs.length, (i) {
                        final isActive = i == _activeTab;
                        return GestureDetector(
                          onTap: () => setState(() => _activeTab = i),
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: IcsSpacing.xs,
                              vertical: IcsSpacing.xs,
                            ),
                            decoration: BoxDecoration(
                              border: Border(
                                bottom: BorderSide(
                                  color: isActive ? IcsColors.accentRed : Colors.transparent,
                                  width: 2,
                                ),
                              ),
                            ),
                            child: Text(
                              _tabs[i],
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w700,
                                letterSpacing: 0.05,
                                color: isActive ? IcsColors.accentRed : mutedColor,
                              ),
                            ),
                          ),
                        );
                      }),
                    ),
                  ),

                  // ── Content pane ──────────────────────────────────────
                  Expanded(
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.all(IcsSpacing.l),
                      child: _OptionsContent(
                        tab: _activeTab,
                        textColor: textColor,
                        mutedColor: mutedColor,
                      ),
                    ),
                  ),
                ],
              ),
            )
          : const SizedBox.shrink(),
    );
  }
}

class _OptionsContent extends StatelessWidget {
  const _OptionsContent({
    required this.tab,
    required this.textColor,
    required this.mutedColor,
  });
  final int tab;
  final Color textColor;
  final Color mutedColor;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(Icons.info_outline, size: 28, color: mutedColor.withValues(alpha: 0.4)),
        const SizedBox(height: IcsSpacing.s),
        Text(
          'Select an element to view ${['relationships', 'details', 'history'][tab]}',
          style: TextStyle(fontSize: 12, color: mutedColor),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}
