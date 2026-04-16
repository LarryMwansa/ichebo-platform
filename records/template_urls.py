from django.urls import path
from . import template_views

app_name = 'records'

urlpatterns = [
    path('', template_views.my_records, name='records-home'),
    path('<uuid:record_id>/', template_views.record_detail, name='records-detail'),
    path('htmx/create/', template_views.htmx_create_record, name='htmx-create'),
    path('htmx/<uuid:record_id>/edit/', template_views.htmx_edit_record, name='htmx-edit'),
    path('htmx/<uuid:record_id>/delete/', template_views.htmx_delete_record, name='htmx-delete'),
]
