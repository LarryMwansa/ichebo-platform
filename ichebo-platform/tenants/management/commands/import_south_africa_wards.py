"""
Create the Ward tier for South Africa by parsing the place-name data in
.docs/country_data/South Africa Data.md directly.

An earlier version of this command read Tenant.location['places'], which
import_geographic_tenants.py populates at import time — but that field
turned out to only be populated for Eastern Cape (6 tenants, 29 places);
the rest of the country's place data was apparently never carried from the
source doc into the JSON that command reads. This version parses the
Markdown source directly instead, since that's what's actually complete.

The source doc's heading levels are NOT consistent country-wide (Eastern
Cape nests Province > ## section-label > ### District > #### Local; Free
State and others flatten District and Local to the same '##' level; Gauteng
mixes both). Rather than replicate every province's specific heading-level
scheme, this parser sidesteps the inconsistency entirely: for ANY heading
(level 2-4), it collects the plain-text lines that follow (until the next
heading, a '---' rule, or EOF) as a candidate place list, and tries to
match the heading's name against an already-existing Tenant (District or
Constituency tier) under the current Province.

That still leaves one ambiguity the doc itself contains: some "candidate
place lists" are not places at all — e.g. under Free State's Fezile Dabi
District, the lines "Mafube Local" / "Metsimaholo Local" / ... are that
district's own child Local Municipalities (already real Tenants), listed
bare with no actual place-level data, not genuine wards. Distinguish the
two by checking each candidate item against the set of already-known
Tenant names under South Africa: an item that resolves to an existing
tenant is a structural cross-reference and is skipped; only genuinely new
names become Ward tenants.

Idempotent on `path`, like the other geographic importers. Always dry-run
against a production restore first.

    python manage.py import_south_africa_wards --dry-run
    python manage.py import_south_africa_wards
"""
import re

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from tenants.models import Tenant

User = get_user_model()

# Doc heading text -> actual Tenant.name for South Africa's 9 provinces.
# Small and fixed, so hand-mapped rather than fuzzy-matched — the doc has
# both a spelling variant ("Mpumulanga" vs "Mpumalanga") and a shortened
# name ("KwaZulu" vs "KwaZulu-Natal") that a naive normalizer would miss.
PROVINCE_NAME_MAP = {
    'eastern cape': 'Eastern Cape',
    'free state': 'Free State',
    'gauteng': 'Gauteng',
    'kwazulu': 'KwaZulu-Natal',
    'limpopo': 'Limpopo',
    'mpumulanga': 'Mpumalanga',
    'mpumalanga': 'Mpumalanga',
    'north-west': 'North West',
    'north west': 'North West',
    'northern cape': 'Northern Cape',
    'western cape': 'Western Cape',
}

_SUFFIX_WORDS = {'local', 'metropolitan', 'municipality', 'municipalities', 'district'}


def _normalize(name):
    """Lowercase, strip punctuation, drop generic tier-designation words —
    so 'Buffalo City Metropolitan' and 'Buffalo City Metropolitan
    Municipality' compare equal, and 'Mafube Local' matches the existing
    'Mafube Local Municipality' tenant so it can be filtered out as a
    structural reference rather than invented as a fake ward."""
    words = re.sub(r'[^a-z0-9\s]', ' ', name.lower()).split()
    core = [w for w in words if w not in _SUFFIX_WORDS]
    return ' '.join(core).strip()


class _DryRun(Exception):
    pass


