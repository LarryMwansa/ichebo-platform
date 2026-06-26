Attached Element Context from Integrated Browser

Element: div

URL: http://localhost:8001/handbook/records/new/

HTML Path: div#ics-shell.ics-shell > aside#ics-options-bar.ics-options-bar > div.ics-options-bar__content > div#pane-relations.ws-options-pane.active > div

Outer HTML:
```html
<div style="padding: var(--space-m);">
                        
    <div id="dynamic-stewardship-panel" style="display: flex; flex-direction: column; height: 100%; overflow: hidden;">

    
    <div style="display: flex; border-bottom: 1px solid var(--border); margin-bottom: 16px; flex-shrink: 0;">
        <button class="desk-tab desk-tab--active" data-tab="details" onclick="DeskTabs.show('details', this)">Details</button>
        <button class="desk-tab" data-tab="relations" onclick="DeskTabs.show('relations', this)">Relations</button>
        <button class="desk-tab" data-tab="recent" onclick="DeskTabs.show('recent', this)">Recent</button>
    </div>

    <div id="desk-tab-details" class="desk-tab-pane" style="overflow-y: auto; flex: 1; padding-right: 2px;">

        
        <div class="dopt-section">
            <div class="ws-label-tag" style="margin-bottom: 8px;">Status</div>
            <select name="status" class="editorial-type-picker" style="width: 100%;" form="editorial-form">
                <option value="draft">Draft</option>
                <option value="active" selected="">Active</option>
                <option value="archived">Archived</option>
            </select>
        </div>

        <div class="dopt-divider"></div>

        
        <div id="fields-journal" class="dynamic-field-group dopt-section">
            <div class="ws-label-tag" style="margin-bottom: 8px;">Journal</div>
            <div class="dopt-field">
                <label class="dopt-label">Mood / Tone</label>
                <select name="mood" class="editorial-type-picker" style="width: 100%;" form="editorial-form">
                    <option value="">— not set —</option>
                    <option value="reflective">Reflective</option>
                    <option value="grateful">Grateful</option>
                    <option value="burdened">Burdened</option>
                    <option value="hopeful">Hopeful</option>
                    <option value="urgent">Urgent</option>
                </select>
            </div>
        </div>

        
        <div id="fields-governance" class="dynamic-field-group dopt-section" style="display: none;">
            <div class="ws-label-tag" style="margin-bottom: 8px;">Governance</div>
            <div class="dopt-field">
                <label class="dopt-label">Record Class</label>
                <select name="record_class" class="editorial-type-picker" style="width: 100%;" form="editorial-form">
                    <option value="personal">Personal</option>
                    <option value="organizational">Organizational</option>
                    <option value="governance" selected="">Apostolic Decree</option>
                </select>
            </div>
            <div class="dopt-field">
                <label class="dopt-label">Version</label>
                <input type="number" name="version" value="1" min="1" class="editorial-type-picker" style="width: 100%;" form="editorial-form">
            </div>

            <div class="dopt-divider"></div>

            <div class="ws-label-tag" style="margin-bottom: 4px; color: var(--accent-red);">HRS Stewardship</div>
            <p style="font-size: 11px; color: var(--muted); margin: 0 0 12px; line-height: 1.5;">
                Tune the HRS properties of this act.
            </p>

            <div class="dopt-field">
                <label class="dopt-label">Complexity</label>
                <select name="complexity" class="editorial-type-picker" style="width: 100%;" form="editorial-form">
                    <option value="">—</option>
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                    <option value="Transcendent">Transcendent</option>
                </select>
            </div>

            <div class="dopt-field">
                <label class="dopt-label">Polarity</label>
                <select name="polarity" class="editorial-type-picker" style="width: 100%;" form="editorial-form">
                    <option value="">—</option>
                    <option value="subjective">Subjective</option>
                    <option value="objective">Objective</option>
                </select>
            </div>

            <div class="dopt-field">
                <label class="dopt-label">Position / Direction</label>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px;">
                    <select name="position" class="editorial-type-picker" style="width: 100%;" form="editorial-form">
                        <option value="">Pos</option>
                        <option value="up">Up</option>
                        <option value="down">Down</option>
                        <option value="left">Left</option>
                        <option value="right">Right</option>
                    </select>
                    <select name="direction" class="editorial-type-picker" style="width: 100%;" form="editorial-form">
                        <option value="">Dir</option>
                        <option value="forward">Forward</option>
                        <option value="backward">Backward</option>
                    </select>
                </div>
            </div>

            <div class="dopt-field">
                <label class="dopt-label">Symbol</label>
                <input type="text" name="symbol" placeholder="Prophetic Symbol" class="editorial-type-picker" style="width: 100%;" form="editorial-form">
            </div>
        </div>

        
        <div id="fields-activity" class="dynamic-field-group dopt-section" style="display: none;">
            <div class="ws-label-tag" style="margin-bottom: 8px;">Activity</div>
            <div class="dopt-field">
                <label class="dopt-label">Due Date</label>
                <input type="date" name="due_at" class="editorial-type-picker" style="width: 100%;" form="editorial-form">
            </div>
            <div class="dopt-field">
                <label class="dopt-label">Recurrence</label>
                <select name="recurrence" class="editorial-type-picker" style="width: 100%;" form="editorial-form">
                    <option value="none">None</option>
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                </select>
            </div>
            <div class="dopt-field">
                <label class="dopt-label">KGS Pathway</label>
                <select name="kgs_pathway" class="editorial-type-picker" style="width: 100%;" form="editorial-form">
                    <option value="">General</option>
                    <option value="new_life">New Life</option>
                    <option value="spiritual_formation">Spiritual Formation</option>
                    <option value="community_life">Community Life</option>
                    <option value="service">Service</option>
                    <option value="leadership">Leadership</option>
                    <option value="mission">Mission</option>
                    <option value="apostolic_stewardship">Apostolic Stewardship</option>
                </select>
            </div>
        </div>

        
        <div id="fields-community" class="dynamic-field-group dopt-section" style="display: none;">
            <div class="ws-label-tag" style="margin-bottom: 8px;">Gathering</div>
            <div class="dopt-field">
                <label class="dopt-label">Scheduled At</label>
                <input type="datetime-local" name="scheduled_at" class="editorial-type-picker" style="width: 100%;" form="editorial-form">
            </div>
            <div class="dopt-field">
                <label class="dopt-label">Format</label>
                <select name="format" class="editorial-type-picker" style="width: 100%;" form="editorial-form">
                    <option value="in_person">In Person</option>
                    <option value="digital">Digital</option>
                    <option value="hybrid">Hybrid</option>
                </select>
            </div>
            <div class="dopt-field">
                <label class="dopt-label">Location</label>
                <input type="text" name="location" placeholder="Venue or link" class="editorial-type-picker" style="width: 100%;" form="editorial-form">
            </div>
        </div>

        
        <div id="fields-bible" class="dynamic-field-group dopt-section" style="display: none;">
            <div class="ws-label-tag" style="margin-bottom: 8px;">Scripture</div>
            <div class="dopt-field">
                <label class="dopt-label">Passage</label>
                <input type="text" name="passage" placeholder="e.g. John 3:16" class="editorial-type-picker" style="width: 100%;" form="editorial-form">
            </div>
            <div class="dopt-field">
                <label class="dopt-label">Translation</label>
                <select name="translation" class="editorial-type-picker" style="width: 100%;" form="editorial-form">
                    <option value="KJV">KJV</option>
                    <option value="NKJV">NKJV</option>
                    <option value="NIV">NIV</option>
                    <option value="ESV">ESV</option>
                    <option value="AMP">AMP</option>
                </select>
            </div>
        </div>

        <div class="dopt-divider"></div>

        
        <div class="dopt-section">
            <div class="ws-label-tag" style="margin-bottom: 8px;">Tags</div>
            <input type="text" name="tags" id="desk-tags" placeholder="Comma separated…" class="editorial-type-picker" style="width: 100%;" form="editorial-form">
        </div>
    </div>

    <div id="desk-tab-relations" class="desk-tab-pane" style="display: none; overflow-y: auto; flex: 1; padding-right: 2px;">

        
        <div class="dopt-section" id="rel-add-panel">
            <div class="ws-label-tag" style="margin-bottom: 10px;">Link a Record</div>

            
            <input type="text" id="rel-search-input" placeholder="Search records…" class="editorial-type-picker" style="width: 100%; margin-bottom: 8px;" oninput="RelPanel.search(this.value)">
            <div id="rel-search-results" style="display: flex; flex-direction: column; gap: 4px; margin-bottom: 10px; max-height: 160px; overflow-y: auto;">
            </div>

            
            <div id="rel-selected-record" style="display: none; padding: 8px 10px; background: var(--card-2);
                        border: 1px solid var(--primary-alpha); border-radius: 8px;
                        margin-bottom: 8px;">
                <div style="font-size: 10px; color: var(--primary); text-transform: uppercase;
                            letter-spacing: 0.07em; margin-bottom: 2px;">Selected</div>
                <div id="rel-selected-title" style="font-size: 13px; font-weight: 600; color: var(--text);"></div>
                <input type="hidden" id="rel-to-record-id">
            </div>

            
            <div class="dopt-field">
                <label class="dopt-label">Relationship Type</label>
                <select id="rel-type-picker" class="editorial-type-picker" style="width: 100%;">
                    <option value="part_of">Part Of</option>
                    <option value="derived_from">Derived From</option>
                    <option value="aligns_with">Aligns With</option>
                    <option value="authorised_by">Authorised By</option>
                    <option value="references">References</option>
                    <option value="tracks">Tracks</option>
                    <option value="community_ref">Community Ref</option>
                </select>
            </div>

            
            <div class="dopt-field">
                <label class="dopt-label">Notes (optional)</label>
                <textarea id="rel-notes" placeholder="Context for this link…" style="width: 100%; height: 56px; resize: none;
                                 background: var(--card); border: 1px solid var(--border);
                                 border-radius: 6px; padding: 8px 10px;
                                 font-size: 12px; color: var(--text); outline: none;
                                 font-family: var(--ff-body); box-sizing: border-box;"></textarea>
            </div>

            <button type="button" onclick="RelPanel.save()" class="ws-topbar__cta" style="width: 100%; justify-content: center; height: 36px; margin-top: 4px;">
                <span class="material-symbols-outlined" style="font-size: 16px;">add_link</span>
                Establish Link
            </button>
        </div>

        <div class="dopt-divider"></div>

        
        <div class="dopt-section">
            <div class="ws-label-tag" style="margin-bottom: 10px;">Established Links</div>
            <div id="rel-existing-list" style="display: flex; flex-direction: column; gap: 6px;">
                
                <div style="padding: 24px 0; text-align: center;">
                    <span class="material-symbols-outlined" style="font-size: 36px; opacity: 0.12; display: block;">link_off</span>
                    <p style="font-size: 12px; color: var(--muted); margin-top: 8px;">
                        No established links yet.
                    </p>
                </div>
                
            </div>
        </div>
    </div>

    <div id="desk-tab-recent" class="desk-tab-pane" style="display: none; overflow-y: auto; flex: 1; padding-right: 2px;">

        <div class="dopt-section" style="margin-bottom: 16px;">
            <div class="ws-label-tag" style="margin-bottom: 8px;">Journals</div>
            
            <p style="font-size: 12px; color: var(--muted); font-style: italic;">None yet</p>
            
        </div>

        <div class="dopt-divider"></div>

        <div class="dopt-section" style="margin-bottom: 16px;">
            <div class="ws-label-tag" style="margin-bottom: 8px;">Governance</div>
            
            <a href="/handbook/records/566decae-aae6-484a-a667-581102aab5e4/" class="dopt-recent-item">
                <span class="material-symbols-outlined" style="font-size: 14px; color: var(--muted); flex-shrink: 0;">gavel</span>
                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">
                    Sweet roll halvah pastry candy canes
                </span>
                <span style="font-size: 10px; color: var(--muted); flex-shrink: 0;">
                    09 Jun
                </span>
            </a>
            
            <a href="/handbook/records/6d80cfb1-6f6c-4d2d-9db0-92f193ef2cc8/" class="dopt-recent-item">
                <span class="material-symbols-outlined" style="font-size: 14px; color: var(--muted); flex-shrink: 0;">gavel</span>
                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">
                    My test principle is here
                </span>
                <span style="font-size: 10px; color: var(--muted); flex-shrink: 0;">
                    09 Jun
                </span>
            </a>
            
            <a href="/handbook/records/9709cf64-7011-4670-9e53-61e289aa89d5/" class="dopt-recent-item">
                <span class="material-symbols-outlined" style="font-size: 14px; color: var(--muted); flex-shrink: 0;">gavel</span>
                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">
                    Commercialization of the Gentile Court
                </span>
                <span style="font-size: 10px; color: var(--muted); flex-shrink: 0;">
                    09 Jun
                </span>
            </a>
            
            <a href="/handbook/records/55950aa5-3b9d-4391-8051-ad9eb9b34eee/" class="dopt-recent-item">
                <span class="material-symbols-outlined" style="font-size: 14px; color: var(--muted); flex-shrink: 0;">gavel</span>
                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">
                    Candy canes soufflé pudding
                </span>
                <span style="font-size: 10px; color: var(--muted); flex-shrink: 0;">
                    06 Jun
                </span>
            </a>
            
            <a href="/handbook/records/ea08c86e-fb47-4e7e-9fe3-9d060d72a608/" class="dopt-recent-item">
                <span class="material-symbols-outlined" style="font-size: 14px; color: var(--muted); flex-shrink: 0;">gavel</span>
                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">
                    God, The First
                </span>
                <span style="font-size: 10px; color: var(--muted); flex-shrink: 0;">
                    03 Jun
                </span>
            </a>
            
        </div>

        <div class="dopt-divider"></div>

        <div class="dopt-section">
            <div class="ws-label-tag" style="margin-bottom: 8px;">All Recent</div>
            
            <a href="/handbook/records/566decae-aae6-484a-a667-581102aab5e4/" class="dopt-recent-item">
                <span class="material-symbols-outlined" style="font-size: 14px; color: var(--muted); flex-shrink: 0;">history_edu</span>
                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">
                    Sweet roll halvah pastry candy canes
                </span>
                <span style="font-size: 10px; color: var(--muted); flex-shrink: 0;">
                    09 Jun
                </span>
            </a>
            
            <a href="/handbook/records/6d80cfb1-6f6c-4d2d-9db0-92f193ef2cc8/" class="dopt-recent-item">
                <span class="material-symbols-outlined" style="font-size: 14px; color: var(--muted); flex-shrink: 0;">history_edu</span>
                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">
                    My test principle is here
                </span>
                <span style="font-size: 10px; color: var(--muted); flex-shrink: 0;">
                    09 Jun
                </span>
            </a>
            
            <a href="/handbook/records/9709cf64-7011-4670-9e53-61e289aa89d5/" class="dopt-recent-item">
                <span class="material-symbols-outlined" style="font-size: 14px; color: var(--muted); flex-shrink: 0;">history_edu</span>
                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">
                    Commercialization of the Gentile Court
                </span>
                <span style="font-size: 10px; color: var(--muted); flex-shrink: 0;">
                    09 Jun
                </span>
            </a>
            
            <a href="/handbook/records/55950aa5-3b9d-4391-8051-ad9eb9b34eee/" class="dopt-recent-item">
                <span class="material-symbols-outlined" style="font-size: 14px; color: var(--muted); flex-shrink: 0;">history_edu</span>
                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">
                    Candy canes soufflé pudding
                </span>
                <span style="font-size: 10px; color: var(--muted); flex-shrink: 0;">
                    06 Jun
                </span>
            </a>
            
            <a href="/handbook/records/63f589e6-2f1f-4bf5-9b49-002693c92384/" class="dopt-recent-item">
                <span class="material-symbols-outlined" style="font-size: 14px; color: var(--muted); flex-shrink: 0;">history_edu</span>
                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">
                    marshmallow lollipop
                </span>
                <span style="font-size: 10px; color: var(--muted); flex-shrink: 0;">
                    06 Jun
                </span>
            </a>
            
            <a href="/handbook/records/2077cad8-332a-49a3-8b34-ce4197bf0bf2/" class="dopt-recent-item">
                <span class="material-symbols-outlined" style="font-size: 14px; color: var(--muted); flex-shrink: 0;">history_edu</span>
                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">
                    Sweet roll halvah pastry candy canes
                </span>
                <span style="font-size: 10px; color: var(--muted); flex-shrink: 0;">
                    06 Jun
                </span>
            </a>
            
            <a href="/handbook/records/6444c463-db75-44f5-af68-8ca03d7c1f88/" class="dopt-recent-item">
                <span class="material-symbols-outlined" style="font-size: 14px; color: var(--muted); flex-shrink: 0;">history_edu</span>
                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">
                    Sweet roll halvah pastry candy canes
                </span>
                <span style="font-size: 10px; color: var(--muted); flex-shrink: 0;">
                    06 Jun
                </span>
            </a>
            
            <a href="/handbook/records/11936be2-6a87-4b27-9a85-535ab6e66890/" class="dopt-recent-item">
                <span class="material-symbols-outlined" style="font-size: 14px; color: var(--muted); flex-shrink: 0;">history_edu</span>
                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">
                    Tiramisu tiramisu
                </span>
                <span style="font-size: 10px; color: var(--muted); flex-shrink: 0;">
                    06 Jun
                </span>
            </a>
            
        </div>
    </div>
</div>

<style>
/* ── Tabs ── */
.desk-tab {
    flex: 1;
    padding: 8px 4px;
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    color: var(--muted);
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    cursor: pointer;
    transition: color 0.12s, border-color 0.12s;
}
.desk-tab:hover { color: var(--text); }
.desk-tab--active { color: var(--accent-red); border-bottom-color: var(--accent-red); }
.desk-tab-pane { animation: doptFade 0.15s ease; }
@keyframes doptFade { from { opacity: 0; } to { opacity: 1; } }

/* ── Layout helpers ── */
.dopt-section { padding: 0 0 4px; }
.dopt-divider { height: 1px; background: var(--border); margin: 14px 0; }
.dopt-label {
    display: block;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--muted);
    margin-bottom: 6px;
}
.dopt-field { margin-bottom: 12px; }

/* ── Relation cards ── */
.dopt-rel-card {
    padding: 10px 12px;
    background: var(--card-2);
    border: 1px solid var(--border);
    border-radius: 8px;
    transition: border-color 0.12s;
}
.dopt-rel-card:hover { border-color: var(--primary-alpha); }

/* ── Search result items ── */
.rel-result-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 7px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    color: var(--text);
    cursor: pointer;
    background: var(--card-2);
    border: 1px solid var(--border);
    transition: border-color 0.12s, background 0.12s;
}
.rel-result-item:hover { border-color: var(--primary); background: var(--hover); }

/* ── Recent items ── */
.dopt-recent-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    color: var(--text);
    text-decoration: none;
    transition: background 0.12s;
    margin-bottom: 2px;
}
.dopt-recent-item:hover { background: var(--hover); }
</style>

<script>
/* ── Tab switching ── */
const DeskTabs = {
    show(tab, btn) {
        document.querySelectorAll('.desk-tab-pane').forEach(p => p.style.display = 'none');
        document.querySelectorAll('.desk-tab').forEach(b => b.classList.remove('desk-tab--active'));
        const pane = document.getElementById(`desk-tab-${tab}`);
        if (pane) pane.style.display = '';
        if (btn)  btn.classList.add('desk-tab--active');
    }
};

/* ── Dial → show/hide family-specific fields ── */
document.body.addEventListener('dialChanged', (e) => {
    document.querySelectorAll('.dynamic-field-group').forEach(g => g.style.display = 'none');
    const active = document.getElementById(`fields-${e.detail.family}`);
    if (active) active.style.display = '';
});

/* ── Relationship panel ── */
const RelPanel = {
    _searchTimer: null,

    search(q) {
        clearTimeout(this._searchTimer);
        const results = document.getElementById('rel-search-results');
        if (!q || q.length < 2) { results.innerHTML = ''; return; }

        this._searchTimer = setTimeout(() => {
            fetch(`/governance/htmx/global-search/?q=${encodeURIComponent(q)}`, {
                headers: { 'HX-Request': 'true' }
            })
            .then(r => r.text())
            .then(html => {
                // Parse the returned HTML to extract record links
                const parser  = new DOMParser();
                const doc     = parser.parseFromString(html, 'text/html');
                const items   = doc.querySelectorAll('[data-record-id], [data-id]');

                if (items.length) {
                    results.innerHTML = '';
                    items.forEach(item => {
                        const id    = item.dataset.recordId || item.dataset.id;
                        const title = item.textContent.trim();
                        if (id && title) this._addResult(results, id, title);
                    });
                } else {
                    // Fallback: simple title search via records API
                    this._fallbackSearch(q, results);
                }
            })
            .catch(() => this._fallbackSearch(q, results));
        }, 280);
    },

    _fallbackSearch(q, container) {
        fetch(`/records/htmx/search/?q=${encodeURIComponent(q)}`, {
            headers: { 'HX-Request': 'true' }
        })
        .then(r => r.text())
        .then(html => {
            container.innerHTML = '';
            const doc   = new DOMParser().parseFromString(html, 'text/html');
            const items = doc.querySelectorAll('.search-result-item[onclick]');
            let added   = 0;
            items.forEach(item => {
                const m = item.getAttribute('onclick').match(/selectRecord\('([^']+)',\s*'([^']+)'\)/);
                if (m && added < 8) {
                    this._addResult(container, m[1], m[2]);
                    added++;
                }
            });
            if (!added) {
                container.innerHTML = `<p style="font-size:12px;color:var(--muted);padding:4px 0;">No records found.</p>`;
            }
        })
        .catch(() => {
            container.innerHTML = `<p style="font-size:12px;color:var(--muted);padding:4px 0;">Search unavailable.</p>`;
        });
    },

    _addResult(container, id, title, type) {
        const el = document.createElement('div');
        el.className = 'rel-result-item';
        el.innerHTML = `
            <span class="material-symbols-outlined" style="font-size:14px;color:var(--muted);">description</span>
            <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${title}</span>
            ${type ? `<span style="font-size:10px;color:var(--muted);text-transform:uppercase;">${type}</span>` : ''}
        `;
        el.onclick = () => this.select(id, title);
        container.appendChild(el);
    },

    select(id, title) {
        document.getElementById('rel-to-record-id').value  = id;
        document.getElementById('rel-selected-title').textContent = title;
        document.getElementById('rel-selected-record').style.display = '';
        document.getElementById('rel-search-results').innerHTML = '';
        document.getElementById('rel-search-input').value = '';
    },

    save() {
        const recordId  = document.getElementById('record-id-meta')?.value;
        const toId      = document.getElementById('rel-to-record-id').value;
        const relType   = document.getElementById('rel-type-picker').value;
        const notes     = document.getElementById('rel-notes').value.trim();

        if (!toId) {
            alert('Please select a record to link first.');
            return;
        }
        if (!recordId) {
            alert('Save this record first before establishing links.');
            return;
        }

        const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const form = new FormData();
        form.append('from_record_id',    recordId);
        form.append('to_record_id',      toId);
        form.append('relationship_type', relType);
        form.append('notes',             notes);
        form.append('csrfmiddlewaretoken', csrf);

        fetch('/governance/htmx/relationship/create/', {
            method: 'POST',
            body: form,
            headers: { 'HX-Request': 'true' }
        })
        .then(r => {
            if (!r.ok) throw new Error(r.status);
            // Refresh the desk rel cards via the lightweight partial
            return fetch(`/governance/htmx/desk/relationships/${recordId}/`, {
                headers: { 'HX-Request': 'true' }
            });
        })
        .then(r => r.text())
        .then(html => {
            const list = document.getElementById('rel-existing-list');
            if (list) list.innerHTML = html;
            document.getElementById('rel-to-record-id').value = '';
            document.getElementById('rel-selected-record').style.display = 'none';
            document.getElementById('rel-notes').value = '';
            RelPanel._pulse('Link established');
        })
        .catch(() => RelPanel._pulse('Error — try again'));
    },

    _pulse(msg) {
        const el = document.getElementById('save-status');
        if (!el) return;
        const prev = el.textContent;
        el.textContent = msg;
        setTimeout(() => el.textContent = prev, 2500);
    }
};
</script>


                    </div>
```

