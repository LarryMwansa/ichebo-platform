from django.urls import path
from . import api_views

app_name = 'learn-api'

urlpatterns = [
    path('health/', api_views.health, name='health'),

    # Programme catalogue
    path('programmes/', api_views.programme_list, name='programme-list'),
    path('programmes/<uuid:programme_id>/', api_views.programme_detail, name='programme-detail'),
    path('programmes/<uuid:programme_id>/curriculum/', api_views.programme_curriculum, name='programme-curriculum'),
    path('programmes/<uuid:programme_id>/enrol/', api_views.enrol, name='enrol'),
    path('programmes/<uuid:programme_id>/tasks/', api_views.my_lesson_tasks, name='my-lesson-tasks'),

    # My enrolments
    path('enrolments/', api_views.my_enrolments, name='my-enrolments'),

    # Lesson completion
    path('tasks/<uuid:lesson_activity_id>/complete/', api_views.complete_lesson_view, name='complete-lesson'),

    # Certification (steward)
    path('certifications/queue/', api_views.certification_queue, name='certification-queue'),
    path('certifications/<uuid:certification_id>/confirm/', api_views.confirm_certification, name='certification-confirm'),
]
