from django.urls import path
from . import api_views, views

app_name = 'bible'

# API routes
api_urlpatterns = [
    path('health/', api_views.health, name='api-health'),
    path('translations/', api_views.TranslationListView.as_view(), name='api-translations'),
    path('books/', api_views.BookListView.as_view(), name='api-books'),
    path('verses/', api_views.VerseListView.as_view(), name='api-verses'),
    path('verse-context/<uuid:pk>/', api_views.VerseContextView.as_view(), name='api-verse-context'),
]

# Template + HTMX routes
urlpatterns = api_urlpatterns + [
    path('', views.BibleReaderView.as_view(), name='reader'),
    path('<str:book_code>/<int:chapter>/', views.BibleReaderView.as_view(), name='reader-chapter'),
    # HTMX partials
    path('htmx/chapter/', views.htmx_chapter, name='htmx-chapter'),
    path('htmx/annotation/<uuid:verse_id>/', views.htmx_annotation_panel, name='htmx-annotation-panel'),
    path('htmx/note/save/', views.htmx_save_note, name='htmx-save-note'),
    path('htmx/note/<uuid:note_id>/delete/', views.htmx_delete_note, name='htmx-delete-note'),
    path('htmx/translation/set/', views.htmx_set_translation, name='htmx-set-translation'),
]
