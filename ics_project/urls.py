"""
URL configuration for ics_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from accounts import views as accounts_views
from accounts.urls import template_urlpatterns as accounts_template_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/', include('accounts.urls')),
    path('api/', include('tenants.urls')),
    path('api/', include('records.urls')),
    path('api/', include('activity.urls')),
    path('api/bible/', include('bible.api_urls')),
    path('bible/', include('bible.urls', namespace='bible')),
    path('api/learn/', include('learn.api_urls')),
    path('learn/', include('learn.urls', namespace='learn')),
    path('', include('community.urls', namespace='community')),
    path('', include('governance.urls', namespace='governance')),
    path('api/calendar/', include('calendar_app.urls', namespace='calendar-api')),
    path('calendar/', include('calendar_app.template_urls', namespace='calendar')),
    path('api/', include('notifications.urls', namespace='notifications-api')),
    path('api/paraclete/', include('paraclete.urls', namespace='paraclete-api')),
    path('notifications/', include('notifications.template_urls', namespace='notifications')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', accounts_views.RegisterView.as_view(), name='register_ui'),
    path('accounts/', include(accounts_template_urlpatterns)),
    path('', include('dashboard.urls', namespace='dashboard')),
]
