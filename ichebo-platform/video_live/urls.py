from django.urls import path
from . import views, api_views

app_name = 'video_live'

urlpatterns = [
    # ── Mobile API ──
    path('api/feed/', api_views.VideoFeedView.as_view(), name='api-feed'),

    # ── Template views ──
    path('',                          views.video_home,         name='home'),
    path('live/',                     views.video_live_view,    name='live'),
    path('schedule/',                 views.video_schedule,     name='schedule'),
    path('vod/',                      views.video_vod,          name='vod'),
    path('watch/<uuid:event_id>/',    views.video_watch,        name='watch'),
    path('manage/',                   views.video_manage,       name='manage'),
    path('manage/<uuid:event_id>/delete/', views.video_delete_event, name='delete-event'),

    # Studio (Level 3+)
    path('studio/',                               views.video_studio,              name='studio'),
    path('studio/htmx/now-playing/',              views.htmx_studio_now_playing,   name='studio-now-playing'),
    path('studio/htmx/timeline/',                 views.htmx_studio_timeline,      name='studio-timeline'),
    path('studio/htmx/quick-schedule/',           views.htmx_studio_quick_schedule, name='studio-quick-schedule'),
    path('studio/htmx/set-fallback/',             views.htmx_studio_set_fallback,  name='studio-set-fallback'),
]
