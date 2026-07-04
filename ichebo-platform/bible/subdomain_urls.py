"""
URL conf for bible.ichebo.org — serves an open landing page at /.
Full Bible app lives at app.ichebo.org/bible (login required).
"""
from django.urls import include, path
from accounts import views as accounts_views
from accounts.urls import template_urlpatterns as accounts_template_urlpatterns
from bible import views as bible_views

urlpatterns = [
    # Open landing — no auth required
    path('', bible_views.landing, name='bible-landing'),

    # Auth routes — available if the landing page links to login
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', accounts_views.RegisterView.as_view(), name='register_ui'),
    path('accounts/', include((accounts_template_urlpatterns, 'accounts'))),
]
