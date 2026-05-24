import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import '../core/state/shell_state.dart';
import '../core/theme/tokens.dart';
import 'sync_bar.dart';
import 'topbar.dart';

class Stage extends ConsumerWidget {
  const Stage({super.key, required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final shell = ref.watch(shellProvider);
    final isDark = shell.themeMode == ThemeMode.dark;

    final bgColor = isDark ? IcsColors.darkStoneBg : IcsColors.stoneBg;
    final borderColor = isDark ? IcsColors.borderDark : IcsColors.borderLight;

    return Container(
      color: bgColor,
      child: Column(
        children: [
          const StageTopBar(),
          Expanded(
            child: Stack(
              children: [
                // Ghost watermark: behind content, bottom-right
                Positioned(
                  right: 0,
                  bottom: -20,
                  child: IgnorePointer(
                    child: Opacity(
                      opacity: isDark ? 0.03 : 0.05,
                      child: Text(
                        shell.activeSection.watermark,
                        style: GoogleFonts.playfairDisplay(
                          fontSize: 140,
                          fontWeight: FontWeight.w900,
                          color: IcsColors.accentRed,
                          letterSpacing: -0.04 * 140,
                          height: 1,
                        ),
                      ),
                    ),
                  ),
                ),
                // Canvas — each screen manages its own scrolling
                Positioned.fill(
                  child: Container(
                    decoration: BoxDecoration(
                      border: Border(
                        left: BorderSide(color: borderColor, width: 1),
                      ),
                    ),
                    child: child,
                  ),
                ),
              ],
            ),
          ),
          const SyncBar(),
        ],
      ),
    );
  }
}
