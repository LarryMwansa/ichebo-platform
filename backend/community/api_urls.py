from django.urls import path
from . import api_views

app_name = 'community-api'

urlpatterns = [
    path('health/', api_views.community_health, name='community-health'),
]
