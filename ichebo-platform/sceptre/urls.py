"""
URL configuration for sceptre.ichebo.org.
All participant and steward URLs for the Sceptre Community surface.
Mounted at the domain root via request.urlconf, set by
middleware.site_router.SiteRouterMiddleware — not included from
ics_project/urls.py.

No app_name/namespace here, deliberately — request.urlconf makes this
module the *root* resolver for sceptre.ichebo.org requests, bypassing
include() entirely. app_name only creates a usable namespace when a
URLconf is included under one; declaring it here without an include()
left every {% url 'sceptre:...' %} call broken (confirmed directly:
NoReverseMatch: 'sceptre' is not a registered namespace, raised from a
real render() of participant_home). Templates use bare {% url 'home' %}
etc., not {% url 'sceptre:home' %}.
"""
from django.urls import include, path
from accounts import views as accounts_views
from accounts.urls import template_urlpatterns as accounts_template_urlpatterns
from sceptre import views

urlpatterns = [
    # Auth routes — request.urlconf makes this module the *root* resolver
    # for sceptre.ichebo.org, so @login_required's redirect to LOGIN_URL
    # (/accounts/login/) must resolve here too, not just under
    # ics_project.urls. Confirmed via a real browser session (not just
    # the test client, which bypasses this via force_login/c.login):
    # an unauthenticated visit to sceptre.ichebo.org redirected to
    # /accounts/login/ and got a 404, since this urlconf didn't include
    # django.contrib.auth.urls at all.
    #
    # The shared registration/login.html template also calls
    # {% url 'accounts:signup' %} unconditionally — mirrors
    # ics_project/urls.py's accounts: namespace registration exactly, or
    # that link 500s with NoReverseMatch on this surface specifically.
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', accounts_views.RegisterView.as_view(), name='register_ui'),
    path('accounts/', include((accounts_template_urlpatterns, 'accounts'))),

    # Participant routes
    path('', views.participant_home, name='home'),
    path('now-playing/', views.now_playing_partial, name='now_playing_partial'),
    path('community/', views.community_area, name='community'),
    path('learn/', views.learn_summary, name='learn'),
    path('bible/', views.bible_redirect, name='bible'),
    path('support/', views.support_redirect, name='support'),
    path('profile/', views.profile_summary, name='profile'),

    # Steward routes (gated at view level)
    path('steward/members/', views.steward_members, name='steward_members'),
    path('steward/gatherings/', views.steward_gatherings, name='steward_gatherings'),
    path('steward/formation/', views.steward_formation, name='steward_formation'),
    path('steward/announcements/', views.steward_announcements, name='steward_announcements'),
    path('steward/support/', views.steward_support_redirect, name='steward_support'),
    path('steward/settings/', views.steward_settings, name='steward_settings'),
]
