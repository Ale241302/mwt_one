import random
from django.core.management.base import BaseCommand
from apps.clientes.models import ClientSubsidiary

class Command(BaseCommand):
    help = 'P0: Populates legal_name and tax_id for existing subsidiaries.'

    def handle(self, *args, **options):
        subsidiaries = ClientSubsidiary.objects.all()
        count = 0
        for sub in subsidiaries:
            updated = False
            if not sub.legal_name:
                sub.legal_name = f"{sub.name} S.A."
                updated = True
            if not sub.tax_id:
                # Mock tax_id format: XX-XXXXXXXX-X
                sub.tax_id = f"{random.randint(10, 99)}-{random.randint(10000000, 99999999)}-{random.randint(0, 9)}"
                updated = True
            
            if updated:
                sub.save()
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {count} subsidiaries with legal data.'))
