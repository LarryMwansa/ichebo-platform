from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(email='user@example.com', password='testpass123', level=0):
    return User.objects.create_user(
        username=email, email=email, password=password,
        competence_level=level,
    )


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class UserModelTests(TestCase):
    def test_defaults_on_creation(self):
        user = _make_user()
        self.assertEqual(user.competence_level, 0)
        self.assertEqual(user.status, 'seeker')
        self.assertEqual(user.display_name, '')
        self.assertEqual(user.preferences, {})

    def test_str_returns_email(self):
        user = _make_user(email='str@example.com')
        self.assertEqual(str(user), 'str@example.com')

    def test_uuid_primary_key(self):
        user = _make_user(email='uuid@example.com')
        self.assertIsNotNone(user.id)
        self.assertEqual(len(str(user.id)), 36)

    def test_competence_level_can_be_set(self):
        user = _make_user(email='l3@example.com', level=3)
        self.assertEqual(user.competence_level, 3)


# ---------------------------------------------------------------------------
# Register API
# ---------------------------------------------------------------------------

class RegisterAPITests(APITestCase):
    url = '/api/auth/register/'

    def test_register_success_returns_token_and_user(self):
        response = self.client.post(self.url, {'email': 'new@example.com', 'password': 'securepass'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['email'], 'new@example.com')
        self.assertEqual(response.data['user']['competence_level'], 0)

    def test_register_sets_seeker_status(self):
        self.client.post(self.url, {'email': 'seeker@example.com', 'password': 'securepass'})
        user = User.objects.get(email='seeker@example.com')
        self.assertEqual(user.status, 'seeker')
        self.assertEqual(user.competence_level, 0)

    def test_register_password_too_short_fails(self):
        response = self.client.post(self.url, {'email': 'x@example.com', 'password': 'short'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email_fails(self):
        _make_user(email='dup@example.com')
        response = self.client.post(self.url, {'email': 'dup@example.com', 'password': 'securepass'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_email_fails(self):
        response = self.client.post(self.url, {'password': 'securepass'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Login API
# ---------------------------------------------------------------------------

class LoginAPITests(APITestCase):
    url = '/api/auth/login/'

    def setUp(self):
        self.user = _make_user(email='login@example.com', password='correctpass')

    def test_login_success_returns_token(self):
        response = self.client.post(self.url, {'email': 'login@example.com', 'password': 'correctpass'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['email'], 'login@example.com')

    def test_login_wrong_password_fails(self):
        response = self.client.post(self.url, {'email': 'login@example.com', 'password': 'wrongpass'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_user_fails(self):
        response = self.client.post(self.url, {'email': 'ghost@example.com', 'password': 'anypass'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_suspended_user_fails(self):
        self.user.status = 'suspended'
        self.user.save(update_fields=['status'])
        response = self.client.post(self.url, {'email': 'login@example.com', 'password': 'correctpass'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Me API
# ---------------------------------------------------------------------------

class MeAPITests(APITestCase):
    url = '/api/auth/me/'

    def setUp(self):
        self.user = _make_user(email='me@example.com')
        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_me_returns_authenticated_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'me@example.com')
        self.assertEqual(response.data['competence_level'], 0)

    def test_me_unauthenticated_returns_401(self):
        self.client.credentials()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_patch_updates_display_name(self):
        response = self.client.patch(self.url, {'display_name': 'John Doe'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, 'John Doe')

    def test_me_patch_cannot_elevate_competence_level(self):
        self.client.patch(self.url, {'competence_level': 5})
        self.user.refresh_from_db()
        # competence_level is read_only in UserSerializer
        self.assertEqual(self.user.competence_level, 0)


# ---------------------------------------------------------------------------
# Logout API
# ---------------------------------------------------------------------------

class LogoutAPITests(APITestCase):
    url = '/api/auth/logout/'

    def setUp(self):
        self.user = _make_user(email='logout@example.com')
        self.token, _ = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_logout_deletes_token(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_logout_unauthenticated_returns_401(self):
        self.client.credentials()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
