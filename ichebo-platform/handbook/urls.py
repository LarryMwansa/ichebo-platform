from django.urls import path
from . import views
from . import api_views

app_name = 'handbook'

# ── Workspace (template) URLs ─────────────────────────────────────────────────
template_urlpatterns = [
    path('', views.handbook_home, name='home'),
    path('records/new/', views.handbook_new, name='new'),
    path('records/<uuid:pk>/', views.handbook_record, name='record'),
    path('access/', views.handbook_access, name='access'),
]

# ── DRF API URLs ──────────────────────────────────────────────────────────────
api_urlpatterns = [
    path('records/', api_views.HandbookRecordListCreateView.as_view(), name='api-records'),
    path('records/<uuid:pk>/', api_views.HandbookRecordDetailView.as_view(), name='api-record-detail'),
    path('records/<uuid:pk>/publish/', api_views.HandbookPublishView.as_view(), name='api-record-publish'),
    path('records/<uuid:pk>/lock/', api_views.HandbookLockView.as_view(), name='api-record-lock'),
    path('records/<uuid:pk>/new-version/', api_views.HandbookNewVersionView.as_view(), name='api-record-new-version'),
    path('records/<uuid:pk>/history/', api_views.HandbookHistoryView.as_view(), name='api-record-history'),
    path('access/', api_views.HandbookAccessListView.as_view(), name='api-access'),
    path('publish-feed/', api_views.HandbookPublishFeedView.as_view(), name='api-publish-feed'),
]
