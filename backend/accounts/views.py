import json

from django.contrib.auth import login as auth_login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.conf import settings as django_settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views import View
from django.views.generic.edit import FormView
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from tenants.models import UserPermission, Tenant
from .forms import RegisterForm, SignUpForm, ProfileSetupForm
from .models import UserProfile, EmailVerificationToken
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer

User = get_user_model()

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
    success_url = reverse_lazy('community:community-home')

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


# ---------------------------------------------------------------------------
# G2 — Sign-up & Profile Registration
# ---------------------------------------------------------------------------

def _send_verification_email(user, token_obj, request):
    verify_url = request.build_absolute_uri(
        reverse('accounts:verify-email', kwargs={'token': token_obj.token})
    )
    send_mail(
        subject='Verify your Ichebo account',
        message=(
            f'Welcome to Ichebo.\n\n'
            f'Please verify your email address by clicking the link below:\n\n'
            f'{verify_url}\n\n'
            f'This link expires in 24 hours.\n\n'
            f'If you did not create this account, you can ignore this email.'
        ),
        from_email=django_settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


class SignUpView(View):
    """Step 1 — email + password. Sends verification email."""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        return render(request, 'accounts/signup.html', {'form': SignUpForm()})

    def post(self, request):
        form = SignUpForm(request.POST)
        if not form.is_valid():
            return render(request, 'accounts/signup.html', {'form': form})

        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            status='pending_verification',
        )

        token_obj = EmailVerificationToken.create_for_user(user)
        try:
            _send_verification_email(user, token_obj, request)
        except Exception:
            pass  # Don't block registration if email fails in dev

        return render(request, 'accounts/signup_pending.html', {'email': email})


class VerifyEmailView(View):
    """Validates the token from the verification email."""

    def get(self, request, token):
        token_obj = EmailVerificationToken.objects.select_related('user').filter(token=token).first()

        if not token_obj or not token_obj.is_valid:
            return render(request, 'accounts/verify_failed.html')

        user = token_obj.user
        token_obj.consume()

        user.status = 'seeker'
        user.save(update_fields=['status'])

        auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('accounts:profile-setup')


class ProfileSetupView(LoginRequiredMixin, View):
    """Step 2 — collect full profile and place user in Induction Tenant."""

    login_url = '/accounts/login/'

    def _ctx(self, form):
        return {
            'form': form,
            'require_uploads': getattr(django_settings, 'REQUIRE_REFEREE_UPLOADS', False),
        }

    def get(self, request):
        if hasattr(request.user, 'profile') and request.user.profile.terms_accepted:
            return redirect('accounts:welcome')
        return render(request, 'accounts/profile_setup.html', self._ctx(ProfileSetupForm()))

    def post(self, request):
        form = ProfileSetupForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, 'accounts/profile_setup.html', self._ctx(form))

        cd = form.cleaned_data
        user = request.user

        # Save profile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.title = cd.get('title', '')
        profile.full_name = cd['full_name']
        profile.phone_number = cd.get('phone_number', '')
        profile.address = cd.get('address', '')
        profile.country = cd['country']
        profile.id_number = cd.get('id_number') or None
        profile.date_of_birth = cd.get('date_of_birth')
        profile.gender = cd.get('gender', '')
        profile.marital_status = cd.get('marital_status', '')
        profile.occupation = cd.get('occupation', '')
        profile.education = cd.get('education', '')
        profile.interests = cd.get('interests', '')
        profile.gifts_skills = cd.get('gifts_skills', '')
        profile.accepted_christ = cd.get('accepted_christ')
        profile.church_member = cd.get('church_member')
        profile.church_name = cd.get('church_name', '')
        profile.referee_1_name = cd.get('referee_1_name', '')
        profile.referee_2_name = cd.get('referee_2_name', '')
        if request.FILES.get('referee_letter_1'):
            profile.referee_letter_1 = request.FILES['referee_letter_1']
        if request.FILES.get('referee_letter_2'):
            profile.referee_letter_2 = request.FILES['referee_letter_2']
        profile.terms_accepted = True
        profile.terms_accepted_at = timezone.now()
        profile.save()

        # Assign KMN
        profile.assign_member_number()

        # Set display_name from full_name if not already set
        if not user.display_name:
            user.display_name = cd['full_name']

        # Set induction_pathway from form
        pathway = cd['induction_pathway']
        user.induction_pathway = pathway

        # Place user in Induction Tenant
        induction_tenant = Tenant.objects.filter(slug='induction').first()
        if induction_tenant:
            UserPermission.objects.get_or_create(
                user=user,
                tenant=induction_tenant,
                defaults={
                    'tenant_path': '/global/induction/',
                    'role': 'seeker',
                    'level': 0,
                    'is_active': True,
                    'granted_at': timezone.now(),
                    'granted_by': user,
                    'created_by': user,
                }
            )
            user.induction_enrolled_at = timezone.now()

        user.save(update_fields=['display_name', 'induction_pathway', 'induction_enrolled_at'])

        return redirect('accounts:welcome')


class WelcomeView(LoginRequiredMixin, View):
    """Post-registration welcome and orientation screen."""

    login_url = '/accounts/login/'

    def get(self, request):
        user = request.user
        profile = getattr(user, 'profile', None)
        return render(request, 'accounts/welcome.html', {
            'profile': profile,
            'member_number': profile.member_number if profile else None,
        })
