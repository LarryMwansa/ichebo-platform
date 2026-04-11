from django.urls import path
from . import api_views, views

app_name = 'learn'

urlpatterns = [
    # (API routes moved to api_urls.py)

    # ── Django template views ──────────────────────────────────────────────
    path('', views.my_learning, name='learn-home'),
    path('programmes/', views.catalogue, name='learn-catalogue'),
    path('programmes/<uuid:programme_id>/', views.programme_detail, name='learn-programme'),
    path('lessons/<uuid:lesson_id>/', views.lesson_viewer, name='learn-lesson'),
    path('certifications/', views.certification_queue_view, name='learn-cert-queue'),

    # Authorship (Level 4+)
    path('author/', views.authorship, name='learn-author'),
    path('author/programme/', views.author_programme_form, name='learn-author-programme'),
    path('author/course/', views.author_course_form, name='learn-author-course'),
    path('author/lesson/', views.author_lesson_form, name='learn-author-lesson'),

    # Review queue (Level 5)
    path('review/', views.review_queue, name='learn-review'),

    # ── HTMX partial routes ────────────────────────────────────────────────
    path('htmx/enrol/<uuid:programme_id>/', views.htmx_enrol, name='htmx-enrol'),
    path('htmx/complete-lesson/<uuid:lesson_id>/',
         views.htmx_complete_lesson, name='htmx-complete-lesson'),
    path('htmx/confirm-cert/<uuid:cert_id>/',
         views.htmx_confirm_cert, name='htmx-confirm-cert'),
    path('htmx/approve-content/<uuid:record_id>/',
         views.htmx_approve_content, name='htmx-approve-content'),
    path('htmx/return-content/<uuid:record_id>/',
         views.htmx_return_content, name='htmx-return-content'),
]
