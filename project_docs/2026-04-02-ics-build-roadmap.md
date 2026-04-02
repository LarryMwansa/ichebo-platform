# ICS Platform — Full Build Roadmap

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the ICS platform (digital twin of the Kingdom Governance System) from a fresh Django project on a VPS to a fully operational multi-tenant platform with vanilla JS frontend.

**Architecture:** Django + DRF backend (single source of truth) + vanilla JS frontend (mobile-first UI layer making fetch calls to DRF endpoints). No localStorage as primary storage — localStorage is UI state only (theme, session token). All data lives in PostgreSQL via Django. Frontend engine services (`records.service.js` etc.) call DRF endpoints, not localStorage. The data contract document (`2026-03-30-ics-platform-data-contract.md`) is the canonical schema reference throughout.

**Tech Stack:** Python 3.11+, Django 4.2 LTS, Django REST Framework, PostgreSQL, Nginx, Gunicorn, HTML/CSS/Vanilla JS (IIFE modules), VPS (Ubuntu).

---

## Current State Audit

### What exists and is COMPLETE (keep, wire to Django)
- Navigation system: navbar, app drawer, bottom nav, overlay, theme system
- Mobile-first shell: index.html, responsive layout, CSS variables
- `storage.js` — localStorage abstraction (repurpose for UI state only)
- `router.js` — auth guards and navigation (update fetch targets)
- `auth.js` — register/login/logout flows (point to DRF auth endpoints)
- `main.js` — boot and component loader
- Records app UI — forms, list views, detail views (wire to DRF)

### What exists and needs REFACTORING
- `auth.js` — currently reads/writes localStorage users; must call DRF
- `router.js` — auth guard reads localStorage session; must read JWT token
- `storage.js` — remove data persistence role; keep only UI state helpers
- Records app JS — direct localStorage calls must become service calls

### What does NOT exist yet (build in order)
- Django project, apps, models, serializers, views, URLs
- All engine service JS files (`records.service.js`, `activity.service.js` etc.)
- All remaining app JS files (activity, learn, community, governance, dashboard)

---

## Dependency Rules (Non-Negotiable)

These rules govern build order. Violating them causes rework.

```
Django auth → Django tenant → Django records → Django activity
Django models → DRF serializers → DRF views → DRF URLs
DRF endpoints live → JS engine services → JS app files
Engine files complete → App files begin (never in parallel)
Records engine complete → Activity engine begin
Activity engine complete → Paraclete service begin
All engines complete → Dashboard begin
```

---

## Phase 0 — VPS + Django Project Setup

**Exit criteria:** `https://your-domain.com/api/health/` returns `{"status": "ok"}`. Nothing else. Do not proceed to Phase 1 until this passes.

### Task 0.1 — VPS baseline
**Files:** none (server commands only)

1. SSH into VPS
2. Update packages: `sudo apt update && sudo apt upgrade -y`
3. Install dependencies:
   ```bash
   sudo apt install -y python3.11 python3.11-venv python3-pip postgresql postgresql-contrib nginx git
   ```
4. Create deploy user: `sudo adduser ics && sudo usermod -aG sudo ics`
5. Switch to deploy user: `su - ics`
6. Commit: n/a (server setup)

### Task 0.2 — PostgreSQL database
**Files:** none (DB commands only)

1. Start PostgreSQL: `sudo systemctl start postgresql && sudo systemctl enable postgresql`
2. Create DB and user:
   ```bash
   sudo -u postgres psql
   CREATE DATABASE ics_db;
   CREATE USER ics_user WITH PASSWORD 'your-strong-password';
   ALTER ROLE ics_user SET client_encoding TO 'utf8';
   ALTER ROLE ics_user SET default_transaction_isolation TO 'read committed';
   ALTER ROLE ics_user SET timezone TO 'UTC';
   GRANT ALL PRIVILEGES ON DATABASE ics_db TO ics_user;
   \q
   ```
3. Test connection: `psql -U ics_user -d ics_db -h localhost`

### Task 0.3 — Django project scaffold
**Files:**
- Create: `~/ics/` (project root)
- Create: `~/ics/requirements.txt`
- Create: `~/ics/ics_project/settings/base.py`
- Create: `~/ics/ics_project/settings/production.py`
- Create: `~/ics/ics_project/settings/local.py`

1. Create project directory and virtualenv:
   ```bash
   mkdir ~/ics && cd ~/ics
   python3.11 -m venv venv
   source venv/bin/activate
   ```
2. Install packages:
   ```bash
   pip install django==4.2 djangorestframework django-cors-headers psycopg2-binary python-decouple gunicorn
   pip freeze > requirements.txt
   ```
3. Create Django project:
   ```bash
   django-admin startproject ics_project .
   ```
