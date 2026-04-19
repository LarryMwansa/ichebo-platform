# ICS Platform — Django Templates + HTMX Migration
## Architectural Decision Record + Migration Plan

> **Version:** 1.0 — 2026-04-07
> **Status:** LOCKED
> **Scope:** All app UI work going forward. Supersedes the vanilla JS IIFE frontend
> layer described in build roadmap v2 Tasks 2.2, 3.2, 4.1–4.2, 5.1–5.6, 6.2, 7.1.
> DRF endpoints, Django models, serializers, signals — all unchanged.

---

## Part 1 — Architectural Decision

### 1.1 The Decision

All ICS app UI is rendered via **Django templates + HTMX**. The existing vanilla JS
engine service files (`records.service.js`, `activity.service.js`, etc.) are
**not built**. The existing frontend IIFE app files (`records-app.js`, etc.) are
**not built**. Django views serve HTML pages; HTMX handles dynamic interactions
within those pages.

DRF endpoints are **not retired**. They remain the canonical data API for mobile
clients and future integrations. Django template views call the Django ORM and
service layer directly — they do not call DRF endpoints internally.

### 1.2 What Replaces What

| Old (vanilla JS) | New (Django templates + HTMX) |
|---|---|
| `records-app.js` IIFE module | `records/` Django app views + templates |
| `records.service.js` fetch calls | Django ORM calls inside views |
| `learn-app.js` + `learn.service.js` | `learn/` Django app views + templates |
| `activity-app.js` + `activity.service.js` | `activity/` Django app views + templates |
| `auth.js` register/login/logout | Django `django.contrib.auth` views + forms |
| `router.js` auth guard + navigation | Django `@login_required` decorator + middleware |
| `storage.js` data persistence role | **Removed** — Django session handles auth state |

| Kept unchanged | Reason |
|---|---|
| `storage.js` (UI state role only) | Theme preference, sidebar state — not persisted to DB |
| All CSS files (`main.css`, `navbar.css`, `learn.css`, etc.) | Design system is unchanged |
| `navbar.js` for app drawer toggle | Pure UI state interaction — no data involved |
| DRF endpoints at `/api/…` | Mobile + future integration layer |
| Django models, serializers, signals | Backend is unchanged |

### 1.3 Where Vanilla JS Remains Appropriate

Vanilla JS is retained **only** for interactions that are:
- Pure UI state (no server round-trip needed), **or**
- Browser API access (localStorage for theme, matchMedia for responsive hints)

| Vanilla JS use | File | Rationale |
|---|---|---|
| Theme toggle (light/dark/system) | `storage.js` | Reads/writes `localStorage`; no server state |
| App drawer open/close | `navbar.js` | CSS class toggle only |
| Navbar scroll-hide behaviour | `navbar.js` | IntersectionObserver — no data |
| Bottom nav active state | `navbar.js` | Derived from current URL |
| HTMX `htmx:afterSwap` hooks | Inline `<script>` in templates | Re-initialise CSS state after partial swap |

Everything else — form submissions, list loading, progress updates, detail views,
search, filtering, pagination — is HTMX + Django views.

### 1.4 HTMX Usage Patterns

**Pattern A — Form submissions (create/update)**

```html
<form hx-post="{% url 'records:create' %}"
      hx-target="#record-list"
      hx-swap="afterbegin"
      hx-on::after-request="this.reset()">
  {% csrf_token %}
  {{ form.as_p }}
  <button type="submit">Save</button>
</form>
```

The view returns a single rendered `_record_card.html` partial. HTMX prepends it
to the list. No full page reload. No JavaScript written by us.

**Pattern B — List views with pagination / filtering**

```html
<div id="record-list"
     hx-get="{% url 'records:list' %}"
     hx-trigger="load"
     hx-indicator="#list-spinner">
  {# populated by HTMX on page load #}
</div>

<input type="search" name="q"
       hx-get="{% url 'records:list' %}"
       hx-target="#record-list"
       hx-trigger="keyup changed delay:300ms"
       hx-include="[name='q']">
```

**Pattern C — Inline detail expand**

```html
<li hx-get="{% url 'records:detail' record.id %}"
    hx-target="#detail-panel"
    hx-swap="innerHTML"
    hx-push-url="true">
  {{ record.title }}
</li>
```

`hx-push-url="true"` keeps the browser URL in sync so deep links and back-button
work correctly.

**Pattern D — Progress bar / queue refresh (Learn App)**

