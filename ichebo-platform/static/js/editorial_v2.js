/**
 * EditorialUI — Unified writing controller for ICS Apostolic Command Shell.
 * Used by: Governance Desk, Records Desk, The Desk.
 * No third-party editor dependencies.
 */

const EditorialUI = {
    editorId:        'editorial-editor',
    draftsKey:       'ics_editorial_drafts',
    autoSaveDelay:   2500,
    _saveTimer:      null,
    _focusActive:    false,
    editor:          null,

    // ── Boot ────────────────────────────────────────────────────────────────

    init() {
        this.editor = document.getElementById(this.editorId);
        if (!this.editor) return;

        this._setupAutoSave();
        this._setupShortcuts();
        this._setupWordCount();
        this.renderDraftsList();
        this._syncPreview();
    },

    // ── Formatting actions ───────────────────────────────────────────────────

    handleAction(action) {
        if (!this.editor) return;
        const map = {
            'bold':      { pre: '**',  suf: '**'    },
            'italic':    { pre: '_',   suf: '_'     },
            'heading 1': { pre: '# ',  suf: '',  block: true },
            'heading 2': { pre: '## ', suf: '',  block: true },
            'quote':     { pre: '> ',  suf: '',  block: true },
            'bullet':    { pre: '- ',  suf: '',  block: true },
            'link':      { pre: '[',   suf: '](url)' },
        };
        const cfg = map[action];
        if (cfg) this._wrap(cfg.pre, cfg.suf, cfg.block);
    },

    _wrap(pre, suf, isBlock = false) {
        const el    = this.editor;
        const start = el.selectionStart;
        const end   = el.selectionEnd;
        const val   = el.value;
        const sel   = val.substring(start, end);

        let insert;
        if (isBlock) {
            // If there's a selection, prefix each line
            if (sel.includes('\n')) {
                insert = sel.split('\n').map(l => pre + l).join('\n');
            } else {
                insert = (start > 0 && val[start - 1] !== '\n' ? '\n' : '') + pre + sel;
            }
        } else {
            insert = pre + sel + suf;
        }

        el.value = val.substring(0, start) + insert + val.substring(end);
        el.focus();

        // Position cursor sensibly
        if (pre === '[' && !sel) {
            el.setSelectionRange(start + 1, start + 1); // inside link text
        } else if (isBlock) {
            const newPos = start + insert.length;
            el.setSelectionRange(newPos, newPos);
        } else {
            el.setSelectionRange(start + pre.length + sel.length, start + pre.length + sel.length);
        }

        this._syncPreview();
        this._triggerAutoSave();
    },

    // ── Keyboard shortcuts ───────────────────────────────────────────────────

    _setupShortcuts() {
        if (!this.editor) return;
        this.editor.addEventListener('keydown', (e) => {
            const mod = e.ctrlKey || e.metaKey;
            if (!mod) return;
            if (e.key === 'b') { e.preventDefault(); this.handleAction('bold'); }
            if (e.key === 'i') { e.preventDefault(); this.handleAction('italic'); }
            if (e.key === 'p') { e.preventDefault(); this.togglePreview(); }
            if (e.key === 'F' && e.shiftKey) { e.preventDefault(); this.toggleFocus(); }
            // Tab → indent with spaces inside textarea
            if (e.key === 'Tab') {
                e.preventDefault();
                this._wrap('    ', '', false);
            }
        });
    },

    // ── Live preview ─────────────────────────────────────────────────────────

    togglePreview() {
        const preview = document.getElementById('editorial-preview');
        const split   = document.getElementById('editorial-split');
        const btn     = document.getElementById('preview-toggle');
        if (!preview || !this.editor) return;

        const showing = preview.style.display !== 'none';
        if (showing) {
            // Close preview — textarea takes full width
            preview.style.display = 'none';
            this.editor.style.flex = '1';
            btn && btn.classList.remove('active');
        } else {
            // Open preview side-by-side — both panes share 50/50
            this._syncPreview();
            preview.style.display = '';
            this.editor.style.flex = '1';
            btn && btn.classList.add('active');
        }
    },

    _syncPreview() {
        const preview = document.getElementById('editorial-preview');
        if (!preview || !this.editor) return;
        if (preview.style.display === 'none') return;
        if (typeof marked === 'undefined') return;
        marked.setOptions({ breaks: true, gfm: true });
        preview.innerHTML = marked.parse(this.editor.value || '');
    },

    // ── Focus mode ────────────────────────────────────────────────────────────

    toggleFocus() {
        const btn = document.getElementById('focus-toggle');
        this._focusActive = !this._focusActive;
        document.body.classList.toggle('focus-mode', this._focusActive);
        if (btn) {
            btn.classList.toggle('active', this._focusActive);
            btn.querySelector('.material-symbols-outlined').textContent =
                this._focusActive ? 'fullscreen_exit' : 'fullscreen';
        }
        // Return focus to editor so typing continues uninterrupted
        if (this.editor) this.editor.focus();
    },

    // ── Word count ───────────────────────────────────────────────────────────

    _setupWordCount() {
        if (!this.editor) return;
        this._updateWordCount();
        this.editor.addEventListener('input', () => {
            this._updateWordCount();
            this._syncPreview();
        });
    },

    _updateWordCount() {
        const el = document.getElementById('word-count');
        if (!el || !this.editor) return;
        const words = (this.editor.value.trim().match(/\S+/g) || []).length;
        el.textContent = words === 0 ? '' : `${words} w`;
    },

    // ── Auto-save to localStorage ─────────────────────────────────────────────

    _setupAutoSave() {
        if (!this.editor) return;
        this.editor.addEventListener('input', () => {
            this._syncPreview();
            this._triggerAutoSave();
        });
    },

    _triggerAutoSave() {
        clearTimeout(this._saveTimer);
        this._saveTimer = setTimeout(() => this._saveDraft(), this.autoSaveDelay);
    },

    _saveDraft() {
        if (!this.editor || !this.editor.value.trim()) return;

        const title   = document.getElementById('record-title')?.value || 'Untitled';
        const rtype   = document.getElementById('hidden-record-type')?.value ||
                        document.getElementById('record-type')?.value || 'note';
        const family  = document.getElementById('hidden-record-family')?.value || 'journal';

        const draft = {
            id:        Date.now(),
            title,
            content:   this.editor.value,
            summary:   document.getElementById('record-summary')?.value || '',
            family,
            type:      rtype,
            savedAt:   new Date().toISOString(),
        };

        let drafts = JSON.parse(localStorage.getItem(this.draftsKey) || '[]');
        // Deduplicate by title — replace if same title exists
        drafts = drafts.filter(d => d.title !== draft.title);
        drafts.unshift(draft);
        localStorage.setItem(this.draftsKey, JSON.stringify(drafts.slice(0, 8)));

        this.renderDraftsList();
        this._pulse('Draft saved');
    },

    renderDraftsList() {
        const container = document.getElementById('ws-recent-drafts');
        if (!container) return;

        const drafts = JSON.parse(localStorage.getItem(this.draftsKey) || '[]');
        if (!drafts.length) {
            container.innerHTML = `<div style="padding: 8px 4px; font-size: 11px; color: var(--muted); font-style: italic;">No local drafts.</div>`;
            return;
        }

        container.innerHTML = drafts.map(d => {
            const t = new Date(d.savedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            return `
                <div class="ws-draft-item" onclick="EditorialUI.loadDraft(${d.id})">
                    <div style="font-size: 12px; font-weight: 600; color: var(--text);
                                white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                        ${d.title}
                    </div>
                    <div style="font-size: 10px; color: var(--muted); margin-top: 2px;">
                        ${t} · ${d.family}/${d.type}
                    </div>
                </div>`;
        }).join('');
    },

    loadDraft(id) {
        const drafts = JSON.parse(localStorage.getItem(this.draftsKey) || '[]');
        const draft  = drafts.find(d => d.id === id);
        if (!draft || !this.editor) return;

        if (!confirm(`Load "${draft.title}"? Unsaved work will be replaced.`)) return;

        this.editor.value = draft.content;

        const titleEl   = document.getElementById('record-title');
        const summaryEl = document.getElementById('record-summary');
        const typeEl    = document.getElementById('record-type');
        const hiddenT   = document.getElementById('hidden-record-type');
        const hiddenF   = document.getElementById('hidden-record-family');

        if (titleEl)   titleEl.value   = draft.title;
        if (summaryEl) summaryEl.value = draft.summary || '';
        if (typeEl)    typeEl.value    = draft.type;
        if (hiddenT)   hiddenT.value   = draft.type;
        if (hiddenF)   hiddenF.value   = draft.family;

        this._syncPreview();
        this._updateWordCount();
        this._pulse('Draft loaded');
    },

    // ── Status pulse ──────────────────────────────────────────────────────────

    _pulse(msg) {
        const el = document.getElementById('save-status');
        if (!el) return;
        const prev = el.textContent;
        el.textContent = msg;
        el.classList.remove('pulse');
        void el.offsetWidth;
        el.classList.add('pulse');
        setTimeout(() => {
            el.textContent = prev;
            el.classList.remove('pulse');
        }, 2200);
    },
};

// Boot on first load and after HTMX swaps
document.addEventListener('DOMContentLoaded', () => EditorialUI.init());
document.addEventListener('htmx:afterSwap',   () => EditorialUI.init());
