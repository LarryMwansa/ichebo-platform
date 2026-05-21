from django.urls import path
from . import views

urlpatterns = [
    path('upload/init/', views.UploadInitView.as_view(), name='media-upload-init'),
    path('upload/complete/', views.UploadCompleteView.as_view(), name='media-upload-complete'),
    path('videos/', views.VideoListView.as_view(), name='media-video-list'),
    path('videos/<uuid:record_id>/', views.VideoDetailView.as_view(), name='media-video-detail'),
    path('transcode-complete/', views.TranscodeCompleteWebhookView.as_view(), name='media-transcode-complete'),
]
