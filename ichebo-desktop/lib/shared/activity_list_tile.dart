import 'package:flutter/material.dart';
import '../core/theme/tokens.dart';
import 'activity_type_badge.dart';

// Dense 56px activity row: type badge + title + date + status dot + optional attendance count.
class ActivityListTile extends StatefulWidget {
  const ActivityListTile({
    super.key,
    required this.activityType,
    required this.title,
    required this.status,
    this.scheduledAt,
    this.dueAt,
    this.attendanceCount,
    this.selected = false,
    this.onTap,
  });

  final String activityType;
  final String title;
  final String status;
  final String? scheduledAt;
  final String? dueAt;
  final int? attendanceCount; // non-null for gathering type
  final bool selected;
  final VoidCallback? onTap;

  @override
  State<ActivityListTile> createState() => _ActivityListTileState();
}

class _ActivityListTileState extends State<ActivityListTile> {
  bool _hovered = false;

  static Color _statusColor(String status) => switch (status) {
        'completed'   => IcsColors.success,
        'in_progress' => IcsColors.info,
        'cancelled'   => IcsColors.error,
        'deferred'    => IcsColors.warning,
        _             => const Color(0xFF9E9E9E),
      };

  static String _statusLabel(String status) => switch (status) {
        'completed'   => 'Completed',
        'in_progress' => 'In progress',
        'cancelled'   => 'Cancelled',
        'deferred'    => 'Deferred',
        _             => 'Pending',
      };

  String? get _dateLabel {
    final raw = widget.scheduledAt ?? widget.dueAt;
    if (raw == null || raw.isEmpty) return null;
    try {
      final dt = DateTime.parse(raw).toLocal();
      final months = ['Jan','Feb','Mar','Apr','May','Jun',
                      'Jul','Aug','Sep','Oct','Nov','Dec'];
      return '${dt.day} ${months[dt.month - 1]} ${dt.year}';
    } catch (_) {
      return null;
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bgSelected = IcsColors.accentRed.withValues(alpha: isDark ? 0.12 : 0.07);
    final bgHover    = (isDark ? Colors.white : Colors.black).withValues(alpha: 0.04);
    final dotColor   = _statusColor(widget.status);

    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit:  (_) => setState(() => _hovered = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: Container(
          height: 56,
          padding: const EdgeInsets.symmetric(horizontal: IcsSpacing.m),
          decoration: BoxDecoration(
            color: widget.selected ? bgSelected : (_hovered ? bgHover : Colors.transparent),
            border: widget.selected
                ? const Border(left: BorderSide(color: IcsColors.accentRed, width: 3))
                : null,
          ),
          child: Row(
            children: [
              ActivityTypeBadge(type: widget.activityType),
              const SizedBox(width: IcsSpacing.s),
              Expanded(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      widget.title,
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: isDark ? Colors.white : IcsColors.inkBg,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (_dateLabel != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        _dateLabel!,
                        style: TextStyle(
                          fontSize: 11,
                          color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              // Attendance count badge for gatherings
              if (widget.attendanceCount != null) ...[
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: IcsColors.accentRed.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    '${widget.attendanceCount} attended',
                    style: const TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color: IcsColors.accentRed,
                    ),
                  ),
                ),
                const SizedBox(width: IcsSpacing.s),
              ],
              // Status dot
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 7, height: 7,
                    decoration: BoxDecoration(color: dotColor, shape: BoxShape.circle),
                  ),
                  const SizedBox(width: 4),
                  Text(
                    _statusLabel(widget.status),
                    style: TextStyle(fontSize: 10, color: dotColor),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
