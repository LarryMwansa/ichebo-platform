"""
URL conf for learn.ichebo.org — mounted via request.urlconf in SiteRouterMiddleware.
Includes learn.urls (which sets app_name = 'learn') so the 'learn' namespace is
registered and all {% url 'learn:...' %} template calls resolve correctly.
Auth routes added so /accounts/login/ resolves under this urlconf.
"""
from django.urls import include, path
from accounts import views as accounts_views
from accounts.urls import template_urlpatterns as accounts_template_urlpatterns
from learn import views as learn_views

urlpatterns = [
    # Open landing — no auth required
    path('', learn_views.landing, name='learn-landing'),

    # Auth routes — needed so the login page resolves if anything on the landing links to it
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', accounts_views.RegisterView.as_view(), name='register_ui'),
    path('accounts/', include((accounts_template_urlpatterns, 'accounts'))),
]
