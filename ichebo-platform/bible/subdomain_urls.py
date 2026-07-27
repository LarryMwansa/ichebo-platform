"""
URL conf for bible.ichebo.org — serves an open landing page at /.
Full Bible app lives at app.ichebo.org/bible (login required).
"""
from django.urls import include, path
from accounts import views as accounts_views
from accounts.urls import template_urlpatterns as accounts_template_urlpatterns
from bible import views as bible_views

urlpatterns = [
    # Community Scripture Reader (Open access / Standalone)
    path('', bible_views.community_bible_reader, name='home'),
    path('read/<str:book_code>/<int:chapter>/', bible_views.community_bible_reader, name='community_bible_reader'),
    path('htmx/chapter/<str:book_code>/<int:chapter>/', bible_views.htmx_community_chapter, name='htmx_community_chapter'),

    # Auth routes — available if the landing page links to login
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', accounts_views.RegisterView.as_view(), name='register_ui'),
    path('accounts/', include((accounts_template_urlpatterns, 'accounts'))),
]
