from django.core.management.base import BaseCommand
from apps.agreements.models import BrandWorkflowPolicy, TransitionPolicy
from apps.brands.models import Brand
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Seed MLV/TCM workflow policies'

    def handle(self, *args, **kwargs):
        mlv, _ = Brand.objects.get_or_create(code='MLV', defaults={'name': 'MLV'})
        tcm, _ = Brand.objects.get_or_create(code='TCM', defaults={'name': 'TCM'})

        now = timezone.now()

        # MLV Policy
        mlv_policy, _ = BrandWorkflowPolicy.objects.get_or_create(
            brand=mlv,
            status='active'
        )
        
        # Add basic transitions
        TransitionPolicy.objects.get_or_create(
            policy=mlv_policy,
            from_state='REGISTRO',
            to_state='OC',
            command='C3'
        )

        # TCM Policy
        tcm_policy, _ = BrandWorkflowPolicy.objects.get_or_create(
            brand=tcm,
            status='active'
        )

        TransitionPolicy.objects.get_or_create(
            policy=tcm_policy,
            from_state='REGISTRO',
            to_state='PROFORMA',
            command='C2'
        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded MLV and TCM workflow policies'))