4. Create settings split:
   ```bash
   mkdir ics_project/settings
   mv ics_project/settings.py ics_project/settings/base.py
   touch ics_project/settings/production.py
   touch ics_project/settings/local.py
   touch ics_project/settings/__init__.py
   ```
5. `ics_project/settings/base.py` — update DATABASE section:
   ```python
   from decouple import config

   SECRET_KEY = config('SECRET_KEY')
   DEBUG = config('DEBUG', default=False, cast=bool)
   ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

   INSTALLED_APPS = [
       'django.contrib.admin',
       'django.contrib.auth',
       'django.contrib.contenttypes',
       'django.contrib.sessions',
       'django.contrib.messages',
       'django.contrib.staticfiles',
       'rest_framework',
       'rest_framework.authtoken',
       'corsheaders',
   ]

   MIDDLEWARE = [
       'corsheaders.middleware.CorsMiddleware',
       'django.middleware.security.SecurityMiddleware',
       'django.contrib.sessions.middleware.SessionMiddleware',
       'django.middleware.common.CommonMiddleware',
       'django.middleware.csrf.CsrfViewMiddleware',
       'django.contrib.auth.middleware.AuthenticationMiddleware',
       'django.contrib.messages.middleware.MessageMiddleware',
       'django.middleware.clickjacking.XFrameOptionsMiddleware',
   ]

   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': config('DB_NAME'),
           'USER': config('DB_USER'),
           'PASSWORD': config('DB_PASSWORD'),
           'HOST': config('DB_HOST', default='localhost'),
           'PORT': config('DB_PORT', default='5432'),
       }
   }

   REST_FRAMEWORK = {
       'DEFAULT_AUTHENTICATION_CLASSES': [
           'rest_framework.authentication.TokenAuthentication',
       ],
       'DEFAULT_PERMISSION_CLASSES': [
           'rest_framework.permissions.IsAuthenticated',
       ],
       'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
       'PAGE_SIZE': 20,
   }

   CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', cast=lambda v: [s.strip() for s in v.split(',')])
   ```
6. Create `.env` file in project root:
   ```
   SECRET_KEY=generate-a-long-random-string-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
   DB_NAME=ics_db
   DB_USER=ics_user
   DB_PASSWORD=your-strong-password
   DB_HOST=localhost
   DB_PORT=5432
   CORS_ALLOWED_ORIGINS=http://localhost:8000,https://your-domain.com
   ```
7. Run migrations: `python manage.py migrate`
8. Commit: `git init && git add . && git commit -m "chore: django project scaffold"`

### Task 0.4 — Health check endpoint
**Files:**
- Create: `~/ics/core/` (Django app)
- Create: `~/ics/core/views.py`
- Create: `~/ics/core/urls.py`
- Modify: `~/ics/ics_project/urls.py`

1. Create core app: `python manage.py startapp core`
2. Add to `INSTALLED_APPS`: `'core',`
3. `core/views.py`:
   ```python
   from rest_framework.decorators import api_view, permission_classes
   from rest_framework.permissions import AllowAny
   from rest_framework.response import Response

   @api_view(['GET'])
   @permission_classes([AllowAny])
   def health_check(request):
       return Response({'status': 'ok'})
   ```
4. `core/urls.py`:
   ```python
   from django.urls import path
   from . import views

   urlpatterns = [
       path('health/', views.health_check, name='health-check'),
   ]
   ```
5. `ics_project/urls.py`:
   ```python
   from django.contrib import admin
   from django.urls import path, include

   urlpatterns = [
       path('admin/', admin.site.urls),
       path('api/', include('core.urls')),
   ]
   ```
6. Run server: `python manage.py runserver`
7. Test: `curl http://localhost:8000/api/health/`
   Expected: `{"status": "ok"}`
8. Commit: `git add . && git commit -m "feat: health check endpoint"`

### Task 0.5 — Nginx + Gunicorn (production)
**Files:**
- Create: `/etc/nginx/sites-available/ics`
- Create: `~/ics/gunicorn.conf.py`

1. `gunicorn.conf.py`:
   ```python
   bind = "127.0.0.1:8001"
   workers = 3
   timeout = 120
   accesslog = "/var/log/gunicorn/ics_access.log"
   errorlog = "/var/log/gunicorn/ics_error.log"
   ```
2. Nginx config `/etc/nginx/sites-available/ics`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location /api/ {
           proxy_pass http://127.0.0.1:8001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       location /static/ {
           alias /home/ics/ics/staticfiles/;
       }

       location / {
           root /home/ics/ics/frontend/;
           try_files $uri $uri/ /index.html;
       }
   }
   ```
3. Enable site: `sudo ln -s /etc/nginx/sites-available/ics /etc/nginx/sites-enabled/`
4. Test config: `sudo nginx -t`
5. Start Nginx: `sudo systemctl restart nginx`
6. Start Gunicorn: `gunicorn ics_project.wsgi:application -c gunicorn.conf.py`
7. Test: `curl https://your-domain.com/api/health/`
   Expected: `{"status": "ok"}`
