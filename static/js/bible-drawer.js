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

  function openDrawer() {
    drawer.classList.add('active');
    if (overlay) overlay.classList.add('active');
  }

  function closeDrawer() {
    drawer.classList.remove('active');
    if (overlay) overlay.classList.remove('active');
  }

  // Close drawer when close button clicked
  if (closeBtn) {
    closeBtn.addEventListener('click', closeDrawer);
  }

  // Close drawer when overlay clicked
  if (overlay) {
    overlay.addEventListener('click', closeDrawer);
  }

  // Expose drawer API to window
  window.ICSDrawer = {
    open: openDrawer,
    close: closeDrawer
  };
});
