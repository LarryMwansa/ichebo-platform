from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'activities', api_views.ActivityViewSet, basename='activity')

urlpatterns = [
    path('', include(router.urls)),
    path('health/', api_views.health, name='activity-health'),
]