8. Commit: `git add . && git commit -m "chore: nginx + gunicorn production config"`

---

## Phase 1 — Django Foundation (Auth + Tenant + Identity)

**Exit criteria:** Can register a user, log in, receive a token, create a tenant with a materialized path, assign a UserPermission. All via DRF endpoints. No frontend yet.

### Task 1.1 — Accounts Django app
**Files:**
- Create: `~/ics/accounts/models.py`
- Create: `~/ics/accounts/serializers.py`
- Create: `~/ics/accounts/views.py`
- Create: `~/ics/accounts/urls.py`
- Create: `~/ics/accounts/permissions.py`

1. Create app: `python manage.py startapp accounts`
2. Add to `INSTALLED_APPS`: `'accounts',`
3. `accounts/models.py`:
   ```python
   import uuid
   from django.contrib.auth.models import AbstractUser
   from django.db import models

   class User(AbstractUser):
       id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
       display_name = models.CharField(max_length=100, blank=True)
       avatar_url = models.URLField(blank=True, null=True)
       competence_level = models.IntegerField(default=0)
       # 0 = seeker, 1-5 = formation levels per KGS
       status = models.CharField(
           max_length=30,
           choices=[
               ('seeker', 'Seeker'),
               ('active', 'Active'),
               ('suspended', 'Suspended'),
               ('pending_verification', 'Pending Verification'),
           ],
           default='seeker'
       )
       created_at = models.DateTimeField(auto_now_add=True)
       updated_at = models.DateTimeField(auto_now=True)

       class Meta:
           db_table = 'accounts_user'

       def __str__(self):
           return self.email
   ```
4. Add to `settings/base.py`: `AUTH_USER_MODEL = 'accounts.User'`
5. `accounts/serializers.py`:
   ```python
   from rest_framework import serializers
   from django.contrib.auth import authenticate
   from .models import User

   class RegisterSerializer(serializers.ModelSerializer):
       password = serializers.CharField(write_only=True, min_length=8)

       class Meta:
           model = User
           fields = ['id', 'email', 'display_name', 'password']

       def create(self, validated_data):
           user = User.objects.create_user(
               username=validated_data['email'],
               email=validated_data['email'],
               display_name=validated_data.get('display_name', ''),
               password=validated_data['password'],
               status='seeker',
               competence_level=0
           )
           return user

   class LoginSerializer(serializers.Serializer):
       email = serializers.EmailField()
       password = serializers.CharField(write_only=True)

       def validate(self, data):
           user = authenticate(username=data['email'], password=data['password'])
           if not user:
               raise serializers.ValidationError('Invalid credentials')
           if user.status == 'suspended':
               raise serializers.ValidationError('Account suspended')
           data['user'] = user
           return data

   class UserSerializer(serializers.ModelSerializer):
       class Meta:
           model = User
           fields = ['id', 'email', 'display_name', 'avatar_url',
                     'competence_level', 'status', 'created_at']
           read_only_fields = ['id', 'created_at', 'competence_level']
   ```
6. `accounts/views.py`:
   ```python
   from rest_framework import status
   from rest_framework.decorators import api_view, permission_classes
   from rest_framework.permissions import AllowAny, IsAuthenticated
   from rest_framework.response import Response
   from rest_framework.authtoken.models import Token
   from .serializers import RegisterSerializer, LoginSerializer, UserSerializer

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
   ```
7. `accounts/urls.py`:
   ```python
   from django.urls import path
   from . import views

   urlpatterns = [
       path('auth/register/', views.register, name='register'),
       path('auth/login/', views.login, name='login'),
       path('auth/logout/', views.logout, name='logout'),
       path('auth/me/', views.me, name='me'),
   ]
   ```
8. Add to `ics_project/urls.py`: `path('api/', include('accounts.urls')),`
9. Run: `python manage.py makemigrations accounts && python manage.py migrate`
10. Test register:
    ```bash
    curl -X POST http://localhost:8000/api/auth/register/ \
      -H "Content-Type: application/json" \
      -d '{"email":"test@test.com","display_name":"Test","password":"testpass123"}'
    ```
    Expected: `{"token": "...", "user": {...}}`
11. Commit: `git add . && git commit -m "feat: accounts app — register, login, logout, me"`

### Task 1.2 — Tenants Django app
**Files:**
- Create: `~/ics/tenants/models.py`
- Create: `~/ics/tenants/serializers.py`
- Create: `~/ics/tenants/views.py`
- Create: `~/ics/tenants/urls.py`

