from django.urls import path

from . import api_views

urlpatterns = [
    path('now/', api_views.NowPlayingView.as_view(), name='broadcast-now-playing'),
]
