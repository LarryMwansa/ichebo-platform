"""
Bulk-create the geographic scaffold tenants (Province -> District ->
Constituency -> Ward) from a cleaned .docs/country_data/<Country>.md file.

Companion to import_geographic_tenants.py, which handles South Africa's
JSON-sourced shape (Metro/District -> Local Municipality -> places). This
command instead parses the Markdown files produced for Zambia and Zimbabwe,
whose source data never had a machine-readable JSON form. Both target the
same canonical Tenant tier vocabulary:

    continental -> regional -> national -> provincial -> district
      -> constituency -> ward

South Africa is deliberately NOT run through this command — its existing
281 tenants were imported via the JSON path and are left alone here.

Markdown shapes this parser understands (all observed in the cleaned
Zambia/Zimbabwe files, not invented — see .docs/country_data/*.md):

  1. Normal case — most of the file:
       ## <District name>
       ### <Constituency name> (N wards)
       - <Ward name> [VERIFIED: ...] / [BEST-AVAILABLE: ...]

  2. Inline bold-dash case (Zambia's Western Province only):
       ## <District name>
       **<Constituency name>** -- <ward>, <ward>, <ward>

  3. Constituency-names-only case (a district where wards couldn't be
     mapped to individual constituencies, but the constituency names
     themselves are known) — the name list is either a bullet list or a
     comma-separated paragraph, both observed:
       ### Constituencies
       <name>, <name>, <name>.
     or
       ### Constituencies
       - <name>
       - <name>

  4. Unmapped-wards case (wards known, but not which constituency each
     belongs to) — any heading containing the word "wards" that isn't a
     normal "<Name> Constituency (N wards)" heading. Wards here are filed
     under a single synthetic "Unmapped" constituency per district so the
     Ward tier — where a real congregation eventually attaches — still
     exists, rather than silently dropping the data or breaking the usual
     tier-parent convention:
       ### Wards (unmapped to individual constituency in source)
       - <ward>

Any bullet containing the literal text "GAP: not found" is real-data-shaped
but explicitly NOT real data (an unresolved gap flagged during the cleanup
pass) and is skipped rather than imported as a ward.

Idempotent on `path`, like import_geographic_tenants.py. Always dry-run
against a production restore first.

    python manage.py import_geographic_markdown ".docs/country_data/Zambia Data.md" \\
        --country-code ZM --country-name Zambia --path-segment zambia --dry-run
    python manage.py import_geographic_markdown ".docs/country_data/Zambia Data.md" \\
        --country-code ZM --country-name Zambia --path-segment zambia
"""
import re

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from tenants.models import Tenant

User = get_user_model()

GAP_MARKER = 'gap: not found'

_TAG_RE = re.compile(r"\s*`?\[(?:VERIFIED|BEST-AVAILABLE)[^\]]*\]`?\s*$", re.IGNORECASE)
_ITALIC_NOTE_RE = re.compile(r"\s*_\([^)]*\)_\s*$")
_TRAILING_PARENS_RE = re.compile(r"\s*\([^)]*\)\s*$")
_LEADING_NUMBERING_RE = re.compile(r"^\d+\.\s+")
_EM_DASH_TAIL_RE = re.compile(r"\s*[—-]{1,2}\s*[A-Z][^—]*$")
_TRAILING_CONSTITUENCY_RE = re.compile(r"\s+Constituency\s*$", re.IGNORECASE)
_INLINE_BOLD_RE = re.compile(r"^\*\*(.+?)\*\*\s*[—-]+\s*(.+)$")


def _strip_ward_annotations(text):
    text = _TAG_RE.sub('', text)
    text = _ITALIC_NOTE_RE.sub('', text)
    return text.strip()


def _clean_heading(text, *, strip_constituency_word=False):
    text = _LEADING_NUMBERING_RE.sub('', text.strip())
    # Repeatedly strip trailing parenthetical annotations, e.g.
    # "(13 wards per current reporting; 10 named)".
    while True:
        stripped = _TRAILING_PARENS_RE.sub('', text)
        if stripped == text:
            break
        text = stripped
    if strip_constituency_word:
        text = _TRAILING_CONSTITUENCY_RE.sub('', text)
    return text.strip()


class _DryRun(Exception):
    pass