1. Create app: `python manage.py startapp tenants`
2. Add to `INSTALLED_APPS`: `'tenants',`
3. `tenants/models.py`:
   ```python
   import uuid
   from django.db import models
   from django.conf import settings

   class Tenant(models.Model):
       TIER_CHOICES = [
           ('handbook', 'Handbook'),
           ('church_node', 'Church Node'),
           ('church_collective', 'Church Collective'),
           ('district', 'District'),
           ('provincial', 'Provincial'),
           ('national', 'National'),
           ('regional', 'Regional'),
           ('continental', 'Continental'),
           ('global', 'Global'),
       ]
       AFFILIATION_CHOICES = [
           ('ichebo', 'Ichebo'),
           ('independent', 'Independent'),
           ('affiliate', 'Affiliate'),
       ]
       STATUS_CHOICES = [
           ('active', 'Active'),
           ('pending', 'Pending'),
           ('suspended', 'Suspended'),
       ]

       id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
       parent = models.ForeignKey(
           'self', null=True, blank=True,
           on_delete=models.PROTECT, related_name='children'
       )
       created_by = models.ForeignKey(
           settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
           related_name='created_tenants'
       )
       created_at = models.DateTimeField(auto_now_add=True)
       updated_at = models.DateTimeField(auto_now=True)

       name = models.CharField(max_length=200)
       slug = models.SlugField(max_length=200, unique=True)
       # Materialized path — e.g. /global/africa/southafrica/gauteng/pretoria/
       path = models.CharField(max_length=500, db_index=True)

       tier = models.CharField(max_length=30, choices=TIER_CHOICES)
       affiliation = models.CharField(max_length=20, choices=AFFILIATION_CHOICES, default='independent')
       status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
       is_collective = models.BooleanField(default=False)

       description = models.TextField(blank=True, null=True)
       logo_url = models.URLField(blank=True, null=True)

       # Location (JSON field — PostgreSQL)
       location = models.JSONField(default=dict, blank=True)
       settings_data = models.JSONField(default=dict, blank=True)

       class Meta:
           db_table = 'tenants_tenant'
           indexes = [
               models.Index(fields=['path']),
               models.Index(fields=['tier']),
               models.Index(fields=['status']),
           ]

       def get_descendants(self):
           return Tenant.objects.filter(
               path__startswith=self.path
           ).exclude(pk=self.pk)

       def get_ancestors(self):
           parts = self.path.strip('/').split('/')
           ancestor_paths = [
               '/' + '/'.join(parts[:i+1]) + '/'
               for i in range(len(parts) - 1)
           ]
           return Tenant.objects.filter(path__in=ancestor_paths)

       def __str__(self):
           return f"{self.name} ({self.path})"


   class UserPermission(models.Model):
       ROLE_CHOICES = [
           ('seeker', 'Seeker'),
           ('disciple', 'Disciple'),
           ('branch-steward', 'Branch Steward'),
           ('district-steward', 'District Steward'),
           ('provincial-steward', 'Provincial Steward'),
           ('national-steward', 'National Steward'),
           ('regional-steward', 'Regional Steward'),
           ('continental-steward', 'Continental Steward'),
           ('global-steward', 'Global Steward'),
           ('admin', 'Admin'),
       ]

       id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
       tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='permissions')
       user = models.ForeignKey(
           settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
           related_name='tenant_permissions'
       )
       created_by = models.ForeignKey(
           settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
           related_name='granted_permissions'
       )
       created_at = models.DateTimeField(auto_now_add=True)

       tenant_path = models.CharField(max_length=500, db_index=True)
       role = models.CharField(max_length=30, choices=ROLE_CHOICES)
       level = models.IntegerField(default=1)
       is_active = models.BooleanField(default=True)
       granted_at = models.DateTimeField(auto_now_add=True)
       granted_by = models.ForeignKey(
           settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
           related_name='permissions_granted', null=True
       )

       class Meta:
           db_table = 'tenants_userpermission'
           unique_together = [['tenant', 'user', 'role']]
   ```
4. Write serializers and views following the same pattern as Task 1.1 — CRUD for Tenant and UserPermission, all authenticated.
5. Run: `python manage.py makemigrations tenants && python manage.py migrate`
6. Test: create a tenant via POST, verify path is stored correctly.
7. Commit: `git add . && git commit -m "feat: tenants app — tenant model + user permissions"`

### Task 1.3 — accounts/permissions.py (KGS permission helper)
**Files:**
- Create: `~/ics/accounts/permissions.py`

This is the Python implementation of the permission check algorithm from Part 7 of the data contract. Implement once, import everywhere.

