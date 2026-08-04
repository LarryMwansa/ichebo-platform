"""
URL configuration for join.ichebo.org.
Full onboarding surface — registration, profile setup, induction enrolment.
Mounted at the domain root via request.urlconf set by SiteRouterMiddleware.

No app_name/namespace — same pattern as sceptre/urls.py and handbook/subdomain_urls.py.
The accounts app's template_urlpatterns are included with the 'accounts' namespace
so that {% url 'accounts:signup' %}, {% url 'accounts:profile-setup' %} etc. resolve.
"""
from django.urls import include, path
from django.views.generic import RedirectView

from accounts import views as accounts_views
from accounts.urls import template_urlpatterns as accounts_template_urlpatterns

from join import views

urlpatterns = [
    # Auth routes — @login_required redirects to LOGIN_URL (/accounts/login/)
    # which must resolve within this urlconf.
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include((accounts_template_urlpatterns, 'accounts'))),

    # Onboarding flow — the reason this subdomain exists
    path('accounts/register/', accounts_views.RegisterView.as_view(), name='register_ui'),
    path('accounts/signup/', accounts_views.SignUpView.as_view(), name='signup_ui'),
    path('accounts/verify-email/<str:token>/', accounts_views.VerifyEmailView.as_view(), name='verify_email_ui'),

    # Landing page
    path('', views.landing, name='join_landing'),
]
