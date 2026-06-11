from django.urls import path
from django.views.generic import RedirectView
from . import template_views

app_name = 'records'

urlpatterns = [
    path('', template_views.my_records, name='records-home'),
    path('<uuid:record_id>/', template_views.record_detail, name='records-detail'),
    path('htmx/create/', template_views.htmx_create_record, name='htmx-create'),
    path('htmx/fab-sheet/', template_views.htmx_fab_sheet, name='htmx-fab-sheet'),
    path('htmx/<uuid:record_id>/edit/', template_views.htmx_edit_record, name='htmx-edit'),
    path('htmx/<uuid:record_id>/delete/', template_views.htmx_delete_record, name='htmx-delete'),
    path('htmx/<uuid:record_id>/linked-records/', template_views.htmx_linked_records, name='htmx-linked-records'),
    path('htmx/relationship/create/', template_views.htmx_relationship_create, name='htmx-relationship-create'),
    path('htmx/search/', template_views.htmx_record_search, name='htmx-record-search'),
    path('htmx/recent-drafts/', template_views.htmx_recent_drafts, name='htmx-recent-drafts'),
    
    # ── Knowledge Graph — redirects to Handbook ──
    path('graph/', RedirectView.as_view(pattern_name='handbook:graph', permanent=True), name='graph'),
    path('htmx/graph/data/', RedirectView.as_view(pattern_name='handbook:htmx-graph-data', permanent=False), name='htmx-graph-data'),
]
