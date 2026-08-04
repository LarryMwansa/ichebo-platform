"""
URL configuration for handbook.ichebo.org.
Public reader surface for the Ichebo Handbook — no sidebar, no workspace chrome.
Mounted at the domain root via request.urlconf set by SiteRouterMiddleware.

No app_name/namespace here — same pattern as sceptre/urls.py.
The handbook app's own template_urls.py uses app_name='handbook', so all
{% url 'handbook:...' %} calls inside views work because template_urls.py
is included below with its namespace intact.

Handbook routes are mounted at /handbook/ (not /) to preserve every
hardcoded /handbook/records/{pk}/ URL inside HTMX inline HTML responses.
The domain root redirects to /handbook/ automatically.
"""
from django.urls import include, path
from django.views.generic import RedirectView

from accounts import views as accounts_views
from accounts.urls import template_urlpatterns as accounts_template_urlpatterns

urlpatterns = [
    # Auth routes — @login_required on write views redirects to /accounts/login/,
    # which must resolve within this urlconf (same reasoning as sceptre/urls.py).
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', accounts_views.RegisterView.as_view(), name='register_ui'),
    path('accounts/', include((accounts_template_urlpatterns, 'accounts'))),

    # Handbook surface — mounted at /handbook/ to preserve all hardcoded paths
    path('handbook/', include('handbook.template_urls', namespace='handbook')),
    path('api/handbook/', include('handbook.api_urls')),

    # Root redirect → handbook home
    path('', RedirectView.as_view(url='/handbook/', permanent=False)),
]