```html
<div id="progress-bar"
     hx-get="{% url 'learn:progress' activity.id %}"
     hx-trigger="every 5s"
     hx-swap="outerHTML">
  <progress value="{{ activity.progress }}" max="100"></progress>
</div>
```

**Pattern E — Delete with confirmation**

```html
<button hx-delete="{% url 'records:delete' record.id %}"
        hx-target="#record-{{ record.id }}"
        hx-swap="outerHTML swap:0.3s"
        hx-confirm="Delete this record?">
  Delete
</button>
```

The view returns an empty `<span>` (or nothing) and HTMX removes the element.

### 1.5 URL Routing Strategy

Two URL namespaces exist side by side:

```
/api/…          DRF endpoints (JSON, token auth) — mobile + integrations
/…              Django template views (HTML, session auth) — web UI
```

URL routing rules:

```python
# ics_project/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),          # DRF router — all /api/ routes
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', include('accounts.urls')),
    path('records/', include('records.urls', namespace='records')),
    path('learn/', include('learn.urls', namespace='learn')),
    path('activity/', include('activity.urls', namespace='activity')),
    path('community/', include('community.urls', namespace='community')),
    path('governance/', include('governance.urls', namespace='governance')),
    path('', include('dashboard.urls', namespace='dashboard')),
]
```

Template view URL patterns follow a consistent REST-style shape:

```python
# records/urls.py
app_name = 'records'
urlpatterns = [
    path('',                   views.RecordListView.as_view(),   name='list'),
    path('create/',            views.RecordCreateView.as_view(), name='create'),
    path('<uuid:pk>/',         views.RecordDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/',    views.RecordUpdateView.as_view(), name='update'),
    path('<uuid:pk>/delete/',  views.RecordDeleteView.as_view(), name='delete'),
]
```

HTMX partial requests are distinguished from full-page requests via the
`HX-Request` header. Views return partials when this header is present:

```python
class RecordListView(LoginRequiredMixin, View):
    def get(self, request):
        records = Record.objects.filter(tenant=request.user.active_tenant)
        if request.headers.get('HX-Request'):
            return render(request, 'records/_list.html', {'records': records})
        return render(request, 'records/list.html', {'records': records})
```

### 1.6 Authentication Strategy

Django session authentication for template views. DRF token authentication for
`/api/` routes. These are parallel, independent auth stacks.

```
Web UI:   Browser → Django session cookie → @login_required → view
Mobile:   App → Authorization: Token {token} → DRF TokenAuthentication → DRF view
```

The `django.contrib.auth` login view sets the session. No JWT. No localStorage
token. The `router.js` auth guard is retired; Django's `@login_required` and
`LoginRequiredMixin` are the auth guard.

`LOGIN_URL = '/accounts/login/'` in `settings/base.py`. Unauthenticated requests
to any `@login_required` view are redirected there.

Post-login redirect: `LOGIN_REDIRECT_URL = '/'` (dashboard).
Post-logout redirect: `LOGOUT_REDIRECT_URL = '/accounts/login/'`.

### 1.7 CSRF

Django CSRF middleware is active (already in the default middleware stack). HTMX
must send the CSRF token on all state-mutating requests. Add this once in
`base.html`:

```html
<script>
  document.addEventListener('htmx:configRequest', (e) => {
    e.detail.headers['X-CSRFToken'] =
      document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? '';
  });
</script>
```

This is the **only** piece of vanilla JS wiring HTMX requires. It lives in
`base.html` and never needs to be repeated.

---

## Part 2 — Template Structure

### 2.1 Directory Layout

```
ics/
  templates/
    base.html                     ← master shell: navbar, drawer, bottom nav, theme
    base_partial.html             ← HTMX-only base: no chrome, just main content
    components/
      _navbar.html
      _app_drawer.html
      _bottom_nav.html
      _toast.html
      _spinner.html
      _empty_state.html
      _record_card.html
      _activity_card.html
    accounts/
      login.html
      register.html
      profile.html
    records/
      list.html
      _list.html                  ← HTMX partial
      detail.html
      _detail.html                ← HTMX partial
      create.html
      _form.html                  ← HTMX partial (form only)
      edit.html
    learn/
      index.html
      _my_learning.html
      _catalogue.html
      _lesson_viewer.html
      _progress_bar.html
      _cert_queue.html
    activity/
      list.html
      _list.html
      detail.html
    dashboard/
      index.html
      _digest_widget.html
      _activity_widget.html
    community/
      index.html
      _member_list.html
    governance/
      index.html
      _mandate_list.html
```

