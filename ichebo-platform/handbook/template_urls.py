from django.urls import path
from . import views

app_name = 'handbook'

urlpatterns = [
    path('', views.handbook_home, name='home'),
    path('records/new/', views.handbook_new, name='new'),
    path('records/<uuid:pk>/', views.handbook_record, name='record'),
    path('access/', views.handbook_access, name='access'),
]
