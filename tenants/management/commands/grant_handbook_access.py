from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from tenants.models import Tenant, UserPermission
from accounts.models import User


class Command(BaseCommand):
    help = 'Grant a user access to the Handbook (Prime Tenant) at Level 3, 4, or 5'

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
            help='Custom role (defaults to global-steward for level 5, district-steward for level 4, branch-steward for level 3)'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        user_email = options.get('user')
        level = options.get('level')
        custom_role = options.get('role')

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

        # Determine role based on level
        role_map = {
            3: 'branch-steward',
            4: 'district-steward',
            5: 'global-steward',
        }
        role = custom_role or role_map[level]

        # Check if permission already exists
        existing = UserPermission.objects.filter(
            user=user,
            tenant=handbook,
            role=role
        ).first()

        if existing:
            self.stdout.write(
                self.style.WARNING(
                    f'ℹ Permission already exists:\n'
                    f'  User: {user.display_name} ({user.email})\n'
                    f'  Tenant: {handbook.name}\n'
                    f'  Role: {existing.role}\n'
                    f'  Level: {existing.level}\n'
                )
            )
            return

        # Create permission
        perm = UserPermission.objects.create(
            user=user,
            tenant=handbook,
            role=role,
            level=level,
            tenant_path=handbook.path,
            created_by=user,  # Self-granted
            granted_by=user
        )

        access_desc = {
            3: 'Reference Library (read-only)',
            4: 'All types (read-only)',
            5: 'All types (read + write)',
        }

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Handbook access granted:\n'
                f'  User: {user.display_name} ({user.email})\n'
                f'  Tenant: {handbook.name}\n'
                f'  Role: {perm.role}\n'
                f'  Level: {perm.level}\n'
                f'  Access: {access_desc[level]}\n\n'
                f'User can now:\n'
                f'  - Navigate to /governance/\n'
                f'  - View Handbook records at their level\n'
                f'  - Create/edit records (Level 5 only)\n'
            )
        )
