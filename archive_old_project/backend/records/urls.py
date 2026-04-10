from django.urls import path
from . import views

urlpatterns = [
    # Records CRUD
    path('records/', views.record_list_create, name='record-list-create'),
    path('records/<uuid:pk>/', views.record_detail, name='record-detail'),
    path('records/<uuid:pk>/relationships/', views.record_relationships, name='record-relationships'),

    # Relationships CRUD
    path('relationships/', views.relationship_create, name='relationship-create'),
    path('relationships/<uuid:pk>/', views.relationship_delete, name='relationship-delete'),
]
