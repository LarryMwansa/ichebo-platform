import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'tokens.dart';

// Dark mode is non-optional per DESIGN.md. Both themes are always available;
// the system or user preference selects which is active.

class IcheboTheme {
  IcheboTheme._();

  static ThemeData get light => _build(brightness: Brightness.light);
  static ThemeData get dark => _build(brightness: Brightness.dark);

  static ThemeData _build({required Brightness brightness}) {
    final isDark = brightness == Brightness.dark;

    final bg = isDark ? IcheboColors.darkBg : IcheboColors.bg;
    final surface = isDark ? IcheboColors.darkCard : IcheboColors.stone;
    final onSurface = isDark ? IcheboColors.darkText : IcheboColors.text;
    final muted = isDark ? IcheboColors.darkMuted : IcheboColors.muted;
    final border = isDark ? IcheboColors.darkBorder : IcheboColors.lightBorder;

    final colorScheme = ColorScheme(
      brightness: brightness,
      primary: IcheboColors.primary,
      onPrimary: Colors.white,
      primaryContainer: IcheboColors.primaryLight,
      onPrimaryContainer: IcheboColors.primaryDark,
      secondary: IcheboColors.secondary,
      onSecondary: Colors.white,
      secondaryContainer: IcheboColors.secondary.withValues(alpha: 0.12),
      onSecondaryContainer: IcheboColors.secondary,
      error: isDark ? IcheboColors.errorDark : IcheboColors.error,
      onError: Colors.white,
      errorContainer: (isDark ? IcheboColors.errorDark : IcheboColors.error).withValues(alpha: 0.12),
      onErrorContainer: isDark ? IcheboColors.errorDark : IcheboColors.error,
      surface: surface,
      onSurface: onSurface,
      surfaceContainerHighest: isDark ? IcheboColors.inkLight : IcheboColors.stone2,
      outline: border,
      outlineVariant: border,
      shadow: Colors.black,
      scrim: Colors.black54,
      inverseSurface: isDark ? IcheboColors.stone : IcheboColors.ink,
      onInverseSurface: isDark ? IcheboColors.text : IcheboColors.stone,
      inversePrimary: IcheboColors.primary,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: bg,
      fontFamily: IcheboFonts.ui,

      // App bar — dark ink always (matches sidebar and page-hero pattern)
      appBarTheme: AppBarTheme(
        backgroundColor: IcheboColors.ink,
        foregroundColor: IcheboColors.stone,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: IcheboTextStyles.titleLarge.copyWith(
          color: IcheboColors.stone,
          fontSize: 18,
        ),
        systemOverlayStyle: SystemUiOverlayStyle.light,
        iconTheme: const IconThemeData(color: IcheboColors.stone),
        actionsIconTheme: const IconThemeData(color: IcheboColors.stone),
      ),

      // Bottom nav — ink surface
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: isDark ? IcheboColors.ink2 : IcheboColors.ink,
        selectedItemColor: IcheboColors.primary,
        unselectedItemColor: IcheboColors.mutedLight,
        type: BottomNavigationBarType.fixed,
        elevation: 0,
        selectedLabelStyle: IcheboTextStyles.labelCaps.copyWith(fontSize: 10),
        unselectedLabelStyle: IcheboTextStyles.labelCaps.copyWith(fontSize: 10),
      ),

      // NavigationBar (Material 3)
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: isDark ? IcheboColors.ink2 : IcheboColors.ink,
        indicatorColor: IcheboColors.primaryLight,
        iconTheme: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const IconThemeData(color: IcheboColors.primary);
          }
          return const IconThemeData(color: IcheboColors.mutedLight);
        }),
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          final base = IcheboTextStyles.labelCaps.copyWith(fontSize: 10);
          if (states.contains(WidgetState.selected)) {
            return base.copyWith(color: IcheboColors.primary);
          }
          return base.copyWith(color: IcheboColors.mutedLight);
        }),
        height: 64,
      ),

      // Cards
      cardTheme: CardThemeData(
        color: surface,
        elevation: 0,
        shape: const RoundedRectangleBorder(borderRadius: IcheboRadius.l),
        margin: EdgeInsets.zero,
      ),

      // Input fields
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: isDark ? IcheboColors.inkLight : IcheboColors.stone,
        border: OutlineInputBorder(
          borderRadius: IcheboRadius.m,
          borderSide: BorderSide(color: border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: IcheboRadius.m,
          borderSide: BorderSide(color: border),
        ),
        focusedBorder: const OutlineInputBorder(
          borderRadius: IcheboRadius.m,
          borderSide: BorderSide(color: IcheboColors.primary, width: 1.5),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: IcheboRadius.m,
          borderSide: BorderSide(
            color: isDark ? IcheboColors.errorDark : IcheboColors.error,
          ),
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: IcheboSpacing.s,
          vertical: IcheboSpacing.xs,
        ),
        hintStyle: IcheboTextStyles.bodyMedium.copyWith(color: muted),
        labelStyle: IcheboTextStyles.labelLarge.copyWith(color: muted),
      ),

      // Elevated button
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: IcheboColors.primary,
          foregroundColor: Colors.white,
          elevation: 0,
          minimumSize: const Size(double.infinity, kMinTouchTarget),
          shape: const RoundedRectangleBorder(borderRadius: IcheboRadius.m),
          textStyle: IcheboTextStyles.labelLarge,
          padding: const EdgeInsets.symmetric(
            horizontal: IcheboSpacing.m,
            vertical: IcheboSpacing.xs,
          ),
        ),
      ),

      // Outlined button
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: IcheboColors.primary,
          side: const BorderSide(color: IcheboColors.primary),
          minimumSize: const Size(double.infinity, kMinTouchTarget),
          shape: const RoundedRectangleBorder(borderRadius: IcheboRadius.m),
          textStyle: IcheboTextStyles.labelLarge,
          padding: const EdgeInsets.symmetric(
            horizontal: IcheboSpacing.m,
            vertical: IcheboSpacing.xs,
          ),
        ),
      ),

      // Text button
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: IcheboColors.primary,
          textStyle: IcheboTextStyles.labelLarge,
          minimumSize: const Size(0, kMinTouchTarget),
        ),
      ),

      // Divider
      dividerTheme: DividerThemeData(
        color: border,
        thickness: 1,
        space: 0,
      ),

      // Chip
      chipTheme: ChipThemeData(
        backgroundColor: isDark ? IcheboColors.inkLight : IcheboColors.stone2,
        labelStyle: IcheboTextStyles.bodySmall.copyWith(color: onSurface),
        padding: const EdgeInsets.symmetric(
          horizontal: IcheboSpacing.xs,
          vertical: IcheboSpacing.xs3,
        ),
        shape: const StadiumBorder(),
      ),

      // List tile
      listTileTheme: ListTileThemeData(
        contentPadding: const EdgeInsets.symmetric(
          horizontal: IcheboSpacing.s,
          vertical: IcheboSpacing.xs3,
        ),
        minVerticalPadding: IcheboSpacing.xs3,
        titleTextStyle: IcheboTextStyles.bodyMedium.copyWith(color: onSurface),
        subtitleTextStyle: IcheboTextStyles.bodySmall.copyWith(color: muted),
      ),

      // Text theme
      textTheme: TextTheme(
        displayLarge: IcheboTextStyles.displayLarge.copyWith(color: onSurface),
        displayMedium: IcheboTextStyles.displayMedium.copyWith(color: onSurface),
        displaySmall: IcheboTextStyles.displaySmall.copyWith(color: onSurface),
        headlineLarge: IcheboTextStyles.headlineLarge.copyWith(color: onSurface),
        titleLarge: IcheboTextStyles.titleLarge.copyWith(color: onSurface),
        titleMedium: IcheboTextStyles.titleMedium.copyWith(color: onSurface),
        bodyLarge: IcheboTextStyles.bodyLarge.copyWith(color: onSurface),
        bodyMedium: IcheboTextStyles.bodyMedium.copyWith(color: onSurface),
        bodySmall: IcheboTextStyles.bodySmall.copyWith(color: muted),
        labelLarge: IcheboTextStyles.labelLarge.copyWith(color: onSurface),
        labelSmall: IcheboTextStyles.labelCaps.copyWith(color: muted),
      ),
    );
  }
}
