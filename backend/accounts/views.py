import json

from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.edit import FormView
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from tenants.models import UserPermission
from .forms import RegisterForm
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer

# ---------------------------------------------------------------------------
# API views
# ---------------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    request.user.auth_token.delete()
    return Response({'detail': 'Logged out'})


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def me(request):
    if request.method == 'GET':
        return Response(UserSerializer(request.user).data)
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_fcm_token(request):
    """
    POST: Save or update the FCM token for the authenticated user.
    Body: {"fcm_token": "..."}
    """
    token = request.data.get('fcm_token')
    if not token:
        return Response({"error": "fcm_token is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    user.fcm_token = token
    user.save(update_fields=['fcm_token', 'updated_at'])
    
    return Response({"status": "success", "message": "FCM token updated"})


# ---------------------------------------------------------------------------
# Auth form views
# ---------------------------------------------------------------------------

class RegisterView(FormView):
    template_name = 'registration/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('community:my-community')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.username = form.cleaned_data['email']
        user.set_password(form.cleaned_data['password'])
        user.save()
        auth_login(self.request, user)
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Task 5.6 — Profile view
# ---------------------------------------------------------------------------

COMPETENCE_LABELS = {
    0: ('Seeker',          'Level 0 — Connection'),
    1: ('Beginner',        'Level 1 — Formation'),
    2: ('Disciple',        'Level 2 — Alignment'),
    3: ('Steward',         'Level 3 — Service'),
    4: ('Senior Steward',  'Level 4 — Leadership'),
    5: ('Architect',       'Level 5 — Apostolic Stewardship'),
}


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        level = user.competence_level
        kgs_name, platform_label = COMPETENCE_LABELS.get(level, ('Unknown', f'Level {level}'))
        memberships = UserPermission.objects.filter(
            user=user, is_active=True
        ).select_related('tenant')
        context = {
            'profile_user': user,
            'kgs_name': kgs_name,
            'platform_label': platform_label,
            'memberships': memberships,
        }
        return render(request, 'accounts/profile.html', context)


# ---------------------------------------------------------------------------
# Task 5.6 — Settings view
# ---------------------------------------------------------------------------

TIMEZONE_CHOICES = [
    'Africa/Johannesburg', 'Africa/Nairobi', 'Africa/Lagos', 'Africa/Accra',
    'Africa/Cairo', 'Europe/London', 'Europe/Paris', 'Europe/Berlin',
    'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles',
    'America/Sao_Paulo', 'Asia/Dubai', 'Asia/Kolkata', 'Asia/Singapore',
    'Asia/Tokyo', 'Australia/Sydney', 'Pacific/Auckland', 'UTC',
]


class SettingsView(LoginRequiredMixin, View):
    def get(self, request):
        context = {
            'profile_user': request.user,
            'timezone_choices': TIMEZONE_CHOICES,
        }
        return render(request, 'accounts/settings.html', context)


# ---------------------------------------------------------------------------
# Task 5.6 — HTMX handlers
# ---------------------------------------------------------------------------

@login_required
def htmx_display_name_edit(request):
    """
    GET  → return inline edit form (pencil click)
    POST → save display_name and return read-state partial
    """
    if request.method == 'GET':
        # Cancel button also hits GET — if ?show=1 return the read view
        if request.GET.get('show'):
            return render(request, 'accounts/_display_name_show.html', {
                'profile_user': request.user,
            })
        return render(request, 'accounts/_display_name_edit.html', {
            'profile_user': request.user,
        })
    if request.method != 'POST':
        return HttpResponse(status=405)
    display_name = request.POST.get('display_name', '').strip()
    if display_name:
        request.user.display_name = display_name
        request.user.save(update_fields=['display_name'])
    return render(request, 'accounts/_display_name_show.html', {
        'profile_user': request.user,
    })


@login_required
def htmx_settings_theme(request):
    """PATCH: save theme preference and return save-confirm partial."""
    theme = request.POST.get('theme', 'system')
    if theme not in ('system', 'light', 'dark'):
        theme = 'system'
    prefs = request.user.preferences or {}
    prefs['theme'] = theme
    request.user.preferences = prefs
    request.user.save(update_fields=['preferences'])
    return render(request, 'accounts/_save_confirm.html', {'message': 'Theme saved'})


@login_required
def htmx_settings_region(request):
    """PATCH: save language + timezone and return save-confirm partial."""
    language = request.POST.get('language', 'en')
    timezone = request.POST.get('timezone', 'UTC')
    if timezone not in TIMEZONE_CHOICES:
        timezone = 'UTC'
    prefs = request.user.preferences or {}
    prefs['language'] = language
    prefs['timezone'] = timezone
    request.user.preferences = prefs
    request.user.save(update_fields=['preferences'])
    return render(request, 'accounts/_save_confirm.html', {'message': 'Region settings saved'})
