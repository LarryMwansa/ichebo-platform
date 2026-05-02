/**
 * Editorial Controller (v2)
 * Handles Markdown formatting, auto-saving, and drafting logic.
 */

const EditorialUI = {
    editorId: 'editorial-editor',
    draftsKey: 'ics_editorial_drafts',
    autoSaveInterval: 3000, // 3 seconds
    saveTimer: null,

    init() {
        this.editor = document.getElementById(this.editorId);
        if (!this.editor) return;

        this.setupToolbar();
        this.setupShortcuts();
        this.setupAutoSave();
        this.renderDraftsList();
        this.updatePreview(); // Initial render
    },

    // ── Formatting Logic ─────────────────────────────────────────────────────

    setupToolbar() {
        const toolbar = document.querySelector('.editorial-toolbar');
        if (!toolbar) return;

        toolbar.addEventListener('click', (e) => {
            const btn = e.target.closest('.editorial-toolbar__btn');
            if (!btn) return;

            const action = btn.title.toLowerCase();
            this.handleAction(action);
        });
    },

    handleAction(action) {
        if (!this.editor) return;

        const actions = {
            'bold': { prefix: '**', suffix: '**' },
            'italic': { prefix: '_', suffix: '_' },
            'heading 1': { prefix: '# ', suffix: '', block: true },
            'heading 2': { prefix: '## ', suffix: '', block: true },
            'quote': { prefix: '> ', suffix: '', block: true },
            'link': { prefix: '[', suffix: '](url)' },
        };

        const config = actions[action];
        if (config) {
            this.wrapSelection(config.prefix, config.suffix, config.block);
        }
    },

    wrapSelection(prefix, suffix, isBlock = false) {
        const start = this.editor.selectionStart;
        const end = this.editor.selectionEnd;
        const text = this.editor.value;
        const selection = text.substring(start, end);

        let replacement = '';
        if (isBlock) {
            // Block elements usually need a newline
            replacement = `\n${prefix}${selection}`;
        } else {
            replacement = `${prefix}${selection}${suffix}`;
        }

        this.editor.value = text.substring(0, start) + replacement + text.substring(end);
        
        // Restore focus and selection
        this.editor.focus();
        const newPos = start + prefix.length + (selection.length > 0 ? selection.length : 0) + suffix.length;
        
        // If it's a link and no selection, put cursor inside the URL part
        if (prefix === '[' && suffix === '](url)' && selection.length === 0) {
            const linkPos = start + 3; // After '[' and before '](url)'
            this.editor.setSelectionRange(linkPos, linkPos);
        } else {
            this.editor.setSelectionRange(newPos, newPos);
        }
        
        this.triggerAutoSave();
    },

    setupShortcuts() {
        this.editor.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey)) {
                if (e.key === 'b') { e.preventDefault(); this.handleAction('bold'); }
                if (e.key === 'i') { e.preventDefault(); this.handleAction('italic'); }
                if (e.key === 'p') { e.preventDefault(); this.togglePreview(); }
            }
        });
    },

    togglePreview() {
        const preview = document.getElementById('editorial-preview');
        const btn = document.getElementById('preview-toggle');
        if (!preview || !this.editor) return;

        const isVisible = preview.style.display !== 'none';
        if (isVisible) {
            preview.style.display = 'none';
            this.editor.style.display = 'block';
            if (btn) btn.classList.remove('active');
        } else {
            this.updatePreview();
            preview.style.display = 'block';
            this.editor.style.display = 'none';
            if (btn) btn.classList.add('active');
        }
    },

    updatePreview() {
        const preview = document.getElementById('editorial-preview');
        if (!preview || !this.editor || typeof marked === 'undefined') return;
        preview.innerHTML = marked.parse(this.editor.value);
    },

    // ── Auto-Save Logic ──────────────────────────────────────────────────────

    setupAutoSave() {
        this.editor.addEventListener('input', () => {
            this.updatePreview();
            this.triggerAutoSave();
        });
    },

    triggerAutoSave() {
        clearTimeout(this.saveTimer);
        this.saveTimer = setTimeout(() => this.saveDraft(), this.autoSaveInterval);
    },

    saveDraft() {
        if (!this.editor || !this.editor.value.trim()) return;

        const drafts = JSON.parse(localStorage.getItem(this.draftsKey) || '[]');
        const currentDraft = {
            id: Date.now(),
            title: document.getElementById('record-title')?.value || 'Untitled Draft',
            content: this.editor.value,
            timestamp: new Date().toISOString(),
            type: document.getElementById('record-type')?.value || 'note'
        };

        // For simplicity, we'll just keep the latest 5 drafts
        drafts.unshift(currentDraft);
        const uniqueDrafts = drafts.slice(0, 5);
        
        localStorage.setItem(this.draftsKey, JSON.stringify(uniqueDrafts));
        this.renderDraftsList();
        
        // Visual Feedback: Pulse the status label
        const statusLabel = document.getElementById('save-status');
        if (statusLabel) {
            statusLabel.textContent = 'Draft Saved';
            statusLabel.classList.remove('pulse');
            void statusLabel.offsetWidth; // Trigger reflow
            statusLabel.classList.add('pulse');
            
            setTimeout(() => {
                statusLabel.textContent = 'Drafting Official Act';
            }, 2000);
        }
        
        console.log('Draft auto-saved to localStorage');
    },

    renderDraftsList() {
        const container = document.getElementById('ws-recent-drafts');
        if (!container) return;

        const drafts = JSON.parse(localStorage.getItem(this.draftsKey) || '[]');
        if (drafts.length === 0) {
            container.innerHTML = '<div class="ws_detail-empty" style="padding: var(--space-s); font-size: 11px; color: var(--muted);">No local drafts found.</div>';
            return;
        }

        let html = '<div style="display: flex; flex-direction: column; gap: 4px; margin-top: 8px;">';
        drafts.forEach(draft => {
            const time = new Date(draft.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            html += `
                <div class="ws-draft-item" onclick="EditorialUI.loadDraft(${draft.id})" 
                     style="padding: 8px; border-radius: 4px; cursor: pointer; border: 1px solid transparent; transition: all 0.2s;">
                    <div style="font-size: 12px; font-weight: 600; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${draft.title}</div>
                    <div style="font-size: 10px; color: var(--muted);">${time} · ${draft.type}</div>
                </div>
            `;
        });
        html += '</div>';
        container.innerHTML = html;
    },

    loadDraft(id) {
        const drafts = JSON.parse(localStorage.getItem(this.draftsKey) || '[]');
        const draft = drafts.find(d => d.id === id);
        if (draft && this.editor) {
            if (confirm('Load this draft? Current unsaved work will be replaced.')) {
                this.editor.value = draft.content;
                const titleInput = document.getElementById('record-title');
                if (titleInput) titleInput.value = draft.title;
            }
        }
    }
};

// Initialize on load
document.addEventListener('DOMContentLoaded', () => EditorialUI.init());
document.addEventListener('htmx:afterSwap', () => EditorialUI.init());
