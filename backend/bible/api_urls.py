from django.urls import path
from . import api_views

app_name = 'bible-api'

urlpatterns = [
    path('health/',                    api_views.health,                        name='health'),
    path('translations/',              api_views.TranslationListView.as_view(), name='translations'),
    path('books/',                     api_views.BookListView.as_view(),         name='books'),
    path('chapters/',                  api_views.chapter_list,                  name='chapters'),
    path('verses/',                    api_views.VerseListView.as_view(),        name='verses'),
    path('search/',                    api_views.search_verses,                 name='search'),
    path('verse-context/<uuid:pk>/',   api_views.VerseContextView.as_view(),    name='verse-context'),
]
