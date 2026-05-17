/**
 * bible-drawer.js — Bible app drawer control
 * Provides window.ICSDrawer API for opening/closing the drawer
 * Used by Bible topbar settings button and verse taps
 */

document.addEventListener('DOMContentLoaded', () => {
  const drawer = document.getElementById('drawer');
  const overlay = document.getElementById('overlay');
  const closeBtn = document.getElementById('closeBtn');

  if (!drawer) return; // Drawer not present on this page

  function openDrawer(titleText) {
    if (!drawer) return;
    if (titleText) {
      const titleEl = drawer.querySelector('.drawer-title');
      if (titleEl) titleEl.textContent = titleText;
    }
    drawer.classList.add('active');
    if (overlay) overlay.classList.add('active');
  }

  function closeDrawer() {
    if (!drawer) return;
    drawer.classList.remove('active');
    if (overlay) overlay.classList.remove('active');
  }

  if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
  if (overlay)  overlay.addEventListener('click', closeDrawer);

  window.ICSDrawer = {
    open: openDrawer,
    close: closeDrawer
  };
});
