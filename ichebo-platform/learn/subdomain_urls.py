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
    # Open landing & course catalog — no auth required
    path('', learn_views.community_learn_catalog, name='learn-landing'),
    path('catalog/', learn_views.community_learn_catalog, name='community_learn_catalog'),
    path('my-learning/', learn_views.community_my_learning, name='community_my_learning'),
    path('programme/<uuid:programme_id>/', learn_views.community_programme_detail, name='community_programme_detail'),
    path('lesson/<uuid:lesson_id>/', learn_views.community_lesson_viewer, name='community_lesson_viewer'),
    path('enrol/<uuid:programme_id>/', learn_views.community_enrol, name='community_enrol'),

    # Auth routes — needed so login/register resolve under learn.ichebo.org
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', accounts_views.RegisterView.as_view(), name='register_ui'),
    path('accounts/', include((accounts_template_urlpatterns, 'accounts'))),
]
