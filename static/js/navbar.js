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
  const launcherBtn  = document.getElementById('launcherBtn');

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

  // Pointer Drag Logic (Universal for Touch and Mouse)
  if (drawer) {
    drawer.addEventListener('pointerdown', (e) => {
      // Only drag if on the handle or header
      if (e.target.classList.contains('drawer-handle') || e.target.closest('.drawer-header')) {
        startY = e.clientY;
        isDragging = true;
        drawer.style.transition = 'none';
        drawer.setPointerCapture(e.pointerId);
      }
    });

    drawer.addEventListener('pointermove', (e) => {
      if (!isDragging) return;
      currentY = e.clientY;
      const deltaY = currentY - startY;
      
      if (deltaY > 0) { // Only allow dragging down
        drawer.style.transform = `translateY(${deltaY}px)`;
      }
    });

    drawer.addEventListener('pointerup', (e) => {
      if (!isDragging) return;
      isDragging = false;
      drawer.style.transition = '';
      drawer.releasePointerCapture(e.pointerId);
      
      const deltaY = e.clientY - startY;
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

  themeToggle && themeToggle.addEventListener('click', () => {
    const current = window.ICSStorage.getTheme();
    const next = current === 'dark' ? 'light' : 'dark';
    window.ICSStorage.setTheme(next);
  });

  // ── App Launcher ──────────────────────────────────────────────────────────
  launcherBtn && launcherBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    window._pendingDrawerTitle = 'ICS Ecosystem';
    
    htmx.ajax('GET', '/htmx/launcher/', {
      target: '#drawerInner',
      swap: 'innerHTML'
    });
    
    if (window.navigator && window.navigator.vibrate) {
      window.navigator.vibrate(10);
    }
  });

  // ── FAB (Floating Action Button) ──────────────────────────────────────────
  const fabBtn = document.getElementById('fabBtn');
  
  fabBtn && fabBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    fabBtn.classList.toggle('active');
    
    // Context-aware: determine create URL based on current page
    const path = window.location.pathname;
    let createUrl = '/records/htmx/create/';
    let title = 'New Entry';

    if (path.startsWith('/activity')) {
      createUrl = '/activity/htmx/create/';
      title = 'New Activity';
    } else if (path.startsWith('/governance')) {
      createUrl = '/governance/htmx/record/create/';
      title = 'New Document';
    } else if (path.includes('/explore')) {
      createUrl = '/htmx/explore-menu/';
      title = 'Quick Create';
    } else if (path.includes('/you')) {
      createUrl = '/activity/htmx/create/';
      title = 'New Activity';
    }

    // Load context-aware form into drawer
    // The htmx:beforeRequest listener will handle opening the drawer + title
    window._pendingDrawerTitle = title;
    htmx.ajax('GET', createUrl, {
      target: '#drawerInner',
      swap: 'innerHTML'
    });

    fabBtn.classList.remove('active');

    if (window.navigator && window.navigator.vibrate) {
      window.navigator.vibrate(10);
    }
  });

  // ── Drawer API (for pages to open drawer programmatically) ──────────────────
  window.ICSDrawer = {
    open: openDrawer,
    close: closeDrawer
  };

  // ── Automated Drawer Management (Lasting Solution) ────────────────────────
  document.body.addEventListener('htmx:beforeRequest', (e) => {
    document.body.classList.add('htmx-loading'); // Global loading state
    const target = e.detail.target;
    if (target && (target.id === 'drawerContent' || target.id === 'drawerInner')) {
      // If we don't have a pending title, and the drawer isn't active, show Loading
      // If the drawer IS active, don't flicker the title back to Loading
      if (window._pendingDrawerTitle) {
        openDrawer(window._pendingDrawerTitle);
        window._pendingDrawerTitle = null;
      } else if (!drawer.classList.contains('active')) {
        openDrawer('Loading...');
      }
    }
  });


  document.body.addEventListener('htmx:afterRequest', () => {
    document.body.classList.remove('htmx-loading');
  });

  document.body.addEventListener('htmx:afterSwap', (e) => {
    const target = e.detail.target;
    if (target && (target.id === 'drawerContent' || target.id === 'drawerInner')) {
      htmx.process(target);
      if (!drawer.classList.contains('active')) {
        openDrawer();
      }
    }
  });
});


