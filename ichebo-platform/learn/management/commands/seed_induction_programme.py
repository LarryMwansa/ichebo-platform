"""
Seed the Level 0 Induction Programme as a system Record and re-link
the Induction Training course to it.

The existing seed_induction_course seeds the course and links it to
New Life Programme (Level 1). This command creates the proper Level 0
induction programme container and moves that link.

Structure after running:
  Induction Programme  (record_type: induction, required_level: 0)
  └── Induction Training (record_type: course)  ← part_of link

Usage:
    python manage.py seed_induction_programme
    python manage.py seed_induction_programme --force
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import User
from records.models import Record, Relationship


class Command(BaseCommand):
    help = 'Seed the Level 0 Induction Programme and link the Induction Training course to it.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Delete and re-create the induction programme record.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force = options['force']

        system_user = User.objects.filter(is_superuser=True).first()
        if not system_user:
            self.stderr.write(self.style.ERROR(
                'No superuser found. Run: python manage.py createsuperuser'
            ))
            return

        # ── Check for existing induction programme ────────────────────────
        existing = Record.objects.filter(
            record_family='learning',
            record_type='induction',
            origin='system',
            deleted_at__isnull=True,
        ).first()

        if existing and not force:
            self.stdout.write(self.style.WARNING(
                f'Induction Programme already exists: "{existing.title}" — use --force to reset.'
            ))
            return

        if existing and force:
            Relationship.objects.filter(to_record=existing).delete()
            Relationship.objects.filter(from_record=existing).delete()
            existing.delete()
            self.stdout.write('  reset existing Induction Programme')

        # ── Create the Induction Programme ────────────────────────────────
        programme = Record.objects.create(
            created_by=system_user,
            tenant=None,
            record_class='organizational',
            record_family='learning',
            record_type='induction',
            origin='system',
            title='Induction Programme',
            summary=(
                'The Level 0 entry programme for all new Kingdom members. '
                'Covers the foundations of faith, personal renewal, community life, '
                'and practical Kingdom living. Completion is required before advancing '
                'to the New Life Programme (Level 1).'
            ),
            status='active',
            custom_fields={
                'kgs_qualification': 'Induction Certificate',
                'kgs_pathways': ['new_life', 'community_life'],
                'duration': '12 weeks',
                'prerequisites': 'None — open to all new members',
            },
            permissions_data={
                'required_level': 0,
                'visibility': 'global',
                'roles_allowed': [],
                'can_edit': [],
            },
            metadata={
                'source_app': 'learn',
                'seed': True,
                'context': 'induction',
            },
        )
        self.stdout.write(self.style.SUCCESS(
            f'  create Induction Programme (record_type=induction, required_level=0)'
        ))

        # ── Link Induction Training course to this programme ──────────────
        course = Record.objects.filter(
            record_family='learning',
            record_type='course',
            origin='system',
            title='Induction Training',
            deleted_at__isnull=True,
        ).first()

        if not course:
            self.stdout.write(self.style.WARNING(
                '  Induction Training course not found — run seed_induction_course first.\n'
                '  The programme has been created but has no courses yet.'
            ))
        else:
            # Remove any existing part_of link from this course (e.g. to New Life Programme)
            removed = Relationship.objects.filter(
                from_record=course,
                relationship_type='part_of',
            ).delete()
            if removed[0]:
                self.stdout.write(f'  removed {removed[0]} old part_of link(s) from Induction Training')

            Relationship.objects.create(
                created_by=system_user,
                from_record=course,
                to_record=programme,
                direction='directed',
                relationship_type='part_of',
            )
            self.stdout.write(self.style.SUCCESS(
                '  linked Induction Training → Induction Programme (part_of)'
            ))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            'Done. Induction Programme ready. New users will be auto-enrolled on registration.'
        ))
