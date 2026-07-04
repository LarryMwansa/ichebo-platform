from django.urls import path

from broadcast import views

urlpatterns = [
    path('', views.channel_overview, name='channel_overview'),
    path('slots/add/', views.channel_slot_add, name='channel_slot_add'),
    path('slots/<uuid:slot_id>/delete/', views.channel_slot_delete, name='channel_slot_delete'),
    path('config/<uuid:tenant_id>/', views.channel_config_edit, name='channel_config_edit'),
]