class Command(BaseCommand):
    help = 'Bulk-create geographic scaffold tenants from a cleaned country Markdown file.'

    def add_arguments(self, parser):
        parser.add_argument('md_path', help='Path to the country Markdown file.')
        parser.add_argument('--country-code', required=True, help="e.g. 'ZM', 'ZW'.")
        parser.add_argument('--country-name', required=True, help="e.g. 'Zambia'.")
        parser.add_argument('--path-segment', required=True, help="e.g. 'zambia'.")
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument(
            '--author-email', default=None,
            help='User to own created tenants. Defaults to the first superuser.',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.stats = {
            'province': 0, 'district': 0, 'constituency': 0, 'ward': 0,
            'skipped_gap': 0,
        }
        self.reused = {'province': 0, 'district': 0, 'constituency': 0, 'ward': 0}

        with open(options['md_path'], encoding='utf-8') as f:
            lines = f.read().splitlines()

        if self.dry_run:
            self.stdout.write(self.style.WARNING(
                '\n  DRY RUN — every change below is rolled back at the end.\n'
            ))

        try:
            with transaction.atomic():
                self._run(lines, options)
                if self.dry_run:
                    raise _DryRun
        except _DryRun:
            self.stdout.write(self.style.WARNING('\n  Rolled back. Nothing was written.\n'))
            return

        self.stdout.write(self.style.SUCCESS('\n  Done.\n'))

    # ── top-level orchestration ─────────────────────────────────────────

    def _run(self, lines, options):
        self.author = self._resolve_author(options['author_email'])
        self.stdout.write(f'  Author: {self.author.email}')

        prime = Tenant.objects.filter(slug='prime').first()
        if prime is None:
            raise CommandError("No Tenant with slug='prime' — seed Prime Tenancy first.")

        africa = self._get_or_create(
            path='/global/africa/', name='Africa', tier='continental', parent=prime,
            stat_key=None,
        )
        country = self._get_or_create(
            path=f"/global/africa/{options['path_segment']}/",
            name=options['country_name'], tier='national', parent=africa,
            location={'country_code': options['country_code']}, stat_key=None,
        )

        self._parse(lines, country, options['path_segment'])

        self.stdout.write(
            f'\n  Created: {self.stats}\n  Reused:  {self.reused}'
        )
        self._assert_result(country)

    # ── parsing state machine ───────────────────────────────────────────

    def _parse(self, lines, country, country_segment):
        province = None
        district = None
        constituency = None          # current Tenant, wards attach here
        collecting_names = False     # inside a "### Constituencies" block
        collected_names = []

        def flush_collected_names():
            nonlocal collected_names, collecting_names
            for raw_name in collected_names:
                name = _strip_ward_annotations(raw_name)
                if not name or GAP_MARKER in raw_name.lower():
                    continue
                self._get_or_create(
                    path=f"{district.path}{slugify(name)[:190]}/",
                    name=name, tier='constituency', parent=district,
                    stat_key='constituency',
                )
            collected_names = []
            collecting_names = False

        for raw_line in lines:
            line = raw_line.rstrip()
            stripped = line.strip()

            if not stripped or stripped.startswith('>') or stripped.startswith('```'):
                continue

            # ── Province ──
            if line.startswith('# ') and not line.startswith('# Data structure'):
                if collecting_names:
                    flush_collected_names()
                name = _clean_heading(line[2:])
                province = self._get_or_create(
                    path=f"/global/africa/{country_segment}/{slugify(name)[:190]}/",
                    name=name, tier='provincial', parent=country,
                    stat_key='province',
                )
                district = None
                constituency = None
                continue

            # ── District ──
            if line.startswith('## '):
                if collecting_names:
                    flush_collected_names()
                if province is None:
                    raise CommandError(f'District heading before any Province heading: {line!r}')
                name = _clean_heading(line[3:])
                district = self._get_or_create(
                    path=f"{province.path}{slugify(name)[:190]}/",
                    name=name, tier='district', parent=province,
                    stat_key='district',
                )
                constituency = None
                continue

            # ── Constituency / Constituencies / Wards heading ──
            if line.startswith('### '):
                if collecting_names:
                    flush_collected_names()
                if district is None:
                    raise CommandError(f'Constituency heading before any District heading: {line!r}')
                raw_title = line[4:].strip()
                # Strip trailing parenthetical(s) BEFORE checking for the
                # word "ward" — otherwise a completely normal heading like
                # "Keembe Constituency (12 wards)" false-matches on the
                # word "wards" inside its own ward-count annotation.
                title_stub_lower = _clean_heading(raw_title).lower()

                if title_stub_lower.startswith('constituencies'):
                    collecting_names = True
                    collected_names = []
                    constituency = None
                    continue

                if 'ward' in title_stub_lower:
                    # Unmapped wards — file under one synthetic constituency
                    # per district so the Ward tier still exists.
                    constituency = self._get_or_create(
                        path=f"{district.path}unmapped/",
                        name='Unmapped', tier='constituency', parent=district,
                        stat_key='constituency',
                    )
                    continue

                name = _clean_heading(raw_title, strip_constituency_word=True)
                constituency = self._get_or_create(
                    path=f"{district.path}{slugify(name)[:190]}/",
                    name=name, tier='constituency', parent=district,
                    stat_key='constituency',
                )
                continue

            # ── Inline bold-dash constituency + wards (Western Province) ──
            m = _INLINE_BOLD_RE.match(stripped)
            if m and district is not None:
                if collecting_names:
                    flush_collected_names()
                cname = m.group(1).strip()
                inline_constituency = self._get_or_create(
                    path=f"{district.path}{slugify(cname)[:190]}/",
                    name=cname, tier='constituency', parent=district,
                    stat_key='constituency',
                )
                for ward_name in m.group(2).split(','):
                    ward_name = ward_name.strip().rstrip('.')
                    if not ward_name:
                        continue
                    self._get_or_create(
                        path=f"{inline_constituency.path}{slugify(ward_name)[:190]}/",
                        name=ward_name, tier='ward', parent=inline_constituency,
                        stat_key='ward',
                    )
                continue

            # ── Bullet ward, or bullet constituency-name inside a
            #    "### Constituencies" block ──
            if stripped.startswith('- '):
                content = stripped[2:].strip()
                if collecting_names:
                    collected_names.append(content)
                    continue
                if constituency is None:
                    continue  # nothing to attach this bullet to — skip rather than guess
                if GAP_MARKER in content.lower():
                    self.stats['skipped_gap'] += 1
                    continue
                name = _strip_ward_annotations(content)
                if not name:
                    self.stats['skipped_gap'] += 1
                    continue
                self._get_or_create(
                    path=f"{constituency.path}{slugify(name)[:190]}/",
                    name=name, tier='ward', parent=constituency,
                    stat_key='ward',
                )
                continue

            # ── Plain paragraph — either the comma-list body of a
            #    "### Constituencies" block, or unrelated prose to ignore ──
            if collecting_names:
                for token in stripped.rstrip('.').split(','):
                    token = token.strip()
                    if token:
                        collected_names.append(token)
                continue
            # Otherwise: unrelated prose/notes — ignored by design.

        if collecting_names:
            flush_collected_names()

    # ── tenant creation ──────────────────────────────────────────────────

    def _get_or_create(self, path, name, tier, parent, stat_key, location=None):
        existing = Tenant.objects.filter(path=path).first()
        if existing is not None:
            if stat_key:
                self.reused[stat_key] = self.reused.get(stat_key, 0) + 1
            if stat_key == 'constituency':
                self.stdout.write(f'    [debug reused constituency] {path}')
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
        if stat_key:
            self.stats[stat_key] = self.stats.get(stat_key, 0) + 1
        return tenant

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

    # ── verification ─────────────────────────────────────────────────────

    def _assert_result(self, country):
        self.stdout.write('\n  Checks')
        problems = []

        orphans = [
            t for t in Tenant.objects.filter(path__startswith=country.path).exclude(pk=country.pk)
            if t.parent is None
        ]
        if orphans:
            problems.append(f'{len(orphans)} tenant(s) under this country have no parent set')

        provinces = Tenant.objects.filter(parent=country, tier='provincial').count()
        districts = Tenant.objects.filter(path__startswith=country.path, tier='district').count()
        constituencies = Tenant.objects.filter(path__startswith=country.path, tier='constituency').count()
        wards = Tenant.objects.filter(path__startswith=country.path, tier='ward').count()

        self.stdout.write(f'    provinces: {provinces}')
        self.stdout.write(f'    districts: {districts}')
        self.stdout.write(f'    constituencies: {constituencies}')
        self.stdout.write(f'    wards: {wards}')
        self.stdout.write(f'    skipped [GAP: not found] bullets: {self.stats["skipped_gap"]}')

        if problems:
            raise CommandError('Verification failed:\n' + '\n'.join(f'    - {p}' for p in problems))
        self.stdout.write(self.style.SUCCESS('    all structural checks passed'))
