# Plan: Bible Reader UI Improvements

## Context

The current Bible reader has several UX problems:
1. **Topbar overloaded** — prev/next chapter navigation sits in the topbar, taking space from useful actions (versions, search, settings)
2. **Annotation overlay broken on mobile** — the slide-up panel causes scroll conflicts (page scrolls instead of panel)
3. **Navigator is a half-baked sheet** — book/chapter picker is a side-by-side columns sheet, not immersive enough
4. **No search** — no search page exists yet
5. **No font settings** — no drawer content for Bible settings
6. **No scroll-hide behaviour** — topbar and bottom bar are always visible, reducing reading space

---

## Architecture Changes

### What's Removed
- `bible-annotation-overlay` (`.sheet-overlay`) — dropped entirely (solves mobile scroll bug)
- `bible-navigator` sheet — replaced by full-screen picker page
- `bible-translation-row` inline — moved to dedicated Versions page
- Prev/next buttons from topbar — moved to sticky navigator strip

### What's Added / Changed

#### 1. Topbar (linear, sticky, synchronized hide)
**New content (left → right):**
- `[Book Chapter]` — current passage chip, taps to open picker page
- spacer (flex-grow)
- `[Versions]` icon button → links to versions list page
- `[Search]` icon button → links to search page
- `[Settings]` icon button → opens context drawer with font settings

**Behaviour:**
- Sticky to top on load
- Hides on scroll down (synchronized with bottom bar + navigator strip)
- Reappears on scroll up

#### 2. Sticky Chapter Navigator Strip
**Position:** Fixed, above bottom bar (`bottom: 70px`)
**Content:** `[← Prev]  [Genesis 1]  [Next →]`
- "Genesis 1" button → navigates to full-screen picker
- Prev/Next — HTMX swap chapter content (same as current logic)
- Hides/shows synchronized with topbar and bottom bar

#### 3. Full-Screen Chapter Picker (new page)
**URL:** `/bible/pick/` (GET params: `book_code`, `chapter`, `back_url`)
**Template:** `templates/bible/picker.html`
**Base:** Custom base (no global navbar, no bottom bar — immersive)
- **Back arrow** top-left → returns to `back_url` (current chapter URL)
- **Cascading step by step:** Step 1 Book → Step 2 Chapter → Step 3 Verse
- Selecting verse → redirects to `bible:reader-chapter` at that verse

#### 4. Search Page (new)
**URL:** `/bible/search/`
**View:** `bible_search_view` (GET) + `htmx_search` (GET, HTMX partial)
**Template:** `templates/bible/search.html`
**Base:** Custom base (back button + sticky search input, no bottom nav during search)
- Search input sticky at top
- HTMX: `hx-get` on `keyup` with 300ms debounce → swaps `#search-results`
- Results: `Book · Chapter:Verse` + text snippet
- Click result → navigates to `bible:reader-chapter`

#### 5. Verse Notes → Context Drawer
**Replaces annotation overlay**
- Verse tap → HTMX populates `#drawer` content + calls `window.ICSDrawer.open()`
- `drawer_title` = "Verse Note"
- Drawer content = note textarea + save button (existing `htmx_save_note` endpoint)
- Fixes mobile scroll conflict entirely

#### 6. Bible Settings Drawer
- Settings icon button in topbar → `window.ICSDrawer.open()`
- `drawer_title` = "Bible Settings"
- Drawer content: font size controls, font family picker, line spacing

#### 7. Synchronized Scroll Hide/Show (JS)
JS file: `static/js/bible.js`
```
ScrollWatcher:
  let lastY = 0, delta = 8 (threshold)
  on scroll:
    if scrollY > lastY + delta → add .scroll-hidden to .bible-topbar, .bottom-bar, .bible-nav-strip
    if scrollY < lastY - delta → remove .scroll-hidden
    lastY = scrollY
```
CSS: `.scroll-hidden { transform: translateY(-100%) }` for topbar, `translateY(100%)` for bottom bar and nav strip

---

## Files

### Modified
| File | Change |
|------|--------|
| `templates/bible/reader.html` | Full refactor: new topbar, remove overlay/navigator sheet, add nav strip, integrate drawer for notes |
| `static/css/bible.css` | Add nav strip styles, scroll-hidden transitions, remove old overlay styles |
| `bible/urls.py` | Add: `search/`, `pick/`, `htmx/search/` |
| `bible/views.py` | Add: `bible_search_view`, `htmx_search`, `bible_picker_view` |

### Created
| File | Purpose |
|------|---------|
| `templates/bible/search.html` | Full-page search with sticky input + real-time results |
| `templates/bible/_search_results.html` | HTMX partial: verse results list |
| `templates/bible/picker.html` | Full-screen book/chapter/verse picker |
| `templates/bible/base_bible_minimal.html` | Base with no global navbar/bottom bar (for picker + search) |
| `static/js/bible.js` | Scroll detection, synchronized hide/show |

---

## Detailed Implementation Steps

