/**
 * storage.js — ICS Platform UI Preferences Layer
 * Thin wrapper around localStorage for UI state (font size, reader prefs, etc).
 * Theme on workspace pages is owned by WorkspaceUI (shell_v2.js) — do NOT
 * auto-apply theme here, as it would clobber the workspace shell's theme state.
 */

const THEME_KEY = 'ics_theme';

const ICSStorage = (() => {

  // ── Theme — used by mobile/old-shell pages via navbar.js ─────────────────
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

  // ── UI Preferences ────────────────────────────────────────────────────────
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
