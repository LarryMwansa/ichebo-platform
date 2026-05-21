import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'tokens.dart';

TextTheme _buildTextTheme(Color textColor) {
  final inter = GoogleFonts.interTextTheme().apply(
    bodyColor: textColor,
    displayColor: textColor,
  );
  return inter.copyWith(
    displayLarge: GoogleFonts.playfairDisplay(
      fontWeight: FontWeight.w900,
      fontSize: 48,
      color: textColor,
    ),
    displayMedium: GoogleFonts.playfairDisplay(
      fontWeight: FontWeight.w800,
      fontSize: 36,
      color: textColor,
    ),
    displaySmall: GoogleFonts.playfairDisplay(
      fontWeight: FontWeight.w700,
      fontSize: 28,
      color: textColor,
    ),
    headlineLarge: GoogleFonts.playfairDisplay(
      fontWeight: FontWeight.w800,
      fontSize: 24,
      color: textColor,
    ),
    headlineMedium: GoogleFonts.playfairDisplay(
      fontWeight: FontWeight.w700,
      fontSize: 20,
      color: textColor,
    ),
    titleLarge: GoogleFonts.inter(fontWeight: FontWeight.w600, fontSize: 16, color: textColor),
    titleMedium: GoogleFonts.inter(fontWeight: FontWeight.w600, fontSize: 14, color: textColor),
    titleSmall: GoogleFonts.inter(fontWeight: FontWeight.w500, fontSize: 12, color: textColor),
    bodyLarge: GoogleFonts.inter(fontWeight: FontWeight.w400, fontSize: 15, color: textColor, height: 1.7),
    bodyMedium: GoogleFonts.inter(fontWeight: FontWeight.w400, fontSize: 13, color: textColor),
    bodySmall: GoogleFonts.inter(fontWeight: FontWeight.w400, fontSize: 12, color: textColor),
    labelLarge: GoogleFonts.inter(fontWeight: FontWeight.w700, fontSize: 11, letterSpacing: 0.05, color: textColor),
  );
}

ThemeData lightTheme() {
  return ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    colorScheme: ColorScheme.light(
      primary: IcsColors.accentRed,
      secondary: IcsColors.accentRed,
      surface: IcsColors.stoneBg,
      onSurface: IcsColors.textInk,
    ),
    scaffoldBackgroundColor: IcsColors.stoneBg,
    textTheme: _buildTextTheme(IcsColors.textInk),
    dividerColor: IcsColors.borderLight,
    cardColor: IcsColors.stone2,
    iconTheme: const IconThemeData(color: IcsColors.textMuted),
  );
}

ThemeData darkTheme() {
  return ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    colorScheme: ColorScheme.dark(
      primary: IcsColors.accentRed,
      secondary: IcsColors.accentRed,
      surface: IcsColors.darkStoneBg,
      onSurface: IcsColors.textDark,
    ),
    scaffoldBackgroundColor: IcsColors.darkStoneBg,
    textTheme: _buildTextTheme(IcsColors.textDark),
    dividerColor: IcsColors.borderDark,
    cardColor: IcsColors.darkStone2,
    iconTheme: const IconThemeData(color: IcsColors.textMutedDark),
  );
}