```python
# accounts/permissions.py
from rest_framework.permissions import BasePermission
from tenants.models import UserPermission

class IsLevel1OrAbove(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.competence_level >= 1

class IsLevel2OrAbove(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.competence_level >= 2

class IsLevel4OrAbove(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.competence_level >= 4

class IsLevel5OrAbove(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.competence_level >= 5

def check_record_permission(user, record):
    """
    Full permission check per data contract Part 7.
    Returns True if user may read this record, False otherwise.
    """
    if not user or not user.is_authenticated:
        return record.visibility == 'public'

    if user.status == 'seeker':
        return (record.created_by == user) or record.visibility == 'public'

    # Handbook short-circuit
    if record.tenant and record.tenant.path.startswith('/global/handbook/'):
        return user.competence_level >= 5

    visibility = record.permissions_data.get('visibility', 'private')
    required_level = record.permissions_data.get('required_level', 1)
    roles_allowed = record.permissions_data.get('roles_allowed', [])

    if visibility == 'private':
        return record.created_by == user

    if user.competence_level < required_level:
        return False

    if visibility == 'public':
        return True

    user_permissions = UserPermission.objects.filter(
        user=user, is_active=True
    ).values_list('tenant_path', 'role')

    tenant_path = record.tenant.path if record.tenant else ''

    if visibility == 'tenant':
        has_access = any(tp == tenant_path for tp, _ in user_permissions)
    elif visibility == 'collective':
        has_access = any(
            tenant_path.startswith(tp) or tp.startswith(tenant_path)
            for tp, _ in user_permissions
        )
    else:
        has_access = False

    if not has_access:
        return False

    if roles_allowed:
        return any(role in roles_allowed for _, role in user_permissions)

    return True
```

Commit: `git add . && git commit -m "feat: KGS permission helper — check_record_permission"`

---

## Phase 2 — Records Engine (Django + DRF + JS Service)

**Exit criteria:** Can create, read, update, soft-delete a Record via DRF. Can create a Relationship between two Records. JS `records.service.js` calls these endpoints. Records app UI works against real data.

### Task 2.1 — Records Django app (models)
**Files:**
- Create: `~/ics/records/models.py`

```python
import uuid
from django.db import models
from django.conf import settings

class Record(models.Model):
    RECORD_CLASS_CHOICES = [
        ('personal', 'Personal'),
        ('organizational', 'Organizational'),
        ('governance', 'Governance'),
    ]
    RECORD_FAMILY_CHOICES = [
        ('journal', 'Journal'),
        ('governance', 'Governance'),
        ('activity', 'Activity'),
        ('learning', 'Learning'),
        ('reference', 'Reference'),
        ('bible', 'Bible'),
        ('community', 'Community'),
    ]
    ORIGIN_CHOICES = [
        ('user', 'User'),
        ('system', 'System'),
        ('paraclete', 'Paraclete'),
        ('import', 'Import'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
        ('locked', 'Locked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant', null=True, blank=True,
        on_delete=models.PROTECT, related_name='records'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='records'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    record_class = models.CharField(max_length=20, choices=RECORD_CLASS_CHOICES)
    record_family = models.CharField(max_length=20, choices=RECORD_FAMILY_CHOICES)
    record_type = models.CharField(max_length=50)
    origin = models.CharField(max_length=20, choices=ORIGIN_CHOICES, default='user')

    title = models.CharField(max_length=500)
    content = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='locked_records'
    )
    locked_at = models.DateTimeField(null=True, blank=True)

    # Governance versioning
    version = models.IntegerField(null=True, blank=True)
    previous_version = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='next_versions'
    )
    superseded_by = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='supersedes'
    )

    tags = models.JSONField(default=list, blank=True)
    categories = models.JSONField(default=list, blank=True)
    custom_fields = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    permissions_data = models.JSONField(default=dict, blank=True)
    # permissions_data structure: {visibility, required_level, roles_allowed, can_edit}

    class Meta:
        db_table = 'records_record'
        indexes = [
            models.Index(fields=['tenant']),
            models.Index(fields=['record_family']),
            models.Index(fields=['record_type']),
            models.Index(fields=['record_class']),
            models.Index(fields=['created_by']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['tenant', 'record_family']),
            models.Index(fields=['tenant', 'record_class']),
        ]

    def __str__(self):
        return f"{self.record_type}: {self.title}"


class Relationship(models.Model):
    DIRECTION_CHOICES = [
        ('directed', 'Directed'),
        ('bidirectional', 'Bidirectional'),
    ]
    RELATIONSHIP_TYPE_CHOICES = [
        ('relates_to', 'Relates To'),
        ('derived_from', 'Derived From'),
        ('references', 'References'),
        ('answers', 'Answers'),
        ('fulfills', 'Fulfills'),
        ('requests', 'Requests'),
        ('has_symbol', 'Has Symbol'),
        ('matches_pattern', 'Matches Pattern'),
        ('assigned_to', 'Assigned To'),
        ('tracks', 'Tracks'),
        ('completes', 'Completes'),
        ('part_of', 'Part Of'),
        ('aligns_with', 'Aligns With'),
        ('authorised_by', 'Authorised By'),
        ('has_subject', 'Has Subject'),
        ('has_entity', 'Has Entity'),
        ('tagged_in', 'Tagged In'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant', null=True, blank=True,
        on_delete=models.PROTECT
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    from_record = models.ForeignKey(
        Record, on_delete=models.CASCADE, related_name='outgoing_relationships'
    )
    to_record = models.ForeignKey(
        Record, on_delete=models.CASCADE, related_name='incoming_relationships'
    )

    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    relationship_type = models.CharField(max_length=30, choices=RELATIONSHIP_TYPE_CHOICES)
    notes = models.TextField(blank=True, null=True)
    strength = models.CharField(
        max_length=10,
        choices=[('weak','Weak'),('medium','Medium'),('strong','Strong')],
        null=True, blank=True
    )

    class Meta:
        db_table = 'records_relationship'
        indexes = [
            models.Index(fields=['from_record']),
            models.Index(fields=['to_record']),
            models.Index(fields=['relationship_type']),
        ]
```

