"""
URL configuration for handbook.ichebo.org.
Reader + editor surface for the Ichebo Handbook, on apostolic_chrome.html.
Mounted at the domain root via request.urlconf set by SiteRouterMiddleware.

No app_name/namespace here at the top level — same pattern as
sceptre/urls.py. The handbook app's own template_urls.py uses
app_name='handbook', so all {% url 'handbook:...' %} calls inside views
work because template_urls.py is included below with its namespace intact.
Same for bible.urls (app_name='bible').

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

    # Bible reader — moved here from app.ichebo.org/bible/ (which now
    # redirects here); self-contained under the bible: namespace, no
    # dependency on any other namespace, so it works unmodified.
    path('bible/', include('bible.urls', namespace='bible')),

    # Root redirect → handbook home
    path('', RedirectView.as_view(url='/handbook/', permanent=False)),
]
