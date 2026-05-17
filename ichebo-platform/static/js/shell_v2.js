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

  openSearch() {
    const overlay = document.getElementById('ws-search-overlay');
    const input = document.getElementById('ws-global-search-input');
    if (overlay) {
        overlay.classList.add('active');
        this.state.searchFocusIndex = -1; // Reset focus
        if (input) {
            input.value = '';
            input.focus();
            this.handleSearchInput(input.value); // Show default
        }
    }
  },

  closeSearch() {
    const overlay = document.getElementById('ws-search-overlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
  },

  handleSearchInput(val) {
    const resultsContainer = document.getElementById('ws-global-search-results');
    if (val.startsWith('>')) {
        this.renderCommandMode(val.slice(1).trim());
    }
    // HTMX handles the server search automatically via hx-get/hx-trigger
  },

  renderCommandMode(query) {
    const resultsContainer = document.getElementById('ws-global-search-results');
    const commands = [
        { title: 'Toggle Theme', meta: 'Switch Light/Dark mode', icon: 'contrast', action: () => this.toggleTheme() },
        { title: 'Focus Mode', meta: 'Toggle sidebars for writing', icon: 'visibility_off', action: () => this.setFocusMode() },
        { title: 'Open Desk', meta: 'Go to Editorial Desk', icon: 'draw', action: '/governance/desk/' },
        { title: 'Open Calendar', meta: 'View institutional schedule', icon: 'calendar_month', action: '/calendar/' },
        { title: 'Knowledge Graph', meta: 'Apostolic Web visualization', icon: 'hub', action: '/records/graph/' },
    ];

    const filtered = commands.filter(c => c.title.toLowerCase().includes(query.toLowerCase()));
    
    let html = `<div class="ws-search-group">
        <div class="label-caps" style="padding: var(--space-s) var(--space-m); color: var(--accent-red);">System Command Mode</div>`;
    
    filtered.forEach((c, i) => {
        html += `
            <button class="ws-command-item command-mode-item" onclick="WorkspaceUI.executeCommand(${i})">
                <span class="material-symbols-outlined">${c.icon}</span>
                <div class="ws-command-item__info">
                    <div class="ws-command-item__title">${c.title}</div>
                    <div class="ws-command-item__meta">${c.meta}</div>
                </div>
                <kbd>↵</kbd>
            </button>`;
    });

    if (filtered.length === 0) {
        html += `<div style="padding: 20px; opacity: 0.5; font-size: 12px;">No system commands matching "${query}"</div>`;
    }

    html += `</div>`;
    resultsContainer.innerHTML = html;
    this.state.activeCommands = filtered;
    this.updateSearchFocus(0);
  },

  switchOptionsTab(tabName) {
    document.querySelectorAll('.ics-options-tab').forEach(btn => {
        btn.classList.toggle('active', btn.id === `tab-${tabName}`);
    });
    document.querySelectorAll('.ws-options-pane').forEach(pane => {
        pane.classList.toggle('active', pane.id === `pane-${tabName}`);
    });
  },

  setFocusMode(active) {
    if (active === undefined) {
      const isCurrentlyFocus = !this.state.contextOpen && !this.state.optionsOpen;
      active = !isCurrentlyFocus;
    }

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

  executeCommand(index) {
    const cmd = this.state.activeCommands && this.state.activeCommands[index];
    if (cmd) {
        this.closeSearch();
        if (typeof cmd.action === 'function') {
            cmd.action();
        } else if (typeof cmd.action === 'string') {
            window.location.href = cmd.action;
        }
    }
  },

  updateSearchFocus(newIndex) {
    const items = document.querySelectorAll('.ws-command-item, .ws-search-group a');
    if (items.length === 0) return;

    // Boundary check
    if (newIndex < 0) newIndex = items.length - 1;
    if (newIndex >= items.length) newIndex = 0;

    this.state.searchFocusIndex = newIndex;

    items.forEach((item, i) => {
        if (i === newIndex) {
            item.classList.add('focused');
            item.scrollIntoView({ block: 'nearest' });
        } else {
            item.classList.remove('focused');
        }
    });
  },

  bindEvents() {
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      const searchOverlay = document.getElementById('ws-search-overlay');
      const isSearchOpen = searchOverlay && searchOverlay.classList.contains('active');

      if (isSearchOpen) {
          if (e.key === 'ArrowDown') {
              e.preventDefault();
              this.updateSearchFocus(this.state.searchFocusIndex + 1);
          } else if (e.key === 'ArrowUp') {
              e.preventDefault();
              this.updateSearchFocus(this.state.searchFocusIndex - 1);
          } else if (e.key === 'Enter') {
              e.preventDefault();
              const focusedItem = document.querySelector('.ws-command-item.focused, .ws-search-group a.focused');
              if (focusedItem) focusedItem.click();
          }
      }

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
      // CMD/CTRL + / -> Command Palette
      if ((e.metaKey || e.ctrlKey) && e.key === '/') {
        e.preventDefault();
        this.openSearch();
      }
      // ESC -> Close Search
      if (e.key === 'Escape') {
        this.closeSearch();
      }
    });

    // Close on click outside
    const searchOverlay = document.getElementById('ws-search-overlay');
    if (searchOverlay) {
        searchOverlay.addEventListener('click', (e) => {
            if (e.target === searchOverlay) this.closeSearch();
        });
    }

    // Prevent HTMX search when in Command Mode (starting with '>')
    document.addEventListener('htmx:beforeRequest', (e) => {
      if (e.detail.target.id === 'ws-global-search-results') {
          const input = document.getElementById('ws-global-search-input');
          if (input && input.value.startsWith('>')) {
              e.preventDefault(); // Stop HTMX from overwriting local command results
          }
      }
    });

    document.addEventListener('htmx:afterOnLoad', () => {
      // Logic to run after partial content loads
    });
  }
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => WorkspaceUI.init());

// Export to window for global access
window.WorkspaceUI = WorkspaceUI;