Dimensions:
- top: 94px
- left: 907px
- width: 299px
- height: 390px

CSS:
```css
element { padding: var(--space-m); }
*, *::before, *::after { padding: 0;
  margin: 0;
  box-sizing: border-box;
  list-style: none;
  list-style-type: none;
  text-decoration: none;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility; }

/* Inherited */
*, *::before, *::after { list-style: none; list-style-type: none }
.ics-options-bar { color: var(--text-ink) }
html, body { font-family: var(--font-family-base); line-height: var(--line-height-base); font-weight: var(--font-weight-regular) }
body { font-family: var(--ff-body); font-size: 16px; line-height: 1.5; color: var(--text) }
html { font-size: 100%; font-style: normal }
:root { color: var(--text) }

/* Resolved values */
margin: 0px;
padding: 24px;
text-decoration: rgb(245, 243, 240);
-webkit-font-smoothing: antialiased;
box-sizing: border-box;
color: rgb(245, 243, 240);
display: block;
font-family: Inter, system-ui, sans-serif;
font-size: 16px;
font-style: normal;
font-weight: 400;
height: 389.7px;
line-height: 24px;
list-style-image: none;
list-style-position: outside;
list-style-type: none;
text-rendering: optimizelegibility;
unicode-bidi: isolate /*UA*/;
width: 299.2px;

/* CSS variables */
--space-m: 1.5rem;
--font-family-base: 'Inter', system-ui, sans-serif;
--font-weight-regular: 400;
--text: #f5f3f0;
--line-height-base: 1.6;
--text-ink: #F5F3F0;
--ff-body: 'Inter', system-ui, sans-serif;
```