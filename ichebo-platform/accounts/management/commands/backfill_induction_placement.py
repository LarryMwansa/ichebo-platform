from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = 'Place all Level 0 users without an induction tenant membership into /global/induction/'

    @transaction.atomic
    def handle(self, *args, **options):
        from accounts.models import User
        from tenants.models import Tenant, UserPermission

        induction_tenant = Tenant.objects.filter(
            tier='induction', slug='induction'
        ).first()
        if not induction_tenant:
            self.stdout.write(self.style.ERROR(
                'Induction tenant not found. Run seed_induction_tenant first.'
            ))
            return

        seekers = User.objects.filter(competence_level=0)
        placed = 0
        already = 0

        for user in seekers:
            _, created = UserPermission.objects.get_or_create(
                user=user,
                tenant=induction_tenant,
                role='seeker',
                defaults={
                    'created_by': user,
                    'granted_by': user,
                    'tenant_path': induction_tenant.path,
                    'level': 0,
                    'is_active': True,
                },
            )
            if created:
                if not user.induction_enrolled_at:
                    user.induction_enrolled_at = timezone.now()
                    user.save(update_fields=['induction_enrolled_at'])
                placed += 1
            else:
                already += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Placed: {placed} new. Already placed: {already}.'
        ))
