from django.urls import path
from . import api_views

app_name = 'learn-api'

urlpatterns = [
    path('health/', api_views.health, name='health'),
    path('programmes/<uuid:programme_id>/curriculum/',
         api_views.programme_curriculum, name='programme-curriculum'),
    path('certifications/queue/',
         api_views.certification_queue, name='certification-queue'),
    path('certifications/<uuid:certification_id>/confirm/',
         api_views.confirm_certification, name='certification-confirm'),
]
