from django.core.management.base import BaseCommand
from django.db import transaction
from tenants.models import Tenant
from accounts.models import User


class Command(BaseCommand):
    help = 'Create the Handbook (Prime Tenant) singleton at /global/handbook/'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of Handbook if it already exists'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force = options.get('force', False)

        # Check if Handbook already exists
        handbook = Tenant.objects.filter(
            path='/global/handbook/',
            tier='handbook'
        ).first()

        if handbook and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'ℹ Handbook already exists:\n'
                    f'  ID: {handbook.id}\n'
                    f'  Name: {handbook.name}\n'
                    f'  Path: {handbook.path}\n'
                    f'  Status: {handbook.status}\n\n'
                    f'Use --force to recreate.'
                )
            )
            return

        if handbook and force:
            handbook.delete()
            self.stdout.write(self.style.WARNING('⟳ Handbook deleted (--force).'))

        # Get system user (first superuser, or first admin-level user)
        system_user = User.objects.filter(is_superuser=True).first()
        if not system_user:
            self.stdout.write(
                self.style.ERROR(
                    '✗ No superuser found.\n\n'
                    'Create one first:\n'
                    '  python manage.py createsuperuser'
                )
            )
            return

        # Create Handbook tenant
        handbook = Tenant.objects.create(
            name='The Handbook',
            slug='handbook',
            path='/global/handbook/',
            tier='handbook',
            affiliation='ichebo',
            status='active',
            is_collective=False,
            created_by=system_user,
            description='Prime tenant (singleton) containing governance knowledge: Reference Library and Mandate Branch. Level 4+ read access, Level 5 read/write access.',
            settings_data={
                'allow_public_records': False,
                'require_approval': True,
                'max_members': None
            }
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Handbook tenant created successfully:\n'
                f'  Name: {handbook.name}\n'
                f'  ID: {handbook.id}\n'
                f'  Path: {handbook.path}\n'
                f'  Tier: {handbook.tier}\n'
                f'  Status: {handbook.status}\n'
                f'  Affiliation: {handbook.affiliation}\n\n'
                f'Next: Grant yourself access via:\n'
                f'  1. Django admin: /admin/tenants/userpermission/\n'
                f'  2. Or use: python manage.py grant_handbook_access --user=<email> --level=5\n'
            )
        )
