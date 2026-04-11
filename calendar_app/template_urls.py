from django.urls import path
from . import views

app_name = 'calendar'

urlpatterns = [
    path('', views.month_view, name='month'),
    path('week/', views.week_view, name='week'),
]
