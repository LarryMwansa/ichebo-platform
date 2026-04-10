from django.urls import path
from . import views

urlpatterns = [
    path('events/', views.calendar_events, name='calendar-events'),
]
