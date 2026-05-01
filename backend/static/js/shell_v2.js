/**
 * Ichebo Command Shell (v2) — UI State Manager
 * Handles triple-panel toggles and persistence.
 */

const WorkspaceUI = {
  state: {
    contextOpen: true,
    optionsOpen: false,
    sidebarSlim: true,
    theme: 'dark', // Default to dark
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
    
    // Toggle icons and visibility
    const contextBar = document.getElementById('ics-context-bar');
    const optionsBar = document.getElementById('ics-options-bar');
    const contextToggle = document.getElementById('ics-context-toggle');
    const optionsToggle = document.getElementById('ics-options-toggle');
    
    if (contextBar) contextBar.setAttribute('aria-hidden', !this.state.contextOpen);
    if (optionsBar) optionsBar.setAttribute('aria-hidden', !this.state.optionsOpen);

    // Update Stage Toggles
    if (contextToggle) {
        const icon = contextToggle.querySelector('.material-symbols-outlined');
        if (icon) icon.textContent = 'dock_to_right';
        contextToggle.classList.toggle('active', this.state.contextOpen);
    }
    if (optionsToggle) {
        const icon = optionsToggle.querySelector('.material-symbols-outlined');
        if (icon) icon.textContent = 'dock_to_right';
        optionsToggle.classList.toggle('active', this.state.optionsOpen);
    }

    // Theme Management
    if (this.state.theme === 'dark') {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
    
    // Update Theme Toggle Icon
    const themeBtn = document.getElementById('ics-theme-toggle');
    if (themeBtn) {
        themeBtn.querySelector('.material-symbols-outlined').textContent = 
            this.state.theme === 'dark' ? 'light_mode' : 'dark_mode';
    }
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

  toggleTheme() {
    this.state.theme = this.state.theme === 'dark' ? 'light' : 'dark';
    this.applyState();
    this.saveState();
  },

  switchOptionsTab(tabName) {
    // Update Tab Buttons
    document.querySelectorAll('.ics-options-tab').forEach(btn => {
        btn.classList.toggle('active', btn.id === `tab-${tabName}`);
    });
    // Update Panes
    document.querySelectorAll('.ws-options-pane').forEach(pane => {
        pane.classList.toggle('active', pane.id === `pane-${tabName}`);
    });
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