Naming convention:
- Files prefixed with `_` are **partials** — they return fragments, not full pages.
- Files without `_` prefix are **full pages** — they extend `base.html`.

### 2.2 `base.html` — Master Shell

This is the single source of truth for the page chrome. Every full-page template
extends this. It carries the navbar, app drawer, bottom nav, theme system, and
all CSS/JS load order.

```html
<!DOCTYPE html>
<html lang="en" data-theme="system">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}ICS{% endblock %} — Integrated Community System</title>

  {# Design system — load order is fixed; do not reorder #}
  <link rel="stylesheet" href="{% static 'css/main.css' %}">
  <link rel="stylesheet" href="{% static 'css/navbar.css' %}">
  {% block extra_css %}{% endblock %}

  {# HTMX — loaded in <head> so hx-* attributes work on first paint #}
  <script src="{% static 'js/htmx.min.js' %}" defer></script>

  {# UI state only — theme + drawer. Loaded before body renders to prevent flash #}
  <script src="{% static 'js/storage.js' %}"></script>
</head>
<body class="ics-shell" hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>

  {# Top navbar #}
  {% include "components/_navbar.html" %}

  {# App drawer (slide-in overlay) #}
  {% include "components/_app_drawer.html" %}

  {# Main content region — all page content swaps happen here #}
  <main id="main-content" class="ics-main" role="main">
    {# Toast notification anchor #}
    <div id="toast-container" aria-live="polite"></div>

    {% block content %}{% endblock %}
  </main>

  {# Bottom navigation — mobile only #}
  {% include "components/_bottom_nav.html" %}

  {# CSRF wiring for HTMX state-mutating requests #}
  <script>
    document.addEventListener('htmx:configRequest', (e) => {
      e.detail.headers['X-CSRFToken'] = '{{ csrf_token }}';
    });
  </script>

  {# Navbar UI: app drawer toggle, scroll-hide, bottom nav active state #}
  <script src="{% static 'js/navbar.js' %}" defer></script>

  {% block extra_js %}{% endblock %}
</body>
</html>
```

**Notes on `hx-headers`:** Using `hx-headers` on `<body>` is an alternative CSRF
strategy to the `htmx:configRequest` event listener. Both are shown; keep one.
The event listener approach is more explicit and easier to audit — prefer it.

### 2.3 `base_partial.html` — HTMX Fragment Base

Partials must not extend `base.html` (that would return the full chrome on every
HTMX swap). They extend this instead — which is empty:

```html
{# base_partial.html — intentionally empty. Partials extend this. #}
{% block content %}{% endblock %}
```

Partials that need no base at all can simply skip `{% extends %}` entirely. The
convention is to omit `extends` in partials — the template is a fragment by
definition.

### 2.4 Component Pattern — `_navbar.html`

```html
{# components/_navbar.html #}
<header class="ics-navbar" role="banner">
  <button class="ics-navbar__drawer-btn"
          aria-label="Open app menu"
          aria-expanded="false"
          aria-controls="app-drawer"
          id="drawer-toggle">
    <span class="material-icon">menu</span>
  </button>

  <a href="{% url 'dashboard:index' %}" class="ics-navbar__wordmark">ICS</a>

  <nav class="ics-navbar__actions" aria-label="Top actions">
    {% if user.is_authenticated %}
      <a href="{% url 'accounts:notifications' %}"
         class="ics-navbar__icon-btn"
         aria-label="Notifications"
         hx-get="{% url 'accounts:notifications_count' %}"
         hx-trigger="load, every 60s"
         hx-target="#notif-badge">
        <span class="material-icon">notifications</span>
        <span id="notif-badge" class="badge"></span>
      </a>
      <a href="{% url 'accounts:profile' %}" class="ics-navbar__avatar">
        {% if user.avatar_url %}
          <img src="{{ user.avatar_url }}" alt="{{ user.display_name }}">
        {% else %}
          <span class="avatar-initials">{{ user.display_name|first }}</span>
        {% endif %}
      </a>
    {% else %}
      <a href="{% url 'accounts:login' %}" class="btn btn--ghost">Sign in</a>
    {% endif %}
  </nav>
</header>
```

### 2.5 App-Specific CSS Load

Each app that has its own CSS (e.g. `learn.css`) loads it via the `extra_css`
block in the full-page template:

```html
{# learn/index.html #}
{% extends "base.html" %}
{% block extra_css %}
  <link rel="stylesheet" href="{% static 'css/learn.css' %}">
{% endblock %}
{% block content %}
  ...
{% endblock %}
```

