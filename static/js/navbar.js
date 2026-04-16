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

  // ── App Drawer & Draggable Bottom Sheet ──────────────────────────────────
  let startY = 0;
  let currentY = 0;
  let isDragging = false;

  function openDrawer(titleText, actionHtml) {
    if (!drawer) return;
    
    if (titleText) {
      const titleEl = document.getElementById('drawerTitle');
      if (titleEl) titleEl.textContent = titleText;
    }

    const actionsEl = document.getElementById('drawerActions');
    if (actionsEl) {
      actionsEl.innerHTML = actionHtml || '';
    }

    drawer.classList.add('active');
    overlay.classList.add('active');
    drawer.style.transform = 'translateY(0)'; // Reset drag pos
    if (window.drawerToggle) window.drawerToggle.setAttribute('aria-expanded', 'true');
  }

  function closeDrawer() {
    if (!drawer) return;
    drawer.classList.remove('active');
    overlay.classList.remove('active');
    drawer.style.transform = ''; // Clear inline transform
    if (window.drawerToggle) window.drawerToggle.setAttribute('aria-expanded', 'false');
  }

  // Touch Drag Logic
  if (drawer) {
    drawer.addEventListener('touchstart', (e) => {
      // Only drag if on the handle or header
      if (e.target.classList.contains('drawer-handle') || e.target.closest('.drawer-header')) {
        startY = e.touches[0].clientY;
        isDragging = true;
        drawer.style.transition = 'none';
      }
    }, { passive: true });

    document.addEventListener('touchmove', (e) => {
      if (!isDragging) return;
      currentY = e.touches[0].clientY;
      const deltaY = currentY - startY;
      
      if (deltaY > 0) { // Only allow dragging down
        drawer.style.transform = `translateY(${deltaY}px)`;
      }
    }, { passive: true });

    document.addEventListener('touchend', (e) => {
      if (!isDragging) return;
      isDragging = false;
      drawer.style.transition = '';
      
      const deltaY = currentY - startY;
      const threshold = 150; // px to close

      if (deltaY > threshold) {
        closeDrawer();
      } else {
        drawer.style.transform = 'translateY(0)';
      }
    });
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
  // Pages can call window.ICSDrawer.open('Title', 'Action HTML') to open the drawer
  window.ICSDrawer = {
    open: openDrawer,
    close: closeDrawer
  };


});
