from django.urls import path
from . import views

app_name = 'bible'

urlpatterns = [
    path('', views.BibleReaderView.as_view(), name='reader'),
    path('<str:book_code>/<int:chapter>/', views.BibleReaderView.as_view(), name='reader-chapter'),
    # New pages
    path('search/', views.bible_search_view, name='search'),
    path('pick/', views.bible_picker_view, name='picker'),
    path('versions/', views.bible_versions_view, name='versions'),
    path('languages/', views.bible_languages_view, name='languages'),
    # HTMX partials
    path('htmx/chapter/', views.htmx_chapter, name='htmx-chapter'),
    path('htmx/annotation/<uuid:verse_id>/', views.htmx_annotation_panel, name='htmx-annotation-panel'),
    path('htmx/note/save/', views.htmx_save_note, name='htmx-save-note'),
    path('htmx/note/<uuid:note_id>/delete/', views.htmx_delete_note, name='htmx-delete-note'),
    path('htmx/search/', views.htmx_search, name='htmx-search'),
    path('htmx/appearance/', views.htmx_appearance_sheet, name='htmx-appearance'),
]
