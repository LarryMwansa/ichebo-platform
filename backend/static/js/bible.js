/**
 * bible.js — Bible reader utilities
 * Handles synchronized scroll hide/show for topbar, navigator strip, and bottom bar
 */

document.addEventListener('DOMContentLoaded', () => {
  const SCROLL_THRESHOLD = 8; // pixels
  let lastScrollY = window.scrollY;

  const topbar = document.querySelector('.bible-topbar');
  const navStrip = document.querySelector('.bible-nav-strip');
  const bottomBar = document.querySelector('.bottom-bar');

  // Check if any of these elements exist (they won't on non-reader pages)
  if (!topbar && !navStrip && !bottomBar) {
    return;
  }

  /**
   * Hide/show chrome on scroll
   */
  window.addEventListener(
    'scroll',
    () => {
      const currentY = window.scrollY;
      const delta = currentY - lastScrollY;

      if (Math.abs(delta) < SCROLL_THRESHOLD) {
        return; // Not enough movement, ignore
      }

      if (delta > 0 && delta >= SCROLL_THRESHOLD) {
        // Scrolling down — hide chrome
        topbar?.classList.add('scroll-hidden');
        navStrip?.classList.add('scroll-hidden');
        bottomBar?.classList.add('scroll-hidden');
      } else if (delta < 0 && delta <= -SCROLL_THRESHOLD) {
        // Scrolling up — show chrome
        topbar?.classList.remove('scroll-hidden');
        navStrip?.classList.remove('scroll-hidden');
        bottomBar?.classList.remove('scroll-hidden');
      }

      lastScrollY = currentY;
    },
    { passive: true }
  );
});
