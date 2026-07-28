import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ics_project.settings.base")
django.setup()

from django.core.management import call_command
from accounts.models import User
from tenants.models import Tenant
from broadcast.models import ChannelConfig

# Create a superuser and a tenant
call_command('migrate')
u, _ = User.objects.get_or_create(username='testadmin', defaults={'is_superuser': True, 'is_staff': True})
u.set_password('admin123')
u.save()

t, _ = Tenant.objects.get_or_create(name='Test Tenant', slug='test-tenant')
ChannelConfig.objects.get_or_create(tenant=t)
print(f"Tenant ID: {t.id}")
