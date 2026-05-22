import 'package:flutter/material.dart';

// ── Colour ────────────────────────────────────────────────────────────────────

class IcheboColors {
  IcheboColors._();

  // Brand
  static const primary = Color(0xFFAF3236);
  static const primaryDark = Color(0xFF8C2A2D);
  static const primaryLight = Color(0x1FAF3236); // 12% opacity

  static const secondary = Color(0xFF185ABC);

  // Ink surfaces
  static const ink = Color(0xFF0E0E0E);
  static const ink2 = Color(0xFF1A1A1A);
  static const inkLight = Color(0xFF2D2D2D);

  // Stone surfaces
  static const stone = Color(0xFFF5F3F0);
  static const stone2 = Color(0xFFECE9E4);

  // Background
  static const bg = Color(0xFFFFFFFF);

  // Text
  static const text = Color(0xFF1A1A1A);
  static const muted = Color(0xFF6B6B6B);
  static const mutedLight = Color(0xFF9A9A9A);

  // Semantic
  static const success = Color(0xFF16A34A);
  static const successDark = Color(0xFF4ADE80);
  static const warning = Color(0xFFCA8A04);
  static const warningDark = Color(0xFFFBBF24);
  static const error = Color(0xFFDC2626);
  static const errorDark = Color(0xFFF87171);
  static const info = Color(0xFF0C5C9E);
  static const infoDark = Color(0xFF60A5FA);

  // Level colours (KGS Competence)
  static const level0 = Color(0xFF9CA3AF);
  static const level1 = Color(0xFF16A34A);
  static const level2 = Color(0xFF2563EB);
  static const level3 = Color(0xFF7C3AED);
  static const level4 = Color(0xFFEA580C);
  static const level5 = Color(0xFFDC2626);

  static Color forLevel(int level) {
    switch (level) {
      case 1: return level1;
      case 2: return level2;
      case 3: return level3;
      case 4: return level4;
      case 5: return level5;
      default: return level0;
    }
  }

  // Dark mode surface overrides
  static const darkBg = ink;
  static const darkCard = ink2;
  static const darkCard2 = inkLight;
  static const darkText = stone;
  static const darkMuted = mutedLight;
  static const darkBorder = Color(0x14FFFFFF); // rgba(255,255,255,0.08)
  static const lightBorder = Color(0x14000000); // rgba(0,0,0,0.08)
}

// ── Typography ────────────────────────────────────────────────────────────────

class IcheboFonts {
  IcheboFonts._();

  static const display = 'PlayfairDisplay';
  static const ui = 'Inter'; // falls back to system sans-serif
}

class IcheboTextStyles {
  IcheboTextStyles._();

  // Display (Playfair Display) — page titles, heroes, stat numbers
  static const displayLarge = TextStyle(
    fontFamily: IcheboFonts.display,
    fontSize: 48,
    fontWeight: FontWeight.w900,
    letterSpacing: -0.8,
    height: 1.1,
  );
  static const displayMedium = TextStyle(
    fontFamily: IcheboFonts.display,
    fontSize: 40,
    fontWeight: FontWeight.w800,
    letterSpacing: -0.6,
    height: 1.15,
  );
  static const displaySmall = TextStyle(
    fontFamily: IcheboFonts.display,
    fontSize: 32,
    fontWeight: FontWeight.w700,
    letterSpacing: -0.5,
    height: 1.2,
  );
  static const headlineLarge = TextStyle(
    fontFamily: IcheboFonts.display,
    fontSize: 24,
    fontWeight: FontWeight.w700,
    letterSpacing: -0.3,
    height: 1.3,
  );

  // UI (Inter) — all interface text
  static const titleLarge = TextStyle(
    fontFamily: IcheboFonts.ui,
    fontSize: 20,
    fontWeight: FontWeight.w600,
    letterSpacing: 0,
    height: 1.4,
  );
  static const titleMedium = TextStyle(
    fontFamily: IcheboFonts.ui,
    fontSize: 18,
    fontWeight: FontWeight.w500,
    letterSpacing: 0,
    height: 1.4,
  );
  static const bodyLarge = TextStyle(
    fontFamily: IcheboFonts.ui,
    fontSize: 16,
    fontWeight: FontWeight.w400,
    height: 1.6,
  );
  static const bodyMedium = TextStyle(
    fontFamily: IcheboFonts.ui,
    fontSize: 14,
    fontWeight: FontWeight.w400,
    height: 1.5,
  );
  static const bodySmall = TextStyle(
    fontFamily: IcheboFonts.ui,
    fontSize: 12,
    fontWeight: FontWeight.w400,
    height: 1.5,
  );
  static const labelLarge = TextStyle(
    fontFamily: IcheboFonts.ui,
    fontSize: 14,
    fontWeight: FontWeight.w600,
    letterSpacing: 0,
  );
  static const labelCaps = TextStyle(
    fontFamily: IcheboFonts.ui,
    fontSize: 11,
    fontWeight: FontWeight.w700,
    letterSpacing: 1.4,
    height: 1.4,
  );
}

// ── Spacing ───────────────────────────────────────────────────────────────────

class IcheboSpacing {
  IcheboSpacing._();

  static const double xs3 = 4;
  static const double xs2 = 8;
  static const double xs = 12;
  static const double s = 16;
  static const double m = 24;
  static const double l = 32;
  static const double xl = 48;
  static const double xl2 = 64;
  static const double xl3 = 96;
}

// ── Border Radius ─────────────────────────────────────────────────────────────

class IcheboRadius {
  IcheboRadius._();

  static const xs = BorderRadius.all(Radius.circular(3));
  static const s = BorderRadius.all(Radius.circular(4));
  static const m = BorderRadius.all(Radius.circular(8));
  static const l = BorderRadius.all(Radius.circular(12)); // standard card
  static const xl = BorderRadius.all(Radius.circular(16));
  static const xl2 = BorderRadius.all(Radius.circular(20)); // bottom sheets
  static const pill = BorderRadius.all(Radius.circular(999));
}

// ── Motion ────────────────────────────────────────────────────────────────────

class IcheboDuration {
  IcheboDuration._();

  static const micro = Duration(milliseconds: 100);
  static const fast = Duration(milliseconds: 150);
  static const standard = Duration(milliseconds: 300);
  static const deliberate = Duration(milliseconds: 500);
}

const kIcheboCurve = Cubic(0.4, 0, 0.2, 1);

// ── Touch target ──────────────────────────────────────────────────────────────

const double kMinTouchTarget = 48.0;
