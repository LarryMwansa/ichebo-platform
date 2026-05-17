"""
Seed the five KGS Qualification Programmes (Levels 1–5) as system Records.

Run once after initial deployment, or with --force to re-seed.
Level 0 entry is handled separately by seed_induction_course.

Usage:
    python manage.py seed_programmes
    python manage.py seed_programmes --force
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import User
from records.models import Record

PROGRAMMES = [
    {
        'title': 'New Life Programme',
        'summary': (
            'The Certificate programme for new Kingdom members. Prepares individuals '
            'for entry into Kingdom Life, establishes foundations of faith, fellowship, '
            'and a life of discipleship.'
        ),
        'required_level': 1,
        'kgs_qualification': 'Certificate',
        'kgs_pathways': ['new_life', 'community_life', 'learning'],
        'duration': '1 year',
        'prerequisites': 'Induction Training (Level 0)',
    },
    {
        'title': 'Foundation Programme',
        'summary': (
            'The flagship Diploma programme producing a well-rounded believer capable '
            'of participating and working in Kingdom and Sceptre structures. Addresses '
            'New Life, Fellowship, and Work.'
        ),
        'required_level': 2,
        'kgs_qualification': 'Diploma',
        'kgs_pathways': ['spiritual_formation', 'service', 'mission', 'learning'],
        'duration': '3 years',
        'prerequisites': 'New Life Programme (Level 1)',
    },
    {
        'title': 'Leaders Programme',
        'summary': (
            'The Degree programme for team leaders. Develops leadership competence, '
            'teaching skills, mobilisation approaches, and introduction to Kingdom networks.'
        ),
        'required_level': 3,
        'kgs_qualification': 'Degree',
        'kgs_pathways': ['leadership', 'service', 'learning'],
        'duration': '6–12 months',
        'prerequisites': 'Foundation Programme (Level 2)',
    },
    {
        'title': 'Builders Programme',
        'summary': (
            'The Masters programme for Network Stewards. Develops Kingdom networks, '
            'introduces working documents and calendars, and includes research on '
            'Kingdom mobilisation.'
        ),
        'required_level': 4,
        'kgs_qualification': 'Masters',
        'kgs_pathways': ['leadership', 'apostolic_stewardship'],
        'duration': '6–12 months',
        'prerequisites': 'Leaders Programme (Level 3)',
    },
    {
        'title': "Architect's Programme",
        'summary': (
            'The Doctorate programme for Apostolic Stewards. Develops working documents '
            'and the next 7-year Kingdom instance. The capstone of the formation stack.'
        ),
        'required_level': 5,
        'kgs_qualification': 'Doctorate',
        'kgs_pathways': ['leadership', 'apostolic_stewardship'],
        'duration': '2 years',
        'prerequisites': 'Builders Programme (Level 4)',
    },
]


class Command(BaseCommand):
    help = 'Seed the five KGS Qualification Programmes (Levels 1–5) as system Records.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Delete and re-create existing programme records.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force = options['force']

        system_user = User.objects.filter(is_superuser=True).first()
        if not system_user:
            self.stderr.write(self.style.ERROR(
                'No superuser found. Create one first: python manage.py createsuperuser'
            ))
            return

        created = 0
        skipped = 0

        for prog in PROGRAMMES:
            existing = Record.objects.filter(
                record_family='learning',
                record_type='programme',
                origin='system',
                title=prog['title'],
                deleted_at__isnull=True,
            ).first()

            if existing and not force:
                self.stdout.write(f'  skip  {prog["title"]} (already exists — use --force to reset)')
                skipped += 1
                continue

            if existing and force:
                existing.delete()
                self.stdout.write(f'  reset {prog["title"]}')

            Record.objects.create(
                created_by=system_user,
                tenant=None,
                record_class='organizational',
                record_family='learning',
                record_type='programme',
                origin='system',
                title=prog['title'],
                summary=prog['summary'],
                status='active',
                custom_fields={
                    'kgs_qualification': prog['kgs_qualification'],
                    'kgs_pathways': prog['kgs_pathways'],
                    'duration': prog['duration'],
                    'prerequisites': prog['prerequisites'],
                },
                permissions_data={
                    'required_level': prog['required_level'],
                    'visibility': 'global',
                    'roles_allowed': [],
                    'can_edit': [],
                },
                metadata={
                    'source_app': 'learn',
                    'seed': True,
                },
            )
            self.stdout.write(self.style.SUCCESS(
                f'  create {prog["title"]} (Level {prog["required_level"]} — {prog["kgs_qualification"]})'
            ))
            created += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done. {created} programme(s) created, {skipped} skipped.'
        ))
