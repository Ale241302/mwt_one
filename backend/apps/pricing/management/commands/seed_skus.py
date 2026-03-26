from django.core.management.base import BaseCommand
from apps.productos.models import ProductMaster
from apps.pricing.models import PriceList, PriceListItem
from apps.brands.models import Brand
from datetime import timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = 'Seed 565 SKUs + Pricelist COMEX'

    def handle(self, *args, **kwargs):
        brand, _ = Brand.objects.get_or_create(code='COMEX', defaults={'name': 'COMEX'})
        
        now = timezone.now()
        prices_list, created = PriceList.objects.get_or_create(
            brand=brand,
            name='COMEX Base Pricing',
            defaults={
                'valid_from': now,
                'valid_to': now + timedelta(days=365)
            }
        )
        
        if created:
            items_to_create = []
            for i in range(1, 566):
                sku = f"COMEX-SKU-{i:04d}"
                pm, _ = ProductMaster.objects.get_or_create(
                    brand=brand, sku=sku,
                    defaults={'name': f"Product {i}", 'hs_code': '6403.99', 'net_weight': 1.0}
                )
                items_to_create.append(PriceListItem(
                    price_list=prices_list,
                    sku=sku,
                    price=10.0 + (i % 100)
                ))
            PriceListItem.objects.bulk_create(items_to_create)

        self.stdout.write(self.style.SUCCESS('Successfully seeded 565 SKUs and COMEX pricing'))
