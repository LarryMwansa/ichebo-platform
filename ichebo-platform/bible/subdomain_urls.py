"""
URL conf for bible.ichebo.org — mounted via request.urlconf in SiteRouterMiddleware.
Includes bible.urls (which sets app_name = 'bible') so the 'bible' namespace is
registered and all {% url 'bible:...' %} template calls resolve correctly.
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

    # Bible surface — include with namespace so 'bible:*' url tags work in templates
    path('', include('bible.urls', namespace='bible')),
]
