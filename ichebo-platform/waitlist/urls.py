from django.urls import path
from . import views

urlpatterns = [
    path('', views.waitlist_register, name='waitlist-register'),
    path('health/', views.waitlist_health, name='waitlist-health'),
]