class Command(BaseCommand):
    help = "Create Ward-tier tenants for South Africa by parsing .docs/country_data/South Africa Data.md."

    def add_arguments(self, parser):
        parser.add_argument(
            '--md-path', default='.docs/country_data/South Africa Data.md',
            help='Path to the South Africa Markdown source file.',
        )
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

        # Build the "already a real tenant" lookup up front, so structural
        # cross-references (a district heading whose body is just its own
        # locals' bare names) can be recognised and skipped.
        self.known_names = {
            _normalize(t.name) for t in Tenant.objects.filter(path__startswith=country.path)
        }

        provinces = {p.name: p for p in Tenant.objects.filter(parent=country, tier='provincial')}

        with open(options['md_path'], encoding='utf-8') as f:
            lines = f.read().splitlines()

        self.created = 0
        self.reused = 0
        self.no_parent_match = []
        self.ambiguous_match = []
        self.skipped_structural = 0

        self._parse(lines, country, provinces)

        self.stdout.write(f'  Wards created: {self.created}')
        self.stdout.write(f'  Wards reused (already existed): {self.reused}')
        self.stdout.write(f'  Items skipped as structural cross-references: {self.skipped_structural}')
        self.stdout.write(f'  Headings with no matching parent tenant: {len(self.no_parent_match)}')
        for h in self.no_parent_match[:20]:
            self.stdout.write(f'    - {h}')
        self.stdout.write(f'  Headings matching >1 parent tenant (skipped, unresolved): {len(self.ambiguous_match)}')
        for h in self.ambiguous_match[:20]:
            self.stdout.write(f'    - {h}')

        self._assert_result(country)

    # ── parsing ──────────────────────────────────────────────────────────

    def _parse(self, lines, country, provinces):
        current_province_tenant = None
        pending_heading = None  # raw heading text awaiting its body lines
        pending_body = []

        def flush():
            nonlocal pending_heading, pending_body
            if pending_heading is not None and pending_body:
                self._handle_candidate(pending_heading, pending_body, current_province_tenant)
            pending_heading = None
            pending_body = []

        for raw_line in lines:
            line = raw_line.rstrip()
            stripped = line.strip()

            if stripped == '---':
                flush()
                continue

            if line.startswith('# ') and not line.startswith('# Data structure') and not line.startswith('# South Africa Data List'):
                flush()
                heading = line[2:].strip()
                key = _normalize(heading.replace('Province', '').strip())
                mapped_name = PROVINCE_NAME_MAP.get(key)
                current_province_tenant = provinces.get(mapped_name) if mapped_name else None
                if current_province_tenant is None:
                    self.stdout.write(self.style.WARNING(f'  [warn] no province match for heading {heading!r}'))
                continue

            if line.startswith('##'):
                flush()
                heading = re.sub(r'^#+\s*', '', line).strip()
                pending_heading = heading
                pending_body = []
                continue

            if not stripped:
                continue

            if pending_heading is not None:
                pending_body.append(stripped)

        flush()

    def _handle_candidate(self, heading_text, body_lines, province_tenant):
        # Section-label headings ("Metropolitan municipalities:",
        # "District Municipalities") never carry a body of their own —
        # their content is the next-level headings — but guard anyway.
        if heading_text.rstrip(':').strip().lower() in ('metropolitan municipalities', 'district municipalities'):
            return
        if province_tenant is None:
            return

        parent = self._match_parent(heading_text, province_tenant)
        if parent is None:
            self.no_parent_match.append(f'{province_tenant.name} / {heading_text}')
            return

        # Body lines may be one comma-separated line, several such lines,
        # or several bare one-name-per-line entries — flatten to one list
        # of candidate items regardless of which shape it is.
        items = []
        for body_line in body_lines:
            items.extend(part.strip() for part in body_line.split(','))

        for item in items:
            item = item.strip().rstrip('.')
            if not item:
                continue
            if _normalize(item) in self.known_names:
                self.skipped_structural += 1
                continue
            self._create_ward(parent, item)

    def _match_parent(self, heading_text, province_tenant):
        target = _normalize(heading_text)
        if not target:
            return None
        candidates = Tenant.objects.filter(
            path__startswith=province_tenant.path, tier__in=['district', 'constituency'],
        )
        matches = [t for t in candidates if _normalize(t.name) == target]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            self.ambiguous_match.append(f'{province_tenant.name} / {heading_text} ({len(matches)} matches)')
        return None

    def _create_ward(self, parent, name):
        path = f"{parent.path}{slugify(name)[:190]}/"
        existing = Tenant.objects.filter(path=path).first()
        if existing is not None:
            self.reused += 1
            return
        Tenant.objects.create(
            created_by=self.author,
            parent=parent,
            name=name,
            slug=self._unique_slug(path),
            path=path,
            tier='ward',
            status='active',
        )
        self.created += 1
        self.known_names.add(_normalize(name))

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
