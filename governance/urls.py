from django.urls import path
from . import views

app_name = 'governance'

urlpatterns = [
    # ── Health ──────────────────────────────────────────────────────────────
    path('api/governance/health/', views.governance_health, name='api-health'),

    # ── Governance shell ─────────────────────────────────────────────────────
    path('governance/', views.governance_home, name='home'),

    # ── Reference Library ────────────────────────────────────────────────────
    path('governance/library/', views.library_home, name='library-home'),
    path('governance/library/<str:record_type>/', views.library_list, name='library-list'),
    path('governance/library/record/<uuid:record_id>/', views.library_detail, name='library-detail'),

    # ── Mandate branch ───────────────────────────────────────────────────────
    path('governance/mandate/', views.mandate_home, name='mandate-home'),
    path('governance/mandate/<str:record_type>/', views.mandate_list, name='mandate-list'),
    path('governance/mandate/record/<uuid:record_id>/', views.mandate_detail, name='mandate-detail'),

    # ── My Keys ──────────────────────────────────────────────────────────────
    path('governance/keys/', views.keys_list, name='keys-list'),
    path('governance/keys/<uuid:record_id>/', views.keys_detail, name='keys-detail'),

    # ── HTMX partials ────────────────────────────────────────────────────────
    path('governance/htmx/relationships/<uuid:record_id>/',
         views.htmx_linked_records, name='htmx-linked-records'),
    path('governance/htmx/versions/<uuid:record_id>/',
         views.htmx_version_history, name='htmx-version-history'),

    # ── Record CRUD ──────────────────────────────────────────────────────────
    path('governance/htmx/record/create/', views.htmx_record_create, name='htmx-record-create'),
    path('governance/htmx/record/<uuid:record_id>/edit/', views.htmx_record_edit, name='htmx-record-edit'),
    path('governance/htmx/record/<uuid:record_id>/lock/', views.htmx_record_lock, name='htmx-record-lock'),
    path('governance/htmx/record/<uuid:record_id>/supersede/', views.htmx_record_supersede, name='htmx-record-supersede'),

    # ── Relationship create ──────────────────────────────────────────────────
    path('governance/htmx/relationship/create/', views.htmx_relationship_create, name='htmx-relationship-create'),
]
