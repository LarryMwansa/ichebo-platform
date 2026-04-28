from django.urls import path
from . import views

app_name = 'video_live'

urlpatterns = [
    path('',                          views.video_home,         name='home'),
    path('live/',                     views.video_live_view,    name='live'),
    path('schedule/',                 views.video_schedule,     name='schedule'),
    path('vod/',                      views.video_vod,          name='vod'),
    path('watch/<uuid:event_id>/',    views.video_watch,        name='watch'),
    path('manage/',                   views.video_manage,       name='manage'),
    path('manage/<uuid:event_id>/delete/', views.video_delete_event, name='delete-event'),
]
