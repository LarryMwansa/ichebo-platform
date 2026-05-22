from django.urls import path
from .views import health as views
from .views.sync import SyncChangesView, SyncPullView, SyncPushView, ValidateLicenceView

urlpatterns = [
    path('health/', views.health_check, name='health-check'),
    path('sync/validate-licence/', ValidateLicenceView.as_view(), name='sync-validate-licence'),
    path('sync/pull/', SyncPullView.as_view(), name='sync-pull'),
    path('sync/push/', SyncPushView.as_view(), name='sync-push'),
    path('sync/changes/', SyncChangesView.as_view(), name='sync-changes'),  # legacy alias
]
