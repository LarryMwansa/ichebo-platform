"""
URL conf for bible.ichebo.org — mounted via request.urlconf in SiteRouterMiddleware.
No app_name: request.urlconf bypasses include(), so namespaces are never registered.
Auth routes included so /accounts/login/ resolves under this urlconf.
"""
from django.urls import include, path
from accounts import views as accounts_views
from accounts.urls import template_urlpatterns as accounts_template_urlpatterns
from bible import views

urlpatterns = [
    # Auth
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', accounts_views.RegisterView.as_view(), name='register_ui'),
    path('accounts/', include((accounts_template_urlpatterns, 'accounts'))),

    # Bible surface
    path('', views.BibleReaderView.as_view(), name='reader'),
    path('<str:book_code>/<int:chapter>/', views.BibleReaderView.as_view(), name='reader-chapter'),
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
    path('htmx/search/sheet/', views.htmx_search_sheet, name='htmx-search-sheet'),
    path('htmx/appearance/', views.htmx_appearance_sheet, name='htmx-appearance'),
    path('htmx/set-translation/', views.htmx_set_translation, name='htmx-set-translation'),
    path('htmx/relationship/create/', views.htmx_relationship_create, name='htmx-relationship-create'),
    path('htmx/links/<uuid:verse_id>/', views.htmx_verse_links, name='htmx-verse-links'),
    path('htmx/record-search/', views.htmx_bible_record_search, name='htmx-bible-record-search'),
]
