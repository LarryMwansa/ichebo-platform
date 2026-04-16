from django.urls import path
from . import template_views

app_name = 'tenants'

urlpatterns = [
    path('', template_views.my_tenants, name='my-tenants'),
    path('create/', template_views.create_tenant, name='create-tenant'),
    path('<uuid:tenant_id>/created/', template_views.tenant_created, name='tenant-created'),
]
