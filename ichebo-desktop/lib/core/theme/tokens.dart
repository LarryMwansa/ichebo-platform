import 'package:flutter/material.dart';

// ── Apostolic Design Tokens ───────────────────────────────────────────────────

class IcsColors {
  // Ink (always-dark sidebar palette)
  static const inkBg = Color(0xFF0E0E0E);
  static const ink2 = Color(0xFF161616);
  static const inkBorder = Color(0x0DFFFFFF); // rgba(255,255,255,0.05)

  // Stone (stage / light surface)
  static const stoneBg = Color(0xFFF5F3F0);
  static const stone2 = Color(0xFFECE9E4);

  // Dark-mode surface overrides
  static const darkStoneBg = Color(0xFF111111);
  static const darkStone2 = Color(0xFF161616);

  // Accent
  static const accentRed = Color(0xFFAF3236);
  static const accentRedAlpha5 = Color(0x0DAF3236);  // 5% opacity
  static const accentRedAlpha15 = Color(0x26AF3236); // 15% opacity

  // Text
  static const textInk = Color(0xFF1A1A1A);
  static const textMuted = Color(0xFF636E72);
  static const textDark = Color(0xFFF5F3F0);
  static const textMutedDark = Color(0xFF9A9A9A);

  // Borders
  static const borderLight = Color(0x0D000000); // rgba(0,0,0,0.05)
  static const borderDark = Color(0x1AFFFFFF);  // rgba(255,255,255,0.10)

  // Status
  static const success = Color(0xFF10B981);
  static const warning = Color(0xFFD97706);
  static const error = Color(0xFFE53E3E);
  static const info = Color(0xFF3B82F6);

  // Sidebar icon states
  static const sidebarIconInactive = Color(0x66FFFFFF); // rgba(255,255,255,0.40)
  static const sidebarIconHover = Color(0xFFFFFFFF);
  static const sidebarIconHoverBg = Color(0x0DFFFFFF); // rgba(255,255,255,0.05)
}

class IcsSpacing {
  static const xs3 = 2.0;
  static const xs2 = 4.0;
  static const xs = 6.0;
  static const s = 8.0;
  static const m = 12.0;
  static const l = 16.0;
  static const xl = 24.0;
  static const xxl = 32.0;
  static const xxxl = 48.0;
}

class IcsDimensions {
  static const sidebarWidth = 64.0;
  static const contextBarWidth = 240.0;
  static const optionsBarWidth = 300.0;
  static const topBarHeight = 56.0;
  static const sidebarItemSize = 40.0;
  static const ruleOfLeftWidth = 3.0;
  static const canvasMaxWidth = 900.0;
  static const searchBarWidth = 200.0;
  static const levelBadgeSize = 24.0;
  static const avatarSize = 32.0;
  static const logoSize = 32.0;
}

class IcsRadius {
  static const s = Radius.circular(4.0);
  static const m = Radius.circular(8.0);
  static const l = Radius.circular(12.0);
  static const full = Radius.circular(999.0);
}

class IcsDuration {
  static const shell = Duration(milliseconds: 250);
  static const fast = Duration(milliseconds: 150);
  static const toast = Duration(seconds: 5);
}

const shellCurve = Curves.easeInOut;
