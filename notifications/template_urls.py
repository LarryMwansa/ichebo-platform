"""
Template routes for notifications — mounted at /notifications/ in root urls.py.
namespace: notifications
"""
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='list'),
]
