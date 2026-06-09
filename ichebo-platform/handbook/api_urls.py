from django.urls import path
from . import api_views

urlpatterns = [
    path('health/', api_views.handbook_health),
]