Run: `python manage.py makemigrations records && python manage.py migrate`
Commit: `git add . && git commit -m "feat: records models — Record + Relationship"`

### Task 2.2 — Records serializers + views + URLs
**Files:**
- Create: `~/ics/records/serializers.py`
- Create: `~/ics/records/views.py`
- Create: `~/ics/records/urls.py`

Endpoints to implement:
```
GET    /api/records/              list (filtered by tenant, family, type, class)
POST   /api/records/              create
GET    /api/records/{id}/         retrieve
PATCH  /api/records/{id}/         update
DELETE /api/records/{id}/         soft delete (set deleted_at)
GET    /api/records/{id}/relationships/   list related records
POST   /api/relationships/        create relationship
DELETE /api/relationships/{id}/   soft delete relationship
```

All list endpoints filter out soft-deleted records (`deleted_at=None`) by default.
All write endpoints enforce `check_record_permission` from `accounts/permissions.py`.

Commit: `git add . && git commit -m "feat: records DRF endpoints — CRUD + relationships"`

### Task 2.3 — records.service.js (JS engine)
**Files:**
- Create: `~/ics/frontend/assets/js/engines/records.service.js`
- Create: `~/ics/frontend/assets/js/engines/relationships.service.js`
- Create: `~/ics/frontend/assets/js/engines/records.store.js`

```js
// records.service.js — IIFE module, calls DRF endpoints
const ICSRecords = (() => {
  const BASE = '/api/records/'

  function authHeaders() {
    const token = localStorage.getItem('ics_token')
    return {
      'Content-Type': 'application/json',
      'Authorization': `Token ${token}`
    }
  }

  async function list(filters = {}) {
    const params = new URLSearchParams(filters)
    const res = await fetch(`${BASE}?${params}`, { headers: authHeaders() })
    if (!res.ok) throw new Error(`Records list failed: ${res.status}`)
    return res.json()
  }

  async function get(id) {
    const res = await fetch(`${BASE}${id}/`, { headers: authHeaders() })
    if (!res.ok) throw new Error(`Record get failed: ${res.status}`)
    return res.json()
  }

  async function create(data) {
    const res = await fetch(BASE, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(data)
    })
    if (!res.ok) throw new Error(`Record create failed: ${res.status}`)
    return res.json()
  }

  async function update(id, data) {
    const res = await fetch(`${BASE}${id}/`, {
      method: 'PATCH',
      headers: authHeaders(),
      body: JSON.stringify(data)
    })
    if (!res.ok) throw new Error(`Record update failed: ${res.status}`)
    return res.json()
  }

  async function remove(id) {
    const res = await fetch(`${BASE}${id}/`, {
      method: 'DELETE',
      headers: authHeaders()
    })
    if (!res.ok) throw new Error(`Record delete failed: ${res.status}`)
    return true
  }

  return { list, get, create, update, remove }
})()
```

Commit: `git add . && git commit -m "feat: records.service.js + relationships.service.js"`

### Task 2.4 — Wire Records app UI to DRF
**Files:**
- Modify: `~/ics/frontend/assets/js/apps/records-app.js`
- Modify: `~/ics/frontend/assets/js/core/auth.js`
- Modify: `~/ics/frontend/assets/js/core/router.js`

1. Update `auth.js` — replace localStorage user creation with fetch to `/api/auth/register/` and `/api/auth/login/`. Store returned token in `localStorage.setItem('ics_token', token)`.
2. Update `router.js` — auth guard checks `localStorage.getItem('ics_token')` (not a user object). On protected route access without token, redirect to login.
3. Update `records-app.js` — replace all direct storage calls with `ICSRecords.list()`, `ICSRecords.create()` etc.
4. Test: register a user via the UI, create a record, confirm it appears in Django admin.
5. Commit: `git add . && git commit -m "feat: wire records UI to DRF — auth + records CRUD"`

