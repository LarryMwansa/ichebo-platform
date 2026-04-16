from django.urls import path
from . import views

app_name = 'activity'

urlpatterns = [
    path('', views.my_activities, name='activity-home'),

    # HTMX partials
    path('htmx/create/', views.htmx_create_activity, name='htmx-create'),
    path('htmx/list/', views.htmx_activity_list, name='htmx-list'),
    path('htmx/<uuid:activity_id>/complete/', views.htmx_complete_activity, name='htmx-complete'),
    path('htmx/<uuid:activity_id>/edit/', views.htmx_edit_activity, name='htmx-edit'),
    path('htmx/<uuid:activity_id>/delete/', views.htmx_delete_activity, name='htmx-delete'),
]
