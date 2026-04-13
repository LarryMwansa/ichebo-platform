/**
 * navbar.js — ICS Platform UI Shell
 * Handles: app drawer, overlay, profile dropdown, options menu, theme toggle.
 * Pure UI state — no server calls, no auth logic (all handled by Django).
 *
 * Ported from: archive_old_project/frontend/assets/js/components/
 */

document.addEventListener('DOMContentLoaded', () => {

  // ── Elements ──────────────────────────────────────────────────────────────
  const closeBtn      = document.getElementById('closeBtn');
  const drawer        = document.getElementById('drawer');
  const overlay       = document.getElementById('overlay');
  const profileBtn    = document.getElementById('profileBtn');
  const profileMenu   = document.getElementById('profileMenu');
  const optionsBtn    = document.getElementById('optionsBtn');
  const optionsMenu   = document.getElementById('optionsMenu');
  const themeToggle   = document.getElementById('themeToggle');

  // ── App Drawer ────────────────────────────────────────────────────────────
  function openDrawer() {
    if (!drawer) return;
    drawer.classList.add('active');
    overlay.classList.add('active');
    drawerToggle && drawerToggle.setAttribute('aria-expanded', 'true');
  }

  function closeDrawer() {
    if (!drawer) return;
    drawer.classList.remove('active');
    overlay.classList.remove('active');
    drawerToggle && drawerToggle.setAttribute('aria-expanded', 'false');
  }

  closeBtn && closeBtn.addEventListener('click', closeDrawer);
  overlay  && overlay.addEventListener('click', () => {
    closeDrawer();
    closeAllMenus();
  });

  // ── Profile Dropdown ──────────────────────────────────────────────────────
  function closeAllMenus() {
    profileMenu  && profileMenu.classList.remove('active');
    optionsMenu  && optionsMenu.classList.remove('active');
    profileBtn   && profileBtn.setAttribute('aria-expanded', 'false');
    optionsBtn   && optionsBtn.setAttribute('aria-expanded', 'false');
  }

  profileBtn && profileBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = profileMenu.classList.contains('active');
    closeAllMenus();
    if (!isOpen) {
      profileMenu.classList.add('active');
      profileBtn.setAttribute('aria-expanded', 'true');
    }
  });

  // ── Options Menu ──────────────────────────────────────────────────────────
  optionsBtn && optionsBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = optionsMenu.classList.contains('active');
    closeAllMenus();
    if (!isOpen) {
      optionsMenu.classList.add('active');
      optionsBtn.setAttribute('aria-expanded', 'true');
    }
  });

  // Close menus on any outside click
  document.addEventListener('click', closeAllMenus);

  // ── Bottom nav active state ───────────────────────────────────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll('.bottom-bar .nav-item').forEach(item => {
    const href = item.getAttribute('href');
    if (href && href !== '#' && currentPath.startsWith(href)) {
      item.classList.add('active');
    }
  });

  // ── Theme Toggle ──────────────────────────────────────────────────────────
  const THEME_KEY = 'ics_theme';

  function applyTheme(theme) {
    if (theme === 'dark') {
      document.body.classList.add('dark');
    } else {
      document.body.classList.remove('dark');
    }
    localStorage.setItem(THEME_KEY, theme);
  }

  // Apply saved theme on load
  const savedTheme = localStorage.getItem(THEME_KEY) || 'light';
  applyTheme(savedTheme);

  themeToggle && themeToggle.addEventListener('click', () => {
    const isDark = document.body.classList.contains('dark');
    applyTheme(isDark ? 'light' : 'dark');
  });

  // ── Drawer API (for pages to open drawer programmatically) ──────────────────
  // Pages can call window.ICSDrawer.open() to open the drawer
  window.ICSDrawer = {
    open: openDrawer,
    close: closeDrawer
  };

});
