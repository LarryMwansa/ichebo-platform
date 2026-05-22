from django.urls import path
from . import api_views

urlpatterns = [
    path('records/', api_views.HandbookRecordListCreateView.as_view()),
    path('records/<uuid:pk>/', api_views.HandbookRecordDetailView.as_view()),
    path('records/<uuid:pk>/publish/', api_views.HandbookPublishView.as_view()),
    path('records/<uuid:pk>/lock/', api_views.HandbookLockView.as_view()),
    path('records/<uuid:pk>/new-version/', api_views.HandbookNewVersionView.as_view()),
    path('records/<uuid:pk>/history/', api_views.HandbookHistoryView.as_view()),
    path('access/', api_views.HandbookAccessListView.as_view()),
    path('publish-feed/', api_views.HandbookPublishFeedView.as_view()),
]