This keeps CSS scoped to where it is needed without loading everything globally.

---

## Part 3 — Script Load Order

The final, locked load order for the Django template era:

```
HEAD (blocking)
  htmx.min.js          — HTMX engine. Must be present before body renders.
  storage.js           — Theme init. Must run before body renders to prevent flash.

BODY end (defer)
  navbar.js            — App drawer toggle, scroll-hide, bottom nav active state.
  [app-specific JS]    — Only if a page needs minor vanilla JS (e.g. quiz timer).
```

**What is gone:**
- `router.js` — retired. Django `@login_required` + `LoginRequiredMixin` replace it.
- `auth.js` — retired. `django.contrib.auth` views replace it.
- All `*.service.js` files — **never built**. Django views call ORM directly.
- All `*-app.js` IIFE files — **never built**. Django template views replace them.

**What `storage.js` now does (trimmed scope):**

```javascript
// storage.js — UI state only. No data persistence. No auth tokens.
const ICSStorage = (() => {
  const THEME_KEY = 'ics_theme';

  function getTheme() {
    return localStorage.getItem(THEME_KEY) ?? 'system';
  }

  function setTheme(theme) {
    localStorage.setItem(THEME_KEY, theme);
    document.documentElement.setAttribute('data-theme', theme);
  }

  // Apply theme on load (prevents flash)
  setTheme(getTheme());

  return { getTheme, setTheme };
})();
```

Everything else that was in `storage.js` (user objects, records cache, session
token) is removed. Those live in the Django session and PostgreSQL.

---

## Part 4 — Migration Plan

### Phase M0 — Install HTMX + Update Settings

**Files:**
- Download: `frontend/assets/js/htmx.min.js` (or `static/js/htmx.min.js`)
- Modify: `ics_project/settings/base.py`
- Modify: `ics_project/urls.py`

**Step 1:** Download HTMX 1.9.x minified from `https://unpkg.com/htmx.org/dist/htmx.min.js`
and place at `static/js/htmx.min.js`.

**Step 2:** Add to `settings/base.py`:
```python
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
```

**Step 3:** Add to `settings/base.py` middleware (session must be present):
```python
MIDDLEWARE = [
    ...
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    ...
]
```

**Step 4:** Wire `django.contrib.auth.urls` in `ics_project/urls.py`:
```python
path('accounts/', include('django.contrib.auth.urls')),
```

Commit: `git commit -m "chore: install htmx, configure template settings, wire auth urls"`

---

### Phase M1 — Migrate Navigation System

The navbar, app drawer, bottom nav, and theme system move from `index.html` +
inline JS into Django template components. The CSS is **unchanged**.

**Files:**
- Create: `templates/base.html`
- Create: `templates/components/_navbar.html`
- Create: `templates/components/_app_drawer.html`
- Create: `templates/components/_bottom_nav.html`
- Create: `templates/components/_toast.html`
- Create: `templates/components/_spinner.html`
- Trim: `static/js/storage.js` (remove data persistence, keep theme only)
- Keep: `static/js/navbar.js` (unchanged — pure UI state)
- Keep: `static/css/main.css`, `static/css/navbar.css` (unchanged)

**Step 1:** Create `templates/base.html` per the spec in Part 2.2 above.

**Step 2:** Extract navbar HTML from `index.html` → `templates/components/_navbar.html`.
Port hard-coded links to `{% url %}` tags. The structure and CSS classes are
identical — only the link hrefs change.

**Step 3:** Extract app drawer HTML → `templates/components/_app_drawer.html`.
App drawer links become `{% url %}` tags. Active state is set server-side:
```html
<a href="{% url 'records:list' %}"
   class="drawer-item {% if request.resolver_match.app_name == 'records' %}drawer-item--active{% endif %}">
  Records
</a>
```

**Step 4:** Extract bottom nav → `templates/components/_bottom_nav.html`.
Same active-state pattern as above.

**Step 5:** Trim `storage.js` to theme-only per the spec in Part 3.

**Step 6:** Create a smoke-test view:
```python
# dashboard/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    return render(request, 'dashboard/index.html')
```
```python
# dashboard/urls.py
app_name = 'dashboard'
urlpatterns = [path('', views.index, name='index')]
```
```html
{# templates/dashboard/index.html #}
{% extends "base.html" %}
{% block title %}Dashboard{% endblock %}
{% block content %}
  <h1>Dashboard</h1>
{% endblock %}
```

