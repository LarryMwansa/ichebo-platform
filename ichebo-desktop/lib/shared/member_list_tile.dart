import 'package:flutter/material.dart';
import '../core/theme/tokens.dart';
import 'level_badge.dart';

// Dense member list row: LevelBadge + display_name + email + service order.
class MemberListTile extends StatefulWidget {
  const MemberListTile({
    super.key,
    required this.displayName,
    required this.email,
    required this.competenceLevel,
    this.serviceOrder,
    this.selected = false,
    this.onTap,
    this.compact = false,
  });

  final String displayName;
  final String email;
  final int competenceLevel;
  final String? serviceOrder;
  final bool selected;
  final VoidCallback? onTap;
  // compact = true: used inside detail panel for shepherd display
  final bool compact;

  @override
  State<MemberListTile> createState() => _MemberListTileState();
}

class _MemberListTileState extends State<MemberListTile> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bgSelected = isDark
        ? IcsColors.accentRed.withValues(alpha: 0.12)
        : IcsColors.accentRed.withValues(alpha: 0.07);
    final bgHover = isDark
        ? Colors.white.withValues(alpha: 0.04)
        : Colors.black.withValues(alpha: 0.03);

    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: Container(
          height: widget.compact ? 44 : 56,
          padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m),
          decoration: BoxDecoration(
            color: widget.selected
                ? bgSelected
                : _hovered
                    ? bgHover
                    : Colors.transparent,
            border: widget.selected
                ? Border(left: BorderSide(color: IcsColors.accentRed, width: 3))
                : null,
          ),
          child: Row(
            children: [
              LevelBadge(level: widget.competenceLevel),
              const SizedBox(width: IcsSpacing.s),
              Expanded(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      widget.displayName,
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: isDark ? Colors.white : IcsColors.inkBg,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (!widget.compact) ...[
                      const SizedBox(height: 2),
                      Text(
                        widget.email,
                        style: TextStyle(
                          fontSize: 11,
                          color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ],
                ),
              ),
              if (widget.serviceOrder != null) ...[
                const SizedBox(width: IcsSpacing.s),
                Text(
                  widget.serviceOrder!,
                  style: TextStyle(
                    fontSize: 10,
                    color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
