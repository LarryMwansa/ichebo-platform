"""
URL conf for learn.ichebo.org — mounted via request.urlconf in SiteRouterMiddleware.
Includes learn.urls (which sets app_name = 'learn') so the 'learn' namespace is
registered and all {% url 'learn:...' %} template calls resolve correctly.
Auth routes added so /accounts/login/ resolves under this urlconf.
"""
from django.urls import include, path
from accounts import views as accounts_views
from accounts.urls import template_urlpatterns as accounts_template_urlpatterns

urlpatterns = [
    # Auth — must come first so login_required redirects resolve
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', accounts_views.RegisterView.as_view(), name='register_ui'),
    path('accounts/', include((accounts_template_urlpatterns, 'accounts'))),

    # Learn surface — include with namespace so 'learn:*' url tags work in templates
    path('', include('learn.urls', namespace='learn')),
]
