import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/state/shell_state.dart';
import '../core/theme/tokens.dart';

// ── Command definition ────────────────────────────────────────────────────────

class _Command {
  const _Command({
    required this.title,
    required this.meta,
    required this.icon,
    required this.shortcut,
    required this.action,
  });
  final String title;
  final String meta;
  final IconData icon;
  final String shortcut;
  final void Function(ShellNotifier) action;
}

const _defaultCommands = [
  _Command(
    title: 'Editorial Desk',
    meta: 'Draft new mandates',
    icon: Icons.edit_note_outlined,
    shortcut: 'G D',
    action: _goDesk,
  ),
  _Command(
    title: 'Toggle Theme',
    meta: 'Switch Light / Dark',
    icon: Icons.contrast_outlined,
    shortcut: 'T T',
    action: _toggleTheme,
  ),
  _Command(
    title: 'Focus Mode',
    meta: 'Hide both sidebars for writing',
    icon: Icons.visibility_off_outlined,
    shortcut: '⌘ \\',
    action: _focusMode,
  ),
  _Command(
    title: 'Toggle Context Bar',
    meta: 'Show or hide the left panel',
    icon: Icons.dock_outlined,
    shortcut: '⌘ [',
    action: _toggleContext,
  ),
];

void _goDesk(ShellNotifier n) => n.setSection(ShellSection.desk);
void _toggleTheme(ShellNotifier n) => n.toggleTheme();
void _focusMode(ShellNotifier n) => n.setFocusMode(!n.isFocusMode);
void _toggleContext(ShellNotifier n) => n.toggleContext();

// ── Widget ────────────────────────────────────────────────────────────────────

class CommandPalette extends ConsumerStatefulWidget {
  const CommandPalette({super.key});

  @override
  ConsumerState<CommandPalette> createState() => _CommandPaletteState();
}

class _CommandPaletteState extends ConsumerState<CommandPalette> {
  final _controller = TextEditingController();
  final _focusNode = FocusNode();
  int _focusIndex = 0;
  List<_Command> _filtered = _defaultCommands;

  @override
  void initState() {
    super.initState();
    _controller.addListener(_onQueryChanged);
  }

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _onQueryChanged() {
    final q = _controller.text.toLowerCase();
    setState(() {
      _filtered = q.isEmpty
          ? _defaultCommands
          : _defaultCommands
              .where((c) =>
                  c.title.toLowerCase().contains(q) ||
                  c.meta.toLowerCase().contains(q))
              .toList();
      _focusIndex = 0;
    });
  }

  void _execute(int index) {
    if (index < 0 || index >= _filtered.length) return;
    final notifier = ref.read(shellProvider.notifier);
    notifier.closeCommandPalette();
    _filtered[index].action(notifier);
    _controller.clear();
  }

  void _close() {
    ref.read(shellProvider.notifier).closeCommandPalette();
    _controller.clear();
  }

