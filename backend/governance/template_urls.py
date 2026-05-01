from django.urls import path
from . import views, desk_views

app_name = 'governance'

urlpatterns = [
    # ── Workspace Shell Views ────────────────────────────────────────────────
    path('', views.governance_home, name='home'),
    path('desk/', desk_views.universal_desk, name='desk'),
    path('desk/save/', desk_views.universal_save, name='save'),
    path('desk/<uuid:record_id>/', desk_views.universal_desk, name='desk-edit'),
    
    # ── Library ──────────────────────────────────────────────────────────────
    path('library/', views.library_home, name='library-home'),
    path('library/<uuid:record_id>/', views.library_detail, name='library-detail'),
    path('library/<str:record_type>/', views.library_list, name='library-list'),

    # ── Mandate ──────────────────────────────────────────────────────────────
    path('mandate/', views.mandate_home, name='mandate-home'),
    path('mandate/<uuid:record_id>/', views.mandate_detail, name='mandate-detail'),
    path('mandate/<str:record_type>/', views.mandate_list, name='mandate-list'),

    # ── Keys ─────────────────────────────────────────────────────────────────
    path('keys/', views.keys_list, name='keys-list'),
    path('keys/<uuid:record_id>/', views.keys_detail, name='keys-detail'),

    # ── HTMX Operations ──────────────────────────────────────────────────────
    path('htmx/record/create/', views.htmx_record_create, name='htmx-record-create'),
    path('htmx/record/<uuid:record_id>/edit/', views.htmx_record_edit, name='htmx-record-edit'),
    path('htmx/record/<uuid:record_id>/links/', views.htmx_linked_records, name='htmx-linked-records'),
    path('htmx/record/<uuid:record_id>/history/', views.htmx_version_history, name='htmx-version-history'),
]