**Step 7:** Visit `http://localhost:8000/`. Verify:
- Navbar renders with correct links
- App drawer opens/closes via `navbar.js`
- Theme toggle works via `storage.js`
- Bottom nav highlights correct item
- `@login_required` redirects to `/accounts/login/`

Commit: `git commit -m "feat: base.html, nav components, theme system — Django templates"`

---

### Phase M2 — Migrate Auth Flows

The register/login/logout flows move from `auth.js` (DRF fetch calls) to Django
auth views. The DRF `/api/auth/` endpoints remain for mobile.

**Files:**
- Create: `templates/accounts/login.html`
- Create: `templates/accounts/register.html`
- Create: `templates/accounts/profile.html`
- Create: `accounts/forms.py` (registration form)
- Modify: `accounts/views.py` (add RegisterView)
- Modify: `accounts/urls.py`
- Remove from load order: `auth.js`, `router.js`

**Step 1:** `accounts/forms.py`:
```python
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)
    display_name = forms.CharField(max_length=100)

    class Meta:
        model = User
        fields = ['email', 'display_name', 'password']

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password_confirm'):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned
```

**Step 2:** `accounts/views.py` — RegisterView:
```python
from django.contrib.auth import login
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from .forms import RegisterForm

class RegisterView(FormView):
    template_name = 'accounts/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('dashboard:index')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        login(self.request, user)
        return super().form_valid(form)
```

**Step 3:** `templates/accounts/login.html`:
```html
{% extends "base.html" %}
{% block title %}Sign In{% endblock %}
{% block content %}
<div class="auth-card">
  <h1>Sign In</h1>
  <form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit" class="btn btn--primary">Sign In</button>
  </form>
  <p>No account? <a href="{% url 'accounts:register' %}">Register</a></p>
</div>
{% endblock %}
```

**Step 4:** `templates/accounts/register.html` — same pattern as login.

**Step 5:** Verify: register → auto-login → redirect to dashboard. Logout →
redirect to `/accounts/login/`.

Commit: `git commit -m "feat: Django auth views — register, login, logout"`

---

### Phase M3 — Migrate Records App

The Records app UI moves from the vanilla JS IIFE `records-app.js` to Django
class-based views + HTMX partials.

**Files:**
- Create: `records/views.py` (CBVs)
- Create: `records/urls.py`
- Create: `records/forms.py`
- Create: `templates/records/list.html`
- Create: `templates/records/_list.html` (HTMX partial)
- Create: `templates/records/detail.html`
- Create: `templates/records/_detail.html` (HTMX partial)
- Create: `templates/records/_form.html` (HTMX partial)
- Create: `templates/records/create.html`
- Create: `templates/records/edit.html`
- Create: `templates/components/_record_card.html`

**Step 1:** `records/forms.py` — ModelForm wrapping the Record model:
```python
from django import forms
from .models import Record

class RecordForm(forms.ModelForm):
    class Meta:
        model = Record
        fields = ['title', 'record_type', 'record_class', 'record_family',
                  'body', 'status', 'visibility']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 6}),
        }
```

**Step 2:** `records/views.py`:
```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Record
from .forms import RecordForm

class RecordListView(LoginRequiredMixin, ListView):
    model = Record
    context_object_name = 'records'

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['records/_list.html']
        return ['records/list.html']

    def get_queryset(self):
        qs = Record.objects.filter(
            tenant=self.request.user.active_tenant
        ).order_by('-created_at')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(title__icontains=q)
        return qs

class RecordDetailView(LoginRequiredMixin, DetailView):
    model = Record
    context_object_name = 'record'

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['records/_detail.html']
        return ['records/detail.html']

class RecordCreateView(LoginRequiredMixin, CreateView):
    model = Record
    form_class = RecordForm
    success_url = reverse_lazy('records:list')

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['records/_form.html']
        return ['records/create.html']

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.tenant = self.request.user.active_tenant
        return super().form_valid(form)

class RecordUpdateView(LoginRequiredMixin, UpdateView):
    model = Record
    form_class = RecordForm
    success_url = reverse_lazy('records:list')

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['records/_form.html']
        return ['records/edit.html']

class RecordDeleteView(LoginRequiredMixin, DeleteView):
    model = Record
    success_url = reverse_lazy('records:list')

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        if request.headers.get('HX-Request'):
            return HttpResponse('')  # HTMX removes the element
        return response
```

