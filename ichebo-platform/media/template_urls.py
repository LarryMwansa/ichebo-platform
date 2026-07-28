from django.urls import path
from . import template_views

app_name = 'media'

urlpatterns = [
    path('htmx/picker-grid/', template_views.htmx_picker_grid, name='htmx_picker_grid'),
]
