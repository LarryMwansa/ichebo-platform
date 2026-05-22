import 'package:flutter/material.dart';

// ── Colour tokens ─────────────────────────────────────────────────────────────

class IcsColors {
  IcsColors._();

  static const accentRed    = Color(0xFFAF3236);
  static const accentAmber  = Color(0xFFF59E0B);
  static const accentBlue   = Color(0xFF3B82F6);
  static const accentGreen  = Color(0xFF22C55E);

  // Backgrounds
  static const inkBg        = Color(0xFF0F0F0F);
  static const stone1       = Color(0xFF1C1C1C);
  static const stone2       = Color(0xFFF5F5F4);
  static const stone3       = Color(0xFFE7E5E4);

  // Text
  static const textMuted    = Color(0xFF78716C);
  static const textMutedDark= Color(0xFF57534E);

  // Borders
  static const borderDark   = Color(0xFF2A2A2A);
  static const borderLight  = Color(0xFFE5E5E5);
}

// ── Spacing tokens ────────────────────────────────────────────────────────────

class IcsSpacing {
  IcsSpacing._();

  static const double xs =  4.0;
  static const double s  =  8.0;
  static const double m  = 16.0;
  static const double l  = 24.0;
  static const double xl = 32.0;
}
