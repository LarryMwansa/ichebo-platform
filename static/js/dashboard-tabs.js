/**
 * dashboard-tabs.js — Scrollable pill tabs for dashboard
 * Handles tab switching and scroll detection
 */

document.addEventListener('DOMContentLoaded', () => {
  const tabsContainer = document.querySelector('.dashboard-tabs');

  if (!tabsContainer) return; // Exit if no tabs on this page

  const tabs = tabsContainer.querySelectorAll('.dashboard-tab');
  const panes = document.querySelectorAll('.dashboard-pane');

  // Tab click handler
  tabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
      e.preventDefault();

      const tabId = tab.getAttribute('data-tab');
      if (!tabId) return;

      // Remove active from all tabs and panes
      tabs.forEach(t => t.classList.remove('active'));
      panes.forEach(p => p.classList.remove('active'));

      // Add active to clicked tab and corresponding pane
      tab.classList.add('active');
      const pane = document.getElementById(tabId);
      if (pane) {
        pane.classList.add('active');
        // Fire tabActivated so HTMX lazy-load partials can trigger once
        if (typeof htmx !== 'undefined') {
          htmx.trigger(pane, 'tabActivated');
        }
      }

      // Scroll tab into view
      tab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    });
  });

  // Detect scroll and show/hide right indicator
  function updateScrollIndicator() {
    const isScrollable = tabsContainer.scrollWidth > tabsContainer.clientWidth;
    const isScrolledRight =
      tabsContainer.scrollLeft + tabsContainer.clientWidth < tabsContainer.scrollWidth - 10;

    if (isScrollable && isScrolledRight) {
      tabsContainer.classList.add('scrollable');
    } else {
      tabsContainer.classList.remove('scrollable');
    }
  }

  tabsContainer.addEventListener('scroll', updateScrollIndicator);
  window.addEventListener('resize', updateScrollIndicator);

  // Initial check
  updateScrollIndicator();
});
