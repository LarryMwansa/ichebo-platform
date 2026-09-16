"""
Create the Ward tier for South Africa from place-name data that's already
sitting in the database — import_geographic_tenants.py stored each Metro's
and Local Municipality's informal place list in Tenant.location['places']
at import time (see that command's _import_province), but never turned
those into actual Ward-tier Tenant rows. This command closes that gap.

No parsing needed: just walk every South Africa district/constituency
tenant that has a location['places'] list and get_or_create a Ward child
per place name.

Idempotent on `path`, like the other geographic importers. Always dry-run
against a production restore first.

    python manage.py import_south_africa_wards --dry-run
    python manage.py import_south_africa_wards
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from tenants.models import Tenant

User = get_user_model()


class _DryRun(Exception):
    pass


class Command(BaseCommand):
    help = "Create Ward-tier tenants for South Africa from each parent's stored location['places'] list."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument(
            '--author-email', default=None,
            help='User to own created tenants. Defaults to the first superuser.',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']

        if self.dry_run:
            self.stdout.write(self.style.WARNING(
                '\n  DRY RUN — every change below is rolled back at the end.\n'
            ))

        try:
            with transaction.atomic():
                self._run(options)
                if self.dry_run:
                    raise _DryRun
        except _DryRun:
            self.stdout.write(self.style.WARNING('\n  Rolled back. Nothing was written.\n'))
            return

        self.stdout.write(self.style.SUCCESS('\n  Done.\n'))

    def _run(self, options):
        self.author = self._resolve_author(options['author_email'])
        self.stdout.write(f'  Author: {self.author.email}')

        country = Tenant.objects.filter(path='/global/africa/southafrica/').first()
        if country is None:
            raise CommandError("No South Africa country Tenant at path '/global/africa/southafrica/' — import the base scaffold first.")

        parents = list(
            Tenant.objects.filter(path__startswith=country.path, location__has_key='places')
            .exclude(tier='ward')
        )
        self.stdout.write(f'  Parents with a places list: {len(parents)}')

        created = 0
        reused = 0
        empty_lists = 0

        for parent in parents:
            places = parent.location.get('places') or []
            if not places:
                empty_lists += 1
                continue
            for place in places:
                name = place.strip()
                if not name:
                    continue
                path = f"{parent.path}{slugify(name)[:190]}/"
                existing = Tenant.objects.filter(path=path).first()
                if existing is not None:
                    reused += 1
                    continue
                Tenant.objects.create(
                    created_by=self.author,
                    parent=parent,
                    name=name,
                    slug=self._unique_slug(path),
                    path=path,
                    tier='ward',
                    status='active',
                )
                created += 1

        self.stdout.write(f'  Wards created: {created}')
        self.stdout.write(f'  Wards reused (already existed): {reused}')
        self.stdout.write(f'  Parents with an empty places list: {empty_lists}')

        self._assert_result(country)

    def _unique_slug(self, path):
        candidate = slugify(path.strip('/').replace('/', '-'))[:200]
        if not Tenant.objects.filter(slug=candidate).exists():
            return candidate
        suffix = 1
        base = candidate[:190]
        while Tenant.objects.filter(slug=f'{base}-{suffix}').exists():
            suffix += 1
        return f'{base}-{suffix}'

    def _resolve_author(self, email):
        if email:
            try:
                return User.objects.get(email=email)
            except User.DoesNotExist:
                raise CommandError(f'No user with email {email!r}.')
        author = User.objects.filter(is_superuser=True).first()
        if author is None:
            raise CommandError('No superuser found — pass --author-email.')
        return author

    def _assert_result(self, country):
        self.stdout.write('\n  Checks')
        problems = []

        orphans = [
            t for t in Tenant.objects.filter(path__startswith=country.path, tier='ward')
            if t.parent is None
        ]
        if orphans:
            problems.append(f'{len(orphans)} ward tenant(s) have no parent set')

        total_wards = Tenant.objects.filter(path__startswith=country.path, tier='ward').count()
        self.stdout.write(f'    total ward-tier tenants under South Africa: {total_wards}')

        if problems:
            raise CommandError('Verification failed:\n' + '\n'.join(f'    - {p}' for p in problems))
        self.stdout.write(self.style.SUCCESS('    all structural checks passed'))
