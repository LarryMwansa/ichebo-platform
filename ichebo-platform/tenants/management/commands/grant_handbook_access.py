from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from tenants.models import Tenant, UserPermission
from handbook.models import HandbookAccess
from accounts.models import User


# HandbookAccess.role is ranked so re-running this command for an existing
# user can detect an upgrade (e.g. reader -> author) vs. a no-op.
HANDBOOK_ACCESS_RANK = {
    HandbookAccess.ROLE_READER: 1,
    HandbookAccess.ROLE_AUTHOR: 2,
    HandbookAccess.ROLE_EDITOR: 3,
}

# --level (3/4/5) -> HandbookAccess.role. Per the model's own doc comments:
# Level 3-4 = reader (read all governance records incl. drafts), Level 5 =
# author (write governance records). `editor` ("manage access") is not
# level-derived — it's an explicit elevation, requested via --handbook-role.
LEVEL_TO_HANDBOOK_ROLE = {
    3: HandbookAccess.ROLE_READER,
    4: HandbookAccess.ROLE_READER,
    5: HandbookAccess.ROLE_AUTHOR,
}


class Command(BaseCommand):
    help = (
        'Grant a user access to the Handbook (Prime Tenant) at Level 3, 4, or 5. '
        'Creates both the tenant-scoped UserPermission (governs /governance/ and '
        'general tenant-level access) and the HandbookAccess row (governs the '
        '/handbook/ authorship workspace itself) — these are two independent '
        'models and both are required for full access.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            required=True,
            help='Email address of the user to grant access'
        )
        parser.add_argument(
            '--level',
            type=int,
            default=5,
            choices=[3, 4, 5],
            help='Access level (3=read ref library, 4=read all, 5=full write) [default: 5]'
        )
        parser.add_argument(
            '--role',
            type=str,
            default=None,
            help='Custom UserPermission role (defaults to global-steward for level 5, '
                 'district-steward for level 4, branch-steward for level 3)'
        )
        parser.add_argument(
            '--handbook-role',
            type=str,
            default=None,
            choices=[HandbookAccess.ROLE_READER, HandbookAccess.ROLE_AUTHOR, HandbookAccess.ROLE_EDITOR],
            help='Custom HandbookAccess role (defaults to reader for level 3/4, author for '
                 'level 5). Use this to grant "editor" — manage-access rights beyond what '
                 '--level alone implies.'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        user_email = options.get('user')
        level = options.get('level')
        custom_role = options.get('role')
        custom_handbook_role = options.get('handbook_role')

        # Get the user
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            raise CommandError(f'✗ User not found: {user_email}')

        # Get the Handbook
        try:
            handbook = Tenant.objects.get(path='/global/handbook/', tier='handbook')
        except Tenant.DoesNotExist:
            raise CommandError(
                '✗ Handbook tenant does not exist.\n\n'
                'Create it first:\n'
                '  python manage.py create_handbook'
            )

        self._grant_user_permission(user, handbook, level, custom_role)
        self._grant_handbook_access(user, level, custom_handbook_role)

    def _grant_user_permission(self, user, handbook, level, custom_role):
        role_map = {
            3: 'branch-steward',
            4: 'district-steward',
            5: 'global-steward',
        }
        role = custom_role or role_map[level]

        existing = UserPermission.objects.filter(
            user=user,
            tenant=handbook,
            role=role,
        ).first()

        if existing:
            self.stdout.write(
                self.style.WARNING(
                    f'ℹ UserPermission already exists: {existing.role} (level {existing.level})'
                )
            )
            return

        perm = UserPermission.objects.create(
            user=user,
            tenant=handbook,
            role=role,
            level=level,
            tenant_path=handbook.path,
            created_by=user,  # Self-granted
            granted_by=user,
        )

        access_desc = {
            3: 'Reference Library (read-only)',
            4: 'All types (read-only)',
            5: 'All types (read + write)',
        }
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ UserPermission granted: {perm.role} (level {perm.level}) — '
                f'{access_desc[level]} via /governance/'
            )
        )

    def _grant_handbook_access(self, user, level, custom_handbook_role):
        handbook_role = custom_handbook_role or LEVEL_TO_HANDBOOK_ROLE[level]

        existing = HandbookAccess.objects.filter(user=user).first()

        if existing is None:
            HandbookAccess.objects.create(
                user=user,
                role=handbook_role,
                granted_by=user,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ HandbookAccess granted: {handbook_role} — user can now open /handbook/'
                )
            )
            return

        if HANDBOOK_ACCESS_RANK[handbook_role] > HANDBOOK_ACCESS_RANK[existing.role]:
            old_role = existing.role
            existing.role = handbook_role
            existing.granted_by = user
            existing.save(update_fields=['role', 'granted_by'])
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ HandbookAccess upgraded: {old_role} -> {handbook_role}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'ℹ HandbookAccess already exists: {existing.role} (not downgrading to {handbook_role})'
                )
            )
