import 'package:flutter/material.dart';

// Competence level colour pill — L0 (grey) through L5 (accentRed).
// Sizes: normal (32×20) and large (40×24).
class LevelBadge extends StatelessWidget {
  const LevelBadge({super.key, required this.level, this.large = false});

  final int level;
  final bool large;

  static const _colors = [
    Color(0xFF9E9E9E), // L0 — grey
    Color(0xFF4CAF50), // L1 — green
    Color(0xFF2196F3), // L2 — blue
    Color(0xFFFF9800), // L3 — amber
    Color(0xFF9C27B0), // L4 — purple
    Color(0xFFAF3236), // L5 — accentRed
  ];

  Color get _color => _colors[level.clamp(0, 5)];

  @override
  Widget build(BuildContext context) {
    final width = large ? 40.0 : 32.0;
    final height = large ? 24.0 : 20.0;
    final fontSize = large ? 11.0 : 10.0;

    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: _color,
        borderRadius: BorderRadius.circular(height / 2),
      ),
      alignment: Alignment.center,
      child: Text(
        'L$level',
        style: TextStyle(
          fontFamily: 'Playfair Display',
          fontSize: fontSize,
          fontWeight: FontWeight.w700,
          color: Colors.white,
          height: 1,
        ),
      ),
    );
  }
}
