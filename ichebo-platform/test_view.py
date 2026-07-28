import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ics_project.settings.local')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(email='architect@ics.test')

client = Client()
client.force_login(user)

response = client.get('/channel/?view=library')
print(f"Status Code: {response.status_code}")
if response.status_code == 500:
    import traceback
    try:
        raise Exception("500 error triggered")
    except:
        pass
