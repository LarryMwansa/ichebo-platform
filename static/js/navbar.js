document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.getElementById('drawer-toggle');
  const drawer = document.getElementById('app-drawer');

  if (toggleBtn && drawer) {
    toggleBtn.addEventListener('click', () => {
      const isExpanded = toggleBtn.getAttribute('aria-expanded') === 'true';
      toggleBtn.setAttribute('aria-expanded', !isExpanded);
      drawer.style.display = isExpanded ? 'none' : 'block';
    });
  }
});
