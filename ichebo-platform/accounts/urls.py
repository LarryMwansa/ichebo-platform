from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from . import views

urlpatterns = [
    # API routes
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/logout/', views.logout, name='logout'),
    path('auth/me/', views.me, name='me'),
    path('auth/fcm-token/', views.update_fcm_token, name='update-fcm-token'),
]

# Template + HTMX routes (mounted at accounts/ in root urls.py)
template_urlpatterns = [
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    # HTMX partials
    path('htmx/profile/display-name/', views.htmx_display_name_edit, name='htmx-display-name'),
    path('htmx/settings/theme/', views.htmx_settings_theme, name='htmx-theme'),
    path('htmx/settings/region/', views.htmx_settings_region, name='htmx-region'),
    # G2 — Registration flow
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('verify-email/<str:token>/', views.VerifyEmailView.as_view(), name='verify-email'),
    path('profile-setup/', views.ProfileSetupView.as_view(), name='profile-setup'),
    path('welcome/', views.WelcomeView.as_view(), name='welcome'),
    # H1 — Formation
    path('formation/', views.FormationHistoryView.as_view(), name='formation-history'),
    path('htmx/formation-card/', views.htmx_formation_card, name='htmx-formation-card'),
    # You hub (migrated from app.ichebo.org/you/)
    path('you/', views.YouView.as_view(), name='you'),
    # Manage Account
    path('manage/', views.ManageAccountView.as_view(), name='manage-account'),
    path('manage/password/', views.PasswordChangeView.as_view(), name='password-change'),
    path('htmx/manage/reveal-id/', views.htmx_reveal_id_number, name='htmx-reveal-id'),
    path('htmx/manage/mask-id/', views.htmx_mask_id_number, name='htmx-mask-id'),
    path('htmx/avatar/', views.htmx_avatar_upload, name='htmx-avatar'),
]