---

## Phase 3 — Activity Engine (Django + DRF + JS Service)

**Exit criteria:** Can create, read, update, soft-delete an Activity. ActivityLog is written on every status change. Activity → Record linking works via Relationships (no `linked_record_ids`). JS `activity.service.js` calls DRF endpoints.

### Task 3.1 — Activity Django app (models)
**Files:**
- Create: `~/ics/activity/models.py`

Model fields per data contract Part 4. Key points:
- `activity_type`: task | habit | goal | event | campaign | project | programme | reminder | skill
- `parent_activity_id` for nesting: programme → project → campaign → task
- `kgs_pillar` and `kgs_pathway` fields from data contract
- No `linked_record_ids` — linking is via `records.Relationship` only
- `ActivityLog` model for every status/progress change

Run migrations. Commit: `git add . && git commit -m "feat: activity models — Activity + ActivityLog"`

### Task 3.2 — Activity serializers + views + URLs
Endpoints:
```
GET    /api/activities/           list
POST   /api/activities/           create
GET    /api/activities/{id}/      retrieve
PATCH  /api/activities/{id}/      update (auto-writes ActivityLog entry)
DELETE /api/activities/{id}/      soft delete
GET    /api/activities/{id}/log/  activity history
```

Commit: `git add . && git commit -m "feat: activity DRF endpoints"`

### Task 3.3 — activity.service.js + activity.store.js
Same pattern as `records.service.js`. Calls DRF activity endpoints.
Commit: `git add . && git commit -m "feat: activity.service.js + activity.store.js"`

### Task 3.4 — Build activity-app.js UI
Mobile-first. Displays tasks, habits, goals. Links to records via `ICSRelationships.create()`.
Commit: `git add . && git commit -m "feat: activity app UI"`

---

## Phase 4 — Identity + Tenant Service Layer (JS)

**Exit criteria:** `identity.service.js` and `tenant.service.js` exist and call DRF. `router.js` uses `identity.service.js` for competence-level-aware route guarding.

### Task 4.1 — identity.service.js
**Files:**
- Create: `~/ics/frontend/assets/js/engines/identity.service.js`

```js
const ICSIdentity = (() => {
  function authHeaders() {
    const token = localStorage.getItem('ics_token')
    return { 'Authorization': `Token ${token}`, 'Content-Type': 'application/json' }
  }

  async function getCurrentUser() {
    const res = await fetch('/api/auth/me/', { headers: authHeaders() })
    if (!res.ok) return null
    return res.json()
  }

  async function getPermissions() {
    const res = await fetch('/api/auth/me/permissions/', { headers: authHeaders() })
    if (!res.ok) return []
    return res.json()
  }

  function isAuthenticated() {
    return !!localStorage.getItem('ics_token')
  }

  function getToken() {
    return localStorage.getItem('ics_token')
  }

  return { getCurrentUser, getPermissions, isAuthenticated, getToken }
})()
```

Commit: `git add . && git commit -m "feat: identity.service.js"`

### Task 4.2 — tenant.service.js
Calls `/api/tenants/` endpoints. Handles path resolution and membership queries.
Commit: `git add . && git commit -m "feat: tenant.service.js"`

---

## Phase 5 — App Layer (one app per task)

**Exit criteria per app:** App renders real data from DRF. Mobile-first layout. Passes manual smoke test on phone.

Build order is fixed — do not reorder:

### Task 5.1 — Bible app (bible.js + Django bible endpoints)
- Store Bible data as `Record` objects with `record_family: "bible"`, `record_type: "bible_note"`
- Bible reader reads from a static JSON file (no DB needed for scripture text itself)
- Notes and annotations write to Records via `ICSRecords.create()`
- Commit: `git add . && git commit -m "feat: bible app"`

### Task 5.2 — Learn app (learn-app.js + Django learning endpoints)
- Courses are `Record` objects with `record_family: "learning"`
- Competence level gates via `ICSIdentity.getCurrentUser().competence_level`
- Commit: `git add . && git commit -m "feat: learn app"`

