"""
Bulk-create the geographic scaffold tenants (Country -> Province ->
District/Metro -> Local -> Ward) from an Ichebo Sceptre geographic dataset
JSON file.

Currently handles South Africa's shape only:

    country
      province
        metro                          (leaf; wards attach directly later)
        district
          local  (South Africa: "Local Municipality")

Zambia and Zimbabwe are NOT supported by this command yet. Both have a
structurally different shape — District and the tier-4 node (Constituency)
are siblings under Province rather than parent/child, and roughly 15-25% of
them collide on name within a province (e.g. "Chisamba District" and
"Chisamba Constituency" both resolve to the same path). That needs a source
data decision, not an importer change, before it can run safely. Re-check
this docstring and CURRICULUM SHAPE assumptions before pointing this command
at either file.

Tier mapping (five canonical tiers, reused across every country regardless
of local terminology — see tenants.models.Tenant.TIER_CHOICES):

    country  -> national
    province -> provincial
    district -> district
    metro    -> local   (a Metro has no Local Municipality under it; it
                          plays the same ward-parent role a Local does)
    local municipality -> local
    ward     -> not created yet; every country's ward data is placeholder
                only (verified against all three source files 2026-08-19)

Idempotent on `path` — re-running with the same input creates nothing new.
Always dry-run against a production restore first.

    python manage.py import_geographic_tenants data/sceptre-geographic-dataset-south-africa.json --dry-run
    python manage.py import_geographic_tenants data/sceptre-geographic-dataset-south-africa.json
"""
import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from tenants.models import Tenant

User = get_user_model()

# tier_level string (as it appears in the JSON) -> canonical Tenant.tier value
TIER_LEVEL_MAP = {
    'district': 'district',
    'local_municipality': 'local',
    'metro': 'local',
}


class _DryRun(Exception):
    pass


