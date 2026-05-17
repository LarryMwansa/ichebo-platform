from django.core.management.base import BaseCommand
from django.db import transaction
from tenants.models import Tenant
from accounts.models import User


AGENCY_TENANTS = [
    {
        'slug': 'apostolic-ministry',
        'name': 'Apostolic & Spiritual Ministry',
        'description': (
            'Governs apostolic service, prophetic ministry, teaching & doctrine, '
            'and prayer & intercession across the Kingdom. Orders 1–4.'
        ),
    },
    {
        'slug': 'leadership-governance',
        'name': 'Leadership & Governance Support',
        'description': (
            'Governs governance policy, strategic coordination, leadership assistance, '
            'and communication & alignment. Orders 5–8.'
        ),
    },
    {
        'slug': 'formation-teaching',
        'name': 'Formation & Teaching',
        'description': (
            'Governs discipleship facilitation, training & instruction, mentorship & coaching, '
            'and curriculum development. Authority over all induction and formation decisions. Orders 9–12.'
        ),
    },
    {
        'slug': 'mission-outreach',
        'name': 'Mission & Outreach',
        'description': (
            'Governs evangelism, mission teams, community outreach, '
            'and expansion & planting. Orders 13–16.'
        ),
    },
    {
        'slug': 'community-life-care',
        'name': 'Community Life & Care',
        'description': (
            'Governs pastoral care, community building, hospitality & welcome, '
            'and welfare & support. Orders 17–20.'
        ),
    },
    {
        'slug': 'operations-stewardship',
        'name': 'Operations & Stewardship',
        'description': (
            'Governs administration, resource management, logistics & events, '
            'and media & communication. Orders 21–24.'
        ),
    },
]


class Command(BaseCommand):
    help = (
        'Seed the Prime Tenancy (root global tenant) and the 6 constitutional '
        'Agency Tenants (Service Domains) under it.'
    )

    @transaction.atomic
    def handle(self, *args, **options):
        system_user = User.objects.filter(is_superuser=True).first()
        if not system_user:
            self.stdout.write(self.style.ERROR(
                'No superuser found. Create one first:\n  python manage.py createsuperuser'
            ))
            return

        # --- Prime Tenancy ---
        prime, created = Tenant.objects.get_or_create(
            slug='prime',
            defaults={
                'name': 'Prime Tenancy',
                'path': '/global/',
                'tier': 'global',
                'affiliation': 'ichebo',
                'status': 'active',
                'is_collective': False,
                'is_agency': True,
                'created_by': system_user,
                'description': (
                    'The apex governing body of the Kingdom Governance System. '
                    'Holds executive privilege over all service domains when no '
                    'domain steward is active. Cannot be deleted or modified via UI.'
                ),
                'settings_data': {
                    'allow_public_records': False,
                    'require_approval': False,
                    'max_members': None,
                },
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'  Created: Prime Tenancy ({prime.path})'))
        else:
            self.stdout.write(self.style.WARNING(f'  Exists:  Prime Tenancy ({prime.path})'))

        # --- 6 Agency Tenants ---
        for data in AGENCY_TENANTS:
            slug = data['slug']
            path = f'/global/{slug}/'
            agency, created = Tenant.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': data['name'],
                    'path': path,
                    'tier': 'global',
                    'affiliation': 'ichebo',
                    'status': 'active',
                    'is_collective': False,
                    'is_agency': True,
                    'parent': prime,
                    'created_by': system_user,
                    'description': data['description'],
                    'settings_data': {
                        'allow_public_records': False,
                        'require_approval': False,
                        'max_members': None,
                    },
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created: {agency.name} ({agency.path})'))
            else:
                self.stdout.write(self.style.WARNING(f'  Exists:  {agency.name} ({agency.path})'))

        self.stdout.write(self.style.SUCCESS('\nPrime Tenancy and agency tenants ready.'))
        self.stdout.write(
            'Executive Privilege: Prime Tenancy acts for any unstaffed domain automatically.'
        )
