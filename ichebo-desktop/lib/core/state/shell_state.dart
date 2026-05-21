import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

// ── Shell sections (maps to sidebar nav items) ───────────────────────────────

enum ShellSection {
  dashboard,
  desk,
  governance,
  community,
  formation,
  activity,
  bible,
  video,
  tenancy,
}

extension ShellSectionX on ShellSection {
  String get label => switch (this) {
        ShellSection.dashboard => 'Dashboard',
        ShellSection.desk => 'The Desk',
        ShellSection.governance => 'Governance',
        ShellSection.community => 'Community',
        ShellSection.formation => 'Formation',
        ShellSection.activity => 'Activity',
        ShellSection.bible => 'Bible Reader',
        ShellSection.video => 'Video & Broadcast',
        ShellSection.tenancy => 'Tenancy Hub',
      };

  String get watermark => name.toUpperCase();

  String get route => switch (this) {
        ShellSection.dashboard => '/dashboard',
        ShellSection.desk => '/desk',
        ShellSection.governance => '/governance',
        ShellSection.community => '/community',
        ShellSection.formation => '/formation',
        ShellSection.activity => '/activity',
        ShellSection.bible => '/bible',
        ShellSection.video => '/video',
        ShellSection.tenancy => '/tenancy',
      };

  IconData get icon => switch (this) {
        ShellSection.dashboard => Icons.dashboard_outlined,
        ShellSection.desk => Icons.edit_note_outlined,
        ShellSection.governance => Icons.gavel_outlined,
        ShellSection.community => Icons.groups_outlined,
        ShellSection.formation => Icons.school_outlined,
        ShellSection.activity => Icons.task_alt_outlined,
        ShellSection.bible => Icons.menu_book_outlined,
        ShellSection.video => Icons.live_tv_outlined,
        ShellSection.tenancy => Icons.account_balance_outlined,
      };
}

// ── Shell state ───────────────────────────────────────────────────────────────

class ShellState {
  const ShellState({
    this.contextOpen = true,
    this.optionsOpen = false,
    this.themeMode = ThemeMode.dark,
    this.activeSection = ShellSection.dashboard,
    this.commandPaletteOpen = false,
  });

  final bool contextOpen;
  final bool optionsOpen;
  final ThemeMode themeMode;
  final ShellSection activeSection;
  final bool commandPaletteOpen;

  ShellState copyWith({
    bool? contextOpen,
    bool? optionsOpen,
    ThemeMode? themeMode,
    ShellSection? activeSection,
    bool? commandPaletteOpen,
  }) =>
      ShellState(
        contextOpen: contextOpen ?? this.contextOpen,
        optionsOpen: optionsOpen ?? this.optionsOpen,
        themeMode: themeMode ?? this.themeMode,
        activeSection: activeSection ?? this.activeSection,
        commandPaletteOpen: commandPaletteOpen ?? this.commandPaletteOpen,
      );
}

// ── Notifier ──────────────────────────────────────────────────────────────────

class ShellNotifier extends StateNotifier<ShellState> {
  ShellNotifier() : super(const ShellState()) {
    _load();
  }

  static const _themeKey = 'ics_shell_theme';
  static const _contextKey = 'ics_shell_context_open';

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final isDark = prefs.getString(_themeKey) != 'light';
    final contextOpen = prefs.getBool(_contextKey) ?? true;
    state = state.copyWith(
      themeMode: isDark ? ThemeMode.dark : ThemeMode.light,
      contextOpen: contextOpen,
    );
  }

  Future<void> _persist() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_themeKey, state.themeMode == ThemeMode.dark ? 'dark' : 'light');
    await prefs.setBool(_contextKey, state.contextOpen);
  }

  void toggleContext() {
    state = state.copyWith(contextOpen: !state.contextOpen);
    _persist();
  }

  void toggleOptions() {
    state = state.copyWith(optionsOpen: !state.optionsOpen);
  }

  void toggleTheme() {
    state = state.copyWith(
      themeMode: state.themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark,
    );
    _persist();
  }

  void setSection(ShellSection section) {
    state = state.copyWith(activeSection: section);
  }

  void openCommandPalette() {
    state = state.copyWith(commandPaletteOpen: true);
  }

  void closeCommandPalette() {
    state = state.copyWith(commandPaletteOpen: false);
  }

  void setFocusMode(bool active) {
    if (active) {
      state = state.copyWith(contextOpen: false, optionsOpen: false);
    } else {
      state = state.copyWith(contextOpen: true, optionsOpen: false);
    }
    _persist();
  }

  bool get isFocusMode => !state.contextOpen && !state.optionsOpen;
}

final shellProvider = StateNotifierProvider<ShellNotifier, ShellState>(
  (_) => ShellNotifier(),
);