### Step 1 — New topbar in reader.html
Replace the current topbar (which has prev/book title/next) with:
```html
<div class="bible-topbar">
  <a href="{% url 'bible:picker' %}?book_code={{ book.code }}&chapter={{ chapter }}&back={{ request.path }}" class="bible-topbar__passage">
    <span class="material-symbols-outlined">menu_book</span>
    {{ book.name }} {{ chapter }}
  </a>
  <div class="bible-topbar__actions">
    <a href="{% url 'bible:versions' %}" class="bible-topbar__action-btn" aria-label="Bible versions">
      <span class="material-symbols-outlined">translate</span>
    </a>
    <a href="{% url 'bible:search' %}" class="bible-topbar__action-btn" aria-label="Search">
      <span class="material-symbols-outlined">search</span>
    </a>
    <button class="bible-topbar__action-btn" onclick="window.ICSDrawer.open()" aria-label="Settings">
      <span class="material-symbols-outlined">tune</span>
    </button>
  </div>
</div>
```

### Step 2 — Navigator strip (between chapter and bottom bar)
```html
<div class="bible-nav-strip">
  <button class="bible-nav-strip__btn" hx-get="..." hx-target="#bible-chapter">
    <span class="material-symbols-outlined">chevron_left</span>
  </button>
  <a href="{% url 'bible:picker' %}?..." class="bible-nav-strip__chapter">
    {{ book.name }} {{ chapter }}
  </a>
  <button class="bible-nav-strip__btn" hx-get="..." hx-target="#bible-chapter">
    <span class="material-symbols-outlined">chevron_right</span>
  </button>
</div>
```

### Step 3 — Remove annotation overlay
Delete the `#bible-annotation-overlay` div and `#bible-annotation-panel` sheet. Instead, wire verse taps to populate and open the global drawer:
```html
<div class="bible-verse"
     hx-get="{% url 'bible:htmx-annotation-panel' verse.id %}"
     hx-target="#drawer .drawer-content"
     hx-swap="innerHTML"
     hx-on::after-request="window.ICSDrawer.open()">
```

### Step 4 — Drawer blocks in reader.html
```html
{% block drawer_title %}Verse Note{% endblock %}
{% block drawer_content %}{# populated by HTMX #}{% endblock %}
```

### Step 5 — Add views to bible/views.py
```python
def bible_search_view(request):
    return render(request, 'bible/search.html')

def htmx_search(request):
    query = request.GET.get('q', '').strip()
    results = []
    if len(query) >= 2:
        results = BibleVerse.objects.filter(
            text__icontains=query,
            translation=get_user_translation(request.user)
        ).select_related('book')[:30]
    return render(request, 'bible/_search_results.html', {'results': results, 'query': query})

def bible_picker_view(request):
    back_url = request.GET.get('back', '/bible/')
    books = get_all_books()
    book_code = request.GET.get('book_code', DEFAULT_BOOK)
    chapter = int(request.GET.get('chapter', 1))
    chapters = get_book_chapters(book_code)
    book = BibleBook.objects.filter(code=book_code).first()
    return render(request, 'bible/picker.html', {
        'books': books, 'book': book, 'chapter': chapter,
        'chapters': list(chapters), 'back_url': back_url
    })
```

### Step 6 — bible.js scroll watcher
```javascript
const THRESHOLD = 8;
let lastY = window.scrollY;
const topbar = document.querySelector('.bible-topbar');
const navStrip = document.querySelector('.bible-nav-strip');
const bottomBar = document.querySelector('.bottom-bar');

window.addEventListener('scroll', () => {
  const y = window.scrollY;
  if (y > lastY + THRESHOLD) {
    topbar?.classList.add('scroll-hidden');
    navStrip?.classList.add('scroll-hidden');
    bottomBar?.classList.add('scroll-hidden');
  } else if (y < lastY - THRESHOLD) {
    topbar?.classList.remove('scroll-hidden');
    navStrip?.classList.remove('scroll-hidden');
    bottomBar?.classList.remove('scroll-hidden');
  }
  lastY = y;
}, { passive: true });
```

---

## CSS Additions (bible.css)

```css
/* Nav strip */
.bible-nav-strip {
  position: fixed;
  bottom: 70px; /* above bottom bar */
  left: 0; right: 0;
  height: 48px;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 16px;
  background: var(--card);
  border-top: 1px solid var(--border);
  z-index: 90;
  transition: transform 0.3s ease;
}
.bible-nav-strip.scroll-hidden { transform: translateY(100%); }

/* Topbar scroll hide */
.bible-topbar.scroll-hidden { transform: translateY(-100%); }
.bottom-bar.scroll-hidden { transform: translateY(100%); }

/* Main content padding adjustments */
.bible-reader-shell {
  padding-top: 56px;   /* topbar height */
  padding-bottom: 118px; /* nav strip 48px + bottom bar 70px */
}
```

---

## URL Routes to Add (bible/urls.py)

```python
path('search/', views.bible_search_view, name='search'),
path('pick/', views.bible_picker_view, name='picker'),
path('htmx/search/', views.htmx_search, name='htmx-search'),
```

Also need a versions page URL (check if it exists first):
```python
path('versions/', views.bible_versions_view, name='versions'),
```

---

## Verification

1. `python3 manage.py runserver 8001` → open `http://localhost:8001/bible/`
2. Topbar shows: Passage chip | Versions icon | Search icon | Settings icon
3. Scroll down → topbar + bottom bar + nav strip all hide
4. Scroll up → all three reappear
5. Tap passage chip → opens picker page (no global nav)
6. Picker: select book → chapters appear; select chapter → navigates to reader
7. Tap Search icon → opens `/bible/search/` full page
8. Type in search → results appear in real-time
9. Tap verse → drawer opens with note content
10. Tap Settings in topbar → drawer opens with Bible Settings
