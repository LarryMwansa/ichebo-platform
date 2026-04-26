/**
 * storage.js — ICS Platform UI State Layer
 * Scope: localStorage for UI-only state (theme preference).
 * Auth, session, and records data are handled server-side by Django.
 *
 * Ported from: archive_old_project/frontend/assets/js/core/storage.js
 * Trimmed: Session, AppStorage, records cache — all removed (live in Django session + DB).
 */

const THEME_KEY = 'ics_theme';

const ICSStorage = (() => {

  // ── Theme ────────────────────────────────────────────────────────────────
  function getTheme() {
    return localStorage.getItem(THEME_KEY) || 'light';
  }

  function setTheme(theme) {
    localStorage.setItem(THEME_KEY, theme);
    if (theme === 'dark') {
      document.body.classList.add('dark');
    } else {
      document.body.classList.remove('dark');
    }
  }

  // Apply immediately on script load to prevent dark/light flash
  document.addEventListener('DOMContentLoaded', () => {
    setTheme(getTheme());
  });

  // ── UI Preferences ───────────────────────────────────────────────────────
  function getUIState(key, fallback = null) {
    try {
      const val = localStorage.getItem(`ics_ui.${key}`);
      return val !== null ? JSON.parse(val) : fallback;
    } catch (_) {
      return fallback;
    }
  }

  function setUIState(key, value) {
    localStorage.setItem(`ics_ui.${key}`, JSON.stringify(value));
  }

  return { getTheme, setTheme, getUIState, setUIState };
})();

window.ICSStorage = ICSStorage;
