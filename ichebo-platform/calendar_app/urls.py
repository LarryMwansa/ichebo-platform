from django.urls import path
from . import views

app_name = 'calendar-api'

urlpatterns = [
    path('events/', views.calendar_events, name='calendar-events'),
]
