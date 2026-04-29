/**
 * workspace.js — Ichebo Platform Desktop Workspace
 * Path: backend/static/js/workspace.js
 *
 * Handles:
 *   - ws-active class management (redundant safety net — inline script does it first)
 *   - Right panel open/close
 *   - Workspace search (keyboard shortcut /)
 *   - Active nav item highlighting based on current URL
 *   - HTMX navigation target routing (mobile vs desktop)
 *
 * Loaded deferred, Level 3+ users only (see base.html).
 */

(function () {
  'use strict';

  /* ── 1. WS-ACTIVE SAFETY NET ───────────────────────────────
     The inline script in base.html handles the first paint.
     This handles any edge cases after full JS load.
  ────────────────────────────────────────────────────────── */
  function syncWsActive() {
    const isDesktop = window.innerWidth >= 1024;
    const layout = document.getElementById('ws-layout');
    const main = document.getElementById('main-content');

    document.body.classList.toggle('ws-active', isDesktop);

    if (layout) layout.setAttribute('aria-hidden', isDesktop ? 'false' : 'true');
    if (main) main.setAttribute('aria-hidden', isDesktop ? 'true' : 'false');
  }

  syncWsActive();
  window.addEventListener('resize', syncWsActive, { passive: true });


  /* ── 2. ACTIVE NAV ITEM ────────────────────────────────────
     Adds .active class to sidebar nav items matching the
     current pathname. Handles both exact and prefix matches.
  ────────────────────────────────────────────────────────── */
  function setActiveNavItem() {
    const path = window.location.pathname;
    const navItems = document.querySelectorAll('.ws-sidebar__nav-item');

    navItems.forEach(function (item) {
      const href = item.getAttribute('href');
      if (!href || href === '#') return;

      // Exact match or prefix match (for sub-pages)
      const isActive = path === href || (href !== '/' && path.startsWith(href));
      item.classList.toggle('active', isActive);
      item.setAttribute('aria-current', isActive ? 'page' : 'false');
    });
  }

  setActiveNavItem();

  // Re-run after HTMX navigation
  document.addEventListener('htmx:pushUrl', setActiveNavItem);
  document.addEventListener('htmx:replaceUrl', setActiveNavItem);


  /* ── 3. HTMX TARGET ROUTING ────────────────────────────────
     On desktop (ws-active), HTMX requests that target
     #main-content should instead target #ws-content so
     content loads into the workspace panel, not the mobile main.
  ────────────────────────────────────────────────────────── */
  document.body.addEventListener('htmx:configRequest', function (evt) {
    if (!document.body.classList.contains('ws-active')) return;

    var target = evt.detail.target;
    if (target && target.id === 'main-content') {
      var wsContent = document.getElementById('ws-content');
      if (wsContent) {
        evt.detail.target = wsContent;
      }
    }
  });


  /* ── 4. SEARCH SHORTCUT ────────────────────────────────────
     Press / to focus the workspace search input.
  ────────────────────────────────────────────────────────── */
  document.addEventListener('keydown', function (e) {
    if (!document.body.classList.contains('ws-active')) return;
    if (e.key !== '/') return;

    // Don't intercept if user is typing in an input
    var tag = document.activeElement.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

    e.preventDefault();
    var searchInput = document.getElementById('ws-search-input');
    if (searchInput) searchInput.focus();
  });


  /* ── 5. RIGHT PANEL ────────────────────────────────────────
     openPanel(title, url) — fetches content via HTMX and
     slides in the right panel.
     closePanel() — hides the panel.
     Panels are triggered by data-ws-panel="url" attributes.
  ────────────────────────────────────────────────────────── */
  var panel = document.querySelector('.ws-panel');
  var panelTitle = panel ? panel.querySelector('.ws-panel__title') : null;
  var panelContent = panel ? panel.querySelector('.ws-panel__content') : null;
  var panelClose = panel ? panel.querySelector('.ws-panel__close') : null;

  window.openWsPanel = function (title, url) {
    if (!panel) return;

    if (panelTitle) panelTitle.textContent = title || 'Details';

    if (url && panelContent) {
      panelContent.innerHTML = '<div style="padding:2rem;text-align:center;color:var(--muted)"><span class="material-symbols-outlined" style="font-size:2rem;opacity:0.4">hourglass_empty</span></div>';

      htmx.ajax('GET', url, {
        target: panelContent,
        swap: 'innerHTML'
      });
    }

    panel.classList.add('ws-panel--open');
    panel.setAttribute('aria-hidden', 'false');
  };

  window.closeWsPanel = function () {
    if (!panel) return;
    panel.classList.remove('ws-panel--open');
    panel.setAttribute('aria-hidden', 'true');
  };

  if (panelClose) {
    panelClose.addEventListener('click', window.closeWsPanel);
  }

  // Close panel on Escape
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && panel && panel.classList.contains('ws-panel--open')) {
      window.closeWsPanel();
    }
  });

  // Wire data-ws-panel triggers
  document.addEventListener('click', function (e) {
    var trigger = e.target.closest('[data-ws-panel]');
    if (!trigger) return;
    if (!document.body.classList.contains('ws-active')) return;

    e.preventDefault();
    var url = trigger.getAttribute('data-ws-panel');
    var title = trigger.getAttribute('data-ws-panel-title') || 'Details';
    window.openWsPanel(title, url);
  });


  /* ── 6. PROFILE MENU (desktop topbar) ─────────────────────
     Reuses the same #profileMenuBtn and .profile-menu
     from navbar.js — no duplicate code needed.
     navbar.js handles this already.
  ────────────────────────────────────────────────────────── */


  /* ── 7. SIDEBAR SCROLL POSITION PERSISTENCE ───────────────
     Remembers sidebar scroll position across page loads.
  ────────────────────────────────────────────────────────── */
  var sidebarScroll = document.querySelector('.ws-sidebar__scroll');

  if (sidebarScroll) {
    var savedScroll = sessionStorage.getItem('ws_sidebar_scroll');
    if (savedScroll) sidebarScroll.scrollTop = parseInt(savedScroll, 10);

    window.addEventListener('beforeunload', function () {
      sessionStorage.setItem('ws_sidebar_scroll', sidebarScroll.scrollTop);
    });
  }

})();
