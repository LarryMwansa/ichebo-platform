from django.urls import path
from .views import health as views
from .views.sync import SyncChangesView

urlpatterns = [
    path('health/', views.health_check, name='health-check'),
    path('sync/changes/', SyncChangesView.as_view(), name='sync-changes'),
]
