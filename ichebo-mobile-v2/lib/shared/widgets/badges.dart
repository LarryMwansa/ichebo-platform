import 'package:flutter/material.dart';
import '../tokens/tokens.dart';

// ── Level Badge ───────────────────────────────────────────────────────────────

const _levelNames = ['Seeker', 'Member', 'Disciple', 'Steward', 'Senior Steward', 'Architect'];

class LevelBadge extends StatelessWidget {
  const LevelBadge({super.key, required this.level, this.showLabel = true});

  final int level;
  final bool showLabel;

  @override
  Widget build(BuildContext context) {
    final color = IcheboColors.forLevel(level);
    final label = level >= 0 && level < _levelNames.length
        ? _levelNames[level]
        : 'L$level';

    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: IcheboSpacing.xs,
        vertical: IcheboSpacing.xs3,
      ),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: IcheboRadius.pill,
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          if (showLabel) ...[
            const SizedBox(width: IcheboSpacing.xs3),
            Text(
              'L$level · $label',
              style: IcheboTextStyles.labelCaps.copyWith(
                color: color,
                fontSize: 10,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

// ── Status Badge ──────────────────────────────────────────────────────────────

enum StatusVariant { active, warning, danger, muted, seeker, success }

class StatusBadge extends StatelessWidget {
  const StatusBadge({super.key, required this.label, required this.variant});

  final String label;
  final StatusVariant variant;

  static Color _bgColor(StatusVariant v, bool isDark) {
    switch (v) {
      case StatusVariant.active:
      case StatusVariant.success:
        return (isDark ? IcheboColors.successDark : IcheboColors.success).withValues(alpha: 0.12);
      case StatusVariant.warning:
        return (isDark ? IcheboColors.warningDark : IcheboColors.warning).withValues(alpha: 0.12);
      case StatusVariant.danger:
        return (isDark ? IcheboColors.errorDark : IcheboColors.error).withValues(alpha: 0.12);
      case StatusVariant.seeker:
      case StatusVariant.muted:
        return IcheboColors.level0.withValues(alpha: 0.12);
    }
  }

  static Color _fgColor(StatusVariant v, bool isDark) {
    switch (v) {
      case StatusVariant.active:
      case StatusVariant.success:
        return isDark ? IcheboColors.successDark : IcheboColors.success;
      case StatusVariant.warning:
        return isDark ? IcheboColors.warningDark : IcheboColors.warning;
      case StatusVariant.danger:
        return isDark ? IcheboColors.errorDark : IcheboColors.error;
      case StatusVariant.seeker:
      case StatusVariant.muted:
        return IcheboColors.muted;
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final fg = _fgColor(variant, isDark);
    final bg = _bgColor(variant, isDark);

    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: IcheboSpacing.xs,
        vertical: IcheboSpacing.xs3,
      ),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: IcheboRadius.pill,
      ),
      child: Text(
        label.toUpperCase(),
        style: IcheboTextStyles.labelCaps.copyWith(color: fg, fontSize: 10),
      ),
    );
  }
}

// ── Label Tag (section eyebrow — "—— LABEL TEXT") ────────────────────────────

class LabelTag extends StatelessWidget {
  const LabelTag({super.key, required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(width: 20, height: 2, color: IcheboColors.primary),
        const SizedBox(width: IcheboSpacing.xs3),
        Text(
          label.toUpperCase(),
          style: IcheboTextStyles.labelCaps.copyWith(
            color: IcheboColors.primary,
            fontSize: 11,
          ),
        ),
      ],
    );
  }
}
