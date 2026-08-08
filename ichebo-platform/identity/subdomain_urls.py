"""
URL configuration for identity.ichebo.org.
Centralised login, profile, and settings surface for the *.ichebo.org network.
Mounted at the domain root via request.urlconf set by SiteRouterMiddleware.

No app_name/namespace — same pattern as sceptre/urls.py.
accounts_template_urlpatterns are included with the 'accounts' namespace so that
{% url 'accounts:profile' %}, {% url 'accounts:settings' %} etc. resolve here.

The shared session cookie (SESSION_COOKIE_DOMAIN = '.ichebo.org') means a login
issued here is valid on every *.ichebo.org subdomain. LOGIN_URL in settings points
here, so @login_required on any subdomain redirects to this surface.
"""
from django.urls import include, path
from django.views.generic import RedirectView

from accounts.urls import template_urlpatterns as accounts_template_urlpatterns

urlpatterns = [
    # Full Django auth (login, logout, password reset, etc.)
    path('accounts/', include('django.contrib.auth.urls')),

    # Profile, settings, formation history, and all HTMX partials
    path('accounts/', include((accounts_template_urlpatterns, 'accounts'))),

    # Root → login page
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False)),
]
