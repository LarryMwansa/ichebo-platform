/**
 * EditorialUI — Unified writing controller for ICS Apostolic Command Shell.
 * Used by: Governance Desk, Records Desk, The Desk, Handbook.
 * No third-party editor dependencies.
 *
 * Supports multiple concurrent editor instances on one page, keyed by a
 * suffix string ('' for the default/only instance, e.g. '-mobile' for a
 * second copy). This matters because pages like handbook/record.html
 * render the editor partial twice — once inside the desktop shell, once
 * inside the mobile shell (they're sibling DOM subtrees toggled by CSS
 * breakpoint, not one shared node) — so every id in the partial is
 * suffixed per-instance, and this controller must operate on the suffix
 * that was actually interacted with, not always the first instance in
 * document order.
 */

const EditorialUI = {
    draftsKey:     'ics_editorial_drafts',
    autoSaveDelay: 2500,
    _instances:    {},   // suffix -> { editor, cmView, focusActive, saveTimer }

    _state(sfx) {
        sfx = sfx || '';
        if (!this._instances[sfx]) {
            this._instances[sfx] = {
                editor:      null,
                cmView:      null,
                focusActive: false,
                saveTimer:   null,
            };
        }
        return this._instances[sfx];
    },

    // ── Boot ────────────────────────────────────────────────────────────────

    init(sfx) {
        sfx = sfx || '';
        const st = this._state(sfx);
        st.editor = document.getElementById('editorial-editor' + sfx);
        if (!st.editor) return;
        this._setupAutoSave(sfx);
        this._setupShortcuts(sfx);
        this._setupWordCount(sfx);
        this.renderDraftsList();
    },

    // ── CodeMirror 6 init ────────────────────────────────────────────────────

    initCM6(sfx) {
        sfx = sfx || '';
        const st = this._state(sfx);
        const mount = document.getElementById('cm-editor-mount' + sfx);
        if (!mount || !st.editor || typeof createMarkdownEditor === 'undefined') return;

        // Destroy previous instance if re-initialising (HTMX swap)
        if (st.cmView) {
            st.cmView.destroy();
            st.cmView = null;
        }

        const darkMode = document.documentElement.classList.contains('dark') ||
                         document.body.classList.contains('dark');

        st.cmView = createMarkdownEditor({
            targetId:     'cm-editor-mount' + sfx,
            initialValue: st.editor.value,
            darkMode,
            onChange: (val) => {
                // Keep hidden textarea in sync so form submission works
                st.editor.value = val;
                this._updateWordCount(sfx);
                this._triggerAutoSave(sfx);
            },
        });
    },

    // ── Formatting actions ───────────────────────────────────────────────────

    handleAction(sfx, action) {
        sfx = sfx || '';
        const st = this._state(sfx);
        if (!st.editor) return;
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
        if (cfg) this._wrap(sfx, cfg.pre, cfg.suf, cfg.block);
    },

    _wrap(sfx, pre, suf, isBlock = false) {
        sfx = sfx || '';
        const st = this._state(sfx);

        // Route through CodeMirror 6 when available
        if (st.cmView) {
            const view  = st.cmView;
            const state = view.state;
            const { from, to } = state.selection.main;
            const sel = state.sliceDoc(from, to);

            let insert;
            if (isBlock) {
                const lineStart = state.doc.lineAt(from).from;
                const prefix    = from > 0 && state.sliceDoc(lineStart, from) !== '' ? '\n' : '';
                insert = sel.includes('\n')
                    ? sel.split('\n').map(l => pre + l).join('\n')
                    : prefix + pre + sel;
            } else {
                insert = pre + sel + suf;
            }

            view.dispatch({
                changes: { from, to, insert },
                selection: { anchor: from + (pre === '[' && !sel ? 1 : insert.length) },
            });
            view.focus();
            return;
        }

        // Fallback: operate on hidden textarea directly
        const el = st.editor;
        if (!el) return;
        const start = el.selectionStart;
        const end   = el.selectionEnd;
        const val   = el.value;
        const sel   = val.substring(start, end);
        let insert;
        if (isBlock) {
            insert = (start > 0 && val[start - 1] !== '\n' ? '\n' : '') + pre + sel;
        } else {
            insert = pre + sel + suf;
        }
        el.value = val.substring(0, start) + insert + val.substring(end);
        el.focus();
        el.setSelectionRange(start + pre.length + sel.length, start + pre.length + sel.length);
        this._triggerAutoSave(sfx);
    },

    // ── Keyboard shortcuts ───────────────────────────────────────────────────

    _setupShortcuts(sfx) {
        sfx = sfx || '';
        const st = this._state(sfx);
        if (!st.editor) return;
        st.editor.addEventListener('keydown', (e) => {
            const mod = e.ctrlKey || e.metaKey;
            if (!mod) return;
            if (e.key === 'b') { e.preventDefault(); this.handleAction(sfx, 'bold'); }
            if (e.key === 'i') { e.preventDefault(); this.handleAction(sfx, 'italic'); }
            if (e.key === 'p') { e.preventDefault(); this.togglePreview(sfx); }
            if (e.key === 'F' && e.shiftKey) { e.preventDefault(); this.toggleFocus(sfx); }
            // Tab → indent with spaces inside textarea
            if (e.key === 'Tab') {
                e.preventDefault();
                this._wrap(sfx, '    ', '', false);
            }
        });
    },

    // ── Read / Write toggle ──────────────────────────────────────────────────

    togglePreview(sfx) {
        sfx = sfx || '';
        const st = this._state(sfx);
        const mount   = document.getElementById('cm-editor-mount' + sfx);
        const preview = document.getElementById('editorial-preview' + sfx);
        const btn     = document.getElementById('preview-toggle' + sfx);
        if (!preview) return;

        const reading = preview.style.display !== 'none';
        if (reading) {
            // Switch to Write mode — show CodeMirror, hide preview
            preview.style.display = 'none';
            if (mount) mount.style.display = '';
            btn && btn.classList.remove('active');
            btn && btn.setAttribute('title', 'Reading View');
            if (st.cmView) st.cmView.focus();
        } else {
            // Switch to Read mode — render markdown, hide CodeMirror
            if (typeof marked !== 'undefined') {
                marked.setOptions({ breaks: true, gfm: true });
                preview.innerHTML = marked.parse(st.editor ? st.editor.value : '');
            }
            if (mount) mount.style.display = 'none';
            preview.style.display = '';
            btn && btn.classList.add('active');
            btn && btn.setAttribute('title', 'Write Mode');
        }
    },

    _syncPreview() {
        // No-op — preview is now rendered on demand via togglePreview
    },

    // ── Focus mode ────────────────────────────────────────────────────────────

    toggleFocus(sfx) {
        sfx = sfx || '';
        const st = this._state(sfx);
        const btn = document.getElementById('focus-toggle' + sfx);
        st.focusActive = !st.focusActive;
        document.body.classList.toggle('focus-mode', st.focusActive);
        if (btn) {
            btn.classList.toggle('active', st.focusActive);
            btn.querySelector('.material-symbols-outlined').textContent =
                st.focusActive ? 'fullscreen_exit' : 'fullscreen';
        }
        // Return focus to editor so typing continues uninterrupted
        if (st.editor) st.editor.focus();
    },

    // ── Word count ───────────────────────────────────────────────────────────

    _setupWordCount(sfx) {
        sfx = sfx || '';
        const st = this._state(sfx);
        if (!st.editor) return;
        this._updateWordCount(sfx);
        st.editor.addEventListener('input', () => {
            this._updateWordCount(sfx);
            this._syncPreview();
        });
    },

    _updateWordCount(sfx) {
        sfx = sfx || '';
        const st = this._state(sfx);
        const el = document.getElementById('word-count' + sfx);
        if (!el || !st.editor) return;
        const words = (st.editor.value.trim().match(/\S+/g) || []).length;
        el.textContent = words === 0 ? '' : `${words} w`;
    },

    // ── Auto-save to localStorage ─────────────────────────────────────────────

    _setupAutoSave(sfx) {
        sfx = sfx || '';
        const st = this._state(sfx);
        if (!st.editor) return;
        st.editor.addEventListener('input', () => {
            this._syncPreview();
            this._triggerAutoSave(sfx);
        });
    },

    _triggerAutoSave(sfx) {
        sfx = sfx || '';
        const st = this._state(sfx);
        clearTimeout(st.saveTimer);
        st.saveTimer = setTimeout(() => this._saveDraft(sfx), this.autoSaveDelay);
    },

    _saveDraft(sfx) {
        sfx = sfx || '';
        const st = this._state(sfx);
        if (!st.editor || !st.editor.value.trim()) return;

        const title   = document.getElementById('record-title' + sfx)?.value || 'Untitled';
        const rtype   = document.getElementById('hidden-record-type' + sfx)?.value ||
                        document.getElementById('record-type' + sfx)?.value || 'note';
        const family  = document.getElementById('hidden-record-family' + sfx)?.value || 'journal';

        const draft = {
            id:        Date.now(),
            title,
            content:   st.editor.value,
            summary:   document.getElementById('record-summary' + sfx)?.value || '',
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
        this._pulse(sfx, 'Draft saved');
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

    loadDraft(id, sfx) {
        sfx = sfx || '';
        const st = this._state(sfx);
        const drafts = JSON.parse(localStorage.getItem(this.draftsKey) || '[]');
        const draft  = drafts.find(d => d.id === id);
        if (!draft || !st.editor) return;

        if (!confirm(`Load "${draft.title}"? Unsaved work will be replaced.`)) return;

        st.editor.value = draft.content;
        if (st.cmView) {
            st.cmView.dispatch({
                changes: { from: 0, to: st.cmView.state.doc.length, insert: draft.content },
            });
        }

        const titleEl   = document.getElementById('record-title' + sfx);
        const summaryEl = document.getElementById('record-summary' + sfx);
        const typeEl    = document.getElementById('record-type' + sfx);
        const hiddenT   = document.getElementById('hidden-record-type' + sfx);
        const hiddenF   = document.getElementById('hidden-record-family' + sfx);

        if (titleEl)   titleEl.value   = draft.title;
        if (summaryEl) summaryEl.value = draft.summary || '';
        if (typeEl)    typeEl.value    = draft.type;
        if (hiddenT)   hiddenT.value   = draft.type;
        if (hiddenF)   hiddenF.value   = draft.family;

        this._syncPreview();
        this._updateWordCount(sfx);
        this._pulse(sfx, 'Draft loaded');
    },

    // ── Status pulse ──────────────────────────────────────────────────────────

    _pulse(sfx, msg) {
        sfx = sfx || '';
        const el = document.getElementById('save-status' + sfx);
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