### Task 5.3 — Community app (community-app.js + Django community endpoints)
- Tenant membership views
- Member directory (filtered by user's tenant scope)
- Commit: `git add . && git commit -m "feat: community app"`

### Task 5.4 — Governance app (governance-app.js + Django governance endpoints)
- Reads `record_class: "governance"` records only
- Write access gated to Level 4+ (Level 5 for Handbook records)
- Version history view using `previous_version_id` / `superseded_by` chain
- Commit: `git add . && git commit -m "feat: governance app"`

### Task 5.5 — Profile + Settings apps
- Profile: reads/writes `/api/auth/me/`
- Settings: theme, language, timezone — stored in `localStorage` (UI state only, not persisted to DB at this phase)
- Commit: `git add . && git commit -m "feat: profile + settings apps"`

### Task 5.6 — Notifications app (stub)
- Endpoint: `GET /api/notifications/` — returns empty list for now
- UI renders list, marks as read
- Full implementation deferred to Phase 7
- Commit: `git add . && git commit -m "feat: notifications app stub"`

---

## Phase 6 — Paraclete Service

**Exit criteria:** `paraclete.service.js` calls DRF and returns a real `ParacleteDigest` for the logged-in user. Dashboard renders digest data.

### Task 6.1 — Paraclete Django app
**Files:**
- Create: `~/ics/paraclete/` Django app
- Create: `~/ics/paraclete/service.py` — orchestration logic (reads from records + activity, writes nothing)
- Create: `~/ics/paraclete/views.py` — DRF endpoints

Endpoints:
```
GET  /api/paraclete/digest/              daily digest
GET  /api/paraclete/reminders/           pending reminders
GET  /api/paraclete/suggest/{record_id}/ link suggestions
GET  /api/paraclete/prompt/              discipline prompt
POST /api/paraclete/respond/             accept/dismiss suggestion
```

`paraclete/service.py` calls Django ORM directly (not other DRF endpoints). It is a Python orchestration module, not a web service calling itself.

Commit: `git add . && git commit -m "feat: paraclete Django service + endpoints"`

### Task 6.2 — paraclete.service.js
Calls Paraclete DRF endpoints. Returns `ParacleteDigest` for dashboard consumption.
Commit: `git add . && git commit -m "feat: paraclete.service.js"`

---

## Phase 7 — Dashboard

**Exit criteria:** Dashboard renders a real `ParacleteDigest`. Shows pending activities, recent records, active prayer count, discipline prompt. Role-aware and tenant-aware.

### Task 7.1 — dashboard-app.js
- Calls `ICSParaclete.getDailyDigest()`
- Renders widgets: today's focus, pending activities, recent records, prayer count
- Competence level determines which widgets are visible
- Commit: `git add . && git commit -m "feat: dashboard app"`

---

## Phase 8 — Production Hardening

**Exit criteria:** Platform runs stably on VPS. SSL active. Static files served by Nginx. Error logging in place.

### Task 8.1 — SSL (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```
Commit: `git add . && git commit -m "chore: SSL via Let's Encrypt"`

### Task 8.2 — Static files
```bash
python manage.py collectstatic
```
Nginx serves `/static/` from `staticfiles/`. Frontend assets served from `frontend/`.
Commit: `git add . && git commit -m "chore: static files config"`

### Task 8.3 — Error logging + Django admin
- Configure `LOGGING` in Django settings to write errors to file
- Create superuser: `python manage.py createsuperuser`
- Verify Django admin accessible at `/admin/`
- Commit: `git add . && git commit -m "chore: logging + admin setup"`

### Task 8.4 — Systemd service for Gunicorn
Create `/etc/systemd/system/ics.service` so Gunicorn restarts on reboot:
```ini
[Unit]
Description=ICS Gunicorn Service
After=network.target

[Service]
User=ics
WorkingDirectory=/home/ics/ics
ExecStart=/home/ics/ics/venv/bin/gunicorn ics_project.wsgi:application -c gunicorn.conf.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable ics
sudo systemctl start ics
```
Commit: `git add . && git commit -m "chore: systemd gunicorn service"`

---

## Phase Summary

| Phase | What it builds | Entry requirement | Exit criteria |
|-------|---------------|-------------------|---------------|
| 0 | VPS + Django scaffold + health check | VPS access | `/api/health/` returns 200 |
| 1 | Auth + Tenant + Identity + Permissions | Phase 0 done | Register, login, create tenant, assign permission |
| 2 | Records Engine (Django + JS) | Phase 1 done | Full Record + Relationship CRUD, UI wired |
| 3 | Activity Engine (Django + JS) | Phase 2 done | Full Activity CRUD, ActivityLog, linked to Records |
| 4 | Identity + Tenant JS services | Phase 1 done | identity.service.js + tenant.service.js call DRF |
| 5 | All apps (Bible, Learn, Community, Governance, Profile) | Phases 2–4 done | Each app renders real data |
| 6 | Paraclete service | Phase 3 done | DailyDigest returns real data |
| 7 | Dashboard | Phase 6 done | Dashboard renders digest, role-aware |
| 8 | Production hardening | Phase 7 done | SSL, static files, logging, systemd |

## Deferred (post-MVP)
- Full `RecordPermission` table (fine-grained per-user permissions)
- `CustomFieldSchema` formal validation system
- Video/Live streaming app
- In-service Display app
- Donations feature
- Advanced Paraclete AI features (pattern detection, auto-linking)
- Push notifications (mobile)

