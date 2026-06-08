from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = 'Manually verify a user account by email address'

    def add_arguments(self, parser):
        parser.add_argument(
            'email', nargs='?', type=str, default=None,
            help='Email address of the user to verify',
        )
        parser.add_argument(
            '--list-pending',
            action='store_true',
            help='List all users currently pending verification instead of verifying one',
        )

    def handle(self, *args, **options):
        from accounts.models import User

        if options['list_pending'] or not options['email']:
            pending = User.objects.filter(status='pending_verification').order_by('date_joined')
            if not pending.exists():
                self.stdout.write(self.style.SUCCESS('No users pending verification.'))
                return
            self.stdout.write(self.style.WARNING(f'{pending.count()} user(s) pending verification:\n'))
            for u in pending:
                self.stdout.write(f'  {u.email}  (joined {u.date_joined.strftime("%Y-%m-%d %H:%M")})')
            return

        email = options['email'].strip().lower()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise CommandError(f'No user found with email: {email}')

        if user.status != 'pending_verification':
            self.stdout.write(
                self.style.WARNING(f'{email} is already verified (status: {user.status}). No change made.')
            )
            return

        user.status = 'seeker'
        user.save(update_fields=['status'])

        # Consume any outstanding verification tokens so they cannot be replayed
        user.verification_tokens.all().delete()

        self.stdout.write(self.style.SUCCESS(
            f'✓ {email} verified. Status set to seeker. Outstanding tokens cleared.'
        ))