class Command(BaseCommand):
    help = 'Bulk-create geographic scaffold tenants from a Sceptre geographic dataset JSON file.'

    def add_arguments(self, parser):
        parser.add_argument('json_path', help='Path to the country JSON file.')
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument(
            '--author-email', default=None,
            help='User to own created tenants. Defaults to the first superuser.',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.created = {'continent': 0, 'country': 0, 'province': 0, 'metro': 0, 'district': 0, 'local': 0}
        self.reused = {'continent': 0, 'country': 0, 'province': 0, 'metro': 0, 'district': 0, 'local': 0}

        with open(options['json_path']) as f:
            data = json.load(f)

        if data.get('country_code') != 'ZA':
            raise CommandError(
                f"This command only supports South Africa's shape right now "
                f"(country_code 'ZA'); got {data.get('country_code')!r}. "
                f"Zambia and Zimbabwe need their district/constituency shape "
                f"resolved first — see this command's module docstring."
            )

        if self.dry_run:
            self.stdout.write(self.style.WARNING(
                '\n  DRY RUN — every change below is rolled back at the end.\n'
            ))

        try:
            with transaction.atomic():
                self._run(data, options)
                if self.dry_run:
                    raise _DryRun
        except _DryRun:
            self.stdout.write(self.style.WARNING('\n  Rolled back. Nothing was written.\n'))
            return

        self.stdout.write(self.style.SUCCESS('\n  Done.\n'))

    def _run(self, data, options):
        self.author = self._resolve_author(options['author_email'])
        self.stdout.write(f'  Author: {self.author.email}')

        prime = Tenant.objects.filter(slug='prime').first()
        if prime is None:
            raise CommandError("No Tenant with slug='prime' — seed Prime Tenancy first.")

        africa = self._get_or_create(
            path='/global/africa/', name='Africa', tier='continental', parent=prime,
        )

        country = self._get_or_create(
            path=f"/global/africa/{data['path_segment']}/",
            name=data['country'], tier='national', parent=africa,
            location={'country_code': data['country_code']},
        )

        self.stdout.write(f'\n  Provinces ({len(data["provinces"])})')
        for prov in data['provinces']:
            self._import_province(prov, country, data['path_segment'])

        self.stdout.write(
            f'\n  Created: {self.created}\n  Reused:  {self.reused}'
        )
        self._assert_result(data, country)

    # ── tree building ────────────────────────────────────────────────────

    def _import_province(self, prov, country, country_segment):
        prov_path = f"/global/africa/{country_segment}/{prov['path_segment']}/"
        province = self._get_or_create(
            path=prov_path, name=prov['province'], tier='provincial', parent=country,
        )

        metros = prov.get('metros', [])
        districts = prov.get('districts', [])
        self.stdout.write(
            f'    {prov["province"]}: {len(metros)} metro(s), {len(districts)} district(s)'
        )

        for metro in metros:
            self._get_or_create(
                path=metro['path'], name=metro['name'], tier=self._tier_for(metro),
                parent=province,
                location={'seat': metro.get('seat'), 'places': metro.get('places', [])},
            )

        for dist in districts:
            district_tenant = self._get_or_create(
                path=dist['path'], name=dist['name'], tier=self._tier_for(dist),
                parent=province,
                location={'seat': dist.get('seat')},
            )
            for local in dist.get('locals', []):
                self._get_or_create(
                    path=local['path'], name=local['name'], tier=self._tier_for(local),
                    parent=district_tenant,
                    location={'places': local.get('places', [])},
                )

    def _tier_for(self, node):
        raw = node.get('tier_level')
        tier = TIER_LEVEL_MAP.get(raw)
        if tier is None:
            raise CommandError(
                f"Unrecognised tier_level {raw!r} on {node.get('name')!r} — "
                f"add it to TIER_LEVEL_MAP before importing."
            )
        return tier

    def _get_or_create(self, path, name, tier, parent, location=None):
        existing = Tenant.objects.filter(path=path).first()
        key = {
            'continental': 'continent', 'national': 'country', 'provincial': 'province',
        }.get(tier, tier)  # 'local' bucket covers both metro and local_municipality

        if existing is not None:
            self.reused[key] = self.reused.get(key, 0) + 1
            return existing

        tenant = Tenant.objects.create(
            created_by=self.author,
            parent=parent,
            name=name,
            slug=self._unique_slug(path),
            path=path,
            tier=tier,
            status='active',
            location=location or {},
        )
        self.created[key] = self.created.get(key, 0) + 1
        return tenant

    def _unique_slug(self, path):
        """Derive a globally-unique slug from the path itself.

        The path is already guaranteed unique (that's what we key creation
        on), so deriving the slug from it — rather than from the bare name —
        means slugs never collide even when two provinces have same-named
        children, without needing a numeric-suffix fallback loop.
        """
        from django.utils.text import slugify
        candidate = slugify(path.strip('/').replace('/', '-'))[:200]
        if not Tenant.objects.filter(slug=candidate).exists():
            return candidate
        # Path collision would mean a get_or_create hit above already, so
        # this only fires if some unrelated tenant already used this exact
        # slug — extremely unlikely, but stay safe rather than crash.
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

    # ── verification ─────────────────────────────────────────────────────

    def _assert_result(self, data, country):
        self.stdout.write('\n  Checks')
        problems = []

        expected_provinces = len(data['provinces'])
        expected_metros = sum(len(p.get('metros', [])) for p in data['provinces'])
        expected_districts = sum(len(p.get('districts', [])) for p in data['provinces'])
        expected_locals = sum(
            len(d.get('locals', []))
            for p in data['provinces'] for d in p.get('districts', [])
        )

        actual_provinces = Tenant.objects.filter(parent=country, tier='provincial').count()
        actual_geo = Tenant.objects.filter(
            path__startswith=country.path, tier='local',
        ).count()
        actual_districts = Tenant.objects.filter(
            path__startswith=country.path, tier='district',
        ).count()

        if actual_provinces != expected_provinces:
            problems.append(f'expected {expected_provinces} provinces, found {actual_provinces}')
        if actual_districts != expected_districts:
            problems.append(f'expected {expected_districts} districts, found {actual_districts}')
        if actual_geo != expected_metros + expected_locals:
            problems.append(
                f'expected {expected_metros} metros + {expected_locals} locals '
                f'= {expected_metros + expected_locals} local-tier tenants, found {actual_geo}'
            )

        # Every non-root node under this country must resolve its parent
        # chain back to the country with no gaps.
        orphans = [
            t for t in Tenant.objects.filter(path__startswith=country.path).exclude(pk=country.pk)
            if t.parent is None
        ]
        if orphans:
            problems.append(f'{len(orphans)} tenant(s) under this country have no parent set')

        self.stdout.write(f'    provinces: {actual_provinces} (expected {expected_provinces})')
        self.stdout.write(f'    districts: {actual_districts} (expected {expected_districts})')
        self.stdout.write(
            f'    local-tier (metro+local): {actual_geo} '
            f'(expected {expected_metros + expected_locals})'
        )

        if problems:
            raise CommandError('Verification failed:\n' + '\n'.join(f'    - {p}' for p in problems))
        self.stdout.write(self.style.SUCCESS('    all checks passed'))
