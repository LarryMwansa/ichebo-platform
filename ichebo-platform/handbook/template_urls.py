from django.urls import path
from . import views

app_name = 'handbook'

urlpatterns = [
    path('', views.handbook_home, name='home'),
    path('records/new/', views.handbook_new, name='new'),
    path('records/<uuid:record_id>/', views.handbook_record, name='record'),
    path('access/', views.handbook_access, name='access'),

    # ── Desk save (moved from governance) ────────────────────────────────────
    path('save/', views.handbook_save, name='save'),

    # ── Lifecycle HTMX ────────────────────────────────────────────────────────
    path('htmx/<uuid:record_id>/lock/', views.handbook_lock, name='htmx-lock'),
    path('htmx/<uuid:record_id>/publish/', views.handbook_publish, name='htmx-publish'),
    path('htmx/<uuid:record_id>/new-version/', views.handbook_new_version, name='htmx-new-version'),
    path('htmx/<uuid:record_id>/set-status/', views.handbook_set_status, name='htmx-set-status'),
    path('htmx/<uuid:record_id>/links/', views.handbook_linked_records, name='htmx-links'),
    path('htmx/<uuid:record_id>/relationships/', views.handbook_relationship_list, name='htmx-relationship-list'),
    path('htmx/relationship/create/', views.handbook_relationship_create, name='htmx-relationship-create'),
    path('htmx/recent/', views.handbook_recent, name='htmx-recent'),

    # ── Knowledge Graph ───────────────────────────────────────────────────────
    path('graph/', views.handbook_graph, name='graph'),
    path('htmx/graph/data/', views.handbook_graph_data, name='htmx-graph-data'),
]
