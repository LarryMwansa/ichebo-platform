"""
API routes for notifications — mounted at /api/ in root urls.py.
namespace: notifications-api
"""
from django.urls import path
from . import views

app_name = 'notifications-api'

urlpatterns = [
    path('notifications/', views.notification_list, name='list'),
    path('notifications/unread-count/', views.unread_count, name='unread-count'),
    path('notifications/unread-badge/', views.htmx_unread_badge, name='unread-badge'),
    path('notifications/mark-all-read/', views.mark_all_read, name='mark-all-read'),
    path('notifications/health/', views.health, name='health'),
]
