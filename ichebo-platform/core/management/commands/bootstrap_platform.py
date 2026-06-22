"""
bootstrap_platform — single idempotent entry point wrapping every manual
initialisation step a fresh Ichebo deployment currently requires by hand.

See .docs/plans/platform-bootstrap-plan.md for the full specification.

Usage:
    python manage.py bootstrap_platform
    python manage.py bootstrap_platform --dry-run
    python manage.py bootstrap_platform --quiet
    python manage.py bootstrap_platform --force
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

OK = '✅'
WARN = '⚠️ '
FAIL = '❌'


class Command(BaseCommand):
    help = (
        'Idempotent platform bootstrap — wraps every manual seed/init step a '
        'fresh deployment currently requires by hand. Safe to re-run.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Print what would be done without writing anything.',
        )
        parser.add_argument(
            '--quiet', action='store_true',
            help='Only print warnings and errors.',
        )
        parser.add_argument(
            '--force', action='store_true',
            help='Re-run steps even if already complete (for repair scenarios). '
                 'Passed through to the wrapped seed commands that support it.',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.quiet = options['quiet']
        self.force = options['force']
        self.warnings = 0
        self.errors = 0

        self._line('Ichebo Platform Bootstrap')
        self._line('=========================')

        self._step_migrations()
        superuser = self._step_superuser()
        if not superuser:
            self._line('')
            self._line(self.style.ERROR(
                'Bootstrap halted — every remaining step requires a superuser to exist.'
            ))
            return

        self._step_handbook_tenant()
        self._step_induction_tenant()
        self._step_prime_and_agencies()
        self._step_service_orders()
        self._step_handbook_access()
        self._step_induction_backfill()
        self._step_qualification_programmes()
        self._step_genesis_sceptre_community()
        self._step_catalogue_report()

        if not self.dry_run and not self.errors:
            self._mark_bootstrapped(superuser)

        self._line('')
        if self.errors:
            self._line(self.style.ERROR(
                f'Bootstrap incomplete — {self.errors} error(s), {self.warnings} warning(s).'
            ))
        elif self.warnings:
            self._line(self.style.WARNING(
                f'Bootstrap complete. {self.warnings} warning(s) require manual action.'
            ))
        else:
            self._line(self.style.SUCCESS('Bootstrap complete. 0 warnings.'))

    # ── Output helpers ───────────────────────────────────────────────────────

    def _line(self, msg=''):
        if self.quiet and not msg.startswith(('⚠️', '❌')) and msg not in ('', 'Ichebo Platform Bootstrap', '========================='):
            return
        self.stdout.write(msg)

    def _ok(self, msg):
        self._line(f'{OK}  {msg}')

    def _warn(self, msg, hint=None):
        self.warnings += 1
        self.stdout.write(self.style.WARNING(f'{WARN} {msg}'))
        if hint:
            self.stdout.write(f'     → {hint}')

    def _fail(self, msg, hint=None):
        self.errors += 1
        self.stdout.write(self.style.ERROR(f'{FAIL}  {msg}'))
        if hint:
            self.stdout.write(f'     → {hint}')

    # ── Step 1 — migrations ──────────────────────────────────────────────────

    def _step_migrations(self):
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan:
            self._fail(
                f'Migrations — {len(plan)} pending',
                'Run: python manage.py migrate',
            )
        else:
            applied = len(executor.loader.applied_migrations)
            self._ok(f'Migrations — current ({applied} applied)')

    # ── Step 2 — superuser ───────────────────────────────────────────────────

    def _step_superuser(self):
        from accounts.models import User
        su = User.objects.filter(is_superuser=True).first()
        if not su:
            self._fail(
                'Superuser — none found',
                'Run: python manage.py createsuperuser',
            )
            return None
        self._ok(f'Superuser — found ({su.email})')
        return su

    # ── Step 3 — Handbook tenant ─────────────────────────────────────────────

    def _step_handbook_tenant(self):
        from tenants.models import Tenant
        existing = Tenant.objects.filter(tier='handbook').first()
        if existing:
            self._ok(f'Handbook tenant — exists at {existing.path}')
            return
        if self.dry_run:
            self._warn('Handbook tenant — would create (dry-run)')
            return
        call_command('create_handbook', verbosity=0)
        existing = Tenant.objects.filter(tier='handbook').first()
        if existing:
            self._ok(f'Handbook tenant — created at {existing.path}')
        else:
            self._fail('Handbook tenant — creation failed', 'Run create_handbook manually to see the error')

    # ── Step 4 — Induction tenant ────────────────────────────────────────────

    def _step_induction_tenant(self):
        from tenants.models import Tenant
        existing = Tenant.objects.filter(tier='induction', slug='induction').first()
        if existing:
            self._ok(f'Induction tenant — exists at {existing.path}')
            return
        if self.dry_run:
            self._warn('Induction tenant — would create (dry-run)')
            return
        call_command('seed_induction_tenant', verbosity=0)
        existing = Tenant.objects.filter(tier='induction', slug='induction').first()
        if existing:
            self._ok(f'Induction tenant — created at {existing.path}')
        else:
            self._fail('Induction tenant — creation failed', 'Run seed_induction_tenant manually to see the error')

    # ── Step 5 — Prime tenancy + 6 agencies ─────────────────────────────────

    def _step_prime_and_agencies(self):
        from tenants.models import Tenant
        prime_exists = Tenant.objects.filter(tier='global', slug='prime').exists()
        agency_count = Tenant.objects.filter(tier='global', is_agency=True).exclude(slug='prime').count()
        if prime_exists and agency_count >= 6:
            self._ok('Prime tenancy + 6 agencies — exist')
            return
        if self.dry_run:
            self._warn('Prime tenancy + agencies — would create (dry-run)')
            return
        call_command('seed_prime_tenancy', verbosity=0)
        prime_exists = Tenant.objects.filter(tier='global', slug='prime').exists()
        agency_count = Tenant.objects.filter(tier='global', is_agency=True).exclude(slug='prime').count()
        if prime_exists and agency_count >= 6:
            self._ok(f'Prime tenancy + {agency_count} agencies — created')
        else:
            self._fail('Prime tenancy / agencies — incomplete after seeding', 'Run seed_prime_tenancy manually to see the error')

    # ── Step 6 — 24 Service Orders ───────────────────────────────────────────

    def _step_service_orders(self):
        from tenants.models import ServiceOrder
        count = ServiceOrder.objects.count()
        if count >= 24:
            self._ok(f'Service Orders — {count} seeded')
            return
        if self.dry_run:
            self._warn(f'Service Orders — would seed (currently {count}/24, dry-run)')
            return
        call_command('seed_service_orders', verbosity=0)
        count = ServiceOrder.objects.count()
        if count >= 24:
            self._ok(f'Service Orders — {count} seeded')
        else:
            self._fail(f'Service Orders — only {count}/24 after seeding', 'Run seed_service_orders manually to see the error')

    # ── Step 7 — Handbook access for existing Level 5 / superusers ──────────
    #
    # grant_handbook_access requires a specific --user email — it is not a
    # bulk command. bootstrap_platform grants directly via UserPermission
    # rather than shelling out per-user, since the set of recipients (every
    # existing Level 5 user or superuser) is exactly what this step needs.

    def _step_handbook_access(self):
        from accounts.models import User
        from tenants.models import Tenant, UserPermission

        handbook = Tenant.objects.filter(tier='handbook').first()
        if not handbook:
            self._warn('Handbook access — skipped, Handbook tenant does not exist yet')
            return

        recipients = User.objects.filter(is_superuser=True) | User.objects.filter(competence_level__gte=5)
        recipients = recipients.distinct()

        if not recipients.exists():
            self._warn('Handbook access — no Level 5 users or superusers found to grant')
            return

        if self.dry_run:
            self._warn(f'Handbook access — would check/grant for {recipients.count()} user(s) (dry-run)')
            return

        granted = 0
        for user in recipients:
            _, created = UserPermission.objects.get_or_create(
                user=user, tenant=handbook, role='global-steward',
                defaults={
                    'created_by': user, 'granted_by': user,
                    'tenant_path': handbook.path, 'level': 5, 'is_active': True,
                },
            )
            if created:
                granted += 1

        total = UserPermission.objects.filter(tenant=handbook, is_active=True).count()
        self._ok(f'Handbook access — granted to {granted} new user(s), {total} total with access')

    # ── Step 8 — backfill Level 0 users into induction ───────────────────────

    def _step_induction_backfill(self):
        from accounts.models import User
        from tenants.models import Tenant, UserPermission

        induction = Tenant.objects.filter(tier='induction', slug='induction').first()
        if not induction:
            self._warn('Induction backfill — skipped, Induction tenant does not exist yet')
            return

        unplaced = User.objects.filter(competence_level=0).exclude(
            tenant_permissions__tenant=induction, tenant_permissions__is_active=True,
        ).count()

        if unplaced == 0:
            self._ok('Induction backfill — all Level 0 users already placed')
            return

        if self.dry_run:
            self._warn(f'Induction backfill — would place {unplaced} user(s) (dry-run)')
            return

        call_command('backfill_induction_placement', verbosity=0)
        still_unplaced = User.objects.filter(competence_level=0).exclude(
            tenant_permissions__tenant=induction, tenant_permissions__is_active=True,
        ).count()
        placed = unplaced - still_unplaced
        self._ok(f'Induction backfill — {placed} user(s) placed')

    # ── Step 9 — 6 Qualification Programmes ──────────────────────────────────
    #
    # Real dependency order, not documented in the original plan's scope
    # table: seed_programmes (the 5 Level 1-5 programmes) must run before
    # seed_induction_course (links "Induction Training" into New Life
    # Programme), which must run before seed_induction_programme (creates
    # the Level 0 container and re-links the course onto it). Running
    # seed_induction_programme first produces a programme with no courses.

    def _step_qualification_programmes(self):
        from records.models import Record

        programme_count = Record.objects.filter(
            record_family='learning', record_type__in=['induction', 'programme'],
            origin='system', deleted_at__isnull=True,
        ).count()
        if programme_count >= 6:
            self._ok(f'Qualification Programmes — {programme_count} seeded (Induction → Architect\'s)')
            return

        if self.dry_run:
            self._warn(f'Qualification Programmes — would seed (currently {programme_count}/6, dry-run)')
            return

        call_command('seed_programmes', verbosity=0)
        call_command('seed_induction_course', verbosity=0)
        call_command('seed_induction_programme', verbosity=0)

        programme_count = Record.objects.filter(
            record_family='learning', record_type__in=['induction', 'programme'],
            origin='system', deleted_at__isnull=True,
        ).count()
        if programme_count >= 6:
            self._ok(f'Qualification Programmes — {programme_count} seeded (Induction → Architect\'s)')
        else:
            self._fail(
                f'Qualification Programmes — only {programme_count}/6 after seeding',
                'Run seed_programmes, seed_induction_course, seed_induction_programme manually to see the error',
            )

    # ── Step 10 — Genesis Sceptre Community ──────────────────────────────────

    def _step_genesis_sceptre_community(self):
        from tenants.models import Tenant
        existing = Tenant.objects.filter(tier='church_node', slug='genesis-sceptre').first()
        if existing:
            self._ok(f'Genesis Sceptre Community — exists at {existing.path}')
            return
        if self.dry_run:
            self._warn('Genesis Sceptre Community — would create (dry-run)')
            return
        call_command('seed_genesis_sceptre_community', verbosity=0)
        existing = Tenant.objects.filter(tier='church_node', slug='genesis-sceptre').first()
        if existing:
            self._ok(f'Genesis Sceptre Community — created at {existing.path}')
        else:
            self._fail(
                'Genesis Sceptre Community — creation failed',
                'Run seed_genesis_sceptre_community manually to see the error '
                '(requires Prime Tenancy — step 5 — to exist first)',
            )

    # ── Step 11 — catalogue report (report-only, never automated) ──────────

    def _step_catalogue_report(self):
        from records.models import Record
        total_active = Record.objects.filter(
            record_family='learning', record_type='programme',
            status='active', deleted_at__isnull=True,
        ).count()
        if total_active > 5:  # 5 seeded Level 1-5 programmes; induction is record_type='induction'
            self._ok(f'Programme catalogue — {total_active} programmes (beyond the 5 seeded)')
        else:
            self._warn(
                'Programme catalogue — only the seeded programmes exist',
                'Log in as Level 5 and go to /learn/author/ to add more',
            )

    # ── Bootstrap marker — written last, only on a real (non-dry-run) run ───

    def _mark_bootstrapped(self, by_user):
        from core.models import PlatformConfig
        cfg = PlatformConfig.get_solo()
        if not cfg.bootstrapped_at:
            cfg.bootstrapped_at = timezone.now()
            cfg.bootstrapped_by = by_user
            cfg.bootstrap_version = '1.0'
            cfg.save(update_fields=['bootstrapped_at', 'bootstrapped_by', 'bootstrap_version'])
