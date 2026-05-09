"""
Template routes for notifications — mounted at /notifications/ in root urls.py.
namespace: notifications
"""
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='list'),
    path('mark-all-read/', views.htmx_mark_all_read, name='mark-all-read'),
    path('mark-read/<uuid:notification_id>/', views.htmx_mark_one_read, name='mark-read'),
    path('htmx/badge/', views.htmx_unread_badge, name='htmx-badge'),
]