**Step 3:** `templates/records/list.html`:
```html
{% extends "base.html" %}
{% block title %}Records{% endblock %}
{% block content %}
<div class="records-page">
  <header class="page-header">
    <h1>Records</h1>
    <a href="{% url 'records:create' %}" class="btn btn--primary">New Record</a>
  </header>

  <input type="search"
         name="q"
         placeholder="Search records…"
         hx-get="{% url 'records:list' %}"
         hx-target="#record-list"
         hx-trigger="keyup changed delay:300ms"
         hx-include="[name='q']"
         class="search-input">

  <div id="record-list"
       hx-get="{% url 'records:list' %}"
       hx-trigger="load"
       hx-indicator="#list-spinner">
    {% include "components/_spinner.html" with id="list-spinner" %}
  </div>
</div>
{% endblock %}
```

**Step 4:** `templates/records/_list.html` (the partial returned by HTMX):
```html
{% for record in records %}
  {% include "components/_record_card.html" %}
{% empty %}
  {% include "components/_empty_state.html" with message="No records yet." %}
{% endfor %}
```

**Step 5:** `templates/components/_record_card.html`:
```html
<article class="record-card" id="record-{{ record.id }}"
         hx-get="{% url 'records:detail' record.id %}"
         hx-target="#detail-panel"
         hx-push-url="true">
  <h3 class="record-card__title">{{ record.title }}</h3>
  <span class="badge badge--{{ record.record_class }}">{{ record.record_type }}</span>
  <time class="record-card__date">{{ record.created_at|date:"d M Y" }}</time>
</article>
```

**Step 6:** Verify all CRUD operations: create, list, search, detail, edit, delete.
Verify HTMX partials swap correctly without full page reload.

Commit: `git commit -m "feat: records app — Django CBVs + HTMX partials"`

---

### Phase M4 — Update `settings/base.py` Static Files

Move static assets from `frontend/assets/` to Django's standard `static/`
directory so `{% static %}` template tags resolve correctly.

```python
# settings/base.py
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

File moves (copy, not delete — verify before removing originals):
```
frontend/assets/css/main.css    → static/css/main.css
frontend/assets/css/navbar.css  → static/css/navbar.css
frontend/assets/js/storage.js   → static/js/storage.js
frontend/assets/js/navbar.js    → static/js/navbar.js
htmx.min.js                     → static/js/htmx.min.js
```

All app-specific CSS files follow the same pattern (`learn.css`, `records.css`).

Commit: `git commit -m "chore: migrate static assets to Django static/ directory"`

---

## Part 5 — What This Means for Remaining App Builds

All remaining apps (Activity, Learn, Community, Governance, Dashboard, Profile,
Settings, Notifications) follow **Phase M3** as their template. For each app:

1. Create Django app + models (unchanged from roadmap)
2. Create DRF serializers + views + URLs at `/api/<app>/` (unchanged)
3. Create Django CBVs + template views at `/<app>/`
4. Create `templates/<app>/` directory with `list.html`, `detail.html`, partials
5. HTMX handles list loading, form submission, and any polling interactions
6. No `<app>.service.js`, no `<app>-app.js` — these are not built

**Learn App specifically:** Phases A and B from the Learn App system design
(Django `learn` app, models, DRF endpoints, signals) are unchanged. Phases C–G
(UI layer) are implemented as Django template views + HTMX, not `learn-app.js`.
`learn.css` is carried forward identically.

---

## Part 6 — Decision Log

| Decision | Rationale |
|---|---|
| HTMX over React/Vue | No build toolchain. Preserves Django template rendering. Consistent with no-JS-framework constraint. |
| Django session auth (not JWT in browser) | Simpler. No token storage in `localStorage`. CSRF + session cookies are the browser-native security model. |
| DRF endpoints retained | Mobile clients exist. Future integrations exist. Template views and DRF views share the same ORM layer — no duplication of business logic. |
| `hx-push-url="true"` on detail views | Deep links and back-button must work. HTMX does not push URL by default. |
| CBVs over function views | `LoginRequiredMixin`, `get_template_names()` override for partial detection — CBVs make these patterns clean and consistent. |
| Partials named with `_` prefix | Unambiguous convention. Any template starting with `_` is a fragment. Full-page templates never start with `_`. |
| No `base_partial.html` extends | Partials simply omit `{% extends %}`. They are fragments by definition. An explicit empty base adds indirection with no benefit. |
| CSS unchanged | The design system is a solved problem. Migrating to HTMX is an engine swap, not a redesign. |

---

*End of document. This ADR supersedes the vanilla JS IIFE frontend layer described
in build roadmap v2. All subsequent app build sessions should reference this
document as the UI architecture specification.*
