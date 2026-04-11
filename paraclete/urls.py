from django.urls import path
from . import views

app_name = 'paraclete-api'

urlpatterns = [
    path('digest/', views.DigestView.as_view(), name='paraclete-digest'),
    path('reminders/', views.RemindersView.as_view(), name='paraclete-reminders'),
    path('suggest/<uuid:record_id>/', views.SuggestView.as_view(), name='paraclete-suggest'),
    path('prompt/', views.PromptView.as_view(), name='paraclete-prompt'),
    path('respond/', views.RespondView.as_view(), name='paraclete-respond'),
    path('health/', views.health, name='paraclete-health'),
]