  @override
  Widget build(BuildContext context) {
    final isOpen = ref.watch(shellProvider).commandPaletteOpen;
    if (!isOpen) return const SizedBox.shrink();

    // Focus the input when palette opens
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (isOpen) _focusNode.requestFocus();
    });

    return KeyboardListener(
      focusNode: FocusNode(),
      onKeyEvent: (event) {
        if (event is! KeyDownEvent) return;
        if (event.logicalKey == LogicalKeyboardKey.escape) {
          _close();
        } else if (event.logicalKey == LogicalKeyboardKey.arrowDown) {
          setState(() => _focusIndex = (_focusIndex + 1) % _filtered.length);
        } else if (event.logicalKey == LogicalKeyboardKey.arrowUp) {
          setState(() => _focusIndex =
              (_focusIndex - 1 + _filtered.length) % _filtered.length);
        } else if (event.logicalKey == LogicalKeyboardKey.enter) {
          _execute(_focusIndex);
        }
      },
      child: GestureDetector(
        onTap: _close,
        child: Container(
          color: Colors.black.withValues(alpha: 0.85),
          child: BackdropFilter(
            filter: _blurFilter,
            child: Align(
              alignment: const Alignment(0, -0.4),
              child: GestureDetector(
                onTap: () {}, // Prevent close when tapping inside
                child: _PaletteCard(
                  controller: _controller,
                  focusNode: _focusNode,
                  filtered: _filtered,
                  focusIndex: _focusIndex,
                  onExecute: _execute,
                  onClose: _close,
                  onHover: (i) => setState(() => _focusIndex = i),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

final _blurFilter = ImageFilter.blur(sigmaX: 8, sigmaY: 8);

class _PaletteCard extends StatelessWidget {
  const _PaletteCard({
    required this.controller,
    required this.focusNode,
    required this.filtered,
    required this.focusIndex,
    required this.onExecute,
    required this.onClose,
    required this.onHover,
  });
  final TextEditingController controller;
  final FocusNode focusNode;
  final List<_Command> filtered;
  final int focusIndex;
  final void Function(int) onExecute;
  final VoidCallback onClose;
  final void Function(int) onHover;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 680,
      constraints: const BoxConstraints(maxHeight: 500),
      decoration: BoxDecoration(
        color: IcsColors.ink2,
        borderRadius: BorderRadius.all(IcsRadius.l),
        border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.5),
            blurRadius: 60,
            offset: const Offset(0, 30),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // ── Search header ──────────────────────────────────────────
          Container(
            padding: const EdgeInsets.symmetric(
              horizontal: IcsSpacing.l,
              vertical: IcsSpacing.l,
            ),
            decoration: BoxDecoration(
              border: Border(
                bottom: BorderSide(color: Colors.white.withValues(alpha: 0.05)),
              ),
            ),
            child: Row(
              children: [
                const Icon(Icons.terminal, color: IcsColors.accentRed, size: 18),
                const SizedBox(width: IcsSpacing.m),
                Expanded(
                  child: TextField(
                    controller: controller,
                    focusNode: focusNode,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 15,
                      fontWeight: FontWeight.w500,
                    ),
                    decoration: const InputDecoration(
                      border: InputBorder.none,
                      hintText: 'Search mandates, people or type a command...',
                      hintStyle: TextStyle(
                        color: Colors.white38,
                        fontSize: 15,
                      ),
                      isDense: true,
                      contentPadding: EdgeInsets.zero,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.all(IcsRadius.s),
                  ),
                  child: const Text(
                    'ESC',
                    style: TextStyle(
                      color: Colors.white60,
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
          ),

          // ── Results ────────────────────────────────────────────────
          Flexible(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(IcsSpacing.m),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (filtered.isEmpty)
                    Padding(
                      padding: const EdgeInsets.all(IcsSpacing.l),
                      child: Text(
                        'No commands found.',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.3),
                          fontSize: 12,
                        ),
                      ),
                    )
                  else ...[
                    Padding(
                      padding: const EdgeInsets.only(
                        left: IcsSpacing.xs,
                        bottom: IcsSpacing.m,
                      ),
                      child: Text(
                        'QUICK COMMANDS',
                        style: TextStyle(
                          color: IcsColors.accentRed.withValues(alpha: 0.8),
                          fontSize: 9,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 0.08,
                        ),
                      ),
                    ),
                    GridView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      gridDelegate:
                          const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 2,
                        mainAxisSpacing: IcsSpacing.s,
                        crossAxisSpacing: IcsSpacing.s,
                        childAspectRatio: 3.2,
                      ),
                      itemCount: filtered.length,
                      itemBuilder: (context, i) => _CommandItem(
                        command: filtered[i],
                        focused: i == focusIndex,
                        onTap: () => onExecute(i),
                        onHover: () => onHover(i),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),

          // ── Footer ─────────────────────────────────────────────────
          Container(
            padding: const EdgeInsets.symmetric(
              horizontal: IcsSpacing.l,
              vertical: IcsSpacing.s,
            ),
            decoration: BoxDecoration(
              color: Colors.black.withValues(alpha: 0.2),
              border: Border(
                top: BorderSide(color: Colors.white.withValues(alpha: 0.05)),
              ),
              borderRadius: const BorderRadius.only(
                bottomLeft: IcsRadius.l,
                bottomRight: IcsRadius.l,
              ),
            ),
            child: Row(
              children: [
                _footerHint('↑↓', 'Navigate'),
                const SizedBox(width: IcsSpacing.l),
                _footerHint('↵', 'Execute'),
                const SizedBox(width: IcsSpacing.l),
                _footerHint('ESC', 'Dismiss'),
                const Spacer(),
                Text(
                  'Ichebo Command Shell ',
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.3),
                    fontSize: 10,
                  ),
                ),
                const Text(
                  'v2.4',
                  style: TextStyle(
                    color: IcsColors.accentRed,
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _footerHint(String key, String label) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.1),
            borderRadius: BorderRadius.all(IcsRadius.s),
          ),
          child: Text(
            key,
            style: const TextStyle(
              color: Colors.white60,
              fontSize: 9,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: TextStyle(
            color: Colors.white.withValues(alpha: 0.3),
            fontSize: 10,
          ),
        ),
      ],
    );
  }
}

class _CommandItem extends StatefulWidget {
  const _CommandItem({
    required this.command,
    required this.focused,
    required this.onTap,
    required this.onHover,
  });
  final _Command command;
  final bool focused;
  final VoidCallback onTap;
  final VoidCallback onHover;

  @override
  State<_CommandItem> createState() => _CommandItemState();
}

class _CommandItemState extends State<_CommandItem> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    final highlight = widget.focused || _hovered;

    return MouseRegion(
      onEnter: (_) {
        setState(() => _hovered = true);
        widget.onHover();
      },
      onExit: (_) => setState(() => _hovered = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedContainer(
          duration: IcsDuration.fast,
          padding: const EdgeInsets.all(IcsSpacing.m),
          decoration: BoxDecoration(
            color: highlight
                ? Colors.white.withValues(alpha: 0.05)
                : Colors.white.withValues(alpha: 0.02),
            borderRadius: BorderRadius.all(IcsRadius.m),
            border: Border(
              left: BorderSide(
                color: highlight ? IcsColors.accentRed : Colors.transparent,
                width: IcsDimensions.ruleOfLeftWidth,
              ),
              top: BorderSide(color: Colors.white.withValues(alpha: 0.05)),
              right: BorderSide(color: Colors.white.withValues(alpha: 0.05)),
              bottom: BorderSide(color: Colors.white.withValues(alpha: 0.05)),
            ),
          ),
          child: Row(
            children: [
              Icon(widget.command.icon, color: Colors.white70, size: 16),
              const SizedBox(width: IcsSpacing.m),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      widget.command.title,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    Text(
                      widget.command.meta,
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.5),
                        fontSize: 10,
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.all(IcsRadius.s),
                ),
                child: Text(
                  widget.command.shortcut,
                  style: const TextStyle(
                    color: Colors.white38,
                    fontSize: 9,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
