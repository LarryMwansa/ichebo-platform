from django.core.management.base import BaseCommand
from django.db import transaction
from tenants.models import Tenant
from accounts.models import User


class Command(BaseCommand):
    help = 'Seed the Induction Tenant system singleton at /global/induction/'

    @transaction.atomic
    def handle(self, *args, **options):
        existing = Tenant.objects.filter(slug='induction').first()
        if existing:
            self.stdout.write(self.style.WARNING(
                f'Induction Tenant already exists: {existing.path} (id={existing.id})'
            ))
            return

        system_user = User.objects.filter(is_superuser=True).first()
        if not system_user:
            self.stdout.write(self.style.ERROR(
                'No superuser found. Create one first:\n  python manage.py createsuperuser'
            ))
            return

        tenant = Tenant.objects.create(
            name='Induction',
            slug='induction',
            path='/global/induction/',
            tier='induction',
            affiliation='ichebo',
            status='active',
            is_collective=False,
            created_by=system_user,
            description='System-managed induction environment. All new users are placed here on registration. Cannot be deleted or renamed.',
            settings_data={
                'allow_public_records': False,
                'require_approval': False,
                'max_members': None,
            }
        )

        self.stdout.write(self.style.SUCCESS(
            f'Induction Tenant created: {tenant.path} (id={tenant.id})'
        ))
