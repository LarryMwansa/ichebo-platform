from django.urls import path
from . import views

urlpatterns = [
    path('tenants/', views.tenant_list_create, name='tenant-list-create'),
    path('tenants/<uuid:pk>/', views.tenant_detail, name='tenant-detail'),
    path('permissions/', views.user_permission_list_create, name='permission-list-create'),
    path('permissions/<uuid:pk>/', views.user_permission_detail, name='permission-detail'),
]