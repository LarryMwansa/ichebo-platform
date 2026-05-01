/**
 * Ichebo Command Shell (v2) — UI State Manager
 * Handles triple-panel toggles and persistence.
 */

const WorkspaceUI = {
  state: {
    contextOpen: true,
    optionsOpen: false,
    sidebarSlim: true, // v2 is always slim sidebar
  },

  init() {
    console.log('Initializing Workspace UI v2...');
    this.loadState();
    this.applyState();
    this.bindEvents();
  },

  loadState() {
    const saved = localStorage.getItem('ics_shell_v2_state');
    if (saved) {
      try {
        this.state = { ...this.state, ...JSON.parse(saved) };
      } catch (e) {
        console.error('Failed to parse saved shell state', e);
      }
    }
  },

  saveState() {
    localStorage.setItem('ics_shell_v2_state', JSON.stringify(this.state));
  },

  applyState() {
    const root = document.documentElement;
    root.style.setProperty('--context-state', this.state.contextOpen ? '1' : '0');
    root.style.setProperty('--options-state', this.state.optionsOpen ? '1' : '0');
    
    // Toggle aria-hidden for accessibility
    const contextBar = document.getElementById('ics-context-bar');
    const optionsBar = document.getElementById('ics-options-bar');
    
    if (contextBar) contextBar.setAttribute('aria-hidden', !this.state.contextOpen);
    if (optionsBar) optionsBar.setAttribute('aria-hidden', !this.state.optionsOpen);
  },

  toggleContext() {
    this.state.contextOpen = !this.state.contextOpen;
    this.applyState();
    this.saveState();
  },

  toggleOptions() {
    this.state.optionsOpen = !this.state.optionsOpen;
    this.applyState();
    this.saveState();
  },

  setFocusMode(active) {
    if (active) {
      this.state.contextOpen = false;
      this.state.optionsOpen = false;
    } else {
      this.state.contextOpen = true;
      this.state.optionsOpen = false;
    }
    this.applyState();
    this.saveState();
  },

  bindEvents() {
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      // CMD/CTRL + [ -> Toggle Left Panel
      if ((e.metaKey || e.ctrlKey) && e.key === '[') {
        e.preventDefault();
        this.toggleContext();
      }
      // CMD/CTRL + ] -> Toggle Right Panel
      if ((e.metaKey || e.ctrlKey) && e.key === ']') {
        e.preventDefault();
        this.toggleOptions();
      }
      // CMD/CTRL + \ -> Toggle Both Panels (Focus Mode)
      if ((e.metaKey || e.ctrlKey) && e.key === '\\') {
        e.preventDefault();
        const isFocus = !this.state.contextOpen && !this.state.optionsOpen;
        this.setFocusMode(!isFocus);
      }
    });

    // Handle HTMX events if needed
    document.addEventListener('htmx:afterOnLoad', () => {
      // Logic to run after partial content loads
    });
  }
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => WorkspaceUI.init());

// Export to window for global access
window.WorkspaceUI = WorkspaceUI;
