import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ics_project.settings.local')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from tenants.models import Tenant

User = get_user_model()
user = User.objects.get(email='architect@ics.test')
client = Client()
client.force_login(user)

tenants = Tenant.objects.filter(deleted_at__isnull=True)
print(f"Testing {tenants.count()} tenants...")

for t in tenants:
    r1 = client.get(f'/channel/?tenant_id={t.id}&view=scheduler')
    if r1.status_code == 500:
        print(f"500 on scheduler for tenant {t.id}")
    r2 = client.get(f'/channel/?tenant_id={t.id}&view=library')
    if r2.status_code == 500:
        print(f"500 on library for tenant {t.id}")

