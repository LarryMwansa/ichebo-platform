import 'package:flutter/material.dart';

// Coloured activity type pill matching the plan's colour table.
class ActivityTypeBadge extends StatelessWidget {
  const ActivityTypeBadge({super.key, required this.type, this.large = false});

  final String type;
  final bool large;

  static const _colors = <String, Color>{
    'gathering': Color(0xFFAF3236),
    'event':     Color(0xFF2196F3),
    'task':      Color(0xFFFF9800),
    'campaign':  Color(0xFF9C27B0),
    'goal':      Color(0xFF10B981),
    'habit':     Color(0xFF00BCD4),
    'project':   Color(0xFF607D8B),
    'reminder':  Color(0xFF795548),
    'skill':     Color(0xFF4CAF50),
    'programme': Color(0xFF3F51B5),
  };

  static const _labels = <String, String>{
    'gathering': 'Gathering',
    'event':     'Event',
    'task':      'Task',
    'campaign':  'Campaign',
    'goal':      'Goal',
    'habit':     'Habit',
    'project':   'Project',
    'reminder':  'Reminder',
    'skill':     'Skill',
    'programme': 'Programme',
  };

  Color get _color => _colors[type] ?? const Color(0xFF9E9E9E);
  String get _label => _labels[type] ?? type[0].toUpperCase() + type.substring(1);

  @override
  Widget build(BuildContext context) {
    final height = large ? 22.0 : 18.0;
    final fontSize = large ? 10.0 : 9.0;
    final hPad = large ? 8.0 : 6.0;

    return Container(
      height: height,
      padding: EdgeInsets.symmetric(horizontal: hPad),
      decoration: BoxDecoration(
        color: _color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(height / 2),
        border: Border.all(color: _color.withValues(alpha: 0.4)),
      ),
      alignment: Alignment.center,
      child: Text(
        _label,
        style: TextStyle(
          fontSize: fontSize,
          fontWeight: FontWeight.w700,
          color: _color,
          height: 1,
        ),
      ),
    );
  }
}
