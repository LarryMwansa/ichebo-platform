"""
Seed the Induction Training course and its four lessons inside the
New Life Programme.

Structure created:
  New Life Programme (record_type: programme)
  └── Induction Training (record_type: course)   ← linked via part_of
        ├── Keys To the Kingdom                  (record_type: lesson)
        ├── Repentance & Reformation              (record_type: lesson)
        ├── Community Programme                   (record_type: lesson)
        └── The Secret of Living a Fulfilled Life (record_type: lesson)

Run after seed_programmes:
    python manage.py seed_induction_course
    python manage.py seed_induction_course --force
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import User
from records.models import Record, Relationship

LESSONS = [
    {
        'title': 'Keys To the Kingdom',
        'summary': (
            'The Foundation of Faith. Establishes the core Kingdom principles '
            'that underpin all subsequent formation.'
        ),
        'kgs_pathway_focus': 'new_life',
    },
    {
        'title': 'Repentance & Reformation',
        'summary': (
            'The Reconditioning pathway module. Addresses personal renewal, '
            'turning from the old life, and aligning with Kingdom values.'
        ),
        'kgs_pathway_focus': 'new_life',
    },
    {
        'title': 'Community Programme',
        'summary': (
            'Introduction to Sceptre Community life: how Kingdom communities '
            'operate, the covenant of fellowship, and the member\'s place within it.'
        ),
        'kgs_pathway_focus': 'community_life',
    },
    {
        'title': 'The Secret of Living a Fulfilled Life (HAL Beginners)',
        'summary': (
            'Practical formation in the HAF Framework basics. Living a purposeful, '
            'fruitful life as a Kingdom citizen.'
        ),
        'kgs_pathway_focus': 'new_life',
    },
]


class Command(BaseCommand):
    help = 'Seed the Induction Training course + 4 lessons inside New Life Programme.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Delete and re-create existing induction course and lessons.',
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

        # Locate the New Life Programme
        new_life = Record.objects.filter(
            record_family='learning',
            record_type='programme',
            origin='system',
            title='New Life Programme',
            deleted_at__isnull=True,
        ).first()

        if not new_life:
            self.stderr.write(self.style.ERROR(
                'New Life Programme not found. Run seed_programmes first:\n'
                '  python manage.py seed_programmes'
            ))
            return

        # Check for existing Induction Training course
        existing_course = Record.objects.filter(
            record_family='learning',
            record_type='course',
            origin='system',
            title='Induction Training',
            deleted_at__isnull=True,
        ).first()

        if existing_course and not force:
            self.stdout.write(self.style.WARNING(
                'Induction Training course already exists. Use --force to reset.'
            ))
            return

        if existing_course and force:
            # Remove lesson relationships and lesson records linked to this course
            lesson_ids = Relationship.objects.filter(
                to_record=existing_course,
                relationship_type='part_of',
            ).values_list('from_record_id', flat=True)
            Record.objects.filter(id__in=lesson_ids).delete()
            Relationship.objects.filter(to_record=existing_course).delete()
            Relationship.objects.filter(from_record=existing_course).delete()
            existing_course.delete()
            self.stdout.write('  reset Induction Training course and lessons')

        # Create the Induction Training course
        course = Record.objects.create(
            created_by=system_user,
            tenant=None,
            record_class='organizational',
            record_family='learning',
            record_type='course',
            origin='system',
            title='Induction Training',
            summary=(
                '12-week formation course for all new entrants, regardless of background. '
                'Four lessons cover the foundation of faith, personal renewal, community '
                'life, and practical Kingdom living. All four lessons are required for '
                'all entrant types.'
            ),
            status='active',
            custom_fields={
                'duration': '12 weeks',
                'kgs_pathways': ['new_life', 'community_life'],
                'all_lessons_required': True,
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
            },
        )
        self.stdout.write(self.style.SUCCESS('  create Induction Training (course)'))

        # Link course to New Life Programme via part_of
        Relationship.objects.create(
            created_by=system_user,
            from_record=course,
            to_record=new_life,
            direction='directed',
            relationship_type='part_of',
        )
        self.stdout.write('         linked → New Life Programme (part_of)')

        # Create each lesson and link to the course
        for i, lesson_data in enumerate(LESSONS, start=1):
            lesson = Record.objects.create(
                created_by=system_user,
                tenant=None,
                record_class='organizational',
                record_family='learning',
                record_type='lesson',
                origin='system',
                title=lesson_data['title'],
                summary=lesson_data['summary'],
                status='active',
                custom_fields={
                    'kgs_pathway_focus': lesson_data['kgs_pathway_focus'],
                    'lesson_order': i,
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
                },
            )
            Relationship.objects.create(
                created_by=system_user,
                from_record=lesson,
                to_record=course,
                direction='directed',
                relationship_type='part_of',
            )
            self.stdout.write(self.style.SUCCESS(
                f'  create lesson {i}: {lesson_data["title"]}'
            ))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            'Done. Induction Training course + 4 lessons created and linked to New Life Programme.'
        ))
