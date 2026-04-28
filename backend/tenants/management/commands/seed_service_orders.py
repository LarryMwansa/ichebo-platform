from django.core.management.base import BaseCommand
from django.db import transaction
from tenants.models import ServiceOrder


SERVICE_ORDERS = [
    # Apostolic & Spiritual Ministry
    (1,  'order-of-apostolic-service',        'Order of Apostolic Service',        'Apostolic & Spiritual Ministry', 'Office of Apostolic Stewardship'),
    (2,  'order-of-prophetic-ministry',        'Order of Prophetic Ministry',        'Apostolic & Spiritual Ministry', 'Office of Prophetic Discernment'),
    (3,  'order-of-teaching-and-doctrine',     'Order of Teaching and Doctrine',     'Apostolic & Spiritual Ministry', 'Office of Prophetic Discernment'),
    (4,  'order-of-prayer-and-intercession',   'Order of Prayer and Intercession',   'Apostolic & Spiritual Ministry', 'Office of Prophetic Discernment'),
    # Leadership & Governance Support
    (5,  'order-of-governance-support',        'Order of Governance Support',        'Leadership & Governance Support', 'Office of Governance and Policy'),
    (6,  'order-of-strategic-coordination',    'Order of Strategic Coordination',    'Leadership & Governance Support', 'Office of Strategic Development'),
    (7,  'order-of-leadership-assistance',     'Order of Leadership Assistance',     'Leadership & Governance Support', 'Office of Strategic Development'),
    (8,  'order-of-communication-alignment',   'Order of Communication and Alignment', 'Leadership & Governance Support', 'Office of Strategic Development'),
    # Formation & Teaching
    (9,  'order-of-discipleship-facilitation', 'Order of Discipleship Facilitation', 'Formation & Teaching', 'Office of Discipleship Formation'),
    (10, 'order-of-training-and-instruction',  'Order of Training and Instruction',  'Formation & Teaching', 'Office of Leadership Development'),
    (11, 'order-of-mentorship-and-coaching',   'Order of Mentorship and Coaching',   'Formation & Teaching', 'Office of Leadership Development'),
    (12, 'order-of-curriculum-development',    'Order of Curriculum Development',    'Formation & Teaching', 'Office of Leadership Development'),
    # Mission & Outreach
    (13, 'order-of-evangelism',                'Order of Evangelism',                'Mission & Outreach', 'Office of Learning and Qualifications'),
    (14, 'order-of-mission-teams',             'Order of Mission Teams',             'Mission & Outreach', 'Office of Ministry Programmes'),
    (15, 'order-of-community-outreach',        'Order of Community Outreach',        'Mission & Outreach', 'Office of Ministry Programmes'),
    (16, 'order-of-expansion-and-planting',    'Order of Expansion and Planting',    'Mission & Outreach', 'Office of Ministry Programmes'),
    # Community Life & Care
    (17, 'order-of-pastoral-care',             'Order of Pastoral Care',             'Community Life & Care', 'Office of Mission Mobilisation'),
    (18, 'order-of-community-building',        'Order of Community Building',        'Community Life & Care', 'Office of Community Networks'),
    (19, 'order-of-hospitality-and-welcome',   'Order of Hospitality and Welcome',   'Community Life & Care', 'Office of Community Networks'),
    (20, 'order-of-welfare-and-support',       'Order of Welfare and Support',       'Community Life & Care', 'Office of Community Networks'),
    # Operations & Stewardship
    (21, 'order-of-administration',            'Order of Administration',            'Operations & Stewardship', 'Office of Operations and Administration'),
    (22, 'order-of-resource-management',       'Order of Resource Management',       'Operations & Stewardship', 'Office of Resource Stewardship'),
    (23, 'order-of-logistics-and-events',      'Order of Logistics and Events',      'Operations & Stewardship', 'Office of Resource Stewardship'),
    (24, 'order-of-media-and-communication',   'Order of Media and Communication',   'Operations & Stewardship', 'Office of Resource Stewardship'),
]


class Command(BaseCommand):
    help = 'Seed the 24 constitutional Service Orders (fixed controlled vocabulary for UserPermission.metadata.service_order).'

    @transaction.atomic
    def handle(self, *args, **options):
        created_count = 0
        for number, slug, name, domain, office in SERVICE_ORDERS:
            order, created = ServiceOrder.objects.get_or_create(
                order_number=number,
                defaults={
                    'slug': slug,
                    'name': name,
                    'domain': domain,
                    'office': office,
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  {number:2}. {name}'))
            else:
                self.stdout.write(f'  {number:2}. {name} (exists)')

        total = ServiceOrder.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'\n{created_count} orders created. {total}/24 total in database.'
        ))
