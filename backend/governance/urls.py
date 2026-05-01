from django.urls import path
from . import views

app_name = 'governance'

urlpatterns = [
    # ── Health ──────────────────────────────────────────────────────────────
    path('api/health/', views.governance_health, name='api-health'),

    # ── Governance shell ─────────────────────────────────────────────────────
    path('', views.governance_home, name='home'),

    # ── Reference Library ────────────────────────────────────────────────────
    path('reference/', views.library_home, name='library-home'),
    path('reference/<uuid:record_id>/', views.library_detail, name='library-detail'),
    path('reference/<str:record_type>/', views.library_list, name='library-list'),

    # ── Mandate branch ───────────────────────────────────────────────────────
    path('mandate/', views.mandate_home, name='mandate-home'),
    path('mandate/<uuid:record_id>/', views.mandate_detail, name='mandate-detail'),
    path('mandate/<str:record_type>/', views.mandate_list, name='mandate-list'),

    # ── My Keys ──────────────────────────────────────────────────────────────
    path('keys/', views.keys_list, name='keys-list'),
    path('keys/<uuid:record_id>/', views.keys_detail, name='keys-detail'),

    # ── HTMX partials — linked records + version history ────────────────────
    path('htmx/record/<uuid:record_id>/links/',
         views.htmx_linked_records, name='htmx-linked-records'),
    path('htmx/record/<uuid:record_id>/history/',
         views.htmx_version_history, name='htmx-version-history'),

    # ── Record CRUD ──────────────────────────────────────────────────────────
    path('htmx/record/create/', views.htmx_record_create, name='htmx-record-create'),
    path('htmx/record/<uuid:record_id>/edit/', views.htmx_record_edit, name='htmx-record-edit'),
    path('htmx/record/<uuid:record_id>/lock/', views.htmx_record_lock, name='htmx-record-lock'),
    path('htmx/record/<uuid:record_id>/supersede/', views.htmx_record_supersede, name='htmx-record-supersede'),

    # ── Relationship create ──────────────────────────────────────────────────
    path('htmx/relationship/create/', views.htmx_relationship_create, name='htmx-relationship-create'),

    # ── Navigation list partials + journal search ────────────────────────────
    path('htmx/reference/list/', views.htmx_reference_list, name='htmx-reference-list'),
    path('htmx/mandate/list/', views.htmx_mandate_list, name='htmx-mandate-list'),
    path('htmx/journal/search/', views.htmx_journal_search, name='htmx-journal-search'),
    path('htmx/global-search/', views.htmx_global_search, name='htmx-global-search'),
]
