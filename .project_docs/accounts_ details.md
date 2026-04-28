# Accounts Details

This is the current devPrime Tenant account:

```bash
python3 manage.py shell -c "
from accounts.models import User
from rest_framework.authtoken.models import Token

User.objects.filter(email='architect@ics.test').delete()

user = User.objects.create_user(
    username='architect@ics.test',
    email='architect@ics.test',
    display_name='Architect',
    password='Architect123!',
    status='active',
    competence_level=5,
)
Token.objects.get_or_create(user=user)
print('Done — login with architect@ics.test / Architect123!')
"
```

---

## Prime Tenant Details🧮

architect@ics.test / Architect123!


## Production env. details

```bash
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
DEBUG=False
ALLOWED_HOSTS=app.ichebo.online
DB_NAME=ics_db
DB_USER=ics_user
DB_PASSWORD=t1ny@T1m!#247
DB_HOST=localhost
DB_PORT=5432
CORS_ALLOWED_ORIGINS=https://app.ichebo.online

```



Test user

larrypmwansa@gmail.com

Promise4kipa

Kingdom Member Number: 

KMN-ZA-2026-00001