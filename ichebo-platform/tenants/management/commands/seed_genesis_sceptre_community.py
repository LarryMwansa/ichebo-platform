"""
Seed the Genesis Sceptre Community — the default church_node tenant created
on a fresh platform so there is at least one working Church Node to
demonstrate and test against.

Per KGS §4.2.5.1 and the Sceptre Community Programme concept note Part B,
the Sceptre Community is the foundational unit of the whole movement — a
fresh platform with zero communities is a materially incomplete first-run
state. See .docs/plans/platform-bootstrap-plan.md "Doctrinal Grounding".

Usage:
    python manage.py seed_genesis_sceptre_community
    python manage.py seed_genesis_sceptre_community --force
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from tenants.models import Tenant
from accounts.models import User


class Command(BaseCommand):
    help = 'Seed the Genesis Sceptre Community — the default church_node tenant.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Delete and re-create the Genesis Sceptre Community if it already exists.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force = options['force']

        existing = Tenant.objects.filter(slug='genesis-sceptre').first()
        if existing and not force:
            self.stdout.write(self.style.WARNING(
                f'Genesis Sceptre Community already exists: {existing.path} (id={existing.id})'
            ))
            return

        if existing and force:
            existing.delete()
            self.stdout.write('  reset existing Genesis Sceptre Community')

        system_user = User.objects.filter(is_superuser=True).first()
        if not system_user:
            self.stderr.write(self.style.ERROR(
                'No superuser found. Create one first:\n  python manage.py createsuperuser'
            ))
            return

        prime = Tenant.objects.filter(slug='prime', tier='global').first()
        if not prime:
            self.stderr.write(self.style.ERROR(
                'Prime Tenancy not found. Run seed_prime_tenancy first.'
            ))
            return

        tenant = Tenant.objects.create(
            name='Genesis Sceptre Community',
            slug='genesis-sceptre',
            path='/global/genesis-sceptre/',
            tier='church_node',
            affiliation='ichebo',
            status='active',
            is_collective=False,
            is_agency=False,
            parent=prime,
            created_by=system_user,
            description=(
                'The first Sceptre Community on this platform — the foundational '
                'unit of the Kingdom Governance System movement. A demonstration '
                'and onboarding home for the first members of a fresh deployment.'
            ),
            settings_data={
                'allow_public_records': False,
                'require_approval': True,
                'max_members': None,
            },
        )

        self.stdout.write(self.style.SUCCESS(
            f'Genesis Sceptre Community created: {tenant.path} (id={tenant.id})'
        ))
