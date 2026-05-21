import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/state/shell_state.dart';
import '../core/theme/tokens.dart';

class PrimarySidebar extends ConsumerWidget {
  const PrimarySidebar({super.key});

  static const _mainSections = [
    ShellSection.dashboard,
    ShellSection.desk,
    ShellSection.governance,
    ShellSection.community,
    ShellSection.formation,
    ShellSection.activity,
    ShellSection.bible,
    ShellSection.video,
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final shell = ref.watch(shellProvider);
    final notifier = ref.read(shellProvider.notifier);

    return Container(
      width: IcsDimensions.sidebarWidth,
      color: IcsColors.inkBg,
      child: Column(
        children: [
          const SizedBox(height: IcsSpacing.l),
          // Logo
          _SidebarLogo(),
          const SizedBox(height: IcsSpacing.l),
          // Main nav
          Expanded(
            child: Column(
              children: _mainSections.map((s) => _SidebarItem(
                section: s,
                active: shell.activeSection == s,
                onTap: () => notifier.setSection(s),
              )).toList(),
            ),
          ),
          // Bottom separator + tenancy
          Container(
            margin: const EdgeInsets.symmetric(horizontal: IcsSpacing.m),
            height: 1,
            color: IcsColors.inkBorder,
          ),
          const SizedBox(height: IcsSpacing.s),
          _SidebarItem(
            section: ShellSection.tenancy,
            active: shell.activeSection == ShellSection.tenancy,
            onTap: () => notifier.setSection(ShellSection.tenancy),
          ),
          const SizedBox(height: IcsSpacing.s),
        ],
      ),
    );
  }
}

class _SidebarLogo extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: IcsDimensions.logoSize,
      height: IcsDimensions.logoSize,
      child: Center(
        child: Text(
          'I',
          style: TextStyle(
            fontFamily: 'Playfair Display',
            fontSize: 22,
            fontWeight: FontWeight.w900,
            color: IcsColors.accentRed,
          ),
        ),
      ),
    );
  }
}

class _SidebarItem extends StatefulWidget {
  const _SidebarItem({
    required this.section,
    required this.active,
    required this.onTap,
  });
  final ShellSection section;
  final bool active;
  final VoidCallback onTap;

  @override
  State<_SidebarItem> createState() => _SidebarItemState();
}

class _SidebarItemState extends State<_SidebarItem> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    final color = widget.active
        ? Colors.white
        : _hovered
            ? Colors.white
            : IcsColors.sidebarIconInactive;

    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      child: Tooltip(
        message: widget.section.label,
        preferBelow: false,
        decoration: BoxDecoration(
          color: IcsColors.inkBg,
          borderRadius: BorderRadius.all(IcsRadius.s),
          border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
        ),
        textStyle: const TextStyle(
          color: Colors.white,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
        waitDuration: Duration.zero,
        child: GestureDetector(
          onTap: widget.onTap,
          child: Container(
            width: IcsDimensions.sidebarItemSize,
            height: IcsDimensions.sidebarItemSize,
            margin: const EdgeInsets.symmetric(vertical: IcsSpacing.xs2),
            decoration: BoxDecoration(
              color: _hovered && !widget.active
                  ? IcsColors.sidebarIconHoverBg
                  : Colors.transparent,
              borderRadius: BorderRadius.all(IcsRadius.m),
            ),
            child: Stack(
              children: [
                // Rule of Left: 3px accent-red bar, vertically centred
                if (widget.active)
                  Positioned(
                    left: 0,
                    top: IcsDimensions.sidebarItemSize * 0.20,
                    child: Container(
                      width: IcsDimensions.ruleOfLeftWidth,
                      height: IcsDimensions.sidebarItemSize * 0.60,
                      decoration: const BoxDecoration(
                        color: IcsColors.accentRed,
                        borderRadius: BorderRadius.only(
                          topRight: IcsRadius.s,
                          bottomRight: IcsRadius.s,
                        ),
                      ),
                    ),
                  ),
                Center(
                  child: Icon(
                    widget.section.icon,
                    size: 20,
                    color: color,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
