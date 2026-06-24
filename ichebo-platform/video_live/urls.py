from django.urls import path
from . import api_views

app_name = 'video_live'

# All template views and the mobile feed/CRUD API were deleted 2026-06-24
# (video-direction-v2-plan.md) — only the Go engine / MediaMTX webhooks
# remain, since BroadcastSchedule is now created directly by Community's
# digital-Gathering flow rather than through a standalone video app.
urlpatterns = [
    path('api/stream/start/', api_views.StreamStartWebhookView.as_view(), name='api-stream-start'),
    path('api/stream/end/',   api_views.StreamEndWebhookView.as_view(),   name='api-stream-end'),
]
