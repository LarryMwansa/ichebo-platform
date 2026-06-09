from django.urls import path
from . import views

app_name = 'governance'

urlpatterns = [
    # ── Workspace Shell Views (read-only library) ────────────────────────────
    path('', views.governance_home, name='home'),

    # ── Reference Library ────────────────────────────────────────────────────
    path('library/', views.library_home, name='library-home'),
    path('library/<uuid:record_id>/', views.library_detail, name='library-detail'),
    path('library/<str:record_type>/', views.library_list, name='library-list'),

    # ── Mandate Branch ───────────────────────────────────────────────────────
    path('mandate/', views.mandate_home, name='mandate-home'),
    path('mandate/<uuid:record_id>/', views.mandate_detail, name='mandate-detail'),
    path('mandate/<str:record_type>/', views.mandate_list, name='mandate-list'),

    # ── Keys ─────────────────────────────────────────────────────────────────
    path('keys/', views.keys_list, name='keys-list'),
    path('keys/<uuid:record_id>/', views.keys_detail, name='keys-detail'),

    # ── Read-only HTMX panels ────────────────────────────────────────────────
    path('htmx/record/<uuid:record_id>/links/', views.htmx_linked_records, name='htmx-linked-records'),
    path('htmx/record/<uuid:record_id>/history/', views.htmx_version_history, name='htmx-version-history'),
    path('htmx/global-search/', views.htmx_global_search, name='htmx-global-search'),
]
