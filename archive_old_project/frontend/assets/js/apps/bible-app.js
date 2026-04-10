/**
 * bible-app.js
 * ICS Bible App — Scripture reader + personal annotation layer
 *
 * Architecture:
 *   - Scripture text: fetched from /assets/data/bible.json (static, no auth)
 *   - Annotations:    read/written via ICSRecords service (Records Engine)
 *   - Reading position: stored in localStorage as UI state only
 *
 * Dependencies (must be loaded before this file):
 *   - identity.service.js  → ICSIdentity
 *   - records.service.js   → ICSRecords
 *
 * Panels:
 *   1. Book/Chapter navigator (slide-up sheet)
 *   2. Reader view (main scrollable content)
 *   3. Annotation panel (slide-up sheet, per verse)
 */

const ICSBible = (() => {

  // ─── Constants ────────────────────────────────────────────────────────────

  const BIBLE_JSON_PATH = '/assets/data/bible.json'
  const UI_POSITION_KEY = 'ics_ui.bible_last_position'

  // ─── State ────────────────────────────────────────────────────────────────

  let _bibleData    = null   // full parsed bible.json
  let _currentBook  = null   // { id, name, chapters }
  let _currentChapter = null // { chapter, verses }
  let _userNotes    = []     // all bible_note records for current user
  let _activeVerse  = null   // { bookId, chapter, verse, text } — for annotation panel

  // ─── DOM refs (populated on init) ─────────────────────────────────────────

  const $ = id => document.getElementById(id)

  // ─── Initialisation ───────────────────────────────────────────────────────

  async function init() {
    await _loadBible()
    await _loadUserNotes()
    _restorePosition()
    _bindEvents()
  }

  async function _loadBible() {
    try {
      const res = await fetch(BIBLE_JSON_PATH)
      if (!res.ok) throw new Error(`Failed to load Bible data: ${res.status}`)
      _bibleData = await res.json()
    } catch (err) {
      _showError('Could not load scripture. Please refresh.')
      console.error('[ICSBible] _loadBible:', err)
    }
  }

  async function _loadUserNotes() {
    if (!ICSIdentity.isAuthenticated()) return
    try {
      const result = await ICSRecords.list({ record_family: 'bible', record_type: 'bible_note' })
      _userNotes = result || []
    } catch (err) {
      // Non-fatal — reader still works without notes
      console.warn('[ICSBible] _loadUserNotes:', err)
      _userNotes = []
    }
  }

  // ─── Position persistence (UI state only, localStorage) ───────────────────

  function _savePosition(bookId, chapter) {
    try {
      localStorage.setItem(UI_POSITION_KEY, JSON.stringify({ bookId, chapter }))
    } catch (_) { /* ignore — storage may be blocked */ }
  }

  function _restorePosition() {
    if (!_bibleData) return
    try {
      const saved = localStorage.getItem(UI_POSITION_KEY)
      if (saved) {
        const { bookId, chapter } = JSON.parse(saved)
        const book = _bibleData.books.find(b => b.id === bookId)
        if (book) {
          _openChapter(book, chapter)
          return
        }
      }
    } catch (_) { /* fall through to default */ }
    // Default: Genesis 1
    if (_bibleData.books.length) _openChapter(_bibleData.books[0], 1)
  }

  // ─── Navigation ───────────────────────────────────────────────────────────

  function _openChapter(book, chapterNum) {
    _currentBook = book
    _currentChapter = book.chapters.find(c => c.chapter === chapterNum)
    if (!_currentChapter) return
    _savePosition(book.id, chapterNum)
    _renderReader()
    _closeNavigator()
  }

  function _prevChapter() {
    if (!_currentBook || !_currentChapter) return
    const idx = _currentBook.chapters.findIndex(c => c.chapter === _currentChapter.chapter)
    if (idx > 0) {
      _openChapter(_currentBook, _currentBook.chapters[idx - 1].chapter)
    } else {
      // Go to last chapter of previous book
      const bookIdx = _bibleData.books.findIndex(b => b.id === _currentBook.id)
      if (bookIdx > 0) {
        const prevBook = _bibleData.books[bookIdx - 1]
        const lastChapter = prevBook.chapters[prevBook.chapters.length - 1]
        _openChapter(prevBook, lastChapter.chapter)
      }
    }
  }

  function _nextChapter() {
    if (!_currentBook || !_currentChapter) return
    const idx = _currentBook.chapters.findIndex(c => c.chapter === _currentChapter.chapter)
    if (idx < _currentBook.chapters.length - 1) {
      _openChapter(_currentBook, _currentBook.chapters[idx + 1].chapter)
    } else {
      // Go to chapter 1 of next book
      const bookIdx = _bibleData.books.findIndex(b => b.id === _currentBook.id)
      if (bookIdx < _bibleData.books.length - 1) {
        _openChapter(_bibleData.books[bookIdx + 1], 1)
      }
    }
  }

  // ─── Render: Reader ───────────────────────────────────────────────────────

  function _renderReader() {
    const container = $('bible-reader-content')
    const heading   = $('bible-reader-heading')
    if (!container || !_currentChapter) return

    heading.textContent = `${_currentBook.name} ${_currentChapter.chapter}`

    const notesForChapter = _userNotes.filter(n =>
      n.custom_fields?.book_id === _currentBook.id &&
      n.custom_fields?.chapter === _currentChapter.chapter
    )
    const annotatedVerses = new Set(notesForChapter.map(n => n.custom_fields?.verse))

    container.innerHTML = _currentChapter.verses.map(v => `
      <div
        class="bible-verse ${annotatedVerses.has(v.verse) ? 'bible-verse--annotated' : ''}"
        data-verse="${v.verse}"
        role="button"
        tabindex="0"
        aria-label="Verse ${v.verse}"
      >
        <span class="bible-verse__num">${v.verse}</span>
        <span class="bible-verse__text">${_escapeHtml(v.text)}</span>
        ${annotatedVerses.has(v.verse) ? '<span class="bible-verse__dot" aria-label="Has note"></span>' : ''}
      </div>
    `).join('')

    // Scroll reader to top on chapter change
    container.scrollTop = 0

    // Bind verse taps
    container.querySelectorAll('.bible-verse').forEach(el => {
      el.addEventListener('click', () => _onVerseTap(el))
      el.addEventListener('keydown', e => { if (e.key === 'Enter') _onVerseTap(el) })
    })
  }

  // ─── Render: Book/Chapter Navigator ───────────────────────────────────────

  function _renderNavigator() {
    if (!_bibleData) return
    const bookList = $('bible-nav-books')
    bookList.innerHTML = _bibleData.books.map(book => `
      <li>
        <button
          class="bible-nav__book-btn ${_currentBook?.id === book.id ? 'bible-nav__book-btn--active' : ''}"
          data-book-id="${book.id}"
        >${book.name}</button>
      </li>
    `).join('')

    bookList.querySelectorAll('.bible-nav__book-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const book = _bibleData.books.find(b => b.id === btn.dataset.bookId)
        if (book) _renderChapterList(book)
      })
    })

    // Show chapters for current book by default
    if (_currentBook) _renderChapterList(_currentBook)
  }

  function _renderChapterList(book) {
    const chapterList = $('bible-nav-chapters')
    chapterList.innerHTML = book.chapters.map(c => `
      <button
        class="bible-nav__chapter-btn ${
          _currentBook?.id === book.id && _currentChapter?.chapter === c.chapter
            ? 'bible-nav__chapter-btn--active' : ''
        }"
        data-book-id="${book.id}"
        data-chapter="${c.chapter}"
      >${c.chapter}</button>
    `).join('')

    chapterList.querySelectorAll('.bible-nav__chapter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const b = _bibleData.books.find(x => x.id === btn.dataset.bookId)
        if (b) _openChapter(b, parseInt(btn.dataset.chapter, 10))
      })
    })
  }

  // ─── Annotation panel ─────────────────────────────────────────────────────

  function _onVerseTap(el) {
    const verseNum = parseInt(el.dataset.verse, 10)
    const verse    = _currentChapter.verses.find(v => v.verse === verseNum)
    if (!verse) return

    _activeVerse = {
      bookId:  _currentBook.id,
      bookName: _currentBook.name,
      chapter: _currentChapter.chapter,
      verse:   verseNum,
      text:    verse.text
    }

    // Find existing note for this verse if any
    const existingNote = _userNotes.find(n =>
      n.custom_fields?.book_id === _activeVerse.bookId &&
      n.custom_fields?.chapter === _activeVerse.chapter &&
      n.custom_fields?.verse   === _activeVerse.verse
    )

    _openAnnotationPanel(existingNote)
  }

  function _openAnnotationPanel(existingNote = null) {
    const panel     = $('bible-annotation-panel')
    const verseRef  = $('bible-annotation-ref')
    const verseText = $('bible-annotation-versetext')
    const textarea  = $('bible-annotation-textarea')
    const saveBtn   = $('bible-annotation-save')

    verseRef.textContent  = `${_activeVerse.bookName} ${_activeVerse.chapter}:${_activeVerse.verse}`
    verseText.textContent = _activeVerse.text
    textarea.value        = existingNote?.content || ''

    // Store existing note id on save button for update vs create decision
    saveBtn.dataset.noteId = existingNote?.id || ''

    panel.classList.add('bible-annotation-panel--open')
    textarea.focus()
  }

  function _closeAnnotationPanel() {
    const panel = $('bible-annotation-panel')
    panel.classList.remove('bible-annotation-panel--open')
    _activeVerse = null
  }

  async function _saveAnnotation() {
    const textarea = $('bible-annotation-textarea')
    const saveBtn  = $('bible-annotation-save')
    const content  = textarea.value.trim()

    if (!content) {
      textarea.focus()
      return
    }

    // Auth gate — inline prompt, not a redirect
    if (!ICSIdentity.isAuthenticated()) {
      _showSignInPrompt()
      return
    }

    saveBtn.disabled = true
    saveBtn.textContent = 'Saving…'

    try {
      const noteId = saveBtn.dataset.noteId

      const payload = {
        record_class:  'personal',
        record_family: 'bible',
        record_type:   'bible_note',
        title:         `${_activeVerse.bookName} ${_activeVerse.chapter}:${_activeVerse.verse}`,
        content,
        metadata: {
          source_app: 'bible',
          custom_field_definitions: [
            { name: 'book_id',  type: 'string' },
            { name: 'chapter',  type: 'number' },
            { name: 'verse',    type: 'number' }
          ]
        },
        custom_fields: {
          book_id: _activeVerse.bookId,
          chapter: _activeVerse.chapter,
          verse:   _activeVerse.verse
        },
        permissions: {
          visibility:     'private',
          required_level: 1,
          roles_allowed:  [],
          can_edit:       []
        }
      }

      let saved
      if (noteId) {
        saved = await ICSRecords.update(noteId, { content })
        // Update in-memory notes array
        const idx = _userNotes.findIndex(n => n.id === noteId)
        if (idx !== -1) _userNotes[idx] = { ..._userNotes[idx], content }
      } else {
        saved = await ICSRecords.create(payload)
        _userNotes.push(saved)
      }

      _closeAnnotationPanel()
      _renderReader() // re-render to update dot indicators

    } catch (err) {
      console.error('[ICSBible] _saveAnnotation:', err)
      _showError('Could not save note. Please try again.')
    } finally {
      saveBtn.disabled = false
      saveBtn.textContent = 'Save Note'
    }
  }

  // ─── Navigator sheet open/close ───────────────────────────────────────────

  function _openNavigator() {
    _renderNavigator()
    $('bible-navigator').classList.add('bible-navigator--open')
  }

  function _closeNavigator() {
    $('bible-navigator').classList.remove('bible-navigator--open')
  }

  // ─── Sign-in prompt (inline, no redirect) ─────────────────────────────────

  function _showSignInPrompt() {
    const msg = $('bible-signin-prompt')
    if (msg) {
      msg.hidden = false
      setTimeout(() => { msg.hidden = true }, 4000)
    }
  }

  // ─── Error display ────────────────────────────────────────────────────────

  function _showError(message) {
    const el = $('bible-error-msg')
    if (el) {
      el.textContent = message
      el.hidden = false
    }
  }

  // ─── Utilities ────────────────────────────────────────────────────────────

  function _escapeHtml(str) {
    return str
      .replace(/&/g,  '&amp;')
      .replace(/</g,  '&lt;')
      .replace(/>/g,  '&gt;')
      .replace(/"/g,  '&quot;')
  }

  // ─── Event bindings ───────────────────────────────────────────────────────

  function _bindEvents() {
    // Navigator open/close
    const openNavBtn  = $('bible-open-nav')
    const closeNavBtn = $('bible-close-nav')
    const navOverlay  = $('bible-nav-overlay')

    if (openNavBtn)  openNavBtn.addEventListener('click', _openNavigator)
    if (closeNavBtn) closeNavBtn.addEventListener('click', _closeNavigator)
    if (navOverlay)  navOverlay.addEventListener('click', _closeNavigator)

    // Chapter prev/next
    const prevBtn = $('bible-prev-chapter')
    const nextBtn = $('bible-next-chapter')
    if (prevBtn) prevBtn.addEventListener('click', _prevChapter)
    if (nextBtn) nextBtn.addEventListener('click', _nextChapter)

    // Annotation panel
    const closeAnnotation = $('bible-annotation-close')
    const saveAnnotation  = $('bible-annotation-save')
    const annotationOverlay = $('bible-annotation-overlay')

    if (closeAnnotation)   closeAnnotation.addEventListener('click', _closeAnnotationPanel)
    if (saveAnnotation)    saveAnnotation.addEventListener('click', _saveAnnotation)
    if (annotationOverlay) annotationOverlay.addEventListener('click', _closeAnnotationPanel)
  }

  // ─── Public API ───────────────────────────────────────────────────────────

  return { init }

})()

// Boot on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => ICSBible.init())
