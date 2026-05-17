from django.urls import path
from . import views

app_name = 'dashboard'
urlpatterns = [
    path('', views.index, name='index'),
    path('explore/', views.explore, name='explore'),
    path('you/', views.you, name='you'),
    path('htmx/governance/', views.htmx_governance_tab, name='htmx-governance'),
    path('htmx/records/', views.htmx_records_tab, name='htmx-records'),
    path('htmx/launcher/', views.htmx_launcher, name='htmx-launcher'),
    path('htmx/learn/', views.htmx_learn_tab, name='htmx-learn'),
    path('htmx/schedule/', views.htmx_today_schedule, name='htmx-schedule'),
    path('htmx/explore-menu/', views.htmx_explore_create_menu, name='htmx-explore-menu'),
]
