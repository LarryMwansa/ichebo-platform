const ICSStorage = (() => {
  const THEME_KEY = 'ics_theme';

  function getTheme() {
    return localStorage.getItem(THEME_KEY) ?? 'system';
  }

  function setTheme(theme) {
    localStorage.setItem(THEME_KEY, theme);
    document.documentElement.setAttribute('data-theme', theme);
  }

  setTheme(getTheme());

  return { getTheme, setTheme };
})();
