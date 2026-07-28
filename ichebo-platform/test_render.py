import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ics_project.settings")
django.setup()

from django.test import Client
from accounts.models import User
from tenants.models import Tenant
from broadcast.models import ChannelConfig

user = User.objects.first()
tenant = Tenant.objects.first()
config, _ = ChannelConfig.objects.get_or_create(tenant=tenant)

c = Client()
c.force_login(user)
response = c.get(f'/channel/config/{tenant.id}/')
print(response.content.decode('utf-8'))
