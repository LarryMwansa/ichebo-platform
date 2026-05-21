import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/state/shell_state.dart';
import 'command_palette.dart';
import 'context_bar.dart';
import 'options_bar.dart';
import 'primary_sidebar.dart';
import 'stage.dart';
import 'toast.dart';

class DesktopShell extends ConsumerWidget {
  const DesktopShell({super.key, required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifier = ref.read(shellProvider.notifier);

    return CallbackShortcuts(
      bindings: {
        // Cmd/Ctrl + [ — toggle context bar
        const SingleActivator(LogicalKeyboardKey.bracketLeft, meta: true): notifier.toggleContext,
        const SingleActivator(LogicalKeyboardKey.bracketLeft, control: true): notifier.toggleContext,
        // Cmd/Ctrl + ] — toggle options bar
        const SingleActivator(LogicalKeyboardKey.bracketRight, meta: true): notifier.toggleOptions,
        const SingleActivator(LogicalKeyboardKey.bracketRight, control: true): notifier.toggleOptions,
        // Cmd/Ctrl + \ — focus mode
        const SingleActivator(LogicalKeyboardKey.backslash, meta: true): () =>
            notifier.setFocusMode(!notifier.isFocusMode),
        const SingleActivator(LogicalKeyboardKey.backslash, control: true): () =>
            notifier.setFocusMode(!notifier.isFocusMode),
        // Cmd/Ctrl + / — command palette
        const SingleActivator(LogicalKeyboardKey.slash, meta: true): notifier.openCommandPalette,
        const SingleActivator(LogicalKeyboardKey.slash, control: true): notifier.openCommandPalette,
      },
      child: Focus(
        autofocus: true,
        child: Stack(
          children: [
            // ── Four-column shell ──────────────────────────────────────────
            Row(
              children: [
                const PrimarySidebar(),
                const ContextBar(),
                Expanded(
                  child: Stage(child: child),
                ),
                const OptionsBar(),
              ],
            ),

            // ── Command palette (full-screen overlay) ─────────────────────
            const CommandPalette(),

            // ── Toast overlay (bottom-right, above everything) ────────────
            const ToastContainer(),
          ],
        ),
      ),
    );
  }
}
