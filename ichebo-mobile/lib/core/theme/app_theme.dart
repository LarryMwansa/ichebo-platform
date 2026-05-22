import 'package:flutter/material.dart';
import 'tokens.dart';

class IcsTheme {
  IcsTheme._();

  static ThemeData get light => _build(Brightness.light);
  static ThemeData get dark  => _build(Brightness.dark);

  static ThemeData _build(Brightness brightness) {
    final isDark = brightness == Brightness.dark;
    final colorScheme = ColorScheme(
      brightness:       brightness,
      primary:          IcsColors.accentRed,
      onPrimary:        Colors.white,
      secondary:        IcsColors.accentAmber,
      onSecondary:      Colors.black,
      error:            const Color(0xFFDC2626),
      onError:          Colors.white,
      surface:          isDark ? IcsColors.stone1 : Colors.white,
      onSurface:        isDark ? Colors.white : IcsColors.inkBg,
    );

    return ThemeData(
      useMaterial3:     true,
      colorScheme:      colorScheme,
      scaffoldBackgroundColor: isDark ? IcsColors.inkBg : IcsColors.stone2,
      appBarTheme: AppBarTheme(
        backgroundColor: isDark ? IcsColors.stone1 : Colors.white,
        foregroundColor: isDark ? Colors.white : IcsColors.inkBg,
        elevation: 0,
        scrolledUnderElevation: 0,
        titleTextStyle: TextStyle(
          fontFamily: 'PlayfairDisplay',
          fontSize: 18,
          fontWeight: FontWeight.w700,
          color: isDark ? Colors.white : IcsColors.inkBg,
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: isDark ? IcsColors.stone1 : Colors.white,
        indicatorColor: IcsColors.accentRed.withValues(alpha: 0.15),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return IconThemeData(color: IcsColors.accentRed, size: 22);
          }
          return IconThemeData(
            color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
            size: 22,
          );
        }),
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const TextStyle(
              fontSize: 11, fontWeight: FontWeight.w600,
              color: IcsColors.accentRed,
            );
          }
          return TextStyle(
            fontSize: 11,
            color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
          );
        }),
      ),
      cardTheme: CardThemeData(
        color: isDark ? IcsColors.stone1 : Colors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(10),
          side: BorderSide(
            color: isDark ? IcsColors.borderDark : IcsColors.borderLight,
          ),
        ),
        margin: EdgeInsets.zero,
      ),
      dividerTheme: DividerThemeData(
        color: isDark ? IcsColors.borderDark : IcsColors.borderLight,
        thickness: 1,
        space: 1,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: isDark ? IcsColors.stone1 : Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(
            color: isDark ? IcsColors.borderDark : IcsColors.borderLight,
          ),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(
            color: isDark ? IcsColors.borderDark : IcsColors.borderLight,
          ),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: IcsColors.accentRed, width: 1.5),
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: IcsSpacing.m, vertical: 14,
        ),
      ),
      textTheme: TextTheme(
        headlineLarge: TextStyle(
          fontFamily: 'PlayfairDisplay', fontSize: 28, fontWeight: FontWeight.w700,
          color: isDark ? Colors.white : IcsColors.inkBg,
        ),
        headlineMedium: TextStyle(
          fontFamily: 'PlayfairDisplay', fontSize: 22, fontWeight: FontWeight.w700,
          color: isDark ? Colors.white : IcsColors.inkBg,
        ),
        titleLarge: TextStyle(
          fontSize: 16, fontWeight: FontWeight.w600,
          color: isDark ? Colors.white : IcsColors.inkBg,
        ),
        titleMedium: TextStyle(
          fontSize: 14, fontWeight: FontWeight.w600,
          color: isDark ? Colors.white : IcsColors.inkBg,
        ),
        bodyLarge: TextStyle(
          fontSize: 15,
          color: isDark ? Colors.white : IcsColors.inkBg,
        ),
        bodyMedium: TextStyle(
          fontSize: 13,
          color: isDark ? Colors.white : IcsColors.inkBg,
        ),
        bodySmall: TextStyle(
          fontSize: 12,
          color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
        ),
        labelSmall: TextStyle(
          fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 0.8,
          color: isDark ? IcsColors.textMutedDark : IcsColors.textMuted,
        ),
      ),
    );
  }
}
