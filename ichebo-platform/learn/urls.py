from django.urls import path
from . import api_views, views

app_name = 'learn'

urlpatterns = [
    # (API routes moved to api_urls.py)

    # ── Django template views ──────────────────────────────────────────────
    path('', views.my_learning, name='learn-home'),
    path('catalogue/', views.catalogue, name='learn-catalogue'),
    path('programme/<uuid:programme_id>/', views.programme_detail, name='learn-programme'),
    path('course/<uuid:course_id>/', views.course_detail, name='learn-course'),
    path('lesson/<uuid:lesson_id>/', views.lesson_viewer, name='learn-lesson'),
    path('certifications/', views.certification_queue_view, name='learn-cert-queue'),

    # Authorship (Level 4+)
    path('author/', views.authorship, name='learn-author'),
    path('author/programme/', views.author_programme_form, name='learn-author-programme'),
    path('author/programme/<uuid:record_id>/', views.author_programme_form, name='learn-author-programme-edit'),
    path('author/course/', views.author_course_form, name='learn-author-course'),
    path('author/course/<uuid:record_id>/', views.author_course_form, name='learn-author-course-edit'),
    path('author/lesson/', views.author_lesson_form, name='learn-author-lesson'),
    path('author/lesson/<uuid:record_id>/', views.author_lesson_form, name='learn-author-lesson-edit'),
    path('author/<uuid:record_id>/delete/', views.htmx_author_delete, name='htmx-author-delete'),

    # Review queue (Level 5)
    path('review/', views.review_queue, name='learn-review'),
    # Induction review queue (Level 5)
    path('induction/review/', views.induction_review_queue, name='learn-induction-review'),
    path('htmx/induction/confirm-prompt/<uuid:user_id>/', views.htmx_induction_confirm_prompt, name='htmx-induction-confirm-prompt'),
    path('htmx/induction/confirm/<uuid:user_id>/', views.htmx_induction_confirm, name='htmx-induction-confirm'),

    # ── HTMX action routes ─────────────────────────────────────────────────
    path('htmx/enrol/<uuid:programme_id>/', views.htmx_enrol, name='htmx-enrol'),
    path('htmx/complete-lesson/<uuid:lesson_id>/',
         views.htmx_complete_lesson, name='htmx-complete-lesson'),
    path('htmx/submit-assessment/<uuid:lesson_id>/',
         views.htmx_submit_assessment, name='htmx-submit-assessment'),
    path('htmx/confirm-cert/<uuid:cert_id>/',
         views.htmx_confirm_cert, name='htmx-confirm-cert'),
    path('htmx/approve-content/<uuid:record_id>/',
         views.htmx_approve_content, name='htmx-approve-content'),
    path('htmx/return-content/<uuid:record_id>/',
         views.htmx_return_content, name='htmx-return-content'),

    # ── HTMX data partial routes ───────────────────────────────────────────
    path('htmx/my-learning/', views.htmx_my_learning, name='htmx-my-learning'),
    path('htmx/catalogue/', views.htmx_catalogue, name='htmx-catalogue'),
    path('htmx/progress/<uuid:programme_id>/', views.htmx_progress, name='htmx-progress'),
    path('htmx/cert-queue/', views.htmx_cert_queue, name='htmx-cert-queue'),
    path('htmx/linked-records/<uuid:record_id>/', views.htmx_linked_records, name='htmx-linked-records'),
]
